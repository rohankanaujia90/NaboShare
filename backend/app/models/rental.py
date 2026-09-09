import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RentalRequest(Base):
    __tablename__ = "rental_requests"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_rentals_dates"),
        CheckConstraint("borrower_id <> owner_id", name="ck_rentals_not_self"),
        CheckConstraint(
            "rental_amount >= 0 AND platform_fee >= 0 AND security_deposit >= 0",
            name="ck_rentals_amounts",
        ),
        CheckConstraint(
            "status IN ('PENDING','ACCEPTED','REJECTED',"
            "'ACTIVE','RETURNED','CANCELLED')",
            name="ck_rentals_status",
        ),
        Index("ix_rentals_item_booking", "item_id", "status", "start_date", "end_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT")
    )
    borrower_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    rental_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(16, 2))
    security_deposit: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(
        String(16), default="PENDING", server_default="PENDING"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
