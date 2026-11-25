"""Unit tests for the bill recalculation engine (SCRUM-29).

Part 1 uses a made-up tariff with round numbers so every expected value can be
checked by hand (the working is in the comments). It is NOT an official tariff.
Part 2 runs the engine on the real K-Electric files from SCRUM-28.
"""

from copy import deepcopy
from pathlib import Path

import pytest

from models.tariff import TariffCalculationInput, TariffSchedule
from services.tariff_engine import (
    TariffEngineError,
    calculate_bill,
    compare_with_billed_total,
    load_tariff_schedules,
    select_tariff,
)

KE_DIR = (
    Path(__file__).resolve().parents[2]
    / "data" / "tariffs" / "structured" / "k-electric"
)

TEST_TARIFF = {
    "discos": ["K-Electric"],
    "tariff_code": "TEST-1",
    "tariff_category": "Domestic",
    "billing_method": "telescopic",
    "metering_type": "regular",
    "effective_from": "2026-01-01",
    "slabs": [
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
        {"min_units": 100, "max_units": 200, "rate_per_unit_pkr": 15},
        {"min_units": 200, "max_units": None, "rate_per_unit_pkr": 20},
    ],
    "fixed_charge": {"calculation_method": "per_kw_sanctioned_load", "rate_pkr": 100},
    "adjustments": [{"name": "FCA", "rate_pkr_per_unit": 2}],
    "taxes": [
        {"name": "Electricity Duty", "type": "percentage", "rate": 1.5,
         "basis": "Base energy charges only"},
        {"name": "GST", "type": "percentage", "rate": 18,
         "basis": "Energy charges + fixed charges + applicable electricity adjustments"},
    ],
    "source": {
        "url": "https://example.com/test-tariff.pdf",
        "retrieved_on": "2026-01-10",
        "document_name": "Unit-test tariff, not official",
    },
}

TOU_SLABS = [
    {"min_units": 0, "max_units": None, "rate_per_unit_pkr": 40, "time_period": "peak"},
    {"min_units": 0, "max_units": None, "rate_per_unit_pkr": 30, "time_period": "off_peak"},
]


def make_tariff(**changes) -> TariffSchedule:
    data = deepcopy(TEST_TARIFF)
    data.update(changes)
    return TariffSchedule.model_validate(data)


def make_input(**changes) -> TariffCalculationInput:
    data = {
        "disco": "K-Electric",
        "tariff_code": "TEST-1",
        "monthly_units": 150,
        "sanctioned_load_kw": 2,
    }
    data.update(changes)
    return TariffCalculationInput.model_validate(data)


# === Part 1: made-up tariff ==================================================

# --- slab pricing ---

def test_telescopic_splits_units_across_slabs():
    result = calculate_bill(make_tariff(), make_input())

    # 100 x 10 + 50 x 15 = 1000 + 750
    assert [line.units for line in result.slab_lines] == [100, 50]
    assert result.energy_charge_pkr == pytest.approx(1750)


def test_telescopic_reaches_open_ended_top_slab():
    result = calculate_bill(make_tariff(), make_input(monthly_units=250))

    # 100 x 10 + 100 x 15 + 50 x 20 = 1000 + 1500 + 1000
    assert len(result.slab_lines) == 3
    assert result.energy_charge_pkr == pytest.approx(3500)


def test_landing_slab_charges_all_units_at_landing_rate():
    tariff = make_tariff(billing_method="landing_slab")
    result = calculate_bill(tariff, make_input())

    # all 150 units at the 100-200 slab rate: 150 x 15
    assert len(result.slab_lines) == 1
    assert result.energy_charge_pkr == pytest.approx(2250)


def test_landing_on_slab_boundary_stays_in_lower_slab():
    tariff = make_tariff(billing_method="landing_slab")
    result = calculate_bill(tariff, make_input(monthly_units=100))

    # exactly 100 units belongs to the 0-100 slab: 100 x 10
    assert result.energy_charge_pkr == pytest.approx(1000)


