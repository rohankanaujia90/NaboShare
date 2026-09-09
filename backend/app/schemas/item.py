import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

Category = Literal[
    "Electronics", "Tools", "Travel", "Books", "Sports", "Events", "Camping", "Other"
]
Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    category: Category
    rental_price_per_day: Money
    security_deposit: Money
    replacement_value: Money
    image_url: HttpUrl | None = Field(default=None, max_length=2048)
    availability: bool = True


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, min_length=10, max_length=5000)
    category: Category | None = None
    rental_price_per_day: Money | None = None
    security_deposit: Money | None = None
    replacement_value: Money | None = None
    image_url: HttpUrl | None = Field(default=None, max_length=2048)
    availability: bool | None = None

    @model_validator(mode="after")
    def reject_null_fields(self) -> "ItemUpdate":
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        for name in self.model_fields_set - {"image_url"}:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ItemResponse(ItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    owner_id: uuid.UUID
    community_id: uuid.UUID
    created_at: datetime


class ItemFilters(BaseModel):
    category: Category | None = None
    min_price: Money | None = None
    max_price: Money | None = None
    search: str | None = Field(default=None, max_length=160)
    availability: bool | None = None
    limit: int = Field(default=24, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_range(self) -> "ItemFilters":
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("Minimum price cannot exceed maximum price")
        return self


class ItemPage(BaseModel):
    items: list[ItemResponse]
    total: int
