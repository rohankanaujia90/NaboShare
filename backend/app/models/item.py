import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint(
            "rental_price_per_day >= 0 AND security_deposit >= 0 "
            "AND replacement_value >= 0",
            name="ck_items_prices",
        ),
        CheckConstraint(
            "category IN ('Electronics','Tools','Travel','Books',"
            "'Sports','Events','Camping','Other')",
            name="ck_items_category",
        ),
        Index("ix_items_community_created", "community_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    community_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("communities.id"))
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(32))
    rental_price_per_day: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    replacement_value: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    image_url: Mapped[str | None] = mapped_column(String(2048))
    availability: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
