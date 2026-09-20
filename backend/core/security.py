"""Accept a verified cookie session or the existing shared API bearer token."""
import secrets
from fastapi import HTTPException,Request
from backend.core.session import session_user

def require_api_auth(request: Request):
    settings=request.app.state.settings
    required=settings.api_auth_required or settings.app_env.casefold()=='production'
    if not required:return
    if session_user(request) is not None:return
    token=settings.api_auth_token.get_secret_value()
    session_configured=bool(settings.session_secret.get_secret_value())
    if not token and not session_configured:raise HTTPException(503,'API authentication is required but not configured.')
    supplied=request.headers.get('Authorization','')
    if not token or not secrets.compare_digest(supplied.encode(),f'Bearer {token}'.encode()):
        raise HTTPException(401,'Valid API authentication is required.',headers={'WWW-Authenticate':'Bearer'})
