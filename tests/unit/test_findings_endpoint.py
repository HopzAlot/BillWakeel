"""Integration-level test for GET /bills/{bill_id}/findings (SCRUM-31),
wired through the real upload -> extraction-store -> findings pipeline,
same style as test_upload.py.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from services.gemini import GeminiError

client = TestClient(app)

FAKE_JPG = b"\xff\xd8\xff\xe0" + b"0" * 100


@pytest.fixture(autouse=True)
def no_network_gemini(monkeypatch):
    def _raise(*args, **kwargs):
        raise GeminiError("no network in unit tests")

    monkeypatch.setattr("agents.grounding.get_llm", _raise)


def _upload_and_set_extraction(extraction_body: dict) -> str:
    upload_response = client.post(
        "/bills", files={"file": ("bill.jpg", FAKE_JPG, "image/jpeg")}
    )
    bill_id = upload_response.json()["bill_id"]

    put_response = client.put(f"/bills/{bill_id}/extraction", json=extraction_body)
    assert put_response.status_code == 200
    return bill_id


_KE_A1A_BASE = {
    "utility": "electricity",
    "provider": "K-Electric",
    "billing_month": "2026-07",  # inside the QTA's Jun-Aug 2026 window
    "tariff_category": "A-1a(01)",
    "sanctioned_load_kw": 2.0,
    "units_consumed": 145,
    "charges": [
        {"name": "Cost of electricity", "amount_pkr": 1639.45},
        {"name": "Fixed charges", "amount_pkr": 600.0},
        {"name": "Electricity duty", "amount_pkr": 24.59},
    ],
}


def test_findings_for_unknown_bill_is_404():
    response = client.get("/bills/does-not-exist/findings")
    assert response.status_code == 404


def test_findings_before_extraction_is_404():
    upload_response = client.post(
        "/bills", files={"file": ("bill.jpg", FAKE_JPG, "image/jpeg")}
    )
    bill_id = upload_response.json()["bill_id"]

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 404


def test_findings_for_unsupported_disco_is_422():
    body = {**_KE_A1A_BASE, "provider": "HAZECO", "charges": []}
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 422


def test_findings_resolves_iesco_against_the_uniform_national_schedule():
    # Pakistan's electricity tariff is nationally uniform by federal
    # subsidy: the only tariff JSON on file is K-Electric-sourced, but it
    # declares IESCO and LESCO too. An IESCO bill must resolve against it
    # rather than 404/422 just because there's no iesco/ folder of its own.
    # B-1(a) has no consumer_status split, so this is unambiguous.
    body = {
        "utility": "electricity",
        "provider": "IESCO",
        "tariff_category": "B-1(a)",
        "sanctioned_load_kw": 10.0,
        "units_consumed": 1000,
        "charges": [
            {"name": "Cost of electricity", "amount_pkr": 26230.0},  # exact engine value
            {"name": "Fixed charges", "amount_pkr": 1000.0},  # exact engine value
        ],
    }
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_findings_catches_a_seeded_qta_error_end_to_end():
    # A-1(a) status is unknown, so only status-independent lines are checked.
    # QTA for 145 units in July 2026 is 145 x -1.9857 = -287.93.
    body = {
        **_KE_A1A_BASE,
        "charges": [{"name": "Qtr tariff adjustment", "amount_pkr": -187.93}],
    }
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 200

    data = response.json()
    assert data["bill_id"] == bill_id
    assert len(data["findings"]) == 1
    finding = data["findings"][0]
    assert finding["charge_name"] == "Qtr tariff adjustment"
    assert finding["clause_text"]
    assert finding["source_url"].startswith("https://")


def test_findings_for_clean_bill_is_empty():
    body = {
        **_KE_A1A_BASE,
        "charges": [
            *_KE_A1A_BASE["charges"],
            {"name": "GST", "amount_pkr": 355.70},  # exact engine value
        ],
    }
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 200
    assert response.json()["findings"] == []


def test_findings_does_not_flag_status_dependent_charges_when_status_is_unknown():
    body = {**_KE_A1A_BASE, "charges": [
        {"name": "Cost of electricity", "amount_pkr": 2500.0},
        {"name": "GST", "amount_pkr": 900.0},
    ]}
    bill_id = _upload_and_set_extraction(body)

    data = client.get(f"/bills/{bill_id}/findings").json()

    assert data["findings"] == []
    assert any("were not checked" in w for w in data["warnings"])

