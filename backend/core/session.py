"""Signed, short-lived application sessions stored only in HttpOnly cookies."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Request


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _secret(settings: Any) -> bytes:
    return settings.session_secret.get_secret_value().encode("utf-8")


def issue_session(settings: Any, user: dict[str, str]) -> str:
    """Create a tamper-evident, expiring session containing verified profile claims."""
    secret = _secret(settings)
    if not secret:
        raise ValueError("Session signing is not configured.")
    now = int(time.time())
    payload = {
        "v": 1,
        "sub": user["sub"],
        "email": user["email"],
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "iat": now,
        "exp": now + settings.session_ttl_seconds,
    }
    encoded_payload = _encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_encode(signature)}"


def read_session(settings: Any, token: str | None) -> dict[str, str] | None:
    """Return an authenticated user only for a valid signed, unexpired session."""
    secret = _secret(settings)
    if not secret or not token:
        return None
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        expected = hmac.new(secret, encoded_payload.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _decode(encoded_signature)):
            return None
        payload = json.loads(_decode(encoded_payload))
        if payload.get("v") != 1 or int(payload.get("exp", 0)) < int(time.time()):
            return None
        sub = payload.get("sub")
        email = payload.get("email")
        if not isinstance(sub, str) or not sub or not isinstance(email, str) or not email:
            return None
        return {
            "sub": sub,
            "email": email,
            "name": payload.get("name") if isinstance(payload.get("name"), str) else "",
            "picture": payload.get("picture") if isinstance(payload.get("picture"), str) else "",
        }
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def session_user(request: Request) -> dict[str, str] | None:
    settings = request.app.state.settings
    return read_session(settings, request.cookies.get(settings.session_cookie_name))
