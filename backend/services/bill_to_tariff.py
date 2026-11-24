"""Bridges a `BillExtraction` to the tariff engine's `TariffCalculationInput`
(SCRUM-31's `/findings` endpoint glue, between SCRUM-29's engine and
SCRUM-10's extraction schema).

Best-effort by design: a bill the engine genuinely can't place raises
`TariffEngineError`, which the endpoint turns into a 422, rather than
guessing a tariff and silently producing a wrong recalculation.
"""

from __future__ import annotations

import re

from models.bill import BillExtraction
from models.tariff import DISCO, TariffCalculationInput
from services.tariff_engine import TariffEngineError

_DISCO_ALIASES: dict[str, DISCO] = {
    "k-electric": "K-Electric",
    "k-electric (ke)": "K-Electric",
    "ke": "K-Electric",
    "iesco": "IESCO",
    "lesco": "LESCO",
}

# "A-1a(01)" (how the Extraction Agent writes a category it read off a bill)
# -> letter "A", number "1", sub-letter "a". Also accepts the tariff JSON's
# own already-bracketed form ("A-1(a)") via the optional parens. Codes with
# no sub-letter ("B-3", "G", "K") don't match the sub-letter group and pass
# through unchanged.
_CODE_RE = re.compile(r"^([A-Za-z]+)-?(\d+)\(?([a-zA-Z]?)\)?")

# Consumer status (lifeline/protected/unprotected) isn't in the extraction
# schema yet — a gap, not a design choice; see docs/decisions.md
# (2026-11-25). A-1(a) is the one code where NEPRA's structured tariff JSON
# actually splits by status, so leaving it unset means "no tariff matches"
# for every A-1(a) bill. Default to 'protected', NEPRA's standard
# residential safeguard category and what the Sprint 1 sample bills turn
# out to be, and surface the assumption as a warning rather than hide it.
_STATUS_GUESS: dict[str, str] = {"A-1(a)": "protected"}


def normalize_disco(provider: str | None) -> DISCO:
    disco = _DISCO_ALIASES.get((provider or "").strip().lower())
    if disco is None:
        raise TariffEngineError(
            f"'{provider}' is not a supported DISCO this sprint "
            "(K-Electric, IESCO, LESCO only)."
        )
    return disco


def normalize_tariff_code(tariff_category: str | None) -> str:
    if not tariff_category:
        raise TariffEngineError("bill has no tariff_category; cannot select a tariff")

    match = _CODE_RE.match(tariff_category.strip())
    if not match:
        return tariff_category.strip()

    letter, number, sub_letter = match.groups()
    if not sub_letter:
        return f"{letter.upper()}-{number}"
    return f"{letter.upper()}-{number}({sub_letter.lower()})"


def build_calculation_input(
    extraction: BillExtraction, disco: DISCO, tariff_code: str
) -> tuple[TariffCalculationInput, list[str]]:
    """Returns (input, warnings) ready for `select_tariff`/`calculate_bill`."""
    if extraction.units_consumed is None:
        raise TariffEngineError("bill has no units_consumed; cannot recalculate")
    if extraction.sanctioned_load_kw is None:
        raise TariffEngineError("bill has no sanctioned_load_kw; cannot recalculate")

    warnings: list[str] = []
    consumer_status = _STATUS_GUESS.get(tariff_code)
    if consumer_status is not None:
        warnings.append(
            "consumer_status is not in the extraction schema yet; assumed "
            f"'{consumer_status}' for tariff {tariff_code}, which may be wrong "
            "for this specific consumer."
        )

    calc_input = TariffCalculationInput(
        disco=disco,
        tariff_code=tariff_code,
        monthly_units=extraction.units_consumed,
        sanctioned_load_kw=extraction.sanctioned_load_kw,
        consumer_status=consumer_status,
    )
    return calc_input, warnings
