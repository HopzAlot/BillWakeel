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


def test_findings_catches_a_seeded_gst_error_end_to_end():
    # 351.27 is the exact engine value as of 2026-11-25 (after SCRUM-31
    # added the real Quarterly Tariff Adjustment to the tariff JSON, which
    # changed the base GST is a percentage of).
    body = {
        **_KE_A1A_BASE,
        "charges": [
            *_KE_A1A_BASE["charges"],
            {"name": "GST", "amount_pkr": 351.27 + 500},  # seeded error
        ],
    }
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 200

    data = response.json()
    assert data["bill_id"] == bill_id
    assert len(data["findings"]) == 1
    finding = data["findings"][0]
    assert finding["charge_name"] == "GST"
    assert finding["clause_text"]
    assert finding["source_url"].startswith("https://")


def test_findings_for_clean_bill_is_empty():
    body = {
        **_KE_A1A_BASE,
        "charges": [
            *_KE_A1A_BASE["charges"],
            {"name": "GST", "amount_pkr": 351.27},  # exact engine value
        ],
    }
    bill_id = _upload_and_set_extraction(body)

    response = client.get(f"/bills/{bill_id}/findings")
    assert response.status_code == 200
    assert response.json()["findings"] == []
