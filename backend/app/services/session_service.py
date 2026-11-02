
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.session import UserSession

SESSION_COOKIE = "app_session"
SESSION_LIFETIME = timedelta(days=7)


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_session(
    db: Session,
    user_id: int,
) -> str:
    raw_token = secrets.token_urlsafe(32)

    now = datetime.now(timezone.utc)

    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        created_at=now,
        expires_at=now + SESSION_LIFETIME,
    )

    db.add(session)
    db.commit()

    return raw_token


def get_valid_session(
    db: Session,
    raw_token: str,
) -> UserSession | None:
    token_hash = hash_token(raw_token)

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == token_hash
        )
    )

    if session is None:
        return None

    expiry = session.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry <= datetime.now(timezone.utc):
        return None

    return session


def revoke_session(
    db: Session,
    raw_token: str,
) -> None:
    session = get_valid_session(db, raw_token)

    if session is not None:
        db.delete(session)
        db.commit()
