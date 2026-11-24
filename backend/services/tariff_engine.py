"""Deterministic bill recalculation engine (SCRUM-29).

Works out what an electricity bill should cost from a ``TariffSchedule`` and a
``TariffCalculationInput`` (both defined in ``models/tariff.py``, SCRUM-28).
Plain Python arithmetic only: no LLM and no network. The same inputs always
give the same output, which is the "arithmetic lives in code, not in the LLM"
rule from the roadmap.

Order of calculation:
    1. energy charge   = units priced through the slabs, using the tariff's
                         billing_method (telescopic, landing_slab or flat);
                         TOU tariffs price peak and off-peak units separately
    2. fixed charge    = the slab's own fixed charge if it has one, otherwise
                         the schedule's, using its calculation_method
    3. minimum charge  = top-up to minimum_monthly_charge_pkr, only when no
                         fixed charge applies
    4. adjustments     = rate per unit x units (FCA / FPA / QTA, may be negative)
    5. subtotal        = energy + fixed + minimum top-up + adjustments
    6. taxes           = percentage of a named basis, or a fixed amount
    7. total           = subtotal + taxes
"""

import json
from pathlib import Path

from pydantic import BaseModel

from models.tariff import (
    TariffAdjustment,
    TariffCalculationInput,
    TariffFixedCharge,
    TariffSchedule,
    TariffSlab,
    TariffSource,
)

# Tax "basis" text -> the amount the percentage is taken from. The long
# strings are the exact wording used in the SCRUM-28 tariff JSON files.
TAX_BASES = {
    "energy_charge": "energy_charge",
    "Base energy charges only": "energy_charge",
    "fixed_charge": "fixed_charge",
    "subtotal": "subtotal",
    "Energy charges + fixed charges + applicable electricity adjustments": "subtotal",
}

# Provisional: a recalculated total within this many rupees of the billed
# total counts as a match. Revisit once real bills have been checked.
DEFAULT_TOLERANCE_PKR = 1.0

# Peak + off-peak units may differ from monthly_units by this much (rounding).
TOU_UNITS_TOLERANCE = 0.01


class TariffEngineError(ValueError):
    """The bill cannot be calculated from this tariff and this input."""


class SlabLine(BaseModel):
    time_period: str
    min_units: float
    max_units: float | None
    units: float
    rate_per_unit_pkr: float
    amount_pkr: float


class ChargeItem(BaseModel):
    name: str
    amount_pkr: float


class BillCalculation(BaseModel):
    disco: str
    tariff_code: str
    tariff_category: str
    consumer_status: str | None
    billing_method: str
    metering_type: str
    units_consumed: float
    slab_lines: list[SlabLine]
    energy_charge_pkr: float
    fixed_charge_method: str
    fixed_charge_pkr: float
    minimum_charge_topup_pkr: float
    adjustments: list[ChargeItem]
    subtotal_pkr: float
    taxes: list[ChargeItem]
    total_pkr: float
    source: TariffSource
    warnings: list[str]


class BillComparison(BaseModel):
    expected_total_pkr: float
    billed_total_pkr: float
    difference_pkr: float  # billed minus expected; positive means overbilled
    tolerance_pkr: float
    within_tolerance: bool


def _money(amount: float) -> float:
    """Round to paisa. Adding 0.0 turns -0.0 into 0.0."""
    return round(amount, 2) + 0.0


# --- checking the tariff fits the consumer ----------------------------------

def _check_applicable(tariff: TariffSchedule, data: TariffCalculationInput) -> None:
    if data.disco not in tariff.discos:
        raise TariffEngineError(
            f"tariff {tariff.tariff_code} does not apply to {data.disco}"
        )
    if data.tariff_code != tariff.tariff_code:
        raise TariffEngineError(
            f"input is for tariff {data.tariff_code}, "
            f"but this schedule is {tariff.tariff_code}"
        )
    if (
        tariff.consumer_status is not None
        and data.consumer_status != tariff.consumer_status
    ):
        raise TariffEngineError(
            f"this {tariff.tariff_code} schedule is for "
            f"{tariff.consumer_status} consumers, input says {data.consumer_status}"
        )


def _load_warnings(tariff: TariffSchedule, data: TariffCalculationInput) -> list[str]:
    """Out-of-range load is reported, not rejected: the bill may still be right."""
    low, high = tariff.min_sanctioned_load_kw, tariff.max_sanctioned_load_kw
    load = data.sanctioned_load_kw
    if (low is not None and load < low) or (high is not None and load > high):
        return [
            f"sanctioned load {load} kW is outside the {tariff.tariff_code} "
            f"range ({low} to {high} kW)"
        ]
    return []