def test_tou_prices_peak_and_off_peak_separately():
    tariff = make_tariff(billing_method="flat", metering_type="tou", slabs=TOU_SLABS)
    data = make_input(monthly_units=100, peak_units=20, off_peak_units=80)
    result = calculate_bill(tariff, data)

    # 20 x 40 + 80 x 30 = 800 + 2400
    assert result.energy_charge_pkr == pytest.approx(3200)


def test_zero_units_still_pays_fixed_charge_and_its_tax():
    result = calculate_bill(make_tariff(), make_input(monthly_units=0))

    # energy 0, fixed 100 x 2 kW = 200, GST 18% of 200 = 36
    assert result.slab_lines == []
    assert result.total_pkr == pytest.approx(236)


# --- fixed charge ---

@pytest.mark.parametrize("rule, load, mdi, expected", [
    ({"calculation_method": "per_consumer", "rate_pkr": 1000}, 10, None, 1000),
    ({"calculation_method": "per_kw_sanctioned_load", "rate_pkr": 100}, 10, None, 1000),
    # 25% of 10 kW = 2.5 kW (bigger than no MDI) -> 2.5 x 1250
    ({"calculation_method": "per_kw_max_25_percent_load_or_mdi", "rate_pkr": 1250}, 10, None, 3125),
    # MDI 4 kW is bigger than 2.5 kW -> 4 x 1250
    ({"calculation_method": "per_kw_max_25_percent_load_or_mdi", "rate_pkr": 1250}, 10, 4, 5000),
    # 50% of 10 kW = 5 kW, bigger than MDI 3 kW -> 5 x 675
    ({"calculation_method": "per_kw_max_50_percent_load_or_mdi", "rate_pkr": 675}, 10, 3, 3375),
    ({"calculation_method": "per_kw_max_load_or_mdi", "rate_pkr": 100}, 10, 12, 1200),
    ({"calculation_method": "exempt", "rate_pkr": 0}, 10, None, 0),
])
def test_fixed_charge_methods(rule, load, mdi, expected):
    tariff = make_tariff(fixed_charge=rule)
    result = calculate_bill(tariff, make_input(sanctioned_load_kw=load, mdi_kw=mdi))

    assert result.fixed_charge_pkr == pytest.approx(expected)


def test_slab_fixed_charge_overrides_schedule_fixed_charge():
    slabs = deepcopy(TEST_TARIFF["slabs"])
    slabs[1]["fixed_charge"] = {"calculation_method": "per_kw_sanctioned_load", "rate_pkr": 300}
    tariff = make_tariff(slabs=slabs)

    # 150 units lands in slab 2: 300 x 2 kW. 50 units stays on schedule: 100 x 2 kW.
    assert calculate_bill(tariff, make_input()).fixed_charge_pkr == pytest.approx(600)
    assert calculate_bill(tariff, make_input(monthly_units=50)).fixed_charge_pkr == pytest.approx(200)


def test_minimum_charge_tops_up_only_without_fixed_charge():
    tariff = make_tariff(fixed_charge=None, minimum_monthly_charge_pkr=75, taxes=[])
    result = calculate_bill(tariff, make_input(monthly_units=5))

    # energy 5 x 10 = 50, below the 75 minimum -> top-up 25 (+ FCA 5 x 2 = 10)
    assert result.minimum_charge_topup_pkr == pytest.approx(25)
    assert result.total_pkr == pytest.approx(85)

    with_fixed = make_tariff(minimum_monthly_charge_pkr=75, taxes=[])
    assert calculate_bill(with_fixed, make_input(monthly_units=5)).minimum_charge_topup_pkr == 0


# --- adjustments, taxes and total ---

def test_adjustments_are_per_unit_and_can_be_credits():
    tariff = make_tariff(adjustments=[
        {"name": "FCA", "rate_pkr_per_unit": 2},
        {"name": "QTA", "rate_pkr_per_unit": -2},
    ])
    result = calculate_bill(tariff, make_input())

    amounts = {item.name: item.amount_pkr for item in result.adjustments}
    assert amounts == {"FCA": pytest.approx(300), "QTA": pytest.approx(-300)}


