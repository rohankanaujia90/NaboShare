import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.community import Community
from app.models.user import User
from app.schemas.community import CreateCommunityRequest

INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class AlreadyInCommunityError(Exception):
    pass


class CommunityNotFoundError(Exception):
    pass


class CommunityCreationError(Exception):
    pass


def generate_invite_code() -> str:
    return "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(8))


def create_community(
    db: Session,
    current_user: User,
    data: CreateCommunityRequest,
) -> Community:
    if current_user.community_id is not None:
        raise AlreadyInCommunityError

    community = Community(
        name=data.name,
        type=data.type.value,
        city=data.city,
        invite_code=generate_invite_code(),
    )
    db.add(community)
    current_user.community = community
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise CommunityCreationError from exc
    db.refresh(community)
    return community


def join_community(db: Session, current_user: User, invite_code: str) -> Community:
    community = db.scalar(select(Community).where(Community.invite_code == invite_code))
    if community is None:
        raise CommunityNotFoundError
    if current_user.community_id is not None:
        if current_user.community_id == community.id:
            return community
        raise AlreadyInCommunityError

    current_user.community = community
    db.commit()
    db.refresh(community)
    return community


def get_user_community(db: Session, current_user: User) -> Community | None:
    if current_user.community_id is None:
        return None
    return db.get(Community, current_user.community_id)
