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
from models.tariff import DISCO, TariffCalculationInput, TariffSchedule
from services.charge_names import CHARGE_NAME_ALIASES, is_surcharge, normalize_charge_name
from services.tariff_engine import TariffEngineError, calculate_bill, select_tariff

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
# schema yet (SCRUM-51), and only A-1(a) splits its rates by it. See
# resolve_consumer_status for what can be worked out from one bill.
_STATUS_SPLIT_CODE = "A-1(a)"

# Protected status requires staying at or below this for six months, so a
# month above it can only be billed as unprotected.
_PROTECTED_MAX_UNITS = 200

# Same per-line tolerance as the grounding agent.
_ENERGY_MATCH_TOLERANCE_PKR = 1.0


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
    """Returns (input, warnings). For A-1(a), pass the input through
    `resolve_consumer_status` before `select_tariff`."""
    if extraction.units_consumed is None:
        raise TariffEngineError("bill has no units_consumed; cannot recalculate")
    if extraction.sanctioned_load_kw is None:
        raise TariffEngineError("bill has no sanctioned_load_kw; cannot recalculate")

    warnings: list[str] = []
    calc_input = TariffCalculationInput(
        disco=disco,
        tariff_code=tariff_code,
        monthly_units=extraction.units_consumed,
        sanctioned_load_kw=extraction.sanctioned_load_kw,
        billing_month=extraction.billing_month,
        billed_surcharges_pkr=sum(
            charge.amount_pkr for charge in extraction.charges if is_surcharge(charge.name)
        ),
    )
    if extraction.billing_month is None:
        warnings.append(
            "bill has no billing_month; any time-bounded tariff adjustment "
            "(e.g. the current quarter's QTA) will be skipped rather than guessed."
        )
    return calc_input, warnings


def resolve_consumer_status(
    extraction: BillExtraction,
    calc_input: TariffCalculationInput,
    schedules: list[TariffSchedule],
) -> tuple[TariffCalculationInput, list[str], frozenset[str]]:
    """Fill in `consumer_status` for A-1(a).

    Returns (input, warnings, unverifiable), where `unverifiable` names the
    components that must not be flagged because the status is unknown.
    Over 200 units it is unprotected. Otherwise it is taken from whichever
    status's rates reproduce the printed energy charge, if exactly one does.
    That reads the utility's classification; it cannot check it.
    """
    if calc_input.tariff_code != _STATUS_SPLIT_CODE:
        return calc_input, [], frozenset()

    units = calc_input.monthly_units
    if units > _PROTECTED_MAX_UNITS:
        warning = f"treated as unprotected: {units:g} units is above {_PROTECTED_MAX_UNITS}"
        return calc_input.model_copy(update={"consumer_status": "unprotected"}), [warning], frozenset()

    printed = [
        charge.amount_pkr
        for charge in extraction.charges
        if CHARGE_NAME_ALIASES.get(normalize_charge_name(charge.name)) == "energy"
    ]
    matches = []
    for status in ("lifeline", "protected", "unprotected"):
        candidate = calc_input.model_copy(update={"consumer_status": status})
        try:
            energy = calculate_bill(select_tariff(schedules, candidate), candidate).energy_charge_pkr
        except TariffEngineError:
            continue  # e.g. lifeline does not reach this many units
        if len(printed) == 1 and abs(printed[0] - energy) <= _ENERGY_MATCH_TOLERANCE_PKR:
            matches.append(candidate)

    if len(matches) == 1:
        warning = (
            f"treated as {matches[0].consumer_status}: the printed energy charge matches "
            "that rate. Whether this is the right category for you was not checked."
        )
        return matches[0], [warning], frozenset()

    unverifiable = {"energy", "fixed", "gst", "electricity_duty"}
    if units <= 100:
        unverifiable.add("qta")  # lifeline consumers are exempt from it
    warning = (
        "could not tell whether this is a lifeline, protected or unprotected consumer, "
        "so charges that depend on it were not checked. The recalculated total assumes protected."
    )
    return (
        calc_input.model_copy(update={"consumer_status": "protected"}),
        [warning],
        frozenset(unverifiable),
    )
