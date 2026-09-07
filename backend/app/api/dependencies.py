from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.community import Community
from app.models.user import User
from app.services.auth import get_user_by_id
from app.services.community import get_user_community

bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as exc:
        raise unauthorized() from exc

    user = get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized()
    return user


def require_current_community(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Community:
    """Resolve the server-side community scope for community-owned resources."""
    community = get_user_community(db, current_user)
    if community is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Join a community before accessing community items",
        )
    return community
