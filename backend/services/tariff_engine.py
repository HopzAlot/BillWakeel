"""Deterministic bill recalculation engine (SCRUM-29).

Works out what a bill should cost from a ``TariffSchedule``. Plain Python
arithmetic only: no LLM, no files, no network. The same inputs always give
the same output, which is the "arithmetic lives in code, not in the LLM"
rule from the roadmap.

Order of calculation:
    1. energy charge   = units priced through the slabs
    2. fixed charge    = tariff.fixed_charge_pkr
    3. adjustments     = rate per unit x units (FCA / FPA / QTA, may be negative)
    4. subtotal        = energy + fixed + adjustments
    5. taxes           = percentage of a named basis, or a fixed amount
    6. total           = subtotal + taxes
"""

from typing import Literal

from pydantic import BaseModel

from models.tariff import TariffSchedule, TariffSlab

SlabMethod = Literal["telescopic", "landing"]

# Values a percentage tax may use in its ``basis`` field.
SUPPORTED_TAX_BASES = ("energy_charge", "fixed_charge", "subtotal")

# Provisional: a recalculated total within this many rupees of the billed
# total counts as a match. Revisit once real tariff data is loaded.
DEFAULT_TOLERANCE_PKR = 1.0


class TariffEngineError(ValueError):
    """The bill cannot be calculated from this tariff and these units."""


class SlabLine(BaseModel):
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
    tariff_category: str
    units_consumed: float
    slab_method: SlabMethod
    slab_lines: list[SlabLine]
    energy_charge_pkr: float
    fixed_charge_pkr: float
    adjustments: list[ChargeItem]
    subtotal_pkr: float
    taxes: list[ChargeItem]
    total_pkr: float


class BillComparison(BaseModel):
    expected_total_pkr: float
    billed_total_pkr: float
    difference_pkr: float  # billed minus expected; positive means overbilled
    tolerance_pkr: float
    within_tolerance: bool


def _money(amount: float) -> float:
    """Round to paisa. Adding 0.0 turns -0.0 into 0.0."""
    return round(amount, 2) + 0.0


def _sorted_slabs(slabs: list[TariffSlab]) -> list[TariffSlab]:
    """Return slabs in order, after checking they start at 0 with no gaps."""
    ordered = sorted(slabs, key=lambda slab: slab.min_units)
    if ordered[0].min_units != 0:
        raise TariffEngineError("first slab must start at 0 units")
    for previous, current in zip(ordered, ordered[1:]):
        if previous.max_units is None:
            raise TariffEngineError("only the last slab may be open-ended")
        if current.min_units != previous.max_units:
            raise TariffEngineError(
                f"gap or overlap between slabs at {previous.max_units} units"
            )
    return ordered


def _telescopic_lines(slabs: list[TariffSlab], units: float) -> list[SlabLine]:
    """Each slab charges only the units that fall inside it."""
    lines = []
    for slab in slabs:
        upper = units if slab.max_units is None else min(units, slab.max_units)
        units_in_slab = upper - slab.min_units
        if units_in_slab <= 0:
            break
        lines.append(
            SlabLine(
                min_units=slab.min_units,
                max_units=slab.max_units,
                units=units_in_slab,
                rate_per_unit_pkr=slab.rate_per_unit_pkr,
                amount_pkr=_money(units_in_slab * slab.rate_per_unit_pkr),
            )
        )
    return lines


def _landing_lines(slabs: list[TariffSlab], units: float) -> list[SlabLine]:
    """All units are charged at the rate of the slab the total lands in."""
    if units == 0:
        return []
    for slab in slabs:
        if slab.max_units is None or units <= slab.max_units:
            return [
                SlabLine(
                    min_units=slab.min_units,
                    max_units=slab.max_units,
                    units=units,
                    rate_per_unit_pkr=slab.rate_per_unit_pkr,
                    amount_pkr=_money(units * slab.rate_per_unit_pkr),
                )
            ]
    raise TariffEngineError("units are not covered by any slab")


def calculate_bill(
    tariff: TariffSchedule,
    units_consumed: float,
    slab_method: SlabMethod = "telescopic",
) -> BillCalculation:
    """Recalculate a bill from the tariff and the units consumed."""
    if units_consumed < 0:
        raise TariffEngineError("units_consumed cannot be negative")

    slabs = _sorted_slabs(tariff.slabs)
    top = slabs[-1].max_units
    if top is not None and units_consumed > top:
        raise TariffEngineError(
            f"{units_consumed} units is above the last slab ({top} units)"
        )

    if slab_method == "telescopic":
        slab_lines = _telescopic_lines(slabs, units_consumed)
    elif slab_method == "landing":
        slab_lines = _landing_lines(slabs, units_consumed)
    else:
        raise TariffEngineError(f"unknown slab_method: {slab_method}")

    energy = _money(sum(line.amount_pkr for line in slab_lines))
    fixed = _money(tariff.fixed_charge_pkr)
    adjustments = [
        ChargeItem(
            name=adjustment.name,
            amount_pkr=_money(adjustment.rate_pkr_per_unit * units_consumed),
        )
        for adjustment in tariff.adjustments
    ]
    subtotal = _money(energy + fixed + sum(a.amount_pkr for a in adjustments))

    bases = {"energy_charge": energy, "fixed_charge": fixed, "subtotal": subtotal}
    taxes = []
    for tax in tariff.taxes:
        if tax.type == "fixed":
            amount = tax.rate
        elif tax.basis in bases:
            amount = bases[tax.basis] * tax.rate / 100
        else:
            raise TariffEngineError(
                f"tax '{tax.name}' has unsupported basis '{tax.basis}'; "
                f"use one of {', '.join(SUPPORTED_TAX_BASES)}"
            )
        taxes.append(ChargeItem(name=tax.name, amount_pkr=_money(amount)))

    total = _money(subtotal + sum(t.amount_pkr for t in taxes))

    return BillCalculation(
        disco=tariff.disco,
        tariff_category=tariff.tariff_category,
        units_consumed=units_consumed,
        slab_method=slab_method,
        slab_lines=slab_lines,
        energy_charge_pkr=energy,
        fixed_charge_pkr=fixed,
        adjustments=adjustments,
        subtotal_pkr=subtotal,
        taxes=taxes,
        total_pkr=total,
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