def test_full_bill_total():
    result = calculate_bill(make_tariff(), make_input())

    # energy 1750 + fixed 200 + FCA 300 = subtotal 2250
    # ED 1.5% of 1750 = 26.25, GST 18% of 2250 = 405
    # total = 2250 + 26.25 + 405 = 2681.25
    taxes = {item.name: item.amount_pkr for item in result.taxes}
    assert result.subtotal_pkr == pytest.approx(2250)
    assert taxes == {"Electricity Duty": pytest.approx(26.25), "GST": pytest.approx(405)}
    assert result.total_pkr == pytest.approx(2681.25)


def test_fixed_tax_adds_flat_amount():
    tariff = make_tariff(taxes=[
        {"name": "PTV Fee", "type": "fixed", "rate": 35, "basis": "per_bill"},
    ])
    # subtotal 2250 + flat 35
    assert calculate_bill(tariff, make_input()).total_pkr == pytest.approx(2285)


def test_same_input_gives_same_output():
    data = make_input(monthly_units=333.5)
    assert calculate_bill(make_tariff(), data) == calculate_bill(make_tariff(), data)


def test_load_outside_tariff_range_is_a_warning_not_an_error():
    tariff = make_tariff(max_sanctioned_load_kw=5)
    result = calculate_bill(tariff, make_input(sanctioned_load_kw=8))

    assert len(result.warnings) == 1
    assert result.total_pkr > 0


# --- rejected input ---

@pytest.mark.parametrize("changes", [
    {"disco": "IESCO"},
    {"tariff_code": "A-2(a)"},
])
def test_input_for_another_disco_or_tariff_is_rejected(changes):
    with pytest.raises(TariffEngineError):
        calculate_bill(make_tariff(), make_input(**changes))


def test_wrong_consumer_status_is_rejected():
    tariff = make_tariff(consumer_status="protected")
    with pytest.raises(TariffEngineError, match="protected"):
        calculate_bill(tariff, make_input(consumer_status="unprotected"))


def test_tou_without_peak_split_is_rejected():
    tariff = make_tariff(billing_method="flat", metering_type="tou", slabs=TOU_SLABS)
    with pytest.raises(TariffEngineError, match="peak_units"):
        calculate_bill(tariff, make_input(monthly_units=100))


def test_tou_split_that_does_not_add_up_is_rejected():
    tariff = make_tariff(billing_method="flat", metering_type="tou", slabs=TOU_SLABS)
    data = make_input(monthly_units=100, peak_units=20, off_peak_units=70)
    with pytest.raises(TariffEngineError, match="does not equal"):
        calculate_bill(tariff, data)


@pytest.mark.parametrize("slab, message", [
    ({"min_units": 0, "max_units": None, "rate_min_pkr": 50, "rate_max_pkr": 55}, "rate range"),
    ({"min_units": 0, "max_units": None, "rate_multiplier": 1.25}, "derived"),
])
def test_rates_that_cannot_be_calculated_exactly_are_rejected(slab, message):
    tariff = make_tariff(slabs=[slab])
    with pytest.raises(TariffEngineError, match=message):
        calculate_bill(tariff, make_input())


def test_unsupported_fixed_charge_method_is_rejected():
    tariff = make_tariff(fixed_charge={
        "calculation_method": "derived_from_base_tariff", "rate_pkr": 0, "rate_multiplier": 1.25,
    })
    with pytest.raises(TariffEngineError, match="not supported"):
        calculate_bill(tariff, make_input())


def test_unknown_tax_basis_is_rejected():
    tariff = make_tariff(taxes=[
        {"name": "GST", "type": "percentage", "rate": 18, "basis": "whole bill"},
    ])
    with pytest.raises(TariffEngineError, match="unsupported basis"):
        calculate_bill(tariff, make_input())


