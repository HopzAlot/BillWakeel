import pytest

from models.bill import BillExtraction
from services.bill_to_tariff import (
    build_calculation_input,
    normalize_disco,
    normalize_tariff_code,
    withhold_status_dependent_checks,
)
from services.charge_names import is_surcharge
from services.tariff_engine import TariffEngineError


@pytest.mark.parametrize(
    "provider, expected",
    [
        ("K-Electric", "K-Electric"),
        ("k-electric", "K-Electric"),
        ("KE", "K-Electric"),
        ("IESCO", "IESCO"),
        ("lesco", "LESCO"),
        # as the Extraction Agent actually returns them
        ("ISLAMABAD ELECTRIC SUPPLY COMPANY (LTD).", "IESCO"),
        ("Lahore Electric Supply Company Limited", "LESCO"),
        ("K-Electric Limited", "K-Electric"),
    ],
)
def test_normalize_disco_known_aliases(provider, expected):
    assert normalize_disco(provider) == expected


@pytest.mark.parametrize("provider", [
    "HAZECO", "HAZARA ELECTRIC SUPPLY COMPANY", "Hyderabad Electric Supply Company", None,
])
def test_normalize_disco_rejects_unsupported_provider(provider):
    with pytest.raises(TariffEngineError):
        normalize_disco(provider)


@pytest.mark.parametrize(
    "tariff_category, expected",
    [
        ("A-1a(01)", "A-1(a)"),
        ("A-1(a)", "A-1(a)"),
        ("B-3", "B-3"),
        ("K", "K"),
    ],
)
def test_normalize_tariff_code(tariff_category, expected):
    assert normalize_tariff_code(tariff_category) == expected


def test_normalize_tariff_code_rejects_missing_category():
    with pytest.raises(TariffEngineError):
        normalize_tariff_code(None)


@pytest.mark.parametrize("units, assumed, qta_blocked", [
    (80, "protected", True),     # could be lifeline, which pays no QTA
    (181, "protected", False),
    (323, "unprotected", False),  # only schedule that covers it
])
def test_a1a_status_dependent_charges_are_not_checked(units, assumed, qta_blocked):
    extraction = BillExtraction(
        provider="K-Electric", tariff_category="A-1a(01)",
        sanctioned_load_kw=2.0, units_consumed=units,
    )
    calc_input, _ = build_calculation_input(extraction, "K-Electric", "A-1(a)")
    calc_input, warnings, unverifiable = withhold_status_dependent_checks(calc_input)

    assert calc_input.consumer_status == assumed
    assert {"energy", "fixed", "gst", "electricity_duty"} <= unverifiable
    assert ("qta" in unverifiable) is qta_blocked
    assert "were not checked" in warnings[0]


def test_build_calculation_input_warns_when_billing_month_missing():
    extraction = BillExtraction(
        provider="IESCO", tariff_category="B-1(a)",
        sanctioned_load_kw=10.0, units_consumed=500,
    )
    calc_input, warnings = build_calculation_input(extraction, "IESCO", "B-1(a)")

    assert calc_input.billing_month is None
    assert any("billing_month" in w for w in warnings)


def test_build_calculation_input_requires_units_consumed():
    extraction = BillExtraction(provider="K-Electric", sanctioned_load_kw=2.0)
    with pytest.raises(TariffEngineError):
        build_calculation_input(extraction, "K-Electric", "B-1(a)")


@pytest.mark.parametrize("name, counted", [
    ("F.C surcharge", True),
    ("N.J. Surcharge", True),
    ("Late payment surcharge", False),
    ("L.P. Surcharge", False),
    ("GST on FC surcharge", False),
    ("Fuel price adjustment", False),
])
def test_only_supply_surcharges_enter_the_gst_base(name, counted):
    assert is_surcharge(name) is counted
