"""SCRUM-30 acceptance test: documents chunked and embedded; top-3 retrieval
returns the correct clause on a set of 10 test questions.

Each question is paired with a substring that only appears in the one
section of the real tariff extract that answers it. The test is a manual
check turned into an assertion: if the expected text isn't in any of the
top-3 chunks, retrieval failed that question.
"""

from pathlib import Path

import pytest

from agents.grounding import _citation_filter
from models.tariff import TariffCalculationInput
from services.tariff_engine import calculate_bill, load_tariff_schedules, select_tariff
from services.tariff_retrieval import (
    RAW_TARIFF_DIR,
    _get_index,
    chunk_document,
    retrieve,
    row_tariff_code,
    superseded_rows,
)

KE_DIR = RAW_TARIFF_DIR.parent / "structured" / "k-electric"

# (question, disco, substring expected somewhere in the top-3 chunks)
TEST_QUESTIONS = [
    (
        "What is the K-Electric A-1 Lifeline rate for up to 50 units?",
        "k-electric",
        "Rs. 3.95",
    ),
    (
        "What is the fixed charge for a protected K-Electric A-1a consumer using 101 to 200 units?",
        "k-electric",
        "Rs. 300 / kW",
    ),
    (
        "What is the GST rate applied on electricity bills?",
        "k-electric",
        "18%",
    ),
    (
        "What is the Late Payment Surcharge for an overdue electricity bill?",
        "k-electric",
        "10% of current bill",
    ),
    (
        "What is the fixed charge for a commercial A-2(a) connection under 5 kW?",
        "k-electric",
        "Rs. 1,000 / Cons / M",
    ),
    (
        "What is the variable rate for a small industrial B-1(a) regular connection?",
        "k-electric",
        "Rs. 26.23",
    ),
    (
        "What is the fixed charge for an agricultural tube well under D-2?",
        "k-electric",
        "Rs. 400 / kW / M",
    ),
    (
        "What is the Neelum-Jhelum surcharge rate per unit?",
        "k-electric",
        "Rs. 0.10 / kWh",
    ),
    (
        "What is the IESCO A-1 Lifeline rate for up to 50 units?",
        "iesco",
        "Rs. 3.95",
    ),
    (
        "What is the LESCO GST rate on electricity bills?",
        "lesco",
        "18%",
    ),
]


@pytest.mark.parametrize("question, disco, expected_substring", TEST_QUESTIONS)
def test_top3_retrieval_contains_expected_clause(question, disco, expected_substring):
    results = retrieve(question, disco, top_k=3)

    assert len(results) == 3
    assert any(expected_substring in result.chunk.text for result in results), (
        f"None of the top-3 chunks for {question!r} contained {expected_substring!r}: "
        f"{[r.chunk.clause_id for r in results]}"
    )


def test_retrieve_rejects_unknown_disco():
    with pytest.raises(ValueError):
        retrieve("What is the GST rate?", "SNGPL", top_k=3)


def test_chunks_carry_clause_ids_and_source_file():
    results = retrieve("What is the GST rate applied on electricity bills?", "k-electric", top_k=1)
    chunk = results[0].chunk

    assert chunk.clause_id.startswith("KE-")
    assert chunk.disco == "KE"
    assert chunk.source_file == "data/tariffs/raw/k-electric/tariff_extract_2026.md"


@pytest.mark.parametrize("disco_dir", ["k-electric", "iesco", "lesco"])
def test_every_superseded_guide_row_exists_and_leaves_the_index(disco_dir):
    path = RAW_TARIFF_DIR / disco_dir / "tariff_extract_2026.md"
    labels = {c.row_label for c in chunk_document(path, "KE")}
    # a renamed guide row would otherwise silently stay searchable
    assert superseded_rows() <= labels

    guide_labels = {
        c.row_label for c in _get_index(disco_dir).chunks if c.source_url is None
    }
    assert not guide_labels & superseded_rows()


@pytest.mark.parametrize("code, rate", [
    ("B-5", 23.13), ("D-2(b)", 28.69), ("E-1(i)", 52.89), ("E-1(ii)", 53.44),
    ("E-2", 42.25), ("G", 42.91), ("H", 42.10), ("K", 42.25),
])
def test_official_rows_are_cited_for_corrected_tariffs(code, rate):
    results = retrieve(f"What is the Energy charges for {code}?", "k-electric",
                       tariff_code=code, contains=f"{rate:.2f}")
    assert results and results[0].chunk.source_url
    assert row_tariff_code(results[0].chunk.row_label) == code


def test_every_tariff_file_can_cite_its_own_rate_row():
    """Run each schedule through the engine and check that an energy or fixed
    charge finding has a row of that tariff to cite."""
    missing = []
    for tariff in load_tariff_schedules(KE_DIR):
        if tariff.derived_from_tariff_code:
            continue
        for units in (40, 80, 150, 250, 450, 800):
            if tariff.consumer_status == "lifeline" and units > 100:
                continue
            if tariff.consumer_status == "protected" and units > 200:
                continue
            data = TariffCalculationInput(
                disco=tariff.discos[0], tariff_code=tariff.tariff_code,
                consumer_status=tariff.consumer_status, monthly_units=units,
                sanctioned_load_kw=3, peak_units=units / 4,
                off_peak_units=units * 3 / 4,
            )
            calculation = calculate_bill(tariff, data)
            for name in ("Energy charges", "Fixed charges"):
                results = retrieve(
                    f"What is the {name} for {tariff.tariff_code}?",
                    calculation.disco, **_citation_filter(name, 0, calculation),
                )
                if not results:
                    missing.append((tariff.tariff_code, tariff.consumer_status, units, name))
    assert not missing


@pytest.mark.parametrize("month, rate, sro", [
    ("2026-01", "0.3298", "2408"),
    ("2026-04", "0.3504", "459"),
    ("2026-07", "1.9857", "953"),
    ("2026-11", "0.5194", "1501"),
])
def test_qta_clause_matches_the_billing_month(month, rate, sro):
    query = "What is the Quarterly Tariff Adjustment (QTA) for A-1(a)?"
    best = retrieve(query, "k-electric", top_k=1, billing_month=month)[0].chunk

    assert rate in best.text
    assert best.clause_id.startswith(f"KE-{sro}-")
    assert sro in best.source_url


@pytest.mark.parametrize("code, status, name, row_label", [
    ("A-1(a)", "protected", "GST", "General Sales Tax (GST)"),
    ("A-1(a)", "protected", "Electricity Duty", "Electricity Duty (ED)"),
    # commercial duty is 2%, which no clause states: better dropped than mis-cited
    ("A-2(a)", None, "Electricity Duty", None),
])
def test_tax_citations_come_from_their_own_row(code, status, name, row_label):
    schedules = load_tariff_schedules(KE_DIR)
    data = TariffCalculationInput(disco="K-Electric", tariff_code=code,
                                  consumer_status=status, monthly_units=150,
                                  sanctioned_load_kw=3)
    calculation = calculate_bill(select_tariff(schedules, data), data)
    amount = next(t.amount_pkr for t in calculation.taxes if t.name == name)

    results = retrieve(f"What is the {name} for {code}?", "k-electric",
                       **_citation_filter(name, amount, calculation))

    assert [r.chunk.row_label for r in results][:1] == ([row_label] if row_label else [])
