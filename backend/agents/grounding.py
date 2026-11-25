"""Tariff-Grounding Agent (SCRUM-31): compares a bill's printed charges to
the deterministic engine's expected amounts (SCRUM-29) and produces a
`Finding` for each real discrepancy, each backed by a retrieved tariff
clause (SCRUM-30). A discrepancy with no verifiable clause is dropped
before the LLM ever sees it — citation verification is a gate in code,
not a prompt instruction the model could ignore.

Known gap, not a bug: the tariff JSON's `adjustments` hold only the
Quarterly Tariff Adjustment (QTA), four time-bounded windows covering
December 2025 to November 2026 (data/tariffs/raw/sources.md S07 and
S10-S12), for non-lifeline, non-prepaid consumers. The engine skips it,
with a warning, for any bill whose `billing_month` is outside every
window or isn't known.
FCA/FPA (changes monthly, no single rate to record) and the FC/NJ
surcharges (slab-dependent, published as ranges) still have no engine
counterpart anywhere. Bill charge lines for those — and compound lines
like "GST on FPA" — are left unmatched by `_match_component`, so this
agent correctly produces no finding for them, rather than guessing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from config import settings
from models.bill import BillExtraction
from models.finding import Finding, FindingsResponse
from services.gemini import GeminiError, extract_text, get_llm, invoke_with_retry
from services.tariff_engine import BillCalculation
from services.tariff_retrieval import retrieve

PROMPT_VERSION = "v1"
RETRY_ATTEMPTS = 1

# Below this cosine similarity, the retrieved chunk isn't a reliable enough
# citation to show the user — the finding is dropped, not shown uncited.
MIN_CITATION_SIMILARITY = 0.3

# A matched component within this many rupees of the billed amount isn't a
# discrepancy. Same order of magnitude as the engine's own
# DEFAULT_TOLERANCE_PKR (tariff_engine.py), but per matched charge line
# rather than the whole bill total; provisional until checked against more
# real bills.
TOLERANCE_PKR = 1.0

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_PROMPT_PATH = _REPO_ROOT / "prompts" / "grounding" / f"{PROMPT_VERSION}.md"

# Normalized bill charge-line wording -> canonical component key.
# "Canonical key" is either "energy"/"fixed" (the engine's own fields) or
# the slug of a tax/adjustment's name in the tariff JSON (e.g. "gst").
_CHARGE_NAME_ALIASES: dict[str, str] = {
    "cost of electricity": "energy",
    "energy charges": "energy",
    "energy charge": "energy",
    "units charges": "energy",
    "electricity charges": "energy",
    "fixed charges": "fixed",
    "fixed charge": "fixed",
    "meter rent": "fixed",
    "service rent": "fixed",
    "electricity duty": "electricity_duty",
    "e d": "electricity_duty",
    "gst": "gst",
    "general sales tax": "gst",
    "sales tax": "gst",
    "quarterly tariff adjustment": "qta",
    "qtr tariff adjustment": "qta",
    "qta": "qta",
}

# A tax/adjustment's own name in the tariff JSON resolves to its canonical
# key by keyword, not by exact phrase — unlike _CHARGE_NAME_ALIASES above,
# which must stay exact (a bill's "GST" and "GST on FPA" are different
# charges and must never collide into the same key). This only matters
# for the one name on the JSON side, so a looser match is safe and keeps
# the key stable if the tariff JSON's exact wording changes.
_ADJUSTMENT_KEY_KEYWORDS: list[tuple[str, str]] = [
    ("quarterly tariff adjustment", "qta"),
    ("qta", "qta"),
]


def _canonical_component_key(name: str) -> str:
    normalized = _normalize_charge_name(name)
    for keyword, key in _ADJUSTMENT_KEY_KEYWORDS:
        if keyword in normalized:
            return key
    return _slug(name)


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text()


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def _normalize_charge_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.strip().lower()).strip()


def _money(amount: float) -> float:
    return round(amount, 2) + 0.0


def _expected_components(calculation: BillCalculation) -> dict[str, tuple[str, float]]:
    """Map canonical key -> (display name, expected amount) for everything
    the engine actually computed for this bill."""
    components: dict[str, tuple[str, float]] = {
        "energy": ("Energy charges", calculation.energy_charge_pkr),
        "fixed": ("Fixed charges", calculation.fixed_charge_pkr),
    }
    for item in (*calculation.adjustments, *calculation.taxes):
        components[_canonical_component_key(item.name)] = (item.name, item.amount_pkr)
    return components


def _match_component(
    charge_name: str, components: dict[str, tuple[str, float]]
) -> tuple[str, float] | None:
    """Find the engine component a bill charge line is about, if any.

    Returns None for a charge the engine doesn't model yet (FPA, FC/NJ
    surcharges, "GST on FPA" style compound lines) rather than guessing —
    there's no deterministic expected amount to compare against.
    """
    canonical = _CHARGE_NAME_ALIASES.get(_normalize_charge_name(charge_name))
    if canonical is None:
        canonical = _slug(charge_name)
    return components.get(canonical)


# Tax and adjustment components -> the one clause row that may be cited.
_COMPONENT_ROW_LABELS = {
    "gst": "General Sales Tax (GST)",
    "electricity_duty": "Electricity Duty (ED)",
    "qta": "Quarterly Tariff Adjustment (QTA)",
}


def _citation_filter(
    display_name: str, expected_amount: float, calculation: BillCalculation
) -> dict[str, str]:
    """Which clause rows may be cited for a component.

    Similarity ranking alone cites neighbouring tariffs' rows, so the row is
    pinned down exactly: energy and fixed charges to this tariff's row that
    prints the rate the engine used; taxes and the QTA to their own line.
    Electricity Duty varies by category, so its row must also state the
    percentage the engine applied.
    """
    if display_name in ("Energy charges", "Fixed charges"):
        filters = {"tariff_code": calculation.tariff_code}
        lines = calculation.slab_lines
        if lines:
            # The fixed charge sits on the landing slab's row, or the peak row
            # for TOU (the guide's off-peak rows say "included above").
            peak_row = display_name == "Fixed charges" and calculation.metering_type == "tou"
            rate = lines[0 if peak_row else -1].rate_per_unit_pkr
            filters["contains"] = f"{rate:.2f}"
        return filters

    key = _canonical_component_key(display_name)
    if key not in _COMPONENT_ROW_LABELS:
        return {}
    filters = {"row_label": _COMPONENT_ROW_LABELS[key]}
    if key == "electricity_duty" and calculation.energy_charge_pkr:
        percent = round(expected_amount / calculation.energy_charge_pkr * 100, 1)
        filters["contains"] = f"{percent:g}%"
    return filters


def _confidence(score: float) -> Literal["high", "medium", "low"]:
    if score >= 0.65:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _phrase_finding(
    charge_name: str,
    billed_amount_pkr: float,
    expected_amount_pkr: float,
    difference_pkr: float,
    clause_text: str,
) -> str:
    """Ask Gemini to phrase the discrepancy per prompts/grounding/v1.md.

    Falls back to a plain deterministic sentence if the Gemini call fails,
    so a transient model error doesn't silently drop a finding that the
    engine and retrieval have already verified.
    """
    message = {
        "role": "user",
        "content": (
            f"{_load_prompt()}\n\n"
            f"Charge: {charge_name}\n"
            f"Billed amount: Rs. {billed_amount_pkr:.2f}\n"
            f"Expected amount: Rs. {expected_amount_pkr:.2f}\n"
            f"Difference (billed minus expected): Rs. {difference_pkr:.2f}\n"
            f"Retrieved clause text:\n{clause_text}"
        ),
    }
    try:
        llm = get_llm(temperature=0.2)
        response = invoke_with_retry(llm, [message])
        text = extract_text(response).strip()
        if text:
            return text
    except GeminiError:
        pass

    direction = "more" if difference_pkr > 0 else "less"
    return (
        f"The billed {charge_name} (Rs. {billed_amount_pkr:.2f}) is "
        f"Rs. {abs(difference_pkr):.2f} {direction} than the published "
        f"tariff clause would expect (Rs. {expected_amount_pkr:.2f})."
    )


def ground_bill(
    bill_id: str, extraction: BillExtraction, calculation: BillCalculation
) -> FindingsResponse:
    """Compare a bill's printed charges to the engine's expected amounts.

    Every finding is backed by a clause row matched exactly to the charge
    (see _citation_filter), or failing that one with at least
    MIN_CITATION_SIMILARITY similarity; anything else is dropped before
    the LLM phrasing step runs, per Part A rule 2 ("every finding must
    cite a real clause").
    """
    components = _expected_components(calculation)
    findings: list[Finding] = []

    for charge in extraction.charges:
        match = _match_component(charge.name, components)
        if match is None:
            continue

        display_name, expected_amount = match
        difference = _money(charge.amount_pkr - expected_amount)
        if abs(difference) <= TOLERANCE_PKR:
            continue

        query = f"What is the {display_name} for {calculation.tariff_code}?"
        filters = _citation_filter(display_name, expected_amount, calculation)
        results = retrieve(
            query,
            calculation.disco,
            top_k=3,
            billing_month=extraction.billing_month,
            **filters,
        )
        # No verifiable clause: drop, don't show uncited. An exact row match
        # is the verification; without one, similarity has to clear the bar.
        if not results or (not filters and results[0].score < MIN_CITATION_SIMILARITY):
            continue

        best = results[0]
        # The tariff file's own link (SRO 279) prints the rate rows, not the
        # taxes. A tax clause without its own source has nothing to link to.
        if "row_label" in filters and best.chunk.source_url is None:
            continue
        explanation = _phrase_finding(
            charge.name, charge.amount_pkr, expected_amount, difference, best.chunk.text
        )

        findings.append(
            Finding(
                charge_name=charge.name,
                billed_amount_pkr=charge.amount_pkr,
                expected_amount_pkr=expected_amount,
                difference_pkr=difference,
                clause_id=best.chunk.clause_id,
                clause_text=best.chunk.text,
                explanation=explanation,
                source_url=best.chunk.source_url or str(calculation.source.url),
                confidence="high" if filters else _confidence(best.score),
            )
        )

    return FindingsResponse(
        bill_id=bill_id,
        findings=findings,
        recalculated_total_pkr=calculation.total_pkr,
        model=settings.gemini_model,
    )
