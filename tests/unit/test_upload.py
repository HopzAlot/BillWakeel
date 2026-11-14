# tests/unit/test_upload.py
"""Unit tests for the Sprint 1 API (backend/main.py and backend/api/bills.py)."""
import pytest
from fastapi.testclient import TestClient

from config import settings
from main import app

client = TestClient(app)

# Tiny fake files that start with the real "magic bytes" of each format.
FAKE_JPG = b"\xff\xd8\xff\xe0" + b"0" * 100
FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
FAKE_PDF = b"%PDF-1.4\n" + b"0" * 100


@pytest.fixture(autouse=True)
def temp_upload_dir(tmp_path, monkeypatch):
    """Save test uploads in a temporary folder instead of data/uploads."""
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


def upload(name, content, content_type):
    return client.post("/bills", files={"file": (name, content, content_type)})


# ------------------------------------------------------------------ health
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------- upload: accept
@pytest.mark.parametrize("name, content, content_type", [
    ("bill.jpg", FAKE_JPG, "image/jpeg"),
    ("bill.png", FAKE_PNG, "image/png"),
    ("bill.pdf", FAKE_PDF, "application/pdf"),
])
def test_accepts_valid_file_types(name, content, content_type, temp_upload_dir):
    r = upload(name, content, content_type)
    assert r.status_code == 201
    body = r.json()
    assert body["bill_id"]
    assert body["filename"] == name
    assert body["content_type"] == content_type
    assert body["size_bytes"] == len(content)
    # Saved under the generated id, never the user's filename
    saved = list(temp_upload_dir.iterdir())
    assert len(saved) == 1
    assert saved[0].name.startswith(body["bill_id"])


def test_filename_is_not_used_as_path(temp_upload_dir):
    r = upload("../../evil.png", FAKE_PNG, "image/png")
    assert r.status_code == 201
    saved = list(temp_upload_dir.iterdir())
    assert len(saved) == 1
    assert "evil" not in saved[0].name


# ---------------------------------------------------------- upload: reject
def test_rejects_text_file():
    r = upload("notes.txt", b"hello", "text/plain")
    assert r.status_code == 415
    assert "detail" in r.json()


def test_rejects_empty_file():
    r = upload("empty.png", b"", "image/png")
    assert r.status_code == 400
    assert "detail" in r.json()


def test_rejects_oversized_file(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)  # keep the test fast
    too_big = FAKE_PNG + b"0" * (1024 * 1024)
    r = upload("big.png", too_big, "image/png")
    assert r.status_code == 413
    assert "detail" in r.json()


def test_accepts_file_exactly_at_limit(monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    exact = FAKE_PNG + b"0" * (1024 * 1024 - len(FAKE_PNG))
    r = upload("exact.png", exact, "image/png")
    assert r.status_code == 201


# ------------------------------------------------- extract / save corrections
def test_extract_unknown_bill_returns_404():
    r = client.post("/bills/does-not-exist/extract")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_put_unknown_bill_returns_404():
    r = client.put("/bills/does-not-exist/extraction", json={})
    assert r.status_code == 404


def test_put_saves_valid_correction():
    bill_id = upload("bill.png", FAKE_PNG, "image/png").json()["bill_id"]
    body = {"units_consumed": 145, "charges": [{"name": "GST", "amount_pkr": 366.0}]}
    r = client.put(f"/bills/{bill_id}/extraction", json=body)
    assert r.status_code == 200
    assert r.json()["units_consumed"] == 145
    assert r.json()["charges"][0]["amount_pkr"] == 366.0


def test_put_rejects_invalid_body():
    bill_id = upload("bill.png", FAKE_PNG, "image/png").json()["bill_id"]
    r = client.put(f"/bills/{bill_id}/extraction", json={"charges": [{"name": "GST"}]})
    assert r.status_code == 422
