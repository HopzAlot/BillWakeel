
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from models.tariff import TariffSchedule


VALID_TARIFF = {
    "discos": ["K-Electric", "IESCO", "LESCO"],
    "tariff_code": "A-1(a)",
    "tariff_category": "Domestic",
    "consumer_status": "protected",
    "billing_method": "telescopic",
    "metering_type": "regular",
    "min_sanctioned_load_kw": 0,
    "max_sanctioned_load_kw": 5,
    "effective_from": "2026-01-01",
    "effective_to": None,
    "slabs": [
        {
            "min_units": 0,
            "max_units": 100,
            "rate_per_unit_pkr": 10.54,
            "time_period": "all"
        },
        {
            "min_units": 100,
            "max_units": 200,
            "rate_per_unit_pkr": 13.01,
            "time_period": "all"
        }
    ],
    "fixed_charge": {
        "calculation_method": "per_kw_sanctioned_load",
        "rate_pkr": 200
    },
    "minimum_monthly_charge_pkr": None,
    "adjustments": [],
    "taxes": [],
    "source": {
        "url": "https://example.com/tariff.pdf",
        "retrieved_on": "2026-01-10",
        "document_name": "Sample tariff document",
        "clause": "Sample clause"
    }
}


def test_valid_tariff_is_accepted():
    tariff = TariffSchedule.model_validate(VALID_TARIFF)

    assert "K-Electric" in tariff.discos
    assert tariff.tariff_code == "A-1(a)"
    assert tariff.consumer_status == "protected"
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
    del data["tariff_code"]

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_empty_slabs_are_rejected():
    data = deepcopy(VALID_TARIFF)
    data["slabs"] = []

    with pytest.raises(ValidationError):
        TariffSchedule.model_validate(data)


def test_all_ke_tariff_json_records_validate():
    project_root = Path(__file__).resolve().parents[2]

    tariff_folder = (
        project_root
        / "data"
        / "tariffs"
        / "structured"
        / "k-electric"
    )

    json_files = sorted(tariff_folder.glob("*.json"))

    assert len(json_files) == 39

    for json_path in json_files:
        with json_path.open(encoding="utf-8-sig") as file:
            tariff_data = json.load(file)

        tariff = TariffSchedule.model_validate(tariff_data)

        assert tariff.discos
        assert tariff.tariff_code
        assert tariff.slabs