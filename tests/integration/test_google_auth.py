from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.main import create_app
from config.settings import Settings


@pytest.fixture
def auth_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        gemini_api_key="",
        app_data_dir=tmp_path / "runtime",
        vector_db_path=tmp_path / "vectors",
        api_auth_required=True,
        api_auth_token=SecretStr("legacy-api-token"),
        google_client_id="google-client-id.apps.googleusercontent.com",
        session_secret=SecretStr("test-session-secret-that-is-long-and-random"),
    )


def verified_user() -> dict[str, str]:
    return {
        "sub": "google-subject-123",
        "email": "verified@example.test",
        "name": "Verified Researcher",
        "picture": "https://images.example.test/avatar.png",
    }


def test_google_login_session_me_logout_and_protected_route(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        assert client.get("/api/auth/me").json() == {"authenticated": False, "user": None}
        assert client.get("/api/status").status_code == 401

        login = client.post("/api/auth/google", json={"token": "mocked-google-id-token"})
        assert login.status_code == 200
        assert login.json()["user"] == {
            "email": "verified@example.test",
            "name": "Verified Researcher",
            "picture": "https://images.example.test/avatar.png",
        }
        cookie = login.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=lax" in cookie

        assert client.get("/api/auth/me").json()["user"]["email"] == "verified@example.test"
        assert client.get("/api/status").status_code == 200

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert client.get("/api/auth/me").json() == {"authenticated": False, "user": None}


def test_invalid_google_token_is_rejected(auth_settings, monkeypatch):
    def reject(*_args, **_kwargs):
        raise ValueError("invalid token")

    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", reject)
    with TestClient(create_app(auth_settings)) as client:
        response = client.post("/api/auth/google", json={"token": "bad-token"})
        assert response.status_code == 401
        assert "set-cookie" not in response.headers


def test_existing_bearer_token_remains_valid_and_google_session_is_secure_in_production(auth_settings, monkeypatch):
    auth_settings.app_env = "production"
    auth_settings.api_auth_token = SecretStr("legacy-api-token")
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        assert client.get("/api/status", headers={"Authorization": "Bearer legacy-api-token"}).status_code == 200
        login = client.post("/api/auth/google", json={"token": "mocked-google-id-token"})
        assert login.status_code == 200
        assert "secure" in login.headers["set-cookie"].lower()
