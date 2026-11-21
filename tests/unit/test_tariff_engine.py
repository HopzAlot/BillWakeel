"""Unit tests for the bill recalculation engine (SCRUM-29).

The tariff below is made-up test data with round numbers so every expected
value can be checked by hand. It is NOT an official NEPRA tariff.
"""

from copy import deepcopy

import pytest

from models.tariff import TariffSchedule
from services.tariff_engine import (
    TariffEngineError,
    calculate_bill,
    compare_with_billed_total,
)

TEST_TARIFF = {
    "disco": "K-Electric",
    "tariff_category": "TEST-A1",
    "effective_from": "2026-01-01",
    "effective_to": None,
    "slabs": [
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
        {"min_units": 100, "max_units": 200, "rate_per_unit_pkr": 15},
        {"min_units": 200, "max_units": None, "rate_per_unit_pkr": 20},
    ],
    "fixed_charge_pkr": 100,
    "adjustments": [{"name": "FCA", "rate_pkr_per_unit": 2}],
    "taxes": [
        {"name": "Electricity Duty", "type": "percentage", "rate": 1.5,
         "basis": "energy_charge"},
        {"name": "GST", "type": "percentage", "rate": 18, "basis": "subtotal"},
    ],
    "source": {
        "url": "https://example.com/test-tariff.pdf",
        "retrieved_on": "2026-01-10",
        "document_name": "Unit-test tariff, not official",
        "clause": None,
    },
}


def make_tariff(**changes) -> TariffSchedule:
    data = deepcopy(TEST_TARIFF)
    data.update(changes)
    return TariffSchedule.model_validate(data)


# --- slab pricing -----------------------------------------------------------

def test_telescopic_splits_units_across_slabs():
    result = calculate_bill(make_tariff(), 150, "telescopic")

    # 100 x 10 + 50 x 15 = 1000 + 750
    assert [line.units for line in result.slab_lines] == [100, 50]
    assert result.energy_charge_pkr == pytest.approx(1750)


def test_telescopic_reaches_open_ended_top_slab():
    result = calculate_bill(make_tariff(), 250, "telescopic")

    # 100 x 10 + 100 x 15 + 50 x 20 = 1000 + 1500 + 1000
    assert len(result.slab_lines) == 3
    assert result.energy_charge_pkr == pytest.approx(3500)


def test_landing_charges_all_units_at_landing_slab_rate():
    result = calculate_bill(make_tariff(), 150, "landing")

    # all 150 units at the 100-200 slab rate: 150 x 15
    assert len(result.slab_lines) == 1
    assert result.slab_lines[0].rate_per_unit_pkr == 15
    assert result.energy_charge_pkr == pytest.approx(2250)


def test_landing_on_slab_boundary_stays_in_lower_slab():
    result = calculate_bill(make_tariff(), 100, "landing")

    # exactly 100 units belongs to the 0-100 slab: 100 x 10
    assert result.energy_charge_pkr == pytest.approx(1000)


def test_zero_units_still_pays_fixed_charge_and_its_tax():
    result = calculate_bill(make_tariff(), 0)

    # energy 0, fixed 100, GST 18% of 100 = 18
    assert result.slab_lines == []
    assert result.energy_charge_pkr == 0
    assert result.total_pkr == pytest.approx(118)


# --- adjustments, taxes and total ------------------------------------------

def test_adjustments_are_per_unit_and_can_be_credits():
    tariff = make_tariff(adjustments=[
        {"name": "FCA", "rate_pkr_per_unit": 2},
        {"name": "QTA", "rate_pkr_per_unit": -2},
    ])
    result = calculate_bill(tariff, 150)

    amounts = {item.name: item.amount_pkr for item in result.adjustments}
    assert amounts == {"FCA": pytest.approx(300), "QTA": pytest.approx(-300)}


def test_full_bill_total_telescopic():
    result = calculate_bill(make_tariff(), 150, "telescopic")

    # energy 1750 + fixed 100 + FCA 300 = subtotal 2150
    # ED 1.5% of 1750 = 26.25, GST 18% of 2150 = 387.00
    # total = 2150 + 26.25 + 387 = 2563.25
    taxes = {item.name: item.amount_pkr for item in result.taxes}
    assert result.subtotal_pkr == pytest.approx(2150)
    assert taxes["Electricity Duty"] == pytest.approx(26.25)
    assert taxes["GST"] == pytest.approx(387)
    assert result.total_pkr == pytest.approx(2563.25)


def test_fixed_tax_adds_flat_amount():
    tariff = make_tariff(taxes=[
        {"name": "PTV Fee", "type": "fixed", "rate": 35, "basis": "per_bill"},
    ])
    result = calculate_bill(tariff, 150)

    # subtotal 2150 + flat 35
    assert result.total_pkr == pytest.approx(2185)


def test_same_input_gives_same_output():
    first = calculate_bill(make_tariff(), 333.5, "landing")
    second = calculate_bill(make_tariff(), 333.5, "landing")

    assert first == second


# --- rejected input ---------------------------------------------------------

def test_negative_units_are_rejected():
    with pytest.raises(TariffEngineError):
        calculate_bill(make_tariff(), -1)


def test_unknown_tax_basis_is_rejected():
    tariff = make_tariff(taxes=[
        {"name": "GST", "type": "percentage", "rate": 18, "basis": "whole_bill"},
    ])
    with pytest.raises(TariffEngineError, match="unsupported basis"):
        calculate_bill(tariff, 150)


def test_units_above_closed_last_slab_are_rejected():
    tariff = make_tariff(slabs=[
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
    ])
    with pytest.raises(TariffEngineError, match="above the last slab"):
        calculate_bill(tariff, 150)


def test_gap_between_slabs_is_rejected():
    tariff = make_tariff(slabs=[
        {"min_units": 0, "max_units": 100, "rate_per_unit_pkr": 10},
        {"min_units": 101, "max_units": None, "rate_per_unit_pkr": 15},
    ])
    with pytest.raises(TariffEngineError, match="gap or overlap"):
        calculate_bill(tariff, 150)


# --- comparing with the billed total ---------------------------------------

def test_billed_total_within_tolerance_matches():
    result = calculate_bill(make_tariff(), 150)  # expected 2563.25

    comparison = compare_with_billed_total(result, 2563.75, tolerance_pkr=1)

    assert comparison.difference_pkr == pytest.approx(0.5)
    assert comparison.within_tolerance is True


def test_overbilled_total_is_flagged():
    result = calculate_bill(make_tariff(), 150)  # expected 2563.25

    comparison = compare_with_billed_total(result, 2663.25, tolerance_pkr=1)

    assert comparison.difference_pkr == pytest.approx(100)
    assert comparison.within_tolerance is False
