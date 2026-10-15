"""Extraction Agent — reads a bill image/PDF and returns structured data.

Stub implementation: returns the example JSON from the shared contract
(Brief §8.1) so the frontend and API tests can be built against it.
Rehan will replace this with the real Gemini-based extraction in
SCRUM-10.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.bill import BillExtraction, ChargeLine


class ExtractionError(Exception):
    """The model returned output that could not be parsed into
    a valid ``BillExtraction``. Callers map this to HTTP 422."""


@dataclass
class ExtractionResult:
    """Value object returned by :func:`extract_bill`."""

    extraction: BillExtraction
    prompt_version: str
    model: str


# ---------------------------------------------------------------------------
# Example data from the shared contract (Brief §8.1)
# ---------------------------------------------------------------------------
_STUB_EXTRACTION = BillExtraction(
    utility="electricity",
    provider="K-Electric",
    billing_month="2026-09",
    issue_date="2026-09-10",
    due_date="2026-09-22",
    tariff_category="A-1",
    sanctioned_load_kw=3.0,
    meter_reading_previous=12000,
    meter_reading_current=12310,
    units_consumed=310,
    charges=[
        ChargeLine(name="Energy charges", amount_pkr=6200.0),
        ChargeLine(name="Fuel charge adjustment", amount_pkr=410.5),
        ChargeLine(name="GST", amount_pkr=1150.0),
    ],
    arrears_pkr=0,
    total_payable_by_due_date=8000.0,
    total_payable_after_due_date=8400.0,
    low_confidence_fields=["tariff_category"],
    notes=None,
)


def extract_bill(file_path: str, content_type: str) -> ExtractionResult:
    """Extract structured bill data from an uploaded file.

    Parameters
    ----------
    file_path:
        Absolute path to the saved upload (jpg, png, or pdf).
    content_type:
        MIME type of the uploaded file.

    Returns
    -------
    ExtractionResult
        Contains the ``BillExtraction``, the prompt version used, and the
        model name.

    Raises
    ------
    ExtractionError
        If the model output cannot be parsed (not raised by the stub).
    services.gemini.GeminiError
        If the model call itself fails (not raised by the stub).
    """
    # TODO(SCRUM-10): replace stub with real Gemini extraction.
    return ExtractionResult(
        extraction=_STUB_EXTRACTION,
        prompt_version="stub",
        model="stub",
    )
