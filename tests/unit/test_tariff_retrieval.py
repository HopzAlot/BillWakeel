"""SCRUM-30 acceptance test: documents chunked and embedded; top-3 retrieval
returns the correct clause on a set of 10 test questions.

Each question is paired with a substring that only appears in the one
section of the real tariff extract that answers it. The test is a manual
check turned into an assertion: if the expected text isn't in any of the
top-3 chunks, retrieval failed that question.
"""

import pytest

from services.tariff_retrieval import retrieve

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
