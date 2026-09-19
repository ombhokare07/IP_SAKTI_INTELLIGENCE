from fastapi import APIRouter, Depends
from backend.core.security import require_api_auth

from backend.api.routes.chat import router as chat_router
from backend.api.routes.patentability import router as patentability_router
from backend.api.routes.prior_art import router as prior_art_router


api_router = APIRouter(prefix="/api", dependencies=[Depends(require_api_auth)])
api_router.include_router(chat_router)
api_router.include_router(patentability_router)
api_router.include_router(prior_art_router)

from backend.api.routes import (agents, compliance, compliance_journey, documents,
    health, regulation_changes, regulation_compare, reports, traditional_knowledge, voice)

for module in (agents, compliance, compliance_journey, documents, health,
               regulation_changes, regulation_compare, reports, traditional_knowledge, voice):
    api_router.include_router(module.router)
