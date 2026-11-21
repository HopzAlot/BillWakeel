from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


class TariffSlab(BaseModel):
    min_units: float = Field(ge=0)
    max_units: float | None = Field(default=None, gt=0)
    rate_per_unit_pkr: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_slab_range(self):
        if self.max_units is not None and self.max_units <= self.min_units:
            raise ValueError("max_units must be greater than min_units")
        return self


class TariffAdjustment(BaseModel):
    name: Literal["FPA", "FCA", "QTA"]
    rate_pkr_per_unit: float


class TariffTax(BaseModel):
    name: str
    type: Literal["percentage", "fixed"]
    rate: float = Field(ge=0)
    basis: str


class TariffSource(BaseModel):
    url: HttpUrl
    retrieved_on: date
    document_name: str
    clause: str | None = None


class TariffSchedule(BaseModel):
    disco: str
    tariff_category: str
    effective_from: date
    effective_to: date | None = None
    slabs: list[TariffSlab] = Field(min_length=1)
    fixed_charge_pkr: float = Field(default=0, ge=0)
    adjustments: list[TariffAdjustment] = Field(default_factory=list)
    taxes: list[TariffTax] = Field(default_factory=list)
    source: TariffSource

    @model_validator(mode="after")
    def validate_effective_dates(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "effective_to cannot be earlier than effective_from"
            )
        return self
