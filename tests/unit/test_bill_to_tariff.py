import pytest

from models.bill import BillExtraction
from services.bill_to_tariff import (
    build_calculation_input,
    normalize_disco,
    normalize_tariff_code,
)
from services.tariff_engine import TariffEngineError


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


def test_build_calculation_input_guesses_protected_for_a1a_with_warning():
    extraction = BillExtraction(
        provider="K-Electric", tariff_category="A-1a(01)",
        sanctioned_load_kw=2.0, units_consumed=145,
    )
    calc_input, warnings = build_calculation_input(extraction, "K-Electric", "A-1(a)")

    assert calc_input.consumer_status == "protected"
    assert len(warnings) == 1
    assert "consumer_status" in warnings[0]


def test_build_calculation_input_requires_units_consumed():
    extraction = BillExtraction(provider="K-Electric", sanctioned_load_kw=2.0)
    with pytest.raises(TariffEngineError):
        build_calculation_input(extraction, "K-Electric", "B-1(a)")
