import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RentalStatus = Literal[
    "PENDING", "ACCEPTED", "REJECTED", "ACTIVE", "RETURNED", "CANCELLED"
]
RentalAction = Literal["accept", "reject", "cancel", "start", "return"]


class RentalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: uuid.UUID
    start_date: date
    end_date: date


class RentalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    item_id: uuid.UUID
    borrower_id: uuid.UUID
    owner_id: uuid.UUID
    start_date: date
    end_date: date
    rental_amount: Decimal
    platform_fee: Decimal
    security_deposit: Decimal
    status: RentalStatus
    created_at: datetime


class RentalFilters(BaseModel):
    role: Literal["borrower", "owner"] | None = None
    status: RentalStatus | None = None
    limit: int = Field(default=24, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RentalPage(BaseModel):
    rentals: list[RentalResponse]
    total: int
