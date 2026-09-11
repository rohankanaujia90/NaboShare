import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NaboScoreEvent(Base):
    __tablename__ = "nabo_score_events"
    __table_args__ = (
        UniqueConstraint("user_id", "rental_id", "reason", name="uq_score_event_once"),
        CheckConstraint(
            "reason IN ('ON_TIME_RETURN','POSITIVE_RATING','LATE_RETURN',"
            "'DAMAGED_ITEM_DISPUTE','CANCELLED_ACCEPTED_BOOKING')",
            name="ck_score_events_reason",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    rental_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rental_requests.id", ondelete="RESTRICT"), index=True
    )
    reason: Mapped[str] = mapped_column(String(40))
    delta: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RentalRating(Base):
    __tablename__ = "rental_ratings"
    __table_args__ = (
        UniqueConstraint("rental_id", "rater_id", name="uq_rental_rating_rater"),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_rental_ratings_value"),
        CheckConstraint("rater_id <> rated_user_id", name="ck_rental_ratings_not_self"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rental_requests.id", ondelete="RESTRICT"), index=True
    )
    rater_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    rated_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DamageDispute(Base):
    __tablename__ = "damage_disputes"
    __table_args__ = (
        UniqueConstraint("rental_id", name="uq_damage_dispute_rental"),
        CheckConstraint(
            "reported_by_id <> reported_user_id", name="ck_damage_disputes_not_self"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    rental_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rental_requests.id", ondelete="RESTRICT"), index=True
    )
    reported_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    reported_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
