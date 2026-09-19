from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.api.schemas.chat_schema import ChatRequest, ChatResponse
from services.llm_service import LLMServiceError


router = APIRouter(prefix="/chat", tags=["chat"])

KNOWLEDGE_BASE_EMPTY_MESSAGE = (
    "Knowledge base is empty. Please ingest documents first."
)


def _pipeline_from(request: Request) -> Any:
    pipeline = getattr(request.app.state, "rag_pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail=getattr(
                request.app.state,
                "rag_configuration_error",
                "The RAG pipeline has not been configured.",
            ),
        )
    return pipeline


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> dict[str, Any]:
    """Answer through the configured RAG pipeline and expose trust summary only."""
    pipeline = _pipeline_from(request)
    run = getattr(pipeline, "run", None) or getattr(pipeline, "answer", None)
    if run is None:
        raise HTTPException(status_code=503, detail="The RAG pipeline is invalid.")
    retriever = getattr(pipeline, "retriever", None)
    vector_store = getattr(retriever, "vector_store", None)
    count = getattr(vector_store, "count", None)
    if callable(count):
        try:
            vector_count = int(count())
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="Vector store is unavailable."
            ) from exc
        rag_status = getattr(request.app.state, "rag_status", None)
        if isinstance(rag_status, dict):
            rag_status["vector_store"].update(
                status="initialized", vector_count=vector_count
            )
            rag_status["documents"].update(
                status="indexed" if vector_count > 0 else "not_indexed",
                indexed_chunks=vector_count,
            )
        if vector_count == 0:
            if isinstance(rag_status, dict):
                rag_status["pipeline"].update(
                    status="not_ready", reason=KNOWLEDGE_BASE_EMPTY_MESSAGE
                )
            raise HTTPException(status_code=503, detail=KNOWLEDGE_BASE_EMPTY_MESSAGE)
    try:
        return run(payload.question)
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini service request failed. Please try again.",
        ) from exc