def _filter_adjustments(
    adjustments: list[TariffAdjustment], billing_month: str | None
) -> tuple[list[TariffAdjustment], list[str]]:
    """Split a tariff's adjustments into (applicable, warnings).

    An adjustment with no effective window always applies. One with a
    window is skipped - with a warning, not a silent drop - if the bill
    has no billing_month to check it against, or if billing_month falls
    outside the window. Applying it anyway would be guessing; NEPRA
    adjustments are time-bound by design (FCA monthly, QTA quarterly).
    """
    applicable: list[TariffAdjustment] = []
    warnings: list[str] = []

    for adjustment in adjustments:
        window = f"{adjustment.effective_from_month or '...'} to {adjustment.effective_to_month or '...'}"

        if adjustment.effective_from_month is None and adjustment.effective_to_month is None:
            applicable.append(adjustment)
            continue

        if billing_month is None:
            warnings.append(
                f"'{adjustment.name}' not applied: it only applies {window}, "
                "but this bill has no billing_month to check against"
            )
            continue

        in_range = (
            adjustment.effective_from_month is None or billing_month >= adjustment.effective_from_month
        ) and (
            adjustment.effective_to_month is None or billing_month <= adjustment.effective_to_month
        )
        if in_range:
            applicable.append(adjustment)
        else:
            warnings.append(
                f"'{adjustment.name}' not applied: billing_month {billing_month} "
                f"is outside its {window} window"
            )

    return applicable, warnings


# --- energy charge -----------------------------------------------------------

def _rate(slab: TariffSlab, tariff_code: str) -> float:
    if slab.rate_per_unit_pkr is not None:
        return slab.rate_per_unit_pkr
    if slab.rate_multiplier is not None:
        raise TariffEngineError(
            f"tariff {tariff_code} is derived from another tariff "
            "(rate_multiplier); derived tariffs are not supported yet"
        )
    raise TariffEngineError(
        f"tariff {tariff_code} only publishes a rate range "
        f"({slab.rate_min_pkr} to {slab.rate_max_pkr}); cannot recalculate exactly"
    )


def _slabs_for(tariff: TariffSchedule, period: str) -> list[TariffSlab]:
    """Slabs for one time period, in order, checked to start at 0 with no gaps."""
    slabs = sorted(
        (s for s in tariff.slabs if s.time_period == period),
        key=lambda s: s.min_units,
    )
    if not slabs:
        raise TariffEngineError(
            f"tariff {tariff.tariff_code} has no '{period}' slabs"
        )
    if slabs[0].min_units != 0:
        raise TariffEngineError("first slab must start at 0 units")
    for previous, current in zip(slabs, slabs[1:]):
        if previous.max_units is None:
            raise TariffEngineError("only the last slab may be open-ended")
        if current.min_units != previous.max_units:
            raise TariffEngineError(
                f"gap or overlap between slabs at {previous.max_units} units"
            )
    return slabs


def _landing_slab(slabs: list[TariffSlab], units: float) -> TariffSlab:
    """The slab the total units fall in (0 units falls in the first slab)."""
    for slab in slabs:
        if slab.max_units is None or units <= slab.max_units:
            return slab
    raise TariffEngineError(
        f"{units} units is above the last slab ({slabs[-1].max_units} units)"
    )


def _price_units(
    tariff: TariffSchedule, period: str, units: float
) -> tuple[list[SlabLine], TariffSlab]:
    """Price units through one period's slabs. Returns lines and landing slab."""
    slabs = _slabs_for(tariff, period)
    landing = _landing_slab(slabs, units)
    if units == 0:
        return [], landing

    if tariff.billing_method == "telescopic":
        # Each slab charges only the units that fall inside it.
        chosen = []
        for slab in slabs:
            upper = units if slab.max_units is None else min(units, slab.max_units)
            if upper - slab.min_units <= 0:
                break
            chosen.append((slab, upper - slab.min_units))
    else:
        # landing_slab and flat: every unit at the rate of the landing slab.
        chosen = [(landing, units)]

    lines = []
    for slab, slab_units in chosen:
        rate = _rate(slab, tariff.tariff_code)
        lines.append(
            SlabLine(
                time_period=period,
                min_units=slab.min_units,
                max_units=slab.max_units,
                units=slab_units,
                rate_per_unit_pkr=rate,
                amount_pkr=_money(slab_units * rate),
            )
        )
    return lines, landing


# --- fixed charge ------------------------------------------------------------

def _fixed_charge(rule: TariffFixedCharge | None, data: TariffCalculationInput) -> float:
    if rule is None:
        return 0.0
    method = rule.calculation_method
    load = data.sanctioned_load_kw
    mdi = data.mdi_kw or 0.0

    if method == "exempt":
        return 0.0
    if method == "per_consumer":
        return rule.rate_pkr
    if method == "per_kw_sanctioned_load":
        return rule.rate_pkr * load
    if method == "per_kw_max_load_or_mdi":
        return rule.rate_pkr * max(load, mdi)
    if method == "per_kw_max_25_percent_load_or_mdi":
        return rule.rate_pkr * max(0.25 * load, mdi)
    if method == "per_kw_max_50_percent_load_or_mdi":
        return rule.rate_pkr * max(0.50 * load, mdi)
    raise TariffEngineError(
        f"fixed charge method '{method}' is not supported yet"
    )


# --- main entry points -------------------------------------------------------

