import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_current_community
from app.db.session import get_db
from app.models.community import Community
from app.models.rental import RentalRequest
from app.models.user import User
from app.schemas.rental import (
    RentalAction,
    RentalCreate,
    RentalFilters,
    RentalPage,
    RentalResponse,
)
from app.services import rental as service

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(get_current_user)]
Scope = Annotated[Community, Depends(require_current_community)]


@router.post("", response_model=RentalResponse, status_code=201)
def create(data: RentalCreate, db: DB, user: Member, community: Scope) -> RentalRequest:
    return service.create_rental(db, user, community.id, data)


@router.get("", response_model=RentalPage)
def browse(
    db: DB, user: Member, community: Scope, filters: Annotated[RentalFilters, Query()]
) -> RentalPage:
    return service.list_rentals(db, user.id, community.id, filters)


@router.get("/{rental_id}", response_model=RentalResponse)
def detail(
    rental_id: uuid.UUID, db: DB, user: Member, community: Scope
) -> RentalRequest:
    return service.get_rental(db, user.id, community.id, rental_id)


@router.post("/{rental_id}/{action}", response_model=RentalResponse)
def transition(
    rental_id: uuid.UUID, action: RentalAction, db: DB, user: Member, community: Scope
) -> RentalRequest:
    return service.transition_rental(db, user, community.id, rental_id, action)
