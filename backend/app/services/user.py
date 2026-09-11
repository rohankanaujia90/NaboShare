import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_community_profile(
    db: Session, user_id: uuid.UUID, community_id: uuid.UUID
) -> User | None:
    return db.scalar(
        select(User).where(User.id == user_id, User.community_id == community_id)
    )
