import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_current_community
from app.db.session import get_db
from app.models.community import Community
from app.models.user import User
from app.schemas.auth import PublicUserResponse
from app.services.user import get_community_profile

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(get_current_user)]
Scope = Annotated[Community, Depends(require_current_community)]


@router.get("/{user_id}", response_model=PublicUserResponse)
def profile(user_id: uuid.UUID, db: DB, user: Member, community: Scope) -> User:
    result = get_community_profile(db, user_id, community.id)
    if result is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return result
