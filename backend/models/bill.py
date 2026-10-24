"""Pydantic schemas for bill data.

These are the shared contract (Brief §8.1). Do not change field names
or types without agreement from the whole team.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChargeLine(BaseModel):
    name: str = Field(description="Charge name exactly as printed on the bill")
    amount_pkr: float = Field(description="Amount in PKR; use a negative number for credits")


class BillExtraction(BaseModel):
    """Structured data extracted from a utility bill.

    Every field except ``charges`` and ``low_confidence_fields`` may be
    ``None`` when the bill does not show it or the model is unsure.
    Dates are ISO ``YYYY-MM-DD``; ``billing_month`` is ``YYYY-MM``.
    Money is in PKR as a number. ``units_consumed`` and meter readings
    are floats, not ints — gas bills report fractional HM3 (e.g. 0.389).
    """

    utility: Literal["electricity", "gas", "water", "unknown"] = "unknown"
    provider: Optional[str] = None
    billing_month: Optional[str] = Field(default=None, description="YYYY-MM")
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    tariff_category: Optional[str] = None
    sanctioned_load_kw: Optional[float] = None
    meter_reading_previous: Optional[float] = None
    meter_reading_current: Optional[float] = None
    units_consumed: Optional[float] = None
    charges: list[ChargeLine] = Field(default_factory=list)
    arrears_pkr: Optional[float] = None
    total_payable_by_due_date: Optional[float] = None
    total_payable_after_due_date: Optional[float] = None
    low_confidence_fields: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ExtractionResult(BaseModel):
    """Value object returned by ``extract_bill()``."""

    extraction: BillExtraction
    prompt_version: str
    model: str


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