def test_units_above_closed_last_slab_are_rejected():
    tariff = make_tariff(slabs=[
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
    ])
    with pytest.raises(TariffEngineError, match="above the last slab"):
        calculate_bill(tariff, make_input())


def test_gap_between_slabs_is_rejected():
    tariff = make_tariff(slabs=[
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
        {"min_units": 101, "max_units": None, "rate_per_unit_pkr": 15},
    ])
    with pytest.raises(TariffEngineError, match="gap or overlap"):
        calculate_bill(tariff, make_input())


# --- comparing with the billed total ---

def test_billed_total_within_tolerance_matches():
    result = calculate_bill(make_tariff(), make_input())  # expected 2681.25
    comparison = compare_with_billed_total(result, 2681.75, tolerance_pkr=1)

    assert comparison.difference_pkr == pytest.approx(0.5)
    assert comparison.within_tolerance is True


def test_overbilled_total_is_flagged():
    result = calculate_bill(make_tariff(), make_input())  # expected 2681.25
    comparison = compare_with_billed_total(result, 2781.25, tolerance_pkr=1)

    assert comparison.difference_pkr == pytest.approx(100)
    assert comparison.within_tolerance is False


# === Part 2: real K-Electric tariff files (SCRUM-28) ========================

@pytest.fixture(scope="module")
def ke_tariffs():
    return load_tariff_schedules(KE_DIR)


def ke_input(**changes) -> TariffCalculationInput:
    data = {"disco": "K-Electric", "tariff_code": "A-1(a)", "monthly_units": 150,
            "sanctioned_load_kw": 3, "consumer_status": "protected"}
    data.update(changes)
    return TariffCalculationInput.model_validate(data)


def test_engine_runs_on_every_ke_tariff_except_derived_ones(ke_tariffs):
    for tariff in ke_tariffs:
        # some files in this folder (e.g. D-1(a) SCARP) list only IESCO/LESCO
        data = ke_input(disco=tariff.discos[0], tariff_code=tariff.tariff_code,
                        consumer_status=tariff.consumer_status,
                        monthly_units=80, peak_units=20, off_peak_units=60)
        if tariff.derived_from_tariff_code:
            with pytest.raises(TariffEngineError):
                calculate_bill(tariff, data)
        else:
            assert calculate_bill(tariff, data).total_pkr > 0, tariff.tariff_code


def test_ke_protected_domestic_bill(ke_tariffs):
    # No billing_month here, so the K-Electric schedule's time-bounded QTA
    # (SCRUM-31, 2026-11-25) is correctly skipped - see
    # test_ke_qta_applies_only_within_its_effective_window below for that.
    tariff = select_tariff(ke_tariffs, ke_input())
    result = calculate_bill(tariff, ke_input())

    # telescopic: 100 x 10.54 + 50 x 13.01 = 1054 + 650.50 = 1704.50
    # fixed: lands in 101-200 slab, Rs 300/kW x 3 kW = 900
    # GST 18% of 2604.50 = 468.81, ED 1.5% of 1704.50 = 25.57
    assert result.energy_charge_pkr == pytest.approx(1704.50)
    assert result.fixed_charge_pkr == pytest.approx(900)
    assert result.total_pkr == pytest.approx(3098.88)


def test_ke_unprotected_domestic_bill(ke_tariffs):
    data = ke_input(monthly_units=200, consumer_status="unprotected")
    result = calculate_bill(select_tariff(ke_tariffs, data), data)

    # landing slab: all 200 units x 28.91 = 5782; fixed Rs 300/kW x 3 kW = 900
    # GST 18% of 6682 = 1202.76, ED 1.5% of 5782 = 86.73
    assert result.energy_charge_pkr == pytest.approx(5782)
    assert result.total_pkr == pytest.approx(7971.49)


