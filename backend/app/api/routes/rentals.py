import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_current_community
from app.db.session import get_db
from app.models.community import Community
from app.models.score import DamageDispute, RentalRating
from app.models.user import User
from app.schemas.rental import (
    DamageDisputeResponse,
    RentalAction,
    RentalCreate,
    RentalFilters,
    RentalPage,
    RentalRatingCreate,
    RentalRatingResponse,
    RentalResponse,
)
from app.services import rental as service
from app.services.scoring import report_damage, submit_rating

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(get_current_user)]
Scope = Annotated[Community, Depends(require_current_community)]


@router.post("", response_model=RentalResponse, status_code=201)
def create(
    data: RentalCreate, db: DB, user: Member, community: Scope
) -> RentalResponse:
    return service.create_rental(db, user, community.id, data)


@router.get("", response_model=RentalPage)
def browse(
    db: DB, user: Member, community: Scope, filters: Annotated[RentalFilters, Query()]
) -> RentalPage:
    return service.list_rentals(db, user.id, community.id, filters)


@router.get("/{rental_id}", response_model=RentalResponse)
def detail(
    rental_id: uuid.UUID, db: DB, user: Member, community: Scope
) -> RentalResponse:
    rental = service.get_rental(db, user.id, community.id, rental_id)
    return service.serialize_rental(db, rental, user.id)


@router.post(
    "/{rental_id}/rating", response_model=RentalRatingResponse, status_code=201
)
def rate(
    rental_id: uuid.UUID,
    data: RentalRatingCreate,
    db: DB,
    user: Member,
    community: Scope,
) -> RentalRating:
    rental = service.get_rental(db, user.id, community.id, rental_id)
    return submit_rating(db, rental, user.id, data.rating)


@router.post(
    "/{rental_id}/damage-dispute",
    response_model=DamageDisputeResponse,
    status_code=201,
)
def damage_dispute(
    rental_id: uuid.UUID, db: DB, user: Member, community: Scope
) -> DamageDispute:
    rental = service.get_rental(db, user.id, community.id, rental_id)
    return report_damage(db, rental, user.id)


@router.post("/{rental_id}/{action}", response_model=RentalResponse)
def transition(
    rental_id: uuid.UUID, action: RentalAction, db: DB, user: Member, community: Scope
) -> RentalResponse:
    return service.transition_rental(db, user, community.id, rental_id, action)
