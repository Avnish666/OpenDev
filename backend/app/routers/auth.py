
import secrets
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from fastapi.responses import RedirectResponse

from app.core.auth import get_current_user
from app.services.session_service import (
    SESSION_COOKIE,
    SESSION_LIFETIME,
    create_session,
    revoke_session,
)

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.github_auth import (
    exchange_code_for_token,
    get_github_user,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

STATE_COOKIE = "github_oauth_state"


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "avatar_url": current_user.avatar_url,
    }


def require_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")

    if origin != settings.FRONTEND_URL:
        raise HTTPException(
            status_code=403,
            detail="Untrusted request origin",
        )



@router.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(require_trusted_origin),
):
    token = request.cookies.get(SESSION_COOKIE)

    if token:
        revoke_session(db, token)

    response = Response(
        content='{"message":"Logged out"}',
        media_type="application/json",
    )

    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
    )

    return response



@router.get("/github/login")
def github_login():
    state = secrets.token_urlsafe(32)

    params = urlencode({
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": "read:user",
        "state": state,
    })

    response = RedirectResponse(
        f"https://github.com/login/oauth/authorize?{params}"
    )

    response.set_cookie(
        key=STATE_COOKIE,
        value=state,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=600,
        path="/api/auth/github",
    )

    return response


@router.get("/github/callback")
async def github_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    stored_state = request.cookies.get(STATE_COOKIE)

    if (
        not code
        or not state
        or not stored_state
        or not secrets.compare_digest(state, stored_state)
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid or missing OAuth state",
        )

    try:
        access_token = await exchange_code_for_token(code)
        github_user = await get_github_user(access_token)

    except (httpx.HTTPError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="GitHub authentication failed",
        )

    github_id = github_user["id"]

    user = db.scalar(
        select(User).where(User.github_id == github_id)
    )

    if user is None:
        user = User(
            github_id=github_id,
            username=github_user["login"],
            avatar_url=github_user.get("avatar_url"),
        )
        db.add(user)
    else:
        user.username = github_user["login"]
        user.avatar_url = github_user.get("avatar_url")


    db.commit()
    db.refresh(user)

    # Create a new application session.
    session_token = create_session(
        db=db,
        user_id=user.id,
    )

    # Redirect to React after login.
    response = RedirectResponse(
        url=settings.FRONTEND_URL,
        status_code=303,
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=int(
            SESSION_LIFETIME.total_seconds()
        ),
        path="/",
    )

    response.delete_cookie(
        STATE_COOKIE,
        path="/api/auth/github",
    )

    return response

