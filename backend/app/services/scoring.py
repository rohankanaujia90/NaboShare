import uuid
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rental import RentalRequest
from app.models.score import DamageDispute, NaboScoreEvent, RentalRating
from app.models.user import User

ScoreReason = Literal[
    "ON_TIME_RETURN",
    "POSITIVE_RATING",
    "LATE_RETURN",
    "DAMAGED_ITEM_DISPUTE",
    "CANCELLED_ACCEPTED_BOOKING",
]

SCORE_CHANGES: dict[ScoreReason, int] = {
    "ON_TIME_RETURN": 2,
    "POSITIVE_RATING": 1,
    "LATE_RETURN": -5,
    "DAMAGED_ITEM_DISPUTE": -10,
    "CANCELLED_ACCEPTED_BOOKING": -5,
}


class ScoringError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def score_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Average"
    return "Risky"


def apply_score_event(
    db: Session, user_id: uuid.UUID, rental_id: uuid.UUID, reason: ScoreReason
) -> bool:
    """Apply one auditable event once; caller owns the transaction."""
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise ScoringError(404, "User not found")
    existing = db.scalar(
        select(NaboScoreEvent.id).where(
            NaboScoreEvent.user_id == user_id,
            NaboScoreEvent.rental_id == rental_id,
            NaboScoreEvent.reason == reason,
        )
    )
    if existing is not None:
        return False
    delta = SCORE_CHANGES[reason]
    user.nabo_score = min(100, max(0, user.nabo_score + delta))
    db.add(
        NaboScoreEvent(user_id=user_id, rental_id=rental_id, reason=reason, delta=delta)
    )
    db.flush()
    return True


def submit_rating(
    db: Session,
    rental: RentalRequest,
    rater_id: uuid.UUID,
    rating: int,
) -> RentalRating:
    locked = db.scalar(
        select(RentalRequest)
        .where(RentalRequest.id == rental.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked is None:
        raise ScoringError(404, "Rental request not found")
    rental_id = locked.id
    borrower_id = locked.borrower_id
    owner_id = locked.owner_id
    status = locked.status
    if status != "RETURNED":
        raise ScoringError(409, "Ratings are available after the item is returned")
    rated_user_id = owner_id if rater_id == borrower_id else borrower_id
    existing = db.scalar(
        select(RentalRating.id).where(
            RentalRating.rental_id == rental_id, RentalRating.rater_id == rater_id
        )
    )
    if existing is not None:
        raise ScoringError(409, "You already rated this rental")
    result = RentalRating(
        rental_id=rental_id,
        rater_id=rater_id,
        rated_user_id=rated_user_id,
        rating=rating,
    )
    db.add(result)
    if rating >= 4:
        apply_score_event(db, rated_user_id, rental_id, "POSITIVE_RATING")
    db.commit()
    db.refresh(result)
    return result


def report_damage(
    db: Session, rental: RentalRequest, reporter_id: uuid.UUID
) -> DamageDispute:
    locked = db.scalar(
        select(RentalRequest)
        .where(RentalRequest.id == rental.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if locked is None:
        raise ScoringError(404, "Rental request not found")
    rental_id = locked.id
    owner_id = locked.owner_id
    borrower_id = locked.borrower_id
    status = locked.status
    if reporter_id != owner_id:
        raise ScoringError(403, "Only the item owner can report damage")
    if status not in ("ACTIVE", "RETURNED"):
        raise ScoringError(
            409, "Damage can be reported during or after an active rental"
        )
    if db.scalar(select(DamageDispute.id).where(DamageDispute.rental_id == rental_id)):
        raise ScoringError(409, "Damage was already reported for this rental")
    dispute = DamageDispute(
        rental_id=rental_id,
        reported_by_id=owner_id,
        reported_user_id=borrower_id,
    )
    db.add(dispute)
    apply_score_event(db, borrower_id, rental_id, "DAMAGED_ITEM_DISPUTE")
    db.commit()
    db.refresh(dispute)
    return dispute
