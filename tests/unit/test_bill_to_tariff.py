from pathlib import Path

import pytest

from models.bill import BillExtraction, ChargeLine
from services.bill_to_tariff import (
    build_calculation_input,
    normalize_disco,
    normalize_tariff_code,
    resolve_consumer_status,
)
from services.charge_names import is_surcharge
from services.tariff_engine import TariffEngineError, load_tariff_schedules

KE_DIR = Path(__file__).resolve().parents[2] / "data" / "tariffs" / "structured" / "k-electric"


@pytest.mark.parametrize(
    "provider, expected",
    [
        ("K-Electric", "K-Electric"),
        ("k-electric", "K-Electric"),
        ("KE", "K-Electric"),
        ("IESCO", "IESCO"),
        ("lesco", "LESCO"),
    ],
)
def test_normalize_disco_known_aliases(provider, expected):
    assert normalize_disco(provider) == expected


def test_normalize_disco_rejects_unsupported_provider():
    with pytest.raises(TariffEngineError):
        normalize_disco("HAZECO")


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


def _resolve(units, energy_pkr):
    extraction = BillExtraction(
        provider="K-Electric", tariff_category="A-1a(01)", sanctioned_load_kw=2.0,
        units_consumed=units, billing_month="2026-07",
        charges=[] if energy_pkr is None else
        [ChargeLine(name="Cost of electricity", amount_pkr=energy_pkr)],
    )
    calc_input, _ = build_calculation_input(extraction, "K-Electric", "A-1(a)")
    return resolve_consumer_status(extraction, calc_input, load_tariff_schedules(KE_DIR))


@pytest.mark.parametrize("units, energy, status", [
    (323, 11776.58, "unprotected"),  # above 200 units
    (323, None, "unprotected"),
    (181, 5232.71, "unprotected"),   # 181 x 28.91
    (145, 1639.45, "protected"),     # 100 x 10.54 + 45 x 13.01
    (40, 158.0, "lifeline"),         # 40 x 3.95
])
def test_consumer_status_is_worked_out_from_units_or_printed_rate(units, energy, status):
    calc_input, warnings, unverifiable = _resolve(units, energy)

    assert calc_input.consumer_status == status
    assert warnings and status in warnings[0]
    assert unverifiable == frozenset()


@pytest.mark.parametrize("units, energy, qta_blocked", [
    (145, 2000.0, False),  # matches no status
    (145, None, False),
    (80, 999.0, True),     # could be lifeline, which pays no QTA
])
def test_unknown_consumer_status_blocks_dependent_charges(units, energy, qta_blocked):
    _, warnings, unverifiable = _resolve(units, energy)

    assert {"energy", "fixed", "gst", "electricity_duty"} <= unverifiable
    assert ("qta" in unverifiable) is qta_blocked
    assert "could not tell" in warnings[0]


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
