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
        status = client.get("/api/status")
        assert status.status_code == 200
        assert status.json()["authentication"] == {
            "status": "configured",
            "google_sign_in": "configured",
            "session_cookie": "configured",
            "legacy_bearer": "configured",
            "legacy_bearer_required": True,
            "token_required": True,
        }
        assert status.json()["provider_status"]["authentication"] == status.json()["authentication"]

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200
        assert "max-age=0" in logout.headers["set-cookie"].lower()
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


def test_signin_mode_rejects_new_google_account(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        response = client.post("/api/auth/google", json={"token": "mocked", "mode": "signin"})
        assert response.status_code == 404
        assert "set-cookie" not in response.headers
        assert response.json()["detail"]


def test_signup_creates_then_signin_signs_in(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        created = client.post("/api/auth/google", json={"token": "mocked", "mode": "signup"})
        assert created.status_code == 200
        assert created.json()["mode"] == "account_created"

        signed_in = client.post("/api/auth/google", json={"token": "mocked", "mode": "signin"})
        assert signed_in.status_code == 200
        assert signed_in.json()["mode"] == "signed_in"


def test_me_reports_persisted_account(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        client.post("/api/auth/google", json={"token": "mocked", "mode": "signup"})
        account = client.get("/api/auth/me").json()["user"]["account"]
        assert account["exists"] is True
        assert account["id"] and account["created_at"] and account["updated_at"] and account["last_login_at"]


def test_token_is_never_persisted(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as client:
        response = client.post("/api/auth/google", json={"token": "super-secret-google-id-token", "mode": "signup"})
        assert response.status_code == 200
        user_record = client.app.state.services.db.get("user", "google-subject-123")
        assert user_record is not None
        assert "token" not in user_record
        assert "google-subject-123" == user_record["google_sub"]


def test_verified_email_is_unique_across_google_subjects(auth_settings, monkeypatch):
    identities = iter(
        [
            verified_user(),
            {**verified_user(), "sub": "different-google-subject", "email": "VERIFIED@EXAMPLE.TEST"},
        ]
    )
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: next(identities))
    with TestClient(create_app(auth_settings)) as client:
        assert client.post("/api/auth/google", json={"token": "first", "mode": "signup"}).status_code == 200
        conflict = client.post("/api/auth/google", json={"token": "second", "mode": "signup"})

    assert conflict.status_code == 409
    assert "already exists" in conflict.json()["detail"].lower()


def test_user_account_persists_across_application_restarts(auth_settings, monkeypatch):
    monkeypatch.setattr("backend.api.routes.auth.verify_google_token", lambda token, audience: verified_user())
    with TestClient(create_app(auth_settings)) as first_client:
        created = first_client.post("/api/auth/google", json={"token": "first", "mode": "signup"})
        first_id = first_client.get("/api/auth/me").json()["user"]["account"]["id"]

    with TestClient(create_app(auth_settings)) as second_client:
        signed_in = second_client.post("/api/auth/google", json={"token": "second", "mode": "signin"})
        second_id = second_client.get("/api/auth/me").json()["user"]["account"]["id"]

    assert created.json()["mode"] == "account_created"
    assert signed_in.json()["mode"] == "signed_in"
    assert second_id == first_id
