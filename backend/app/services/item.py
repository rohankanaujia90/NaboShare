import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.rental import RentalRequest
from app.schemas.item import ItemCreate, ItemFilters, ItemPage, ItemResponse, ItemUpdate


class ItemNotFoundError(Exception):
    pass


class ItemOwnershipError(Exception):
    pass


class ItemHasRentalsError(Exception):
    pass


def get_item(db: Session, community_id: uuid.UUID, item_id: uuid.UUID) -> Item:
    item = db.scalar(
        select(Item).where(Item.id == item_id, Item.community_id == community_id)
    )
    if item is None:
        raise ItemNotFoundError
    return item


def list_items(db: Session, community_id: uuid.UUID, filters: ItemFilters) -> ItemPage:
    query = select(Item).where(Item.community_id == community_id)
    if filters.category is not None:
        query = query.where(Item.category == filters.category)
    if filters.min_price is not None:
        query = query.where(Item.rental_price_per_day >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(Item.rental_price_per_day <= filters.max_price)
    if filters.availability is not None:
        query = query.where(Item.availability == filters.availability)
    if filters.search and filters.search.strip():
        term = filters.search.strip()
        query = query.where(
            or_(
                Item.title.icontains(term, autoescape=True),
                Item.description.icontains(term, autoescape=True),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Item.created_at.desc(), Item.id.desc())
        .offset(filters.offset)
        .limit(filters.limit)
    )
    return ItemPage(
        items=[ItemResponse.model_validate(item) for item in items], total=total
    )


def create_item(
    db: Session, community_id: uuid.UUID, owner_id: uuid.UUID, data: ItemCreate
) -> Item:
    values = data.model_dump()
    values["image_url"] = str(data.image_url) if data.image_url else None
    item = Item(**values, owner_id=owner_id, community_id=community_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item: Item, owner_id: uuid.UUID, data: ItemUpdate) -> Item:
    if item.owner_id != owner_id:
        raise ItemOwnershipError
    for key, value in data.model_dump(exclude_unset=True).items():
        if key == "image_url":
            value = str(value) if value else None
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: Item, owner_id: uuid.UUID) -> None:
    if item.owner_id != owner_id:
        raise ItemOwnershipError
    db.scalar(select(Item).where(Item.id == item.id).with_for_update())
    if db.scalar(
        select(RentalRequest.id).where(RentalRequest.item_id == item.id).limit(1)
    ):
        raise ItemHasRentalsError
    db.delete(item)
    db.commit()
