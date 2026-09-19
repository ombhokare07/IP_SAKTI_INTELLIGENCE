"""Optional shared API bearer token for a local/single-operator deployment."""
import secrets
from fastapi import HTTPException,Request

def require_api_auth(request: Request):
    settings=request.app.state.settings
    required=settings.api_auth_required or settings.app_env.casefold()=='production'
    if not required:return
    token=settings.api_auth_token.get_secret_value()
    if not token:raise HTTPException(503,'API authentication is required but not configured.')
    supplied=request.headers.get('Authorization','')
    if not secrets.compare_digest(supplied.encode(),f'Bearer {token}'.encode()):
        raise HTTPException(401,'Valid API authentication is required.',headers={'WWW-Authenticate':'Bearer'})
