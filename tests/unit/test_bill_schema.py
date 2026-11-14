# tests/unit/test_bill_schema.py
"""Unit tests for the BillExtraction schema (backend/models/bill.py)."""
import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from models.bill import BillExtraction

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = REPO_ROOT / "data" / "samples"

# The example from the shared contract (brief section 8.1). Illustrative values.
VALID = {
    "utility": "electricity",
    "provider": "K-Electric",
    "billing_month": "2026-09",
    "issue_date": "2026-09-10",
    "due_date": "2026-09-22",
    "tariff_category": "A-1",
    "sanctioned_load_kw": 3.0,
    "meter_reading_previous": 12000,
    "meter_reading_current": 12310,
    "units_consumed": 310,
    "charges": [
        {"name": "Energy charges", "amount_pkr": 6200.0},
        {"name": "Fuel charge adjustment", "amount_pkr": 410.5},
        {"name": "GST", "amount_pkr": 1150.0},
    ],
    "arrears_pkr": 0,
    "total_payable_by_due_date": 8000.0,
    "total_payable_after_due_date": 8400.0,
    "low_confidence_fields": ["tariff_category"],
    "notes": None,
}


def make(**changes):
    """Return a copy of VALID with some fields changed."""
    data = copy.deepcopy(VALID)
    data.update(changes)
    return data


# ---------------------------------------------------------------- valid input
def test_valid_example_parses():
    bill = BillExtraction.model_validate(VALID)
    assert bill.units_consumed == 310
    assert len(bill.charges) == 3
    assert bill.charges[1].amount_pkr == 410.5


def test_all_optional_fields_can_be_null():
    """Every field may be null except charges, low_confidence_fields and utility.
    utility uses "unknown" instead of null (team decision, see docs/decisions.md)."""
    data = {key: None for key in VALID}
    data["utility"] = "unknown"
    data["charges"] = []
    data["low_confidence_fields"] = []
    bill = BillExtraction.model_validate(data)
    assert bill.units_consumed is None
    assert bill.charges == []


def test_utility_cannot_be_null():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(utility=None))


def test_utility_defaults_to_unknown():
    assert BillExtraction.model_validate({}).utility == "unknown"


def test_gas_units_can_be_fractional():
    bill = BillExtraction.model_validate(make(utility="gas", units_consumed=0.389))
    assert bill.units_consumed == 0.389


def test_empty_object_uses_defaults():
    bill = BillExtraction.model_validate({})
    assert bill.charges == []
    assert bill.low_confidence_fields == []


def test_negative_charge_is_allowed():
    """Adjustments such as quarterly tariff adjustment can be negative."""
    bill = BillExtraction.model_validate(
        make(charges=[{"name": "Quarterly tariff adjustment", "amount_pkr": -288.0}])
    )
    assert bill.charges[0].amount_pkr == -288.0


# -------------------------------------------------------------- invalid input
def test_rejects_charge_without_amount():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(charges=[{"name": "GST"}]))


def test_rejects_charge_with_text_amount():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(charges=[{"name": "GST", "amount_pkr": "abc"}]))


def test_rejects_text_in_units_consumed():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(units_consumed="three hundred"))


def test_rejects_charges_that_is_not_a_list():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(charges="GST 1150"))


def test_rejects_unknown_utility():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(utility="solar"))


def test_rejects_malformed_date():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(issue_date="2026-13-45"))


# Known gap: the brief says billing_month is YYYY-MM, but bill.py does not check
# the format yet. xfail(strict=True) turns red as a reminder once it is fixed.
@pytest.mark.xfail(strict=True, reason="bill.py does not check the YYYY-MM format of billing_month yet")
def test_rejects_malformed_billing_month():
    with pytest.raises(ValidationError):
        BillExtraction.model_validate(make(billing_month="September 2026"))


# ------------------------------------------------- ground-truth sample files
SAMPLE_FILES = sorted(SAMPLES_DIR.glob("*.json"))


def test_samples_folder_has_ground_truth():
    assert len(SAMPLE_FILES) >= 10, f"expected at least 10 ground-truth files in {SAMPLES_DIR}"


@pytest.mark.parametrize("path", SAMPLE_FILES, ids=lambda p: p.name)
def test_ground_truth_file_matches_schema(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    BillExtraction.model_validate(data)


@pytest.mark.parametrize("path", [p for p in SAMPLE_FILES if not p.name.startswith("sngpl_")],
                         ids=lambda p: p.name)
def test_ground_truth_units_match_meter_readings(path):
    """For electricity bills, current - previous reading must equal units consumed."""
    d = json.loads(path.read_text(encoding="utf-8"))
    assert d["meter_reading_current"] - d["meter_reading_previous"] == d["units_consumed"]
