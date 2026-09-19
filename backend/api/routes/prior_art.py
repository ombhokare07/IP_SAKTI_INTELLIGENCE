from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.api.schemas.prior_art_schema import PriorArtSearchRequest, PriorArtSearchResponse
from intelligence.patentability.invention_analyzer import InventionAnalyzer
from backend.api.routes.common import remember
from intelligence.prior_art.providers.base import (
    PriorArtAuthenticationError,
    PriorArtMalformedResponseError,
    PriorArtProviderError,
    PriorArtRateLimitError,
    PriorArtTimeoutError,
)


router = APIRouter(prefix="/prior-art", tags=["prior-art"])


def provider_http_error(exc: PriorArtProviderError) -> HTTPException:
    if isinstance(exc, PriorArtTimeoutError):
        return HTTPException(status_code=504, detail="The prior-art provider timed out.")
    if isinstance(exc, PriorArtAuthenticationError):
        return HTTPException(status_code=502, detail="Prior-art provider authentication failed.")
    if isinstance(exc, PriorArtRateLimitError):
        return HTTPException(status_code=429, detail="The prior-art provider rate limit was reached.")
    if isinstance(exc, PriorArtMalformedResponseError):
        return HTTPException(status_code=502, detail="The prior-art provider returned malformed data.")
    return HTTPException(status_code=502, detail="The prior-art provider search failed.")


@router.post("/search", response_model=PriorArtSearchResponse)
def search_prior_art(payload: PriorArtSearchRequest, request: Request) -> dict[str, Any]:
    engine = getattr(request.app.state, "prior_art_engine", None)
    if engine is None:
        raise HTTPException(status_code=503, detail="Live prior-art provider is not configured.")
    invention_payload = payload.model_dump(exclude={"limit"})
    invention = InventionAnalyzer().analyze(invention_payload)
    try:
        return remember(request,'prior_art',payload.model_dump(),engine.search(invention, limit=payload.limit))
    except PriorArtProviderError as exc:
        raise provider_http_error(exc) from exc
