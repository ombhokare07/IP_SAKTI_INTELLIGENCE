"""Google identity-token exchange and cookie-session endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.core.session import issue_session, session_user


router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=16_384)


def verify_google_token(token: str, audience: str) -> dict[str, str]:
    """Verify Google signature, expiry, issuer, audience and verified identity claims."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    claims: dict[str, Any] = id_token.verify_oauth2_token(token, google_requests.Request(), audience)
    if claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise ValueError("Unexpected token issuer.")
    if not claims.get("email_verified"):
        raise ValueError("Google account email is not verified.")
    sub = claims.get("sub")
    email = claims.get("email")
    if not isinstance(sub, str) or not sub or not isinstance(email, str) or not email:
        raise ValueError("Google token lacks a usable subject.")
    return {
        "sub": sub,
        "email": email,
        "name": claims.get("name") if isinstance(claims.get("name"), str) else "",
        "picture": claims.get("picture") if isinstance(claims.get("picture"), str) else "",
    }


def _cookie_kwargs(settings: Any) -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": settings.app_env.casefold() == "production",
        "samesite": "lax",
        "max_age": settings.session_ttl_seconds,
        "path": "/",
    }


@router.post("/google")
def google_login(payload: GoogleTokenRequest, request: Request, response: Response) -> dict[str, Any]:
    settings = request.app.state.settings
    client_id = settings.google_client_id.strip()
    if not client_id or not settings.session_secret.get_secret_value():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    try:
        user = verify_google_token(payload.token, client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")
    response.set_cookie(settings.session_cookie_name, issue_session(settings, user), **_cookie_kwargs(settings))
    return {"authenticated": True, "user": {key: user[key] for key in ("email", "name", "picture")}}


@router.get("/me")
def current_user(request: Request) -> dict[str, Any]:
    user = session_user(request)
    if user is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": {key: user[key] for key in ("email", "name", "picture")}}


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    settings = request.app.state.settings
    response.delete_cookie(settings.session_cookie_name, path="/", httponly=True,
                           secure=settings.app_env.casefold() == "production", samesite="lax")
    return {"authenticated": False}