def calculate_bill(
    tariff: TariffSchedule, data: TariffCalculationInput
) -> BillCalculation:
    """Recalculate a bill from one tariff schedule and the consumer's input."""
    _check_applicable(tariff, data)
    warnings = _load_warnings(tariff, data)

    if tariff.metering_type == "tou":
        if data.peak_units is None or data.off_peak_units is None:
            raise TariffEngineError(
                f"tariff {tariff.tariff_code} is TOU: peak_units and "
                "off_peak_units are required"
            )
        if abs(data.peak_units + data.off_peak_units - data.monthly_units) > TOU_UNITS_TOLERANCE:
            raise TariffEngineError(
                "peak_units + off_peak_units does not equal monthly_units"
            )
        peak_lines, _ = _price_units(tariff, "peak", data.peak_units)
        off_lines, _ = _price_units(tariff, "off_peak", data.off_peak_units)
        slab_lines = peak_lines + off_lines
        fixed_rule = tariff.fixed_charge
    else:
        slab_lines, landing = _price_units(tariff, "all", data.monthly_units)
        # A slab's own fixed charge overrides the schedule-level one.
        fixed_rule = landing.fixed_charge or tariff.fixed_charge

    energy = _money(sum(line.amount_pkr for line in slab_lines))
    fixed = _money(_fixed_charge(fixed_rule, data))

    minimum = tariff.minimum_monthly_charge_pkr
    topup = 0.0
    if minimum is not None and fixed == 0 and energy < minimum:
        topup = _money(minimum - energy)

    applicable_adjustments, adjustment_warnings = _filter_adjustments(
        tariff.adjustments, data.billing_month
    )
    warnings = warnings + adjustment_warnings
    adjustments = [
        ChargeItem(
            name=adjustment.name,
            amount_pkr=_money(adjustment.rate_pkr_per_unit * data.monthly_units),
        )
        for adjustment in applicable_adjustments
    ]
    subtotal = _money(
        energy + fixed + topup + sum(a.amount_pkr for a in adjustments)
    )

    bases = {"energy_charge": energy, "fixed_charge": fixed, "subtotal": subtotal}
    taxes = []
    for tax in tariff.taxes:
        if tax.type == "fixed":
            amount = tax.rate
        elif tax.basis in TAX_BASES:
            amount = bases[TAX_BASES[tax.basis]] * tax.rate / 100
        else:
            raise TariffEngineError(
                f"tax '{tax.name}' has unsupported basis '{tax.basis}'"
            )
        taxes.append(ChargeItem(name=tax.name, amount_pkr=_money(amount)))

    total = _money(subtotal + sum(t.amount_pkr for t in taxes))

    return BillCalculation(
        disco=data.disco,
        tariff_code=tariff.tariff_code,
        tariff_category=tariff.tariff_category,
        consumer_status=tariff.consumer_status,
        billing_method=tariff.billing_method,
        metering_type=tariff.metering_type,
        units_consumed=data.monthly_units,
        slab_lines=slab_lines,
        energy_charge_pkr=energy,
        fixed_charge_method=fixed_rule.calculation_method if fixed_rule else "none",
        fixed_charge_pkr=fixed,
        minimum_charge_topup_pkr=topup,
        adjustments=adjustments,
        subtotal_pkr=subtotal,
        taxes=taxes,
        total_pkr=total,
        source=tariff.source,
        warnings=warnings,
    )


def compare_with_billed_total(
    calculation: BillCalculation,
    billed_total_pkr: float,
    tolerance_pkr: float = DEFAULT_TOLERANCE_PKR,
) -> BillComparison:
    """Check the recalculated total against the total printed on the bill."""
    difference = _money(billed_total_pkr - calculation.total_pkr)
    return BillComparison(
        expected_total_pkr=calculation.total_pkr,
        billed_total_pkr=billed_total_pkr,
        difference_pkr=difference,
        tolerance_pkr=tolerance_pkr,
        within_tolerance=abs(difference) <= tolerance_pkr,
    )


# --- finding the right tariff file -------------------------------------------

def load_tariff_schedules(directory: str | Path) -> list[TariffSchedule]:
    """Load and validate every tariff JSON file in a folder."""
    schedules = []
    for path in sorted(Path(directory).glob("*.json")):
        with path.open(encoding="utf-8") as file:
            schedules.append(TariffSchedule.model_validate(json.load(file)))
    return schedules


def select_tariff(
    schedules: list[TariffSchedule], data: TariffCalculationInput
) -> TariffSchedule:
    """Pick the one schedule that matches the input's DISCO, code and status."""
    matches = []
    for tariff in schedules:
        try:
            _check_applicable(tariff, data)
        except TariffEngineError:
            continue
        matches.append(tariff)

    if not matches:
        raise TariffEngineError(
            f"no tariff found for {data.disco} {data.tariff_code} "
            f"(consumer_status={data.consumer_status})"
        )
    if len(matches) > 1:
        raise TariffEngineError(
            f"{len(matches)} tariffs match {data.disco} {data.tariff_code}; "
            "set consumer_status to choose one"
        )
    return matches[0]
