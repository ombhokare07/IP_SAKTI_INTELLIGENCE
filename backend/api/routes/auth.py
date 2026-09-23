"""Google identity-token exchange and cookie-session endpoints.

Verified Google identity is exchanged for a signed, HttpOnly application
session. Persistent user accounts are stored in the local SQLite
`artifacts` store (kind="user", id=google_sub) with only lightweight
profile claims; Google ID tokens are never persisted.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from backend.core.session import issue_session, session_user


router = APIRouter(prefix="/auth", tags=["authentication"])


class GoogleTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=16_384)
    mode: Literal["signin", "signup"] = "signup"


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


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {key: user.get(key) for key in ("email", "name", "picture")}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/google")
def google_login(payload: GoogleTokenRequest, request: Request, response: Response) -> dict[str, Any]:
    settings = request.app.state.settings
    client_id = settings.google_client_id.strip()
    if not client_id or not settings.session_secret.get_secret_value():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured.")
    try:
        claims = verify_google_token(payload.token, client_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Google sign-in could not be verified.")

    database = request.app.state.services.db
    account = database.get_user_by_google_sub(claims["sub"])
    mode_out: str
    if account is None:
        if payload.mode == "signin":
            raise HTTPException(
                status_code=404,
                detail="No IP-SAKTI account exists for this Google account. Create an account instead.",
            )
        try:
            account = database.create_user(
                claims["sub"], claims["email"], claims["name"], claims["picture"], _now()
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail="An account already exists for this verified email. Sign in with its original Google identity.",
            ) from exc
        mode_out = "account_created"
    else:
        try:
            account = database.update_user_login(
                claims["sub"], claims["email"], claims["name"], claims["picture"], _now()
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=409,
                detail="This verified email belongs to another account.",
            ) from exc
        mode_out = "signed_in"

    session_user_claims = {key: claims[key] for key in ("sub", "email", "name", "picture")}
    response.set_cookie(settings.session_cookie_name, issue_session(settings, session_user_claims), **_cookie_kwargs(settings))
    return {"authenticated": True, "mode": mode_out, "user": _public_user(account)}


@router.get("/me")
def current_user(request: Request) -> dict[str, Any]:
    user = session_user(request)
    if user is None:
        return {"authenticated": False, "user": None}
    database = request.app.state.services.db
    account = database.get_user_by_google_sub(user["sub"])
    if account is None:
        return {
            "authenticated": True,
            "user": {
                "email": user["email"],
                "name": user["name"],
                "picture": user["picture"],
                "account": {"exists": False},
            },
        }
    return {
        "authenticated": True,
        "user": {
            "email": account.get("email") or user["email"],
            "name": account.get("name") or user["name"],
            "picture": account.get("picture") or user["picture"],
            "account": {
                "exists": True,
                "id": account.get("id"),
                "created_at": account.get("created_at"),
                "updated_at": account.get("updated_at"),
                "last_login_at": account.get("last_login_at"),
            },
        },
    }


@router.post("/logout")
def logout(request: Request, response: Response) -> dict[str, bool]:
    settings = request.app.state.settings
    response.delete_cookie(settings.session_cookie_name, path="/", httponly=True,
                           secure=settings.app_env.casefold() == "production", samesite="lax")
    return {"authenticated": False}
