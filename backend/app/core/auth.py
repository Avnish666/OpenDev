
from fastapi import (
    Cookie,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.services.session_service import (
    SESSION_COOKIE,
    get_valid_session,
)


def get_current_user(
    db: Session = Depends(get_db),
    app_session: str | None = Cookie(
        default=None,
        alias=SESSION_COOKIE,
    ),
) -> User:
    if not app_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session = get_valid_session(db, app_session)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user = db.get(User, session.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    return user


def get_optional_user(db: Session = Depends(get_db), app_session: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> User | None:
    if not app_session:
        return None
    return get_current_user(db, app_session)
