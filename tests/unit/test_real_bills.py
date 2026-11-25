"""The two anonymised IESCO bills in data/samples, run end to end without
Gemini. Both were billed correctly as far as we can check, so any finding
here is a false one.
"""

import json
from pathlib import Path

import pytest

from agents import grounding
from models.bill import BillExtraction
from services.bill_to_tariff import (
    build_calculation_input,
    normalize_disco,
    normalize_tariff_code,
    resolve_consumer_status,
)
from services.gemini import GeminiError
from services.tariff_engine import calculate_bill, load_tariff_schedules, select_tariff

ROOT = Path(__file__).resolve().parents[2]
KE_DIR = ROOT / "data" / "tariffs" / "structured" / "k-electric"


@pytest.fixture(autouse=True)
def no_network_gemini(monkeypatch):
    def _raise(*args, **kwargs):
        raise GeminiError("no network in unit tests")

    monkeypatch.setattr("agents.grounding.get_llm", _raise)


@pytest.mark.parametrize("sample", ["iesco_001", "iesco_002"])
def test_real_bill_has_no_findings_and_matches_to_the_rupee(sample):
    raw = json.loads((ROOT / "data" / "samples" / f"{sample}.json").read_text())
    extraction = BillExtraction.model_validate(
        {k: v for k, v in raw.items() if k in BillExtraction.model_fields}
    )
    disco = normalize_disco(extraction.provider)
    code = normalize_tariff_code(extraction.tariff_category)
    calc_input, _ = build_calculation_input(extraction, disco, code)
    schedules = load_tariff_schedules(KE_DIR)
    calc_input, _, unverifiable = resolve_consumer_status(extraction, calc_input, schedules)
    calculation = calculate_bill(select_tariff(schedules, calc_input), calc_input)

    response = grounding.ground_bill(sample, extraction, calculation, unverifiable)

    assert unverifiable == frozenset()
    assert response.findings == []
    billed = {c.name: c.amount_pkr for c in extraction.charges}
    expected = {t.name: t.amount_pkr for t in calculation.taxes}
    assert expected["GST"] == pytest.approx(billed["GST"], abs=1)
    assert expected["Electricity Duty"] == pytest.approx(billed["E.D."], abs=1)
    assert calculation.energy_charge_pkr == pytest.approx(billed["Cost of electricity"], abs=1)
    assert calculation.fixed_charge_pkr == pytest.approx(billed["Fixed charges"], abs=1)
    assert calculation.adjustments[0].amount_pkr == pytest.approx(billed["Qtr tariff adjustment"], abs=1)
