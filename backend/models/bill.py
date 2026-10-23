"""Pydantic schemas for bill data.

These are the shared contract (Brief §8.1). Do not change field names
or types without agreement from the whole team.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChargeItem(BaseModel):
    """A single line item on a utility bill."""

    name: str
    amount_pkr: float


class BillExtraction(BaseModel):
    """Structured data extracted from a utility bill.

    Every field except ``charges`` and ``low_confidence_fields`` may be
    ``None`` when the bill does not show it or the model is unsure.
    Dates are ISO ``YYYY-MM-DD``; ``billing_month`` is ``YYYY-MM``.
    Money is in PKR as a number.  ``utility`` is one of
    ``electricity``, ``gas``, ``water``, ``unknown``.
    """

    utility: Optional[str] = None
    provider: Optional[str] = None
    billing_month: Optional[str] = None
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    tariff_category: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    meter_reading_previous: Optional[int] = None
    meter_reading_current: Optional[int] = None
    units_consumed: Optional[int] = None
    charges: list[ChargeItem] = Field(default_factory=list)
    arrears_pkr: Optional[float] = None
    total_payable_by_due_date: Optional[float] = None
    total_payable_after_due_date: Optional[float] = None
    low_confidence_fields: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class BillUploadResponse(BaseModel):
    """Returned by ``POST /bills``."""

    bill_id: str
    filename: str
    content_type: str
    size_bytes: int


class ExtractionResponse(BaseModel):
    """Returned by ``POST /bills/{bill_id}/extract``."""

    bill_id: str
    extraction: BillExtraction
    prompt_version: str
    model: str
