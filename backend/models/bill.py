from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChargeLine(BaseModel):
    name: str = Field(description="Charge name exactly as printed on the bill")
    amount_pkr: float = Field(description="Amount in PKR; use a negative number for credits")


class BillExtraction(BaseModel):
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
    extraction: BillExtraction
    prompt_version: str
    model: str