def test_ke_qta_applies_only_within_its_effective_window(ke_tariffs):
    """SCRUM-31 (2026-11-25): the Quarterly Tariff Adjustment is time-bounded
    (effective_from_month/effective_to_month). It must apply inside its
    window, and be skipped - with a warning, not silently - outside it or
    when the bill carries no billing_month at all."""
    tariff = select_tariff(ke_tariffs, ke_input())

    in_window = calculate_bill(tariff, ke_input(billing_month="2026-07"))
    assert in_window.adjustments and in_window.adjustments[0].amount_pkr == pytest.approx(
        150 * -1.9857, abs=0.01
    )
    assert not any("not applied" in w for w in in_window.warnings)

    outside = calculate_bill(tariff, ke_input(billing_month="2026-12"))
    assert outside.adjustments == []
    assert any("not applied" in w and "2026-12" in w for w in outside.warnings)

    no_billing_month = calculate_bill(tariff, ke_input())
    assert no_billing_month.adjustments == []
    assert any("not applied" in w and "no billing_month" in w for w in no_billing_month.warnings)


def test_ke_lifeline_is_exempt_from_fixed_charge_and_gst(ke_tariffs):
    data = ke_input(monthly_units=40, consumer_status="lifeline")
    result = calculate_bill(select_tariff(ke_tariffs, data), data)

    # 40 x 3.95 = 158, no fixed charge, no GST, ED 1.5% = 2.37
    assert result.fixed_charge_pkr == 0
    assert result.total_pkr == pytest.approx(160.37)


@pytest.mark.parametrize("tariff_code,rate", [
    ("A-1(c)", 42.12),
    ("Prepaid Bulk", 44.87),
    ("K", 42.25),
    ("Prepaid Agricultural", 33.15),
])
def test_corrected_rates_match_sro_279(ke_tariffs, tariff_code, rate):
    # Annex-A-1 of SRO 279(I)/2026 (data/tariffs/sources/k-electric/)
    tariff = next(t for t in ke_tariffs if t.tariff_code == tariff_code)
    assert [slab.rate_per_unit_pkr for slab in tariff.slabs] == [rate]


@pytest.mark.parametrize("tariff_code,status,disco,minimum", [
    ("A-1(a)", "lifeline", "K-Electric", 75),
    ("D-1(a)", None, "IESCO", 2000),
])
def test_minimum_monthly_charge_applies_with_zero_units(
    ke_tariffs, tariff_code, status, disco, minimum
):
    data = ke_input(disco=disco, tariff_code=tariff_code,
                    consumer_status=status, monthly_units=0)
    result = calculate_bill(select_tariff(ke_tariffs, data), data)
    assert result.subtotal_pkr == pytest.approx(minimum)


@pytest.mark.parametrize("month,rate", [
    ("2026-01", 0.3298),
    ("2026-04", 0.3504),
    ("2026-07", -1.9857),
    ("2026-11", 0.5194),
])
def test_ke_qta_rate_follows_the_billing_quarter(ke_tariffs, month, rate):
    tariff = select_tariff(ke_tariffs, ke_input())
    result = calculate_bill(tariff, ke_input(billing_month=month))

    assert [a.amount_pkr for a in result.adjustments] == [pytest.approx(150 * rate, abs=0.01)]
    assert not any("not applied" in w for w in result.warnings)


@pytest.mark.parametrize("units,subtotal", [
    (0, 2000),       # fixed 400 x 3 kW = 1200, topped up to the minimum
    (100, 4090),     # 2890 energy + 1200 fixed, already above it
])
def test_agricultural_minimum_is_a_floor_on_energy_plus_fixed(ke_tariffs, units, subtotal):
    data = ke_input(tariff_code="D-2(a)", consumer_status=None, monthly_units=units)
    result = calculate_bill(select_tariff(ke_tariffs, data), data)
    assert result.subtotal_pkr == pytest.approx(subtotal)


def test_select_tariff_needs_consumer_status_for_domestic(ke_tariffs):
    with pytest.raises(TariffEngineError, match="no tariff found"):
        select_tariff(ke_tariffs, ke_input(consumer_status=None))
