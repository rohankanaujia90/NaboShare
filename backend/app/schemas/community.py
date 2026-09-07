import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CommunityType(StrEnum):
    COLLEGE = "college"
    HOSTEL = "hostel"
    APARTMENT_SOCIETY = "apartment_society"
    CORPORATE_CAMPUS = "corporate_campus"


class CreateCommunityRequest(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    type: CommunityType
    city: str = Field(min_length=2, max_length=120)

    @field_validator("name", "city")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("Value must contain at least 2 characters")
        return normalized


class JoinCommunityRequest(BaseModel):
    invite_code: str = Field(min_length=8, max_length=12)

    @field_validator("invite_code")
    @classmethod
    def normalize_invite_code(cls, value: str) -> str:
        return value.strip().upper()


class CommunityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: CommunityType
    city: str
    invite_code: str
    created_at: datetime
