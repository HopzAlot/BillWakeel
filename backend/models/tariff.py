
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, model_validator


DISCO = Literal["K-Electric", "IESCO", "LESCO"]




class TariffFixedCharge(BaseModel):
    calculation_method: Literal[
        "per_kw_sanctioned_load",
        "per_consumer",
        "per_kw_max_load_or_mdi",
        "per_kw_max_25_percent_load_or_mdi",
        "per_kw_max_50_percent_load_or_mdi",
        "exempt",
        "derived_from_base_tariff",
    ]
    rate_pkr: float = Field(default=0, ge=0)

    # Multiplier for tariffs derived from another tariff's fixed charge.
    rate_multiplier: float | None = Field(default=None, gt=0)




class TariffSlab(BaseModel):
    min_units: float = Field(ge=0)
    max_units: float | None = Field(default=None, gt=0)

    # Use either one exact rate or a minimum/maximum rate range.
    rate_per_unit_pkr: float | None = Field(default=None, ge=0)
    rate_min_pkr: float | None = Field(default=None, ge=0)
    rate_max_pkr: float | None = Field(default=None, ge=0)
    rate_multiplier: float | None = Field(default=None, gt=0)

    time_period: Literal["all", "peak", "off_peak"] = "all"

    # Overrides the schedule-level fixed charge when present.
    fixed_charge: TariffFixedCharge | None = None

    
    @model_validator(mode="after")
    def validate_slab(self):
        if self.max_units is not None and self.max_units <= self.min_units:
            raise ValueError("max_units must be greater than min_units")

        exact_rate = self.rate_per_unit_pkr is not None
        has_range = (
            self.rate_min_pkr is not None
            and self.rate_max_pkr is not None
        )
        has_multiplier = self.rate_multiplier is not None

        # Exactly one rate representation must be provided.
        if sum([exact_rate, has_range, has_multiplier]) != 1:
            raise ValueError(
                "Provide exactly one of: exact rate, rate range, or rate multiplier"
            )

        if has_range and self.rate_max_pkr < self.rate_min_pkr:
            raise ValueError(
                "rate_max_pkr must be greater than or equal to rate_min_pkr"
            )

        if (self.rate_min_pkr is None) != (self.rate_max_pkr is None):
            raise ValueError(
                "Both rate_min_pkr and rate_max_pkr must be provided together"
            )

        return self




class TariffAdjustment(BaseModel):
    name: str
    rate_pkr_per_unit: float

    # "YYYY-MM", inclusive on both ends. None means unbounded in that
    # direction. Most adjustments (FCA/FPA monthly, QTA quarterly) are
    # only correct for a specific window, unlike the slabs/taxes around
    # them, which hold for the whole TariffSchedule's effective period.
    effective_from_month: str | None = None
    effective_to_month: str | None = None

    @model_validator(mode="after")
    def validate_window(self):
        if (
            self.effective_from_month is not None
            and self.effective_to_month is not None
            and self.effective_to_month < self.effective_from_month
        ):
            raise ValueError("effective_to_month cannot be earlier than effective_from_month")
        return self


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
    discos: list[DISCO] = Field(min_length=1)
    tariff_code: str
    tariff_category: str
    derived_from_tariff_code: str | None = None

    consumer_status: Literal[
        "lifeline", "protected", "unprotected"
    ] | None = None

    billing_method: Literal[
        "telescopic", "landing_slab", "flat"
    ] = "flat"

    metering_type: Literal["regular", "tou", "prepaid"] = "regular"

    min_sanctioned_load_kw: float | None = Field(default=None, ge=0)
    max_sanctioned_load_kw: float | None = Field(default=None, gt=0)

    effective_from: date
    effective_to: date | None = None

    slabs: list[TariffSlab] = Field(min_length=1)

    fixed_charge: TariffFixedCharge | None = None
    minimum_monthly_charge_pkr: float | None = Field(default=None, ge=0)
    # True when the minimum is a floor on energy + fixed charges (agricultural
    # D tariffs). False: it only applies to bills with no fixed charge.
    minimum_charge_includes_fixed: bool = False

    adjustments: list[TariffAdjustment] = Field(default_factory=list)
    taxes: list[TariffTax] = Field(default_factory=list)

    source: TariffSource

    @model_validator(mode="after")
    def validate_schedule(self):
        if (
            self.effective_to is not None
            and self.effective_to < self.effective_from
        ):
            raise ValueError(
                "effective_to cannot be earlier than effective_from"
            )

        if (
            self.min_sanctioned_load_kw is not None
            and self.max_sanctioned_load_kw is not None
            and self.max_sanctioned_load_kw < self.min_sanctioned_load_kw
        ):
            raise ValueError("Invalid sanctioned load range")

        return self


class TariffCalculationInput(BaseModel):
    disco: DISCO
    tariff_code: str
    monthly_units: float = Field(ge=0)
    sanctioned_load_kw: float = Field(gt=0)

    consumer_status: Literal[
        "lifeline", "protected", "unprotected"
    ] | None = None

    mdi_kw: float | None = Field(default=None, ge=0)
    peak_units: float | None = Field(default=None, ge=0)
    off_peak_units: float | None = Field(default=None, ge=0)

    # "YYYY-MM", same format as BillExtraction.billing_month. Needed to
    # decide whether a time-bounded TariffAdjustment (see above) applies;
    # without it, such adjustments are skipped, not guessed.
    billing_month: str | None = None
