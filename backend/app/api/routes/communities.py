from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.community import Community
from app.models.user import User
from app.schemas.community import (
    CommunityResponse,
    CreateCommunityRequest,
    JoinCommunityRequest,
)
from app.services.community import (
    AlreadyInCommunityError,
    CommunityCreationError,
    CommunityNotFoundError,
    create_community,
    get_user_community,
    join_community,
)

router = APIRouter()


@router.post(
    "",
    response_model=CommunityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and join a community",
)
def create(
    data: CreateCommunityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Community:
    try:
        return create_community(db, current_user, data)
    except AlreadyInCommunityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already belong to a community",
        ) from exc
    except CommunityCreationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create a unique invite code. Please try again.",
        ) from exc


@router.post("/join", response_model=CommunityResponse, summary="Join a community")
def join(
    data: JoinCommunityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Community:
    try:
        return join_community(db, current_user, data.invite_code)
    except CommunityNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No community was found for this invite code",
        ) from exc
    except AlreadyInCommunityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already belong to a different community",
        ) from exc


@router.get("/me", response_model=CommunityResponse, summary="Current community")
def me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Community:
    community = get_user_community(db, current_user)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not joined a community",
        )
    return community
