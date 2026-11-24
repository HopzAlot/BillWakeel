"""SCRUM-31 acceptance test: agent compares bill to engine output; every
finding has a verifiable clause; uncited findings are dropped; zero
uncited on a seeded-error sample.

The seeded-error bill is K-Electric, A-1(a) protected, 145 units,
2 kW sanctioned load — real tariff numbers (checked directly against
`calculate_bill`), with exactly one charge (GST) deliberately inflated by
Rs. 500. Every other charge matches the engine exactly, so a false
positive on those would be a real bug, not noise.
"""

import pytest

from agents.grounding import TOLERANCE_PKR, ground_bill
from models.bill import BillExtraction, ChargeLine
from services.gemini import GeminiError
from services.tariff_engine import (
    calculate_bill,
    load_tariff_schedules,
    select_tariff,
)
from models.tariff import TariffCalculationInput

TARIFFS_DIR = "data/tariffs/structured/k-electric"


@pytest.fixture
def ke_a1a_calculation():
    schedules = load_tariff_schedules(TARIFFS_DIR)
    calc_input = TariffCalculationInput(
        disco="K-Electric",
        tariff_code="A-1(a)",
        monthly_units=145,
        sanctioned_load_kw=2.0,
        consumer_status="protected",
    )
    tariff = select_tariff(schedules, calc_input)
    return calculate_bill(tariff, calc_input)


@pytest.fixture(autouse=True)
def no_network_gemini(monkeypatch):
    """Force the deterministic fallback phrasing (agents/grounding.py's
    own except-GeminiError path) instead of a real network call — same
    as running with no GOOGLE_API_KEY configured."""

    def _raise(*args, **kwargs):
        raise GeminiError("no network in unit tests")

    monkeypatch.setattr("agents.grounding.get_llm", _raise)


def _clean_extraction(gst_amount_pkr: float) -> BillExtraction:
    return BillExtraction(
        utility="electricity",
        provider="K-Electric",
        tariff_category="A-1a(01)",
        sanctioned_load_kw=2.0,
        units_consumed=145,
        charges=[
            ChargeLine(name="Cost of electricity", amount_pkr=1639.45),
            ChargeLine(name="Fixed charges", amount_pkr=600.0),
            ChargeLine(name="Electricity duty", amount_pkr=24.59),
            ChargeLine(name="GST", amount_pkr=gst_amount_pkr),
            # No engine counterpart yet (SCRUM-28 doesn't model adjustments
            # yet) — must never produce a finding.
            ChargeLine(name="Fuel price adjustment", amount_pkr=71.0),
        ],
        total_payable_by_due_date=2485.0,
        total_payable_after_due_date=2586.0,
    )


def test_clean_bill_produces_no_findings(ke_a1a_calculation):
    extraction = _clean_extraction(gst_amount_pkr=403.1)  # exact engine value

    response = ground_bill("bill-1", extraction, ke_a1a_calculation)

    assert response.findings == []
    assert response.recalculated_total_pkr == ke_a1a_calculation.total_pkr


def test_seeded_gst_error_is_caught_with_a_real_citation(ke_a1a_calculation):
    extraction = _clean_extraction(gst_amount_pkr=403.1 + 500)  # seeded error

    response = ground_bill("bill-1", extraction, ke_a1a_calculation)

    assert len(response.findings) == 1
    finding = response.findings[0]
    assert finding.charge_name == "GST"
    assert finding.billed_amount_pkr == pytest.approx(903.1)
    assert finding.expected_amount_pkr == pytest.approx(403.1)
    assert finding.difference_pkr == pytest.approx(500.0)
    assert finding.clause_id.startswith("KE-")
    assert finding.clause_text  # a real retrieved clause, not empty
    assert finding.explanation  # phrased (here: the deterministic fallback)
    assert finding.source_url.startswith("https://")
    assert finding.confidence in {"high", "medium", "low"}


def test_small_difference_within_tolerance_is_not_a_finding(ke_a1a_calculation):
    extraction = _clean_extraction(gst_amount_pkr=403.1 + TOLERANCE_PKR / 2)

    response = ground_bill("bill-1", extraction, ke_a1a_calculation)

    assert response.findings == []


def test_unmatched_charge_lines_are_never_flagged(ke_a1a_calculation):
    # Fuel price adjustment has no engine counterpart (SCRUM-28 gap) even
    # though its billed amount (71.0) differs wildly from zero — the agent
    # must not invent an expected amount to compare it to.
    extraction = _clean_extraction(gst_amount_pkr=403.1)

    response = ground_bill("bill-1", extraction, ke_a1a_calculation)

    assert all(f.charge_name != "Fuel price adjustment" for f in response.findings)


def test_weak_citation_drops_the_finding_even_past_tolerance(ke_a1a_calculation, monkeypatch):
    from services.tariff_retrieval import ChunkResult, TariffChunk

    weak_chunk = TariffChunk(
        disco="KE", clause_id="KE-0", heading="unrelated", text="unrelated text",
        source_file="data/tariffs/raw/k-electric/tariff_extract_2026.md",
    )
    monkeypatch.setattr(
        "agents.grounding.retrieve",
        lambda query, disco, top_k=3: [ChunkResult(chunk=weak_chunk, score=0.05)],
    )

    extraction = _clean_extraction(gst_amount_pkr=403.1 + 500)
    response = ground_bill("bill-1", extraction, ke_a1a_calculation)

    assert response.findings == []
