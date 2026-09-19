from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.api.schemas.patent_schema import PatentabilityRequest, PatentabilityResponse
from services.llm_service import LLMServiceError
from backend.api.routes.prior_art import provider_http_error
from intelligence.prior_art.providers.base import PriorArtConfigurationError, PriorArtProviderError


router = APIRouter(prefix="/patentability", tags=["patentability"])


def _engine_from(request: Request) -> Any:
    engine = getattr(request.app.state, "patentability_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail=getattr(
                request.app.state,
                "rag_configuration_error",
                "The patentability pre-screen has not been configured.",
            ),
        )
    return engine


@router.post(
    "/check", response_model=PatentabilityResponse, response_model_exclude_none=True
)
def check_patentability(
    payload: PatentabilityRequest, request: Request
) -> dict[str, Any]:
    """Run the Phase-2A preliminary, evidence-grounded patentability screen."""
    engine = _engine_from(request)
    run = getattr(engine, "check", None) or getattr(engine, "run", None)
    if run is None:
        raise HTTPException(status_code=503, detail="The patentability engine is invalid.")
    try:
        return run(payload.model_dump())
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini service request failed. Please try again.",
        ) from exc
    except PriorArtConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Live prior-art provider is not configured.") from exc
    except PriorArtProviderError as exc:
        raise provider_http_error(exc) from exc
