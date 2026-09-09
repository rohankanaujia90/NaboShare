import uuid
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.rental import RentalRequest
from app.models.user import User
from app.schemas.rental import (
    RentalAction,
    RentalCreate,
    RentalFilters,
    RentalPage,
    RentalResponse,
)

COMMISSION = Decimal("0.10")
TRANSITIONS: dict[str, dict[str, str]] = {
    "PENDING": {"accept": "ACCEPTED", "reject": "REJECTED", "cancel": "CANCELLED"},
    "ACCEPTED": {"start": "ACTIVE", "cancel": "CANCELLED"},
    "ACTIVE": {"return": "RETURNED"},
}


class RentalError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def today_utc() -> date:
    return datetime.now(UTC).date()


def calculate_amounts(
    start: date, end: date, daily_price: Decimal
) -> tuple[Decimal, Decimal]:
    days = (end - start).days
    if days <= 0:
        raise RentalError(422, "Return date must be after the start date")
    amount = (daily_price * days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    fee = (amount * COMMISSION).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return amount, fee


def next_status(status: str, action: str, is_owner: bool) -> str:
    if action != "cancel" and not is_owner:
        raise RentalError(403, "Only the owner can perform this action")
    target = TRANSITIONS.get(status, {}).get(action)
    if target is None:
        raise RentalError(409, f"Cannot {action} a rental in {status} status")
    return target


def lock_item(db: Session, item_id: uuid.UUID, community_id: uuid.UUID) -> Item:
    # All booking writers lock this same row before checking dates or status.
    item = db.scalar(
        select(Item)
        .where(Item.id == item_id, Item.community_id == community_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if item is None:
        raise RentalError(404, "Item not found")
    return item


def check_community(db: Session, item: Item, borrower_id: uuid.UUID) -> None:
    owner_community = db.scalar(
        select(User.community_id).where(User.id == item.owner_id)
    )
    borrower_community = db.scalar(
        select(User.community_id).where(User.id == borrower_id)
    )
    if owner_community != item.community_id or borrower_community != item.community_id:
        raise RentalError(403, "Owner and borrower must belong to the item's community")


def check_conflict(
    db: Session,
    item_id: uuid.UUID,
    start: date,
    end: date,
    exclude: uuid.UUID | None = None,
) -> None:
    query = select(RentalRequest.id).where(
        RentalRequest.item_id == item_id,
        RentalRequest.status.in_(["ACCEPTED", "ACTIVE"]),
        RentalRequest.start_date < end,
        RentalRequest.end_date > start,
    )
    if exclude is not None:
        query = query.where(RentalRequest.id != exclude)
    if db.scalar(query.limit(1)) is not None:
        raise RentalError(409, "This item is already booked for those dates")


def create_rental(
    db: Session, user: User, community_id: uuid.UUID, data: RentalCreate
) -> RentalRequest:
    if data.start_date < today_utc():
        raise RentalError(422, "Start date cannot be in the past")
    if (data.end_date - data.start_date).days > 365:
        raise RentalError(422, "Rentals cannot exceed 365 days")
    item = lock_item(db, data.item_id, community_id)
    if item.owner_id == user.id:
        raise RentalError(409, "You cannot rent your own item")
    check_community(db, item, user.id)
    if not item.availability:
        raise RentalError(409, "This item is not available")
    amount, fee = calculate_amounts(
        data.start_date, data.end_date, item.rental_price_per_day
    )
    check_conflict(db, item.id, data.start_date, data.end_date)
    duplicate = db.scalar(
        select(RentalRequest.id).where(
            RentalRequest.item_id == item.id,
            RentalRequest.borrower_id == user.id,
            RentalRequest.status == "PENDING",
            RentalRequest.start_date == data.start_date,
            RentalRequest.end_date == data.end_date,
        )
    )
    if duplicate:
        raise RentalError(409, "You already requested this item for those dates")
    rental = RentalRequest(
        item_id=item.id,
        borrower_id=user.id,
        owner_id=item.owner_id,
        start_date=data.start_date,
        end_date=data.end_date,
        rental_amount=amount,
        platform_fee=fee,
        security_deposit=item.security_deposit,
    )
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


def participant_query(
    user_id: uuid.UUID, community_id: uuid.UUID
) -> Select[tuple[RentalRequest]]:
    return (
        select(RentalRequest)
        .join(Item, Item.id == RentalRequest.item_id)
        .where(
            Item.community_id == community_id,
            or_(
                RentalRequest.owner_id == user_id, RentalRequest.borrower_id == user_id
            ),
        )
    )


def get_rental(
    db: Session, user_id: uuid.UUID, community_id: uuid.UUID, rental_id: uuid.UUID
) -> RentalRequest:
    rental = db.scalar(
        participant_query(user_id, community_id).where(RentalRequest.id == rental_id)
    )
    if rental is None:
        raise RentalError(404, "Rental request not found")
    return rental


def list_rentals(
    db: Session, user_id: uuid.UUID, community_id: uuid.UUID, filters: RentalFilters
) -> RentalPage:
    query = participant_query(user_id, community_id)
    if filters.role == "owner":
        query = query.where(RentalRequest.owner_id == user_id)
    elif filters.role == "borrower":
        query = query.where(RentalRequest.borrower_id == user_id)
    if filters.status:
        query = query.where(RentalRequest.status == filters.status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rentals = db.scalars(
        query.order_by(RentalRequest.created_at.desc(), RentalRequest.id.desc())
        .offset(filters.offset)
        .limit(filters.limit)
    )
    return RentalPage(
        rentals=[RentalResponse.model_validate(r) for r in rentals], total=total
    )


def transition_rental(
    db: Session,
    user: User,
    community_id: uuid.UUID,
    rental_id: uuid.UUID,
    action: RentalAction,
) -> RentalRequest:
    rental = get_rental(db, user.id, community_id, rental_id)
    item = lock_item(db, rental.item_id, community_id)
    # Refresh changes made by a competing transaction while we waited for the lock.
    db.refresh(rental)
    target = next_status(rental.status, action, user.id == rental.owner_id)
    if action in ("accept", "start"):
        check_community(db, item, rental.borrower_id)
        if not item.availability:
            raise RentalError(409, "This item is not available")
    if action == "accept":
        if rental.start_date < today_utc():
            raise RentalError(409, "Cannot accept a request with a past start date")
        check_conflict(db, item.id, rental.start_date, rental.end_date, rental.id)
    if action == "start":
        if not rental.start_date <= today_utc() < rental.end_date:
            raise RentalError(409, "Pickup must occur within the booked dates")
        if db.scalar(
            select(RentalRequest.id).where(
                RentalRequest.item_id == item.id, RentalRequest.status == "ACTIVE"
            )
        ):
            raise RentalError(409, "The item has not been returned from another rental")
    if (
        action == "cancel"
        and rental.status == "ACCEPTED"
        and today_utc() >= rental.start_date
    ):
        raise RentalError(
            409, "Accepted rentals can only be cancelled before the start date"
        )
    rental.status = target
    db.commit()
    db.refresh(rental)
    return rental
