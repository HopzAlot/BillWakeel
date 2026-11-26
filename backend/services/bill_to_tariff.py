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
from services.charge_names import is_surcharge, normalize_charge_name
from services.tariff_engine import TariffEngineError

# "A-1a(01)" (how the Extraction Agent writes a category it read off a bill)
# -> letter "A", number "1", sub-letter "a". Also accepts the tariff JSON's
# own already-bracketed form ("A-1(a)") via the optional parens. Codes with
# no sub-letter ("B-3", "G", "K") don't match the sub-letter group and pass
# through unchanged.
_CODE_RE = re.compile(r"^([A-Za-z]+)-?(\d+)\(?([a-zA-Z]?)\)?")

# Consumer status (lifeline/protected/unprotected) isn't in the extraction
# schema yet (SCRUM-51), and only A-1(a) splits its rates by it. Until it is,
# nothing that depends on it is checked: guessing it raised false findings.
_STATUS_SPLIT_CODE = "A-1(a)"
_PROTECTED_MAX_UNITS = 200


# Bills print the company's full name, often with "Ltd" or the short code
# in brackets, so these are matched anywhere in what was read.
_DISCO_PATTERNS: list[tuple[str, DISCO]] = [
    (r"\biesco\b|\bislamabad electric supply\b", "IESCO"),
    (r"\blesco\b|\blahore electric supply\b", "LESCO"),
    (r"\bk electric\b|\bke\b|\bkarachi electric\b", "K-Electric"),
]


def normalize_disco(provider: str | None) -> DISCO:
    words = normalize_charge_name(provider or "")
    found = {disco for pattern, disco in _DISCO_PATTERNS if re.search(pattern, words)}
    if len(found) != 1:
        raise TariffEngineError(
            f"'{provider}' is not a supported DISCO this sprint "
            "(K-Electric, IESCO, LESCO only)."
        )
    return found.pop()


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
    `withhold_status_dependent_checks` before `select_tariff`."""
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


def withhold_status_dependent_checks(
    calc_input: TariffCalculationInput,
) -> tuple[TariffCalculationInput, list[str], frozenset[str]]:
    """For A-1(a), where the consumer's status is not known.

    Returns (input, warnings, unverifiable), where `unverifiable` names the
    components that must not be flagged. A status is filled in only so a
    total can be calculated; it is not a claim about the consumer.
    """
    if calc_input.tariff_code != _STATUS_SPLIT_CODE:
        return calc_input, [], frozenset()

    units = calc_input.monthly_units
    # The protected schedule stops at 200 units, so above it only the
    # unprotected one can produce a total.
    assumed = "protected" if units <= _PROTECTED_MAX_UNITS else "unprotected"
    unverifiable = {"energy", "fixed", "gst", "electricity_duty"}
    if units <= 100:
        unverifiable.add("qta")  # lifeline consumers are exempt from it
    warning = (
        "we do not yet know whether this is a lifeline, protected or unprotected "
        "consumer, so charges that depend on it were not checked. The recalculated "
        f"total assumes {assumed}."
    )
    return (
        calc_input.model_copy(update={"consumer_status": assumed}),
        [warning],
        frozenset(unverifiable),
    )
