
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from models.tariff import TariffSchedule


VALID_TARIFF = {
    "disco": "K-Electric",
    "tariff_category": "A-1",
    "effective_from": "2026-01-01",
    "effective_to": None,
    "slabs": [
        {
            "min_units": 0,
            "max_units": 100,
            "rate_per_unit_pkr": 10
        },
        {
            "min_units": 100,
            "max_units": None,
            "rate_per_unit_pkr": 15
        }
    ],
    "fixed_charge_pkr": 0,
    "adjustments": [
        {
            "name": "FCA",
            "rate_pkr_per_unit": 2
        }
    ],
    "taxes": [
        {
            "name": "GST",
            "type": "percentage",
            "rate": 18,
            "basis": "energy_charge"
        }
    ],
    "source": {
        "url": "https://example.com/tariff.pdf",
        "retrieved_on": "2026-01-10",
        "document_name": "Sample tariff document",
        "clause": "Sample clause"
    }
}


def test_valid_tariff_is_accepted():
    tariff = TariffSchedule.model_validate(VALID_TARIFF)

    assert tariff.disco == "K-Electric"
    assert tariff.tariff_category == "A-1"
    assert len(tariff.slabs) == 2


def test_negative_slab_rate_is_rejected():
    data = deepcopy(VALID_TARIFF)
    data["slabs"][0]["rate_per_unit_pkr"] = -10

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_invalid_slab_range_is_rejected():
    data = deepcopy(VALID_TARIFF)
    data["slabs"][0]["min_units"] = 100
    data["slabs"][0]["max_units"] = 50

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_invalid_effective_dates_are_rejected():
    data = deepcopy(VALID_TARIFF)
    data["effective_from"] = "2026-12-01"
    data["effective_to"] = "2026-01-01"

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_missing_required_field_is_rejected():
    data = deepcopy(VALID_TARIFF)
    del data["tariff_category"]

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_empty_slabs_are_rejected():
    data = deepcopy(VALID_TARIFF)
    data["slabs"] = []

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_ke_tariff_json_structure():
    project_root = Path(__file__).resolve().parents[2]

    json_path = (
        project_root
        / "data"
        / "tariffs"
        / "structured"
        / "ke_tariff.json"
    )

    with json_path.open(encoding="utf-8") as file:
        tariff_data = json.load(file)

    tariff = TariffSchedule.model_validate(tariff_data)

    assert tariff.disco == "K-Electric"
