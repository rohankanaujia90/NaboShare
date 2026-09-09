import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_current_community
from app.db.session import get_db
from app.models.community import Community
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemFilters, ItemPage, ItemResponse, ItemUpdate
from app.services import item as service

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(get_current_user)]
Scope = Annotated[Community, Depends(require_current_community)]


def scoped_item(item_id: uuid.UUID, db: DB, community: Scope) -> Item:
    try:
        return service.get_item(db, community.id, item_id)
    except service.ItemNotFoundError as exc:
        raise HTTPException(404, "Item not found") from exc


@router.post("", response_model=ItemResponse, status_code=201)
def create(data: ItemCreate, db: DB, user: Member, community: Scope) -> Item:
    return service.create_item(db, community.id, user.id, data)


@router.get("", response_model=ItemPage)
def browse(
    db: DB, community: Scope, filters: Annotated[ItemFilters, Query()]
) -> ItemPage:
    return service.list_items(db, community.id, filters)


@router.get("/{item_id}", response_model=ItemResponse)
def detail(item: Annotated[Item, Depends(scoped_item)]) -> Item:
    return item


@router.patch("/{item_id}", response_model=ItemResponse)
def update(
    data: ItemUpdate, db: DB, user: Member, item: Annotated[Item, Depends(scoped_item)]
) -> Item:
    try:
        return service.update_item(db, item, user.id, data)
    except service.ItemOwnershipError as exc:
        raise HTTPException(403, "Only the owner can change this item") from exc


@router.delete("/{item_id}", status_code=204)
def delete(
    db: DB, user: Member, item: Annotated[Item, Depends(scoped_item)]
) -> Response:
    try:
        service.delete_item(db, item, user.id)
    except service.ItemOwnershipError as exc:
        raise HTTPException(403, "Only the owner can delete this item") from exc
    except service.ItemHasRentalsError as exc:
        raise HTTPException(
            409, "Items with rental history cannot be deleted; mark unavailable instead"
        ) from exc
    return Response(status_code=204)
