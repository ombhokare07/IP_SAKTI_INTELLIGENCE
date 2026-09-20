import logging
from importlib.util import find_spec
from collections.abc import Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.router import api_router
from backend.api.routes.auth import router as auth_router
from config.settings import Settings, settings
from database.vector.vector_store import ChromaVectorStore
from rag.embeddings.embedding_service import BGEEmbeddingService
from rag.generation.generator import GroundedAnswerGenerator
from rag.pipeline import RAGPipeline
from rag.retrieval.retriever import ChromaRetriever
from services.llm_service import GeminiLLMService
from intelligence.patentability.patentability_engine import PatentabilityEngine
from intelligence.prior_art.providers.http_json_provider import HTTPJSONPriorArtProvider
from intelligence.prior_art.providers.mock_provider import MockPriorArtProvider
from intelligence.prior_art.search_engine import PriorArtSearchEngine
from intelligence.prior_art.providers.epo_ops_provider import EPOOPSProvider
from services.runtime import Services


logger = logging.getLogger(__name__)


class RAGInitializationError(RuntimeError):
    """Internal component marker whose public message never contains provider details."""

    def __init__(self, component: str, public_message: str) -> None:
        super().__init__(public_message)
        self.component = component
        self.public_message = public_message


def _initial_rag_status(runtime_settings: Settings) -> dict[str, Any]:
    configured = bool(runtime_settings.gemini_api_key.get_secret_value().strip())
    embedding_available = find_spec("sentence_transformers") is not None
    return {
        "gemini": {"status": "configured" if configured else "not_configured"},
        "embedding_model": {
            "status": "available" if embedding_available else "unavailable",
            "model": runtime_settings.embedding_model,
        },
        "vector_store": {
            "status": "not_initialized",
            "collection": runtime_settings.vector_collection,
            "vector_count": None,
        },
        "documents": {"status": "not_indexed", "indexed_chunks": 0},
        "pipeline": {"status": "not_ready", "reason": "RAG startup is pending."},
    }


def _record_vector_status(status: dict[str, Any], vector_store: Any) -> int:
    count = int(vector_store.count())
    status["vector_store"].update(status="initialized", vector_count=count)
    status["documents"].update(
        status="indexed" if count > 0 else "not_indexed",
        indexed_chunks=count,
    )
    return count


def _vector_store_from_runtime(runtime: "RAGRuntime") -> Any | None:
    if runtime.vector_store is not None:
        return runtime.vector_store
    retriever = getattr(runtime.pipeline, "retriever", None)
    return getattr(retriever, "vector_store", None)


def _log_rag_status(status: dict[str, Any]) -> None:
    logger.info(
        "RAG startup status: Gemini=%s; embedding=%s; vector_store=%s; "
        "vector_count=%s; pipeline=%s; reason=%s",
        status["gemini"]["status"],
        status["embedding_model"]["status"],
        status["vector_store"]["status"],
        status["vector_store"]["vector_count"],
        status["pipeline"]["status"],
        status["pipeline"]["reason"],
    )


@dataclass(frozen=True)
class RAGRuntime:
    pipeline: RAGPipeline
    llm_service: GeminiLLMService
    patentability_engine: PatentabilityEngine | None = None
    prior_art_engine: PriorArtSearchEngine | None = None
    vector_store: Any | None = None
    embedding_service: Any | None = None


def build_prior_art_engine(
    runtime_settings: Settings,
    embedder: BGEEmbeddingService,
) -> PriorArtSearchEngine | None:
    provider_name = runtime_settings.prior_art_provider.strip().casefold()
    if not provider_name:
        return None
    if provider_name == "mock":
        if not runtime_settings.prior_art_allow_mock or runtime_settings.app_env.casefold() == "production":
            return None
        provider = MockPriorArtProvider()
        from services.offline_embeddings import OfflineFixtureEmbedding
        embedder = OfflineFixtureEmbedding()
        allow_test_provider = True
    elif provider_name == "epo_ops":
        if not (runtime_settings.epo_ops_consumer_key.get_secret_value().strip()
                and runtime_settings.epo_ops_consumer_secret.get_secret_value().strip()):
            return None
        provider = EPOOPSProvider(
            runtime_settings.epo_ops_consumer_key.get_secret_value(),
            runtime_settings.epo_ops_consumer_secret.get_secret_value(),
            timeout=runtime_settings.prior_art_timeout,
        )
        allow_test_provider = False
    elif provider_name == "http_json":
        if not runtime_settings.prior_art_api_url.strip():
            return None
        provider = HTTPJSONPriorArtProvider(
            runtime_settings.prior_art_api_url,
            api_key=runtime_settings.prior_art_api_key.get_secret_value(),
            timeout=runtime_settings.prior_art_timeout,
        )
        allow_test_provider = False
    else:
        return None
    return PriorArtSearchEngine(
        provider,
        embedder,
        allow_test_provider=allow_test_provider,
        cache_ttl_seconds=runtime_settings.prior_art_cache_ttl,
    )


def build_rag_runtime(
    runtime_settings: Settings,
    *,
    llm_client: Any | None = None,
) -> RAGRuntime:
    """Build the existing Phase-1 stack without ingesting or loading the BGE model."""
    api_key = runtime_settings.gemini_api_key.get_secret_value()
    try:
        embedder = BGEEmbeddingService(model_name=runtime_settings.embedding_model)
    except Exception as exc:
        raise RAGInitializationError(
            "embedding_model", "Embedding model service could not be initialized."
        ) from exc
    try:
        vector_store = ChromaVectorStore(
            path=runtime_settings.vector_db_path,
            collection_name=runtime_settings.vector_collection,
        )
    except Exception as exc:
        raise RAGInitializationError(
            "vector_store", "Vector store could not be initialized."
        ) from exc
    retriever = ChromaRetriever(
        embedding_service=embedder,
        vector_store=vector_store,
        top_k=runtime_settings.top_k,
    )
    try:
        llm_service = GeminiLLMService(
            api_key=api_key,
            model_name=runtime_settings.gemini_model,
            client=llm_client,
        )
    except Exception as exc:
        raise RAGInitializationError(
            "gemini", "Gemini provider could not be initialized."
        ) from exc
    generator = GroundedAnswerGenerator(llm_service)
    pipeline = RAGPipeline(
        retriever,
        generator,
        relevance_threshold=runtime_settings.evidence_relevance_threshold,
        sufficiency_threshold=runtime_settings.evidence_sufficiency_threshold,
        min_relevant_chunks=runtime_settings.evidence_min_relevant_chunks,
    )
    prior_art_engine = build_prior_art_engine(runtime_settings, embedder)
    patentability_engine = PatentabilityEngine(
        retriever,
        llm_service=llm_service,
        relevance_threshold=runtime_settings.evidence_relevance_threshold,
        sufficiency_threshold=runtime_settings.evidence_sufficiency_threshold,
        min_relevant_chunks=runtime_settings.evidence_min_relevant_chunks,
        prior_art_engine=prior_art_engine,
    )
    return RAGRuntime(
        pipeline=pipeline,
        llm_service=llm_service,
        patentability_engine=patentability_engine,
        prior_art_engine=prior_art_engine,
        vector_store=vector_store,
        embedding_service=embedder,
    )


RuntimeBuilder = Callable[[Settings], RAGRuntime]


def create_app(
    runtime_settings: Settings = settings,
    *,
    runtime_builder: RuntimeBuilder = build_rag_runtime,
) -> FastAPI:
    """Create the Phase-1 API and initialize its RAG runtime once."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        runtime: RAGRuntime | None = None
        application.state.services = Services(runtime_settings)
        application.state.rag_status = _initial_rag_status(runtime_settings)
        application.state.vector_store = None
        rag_status = application.state.rag_status
        api_key = runtime_settings.gemini_api_key.get_secret_value().strip()
        if not api_key:
            application.state.rag_pipeline = None
            application.state.patentability_engine = None
            application.state.prior_art_engine = None
            application.state.rag_configuration_error = (
                "Gemini API key not configured - full RAG chat is unavailable."
            )
            try:
                vector_store = ChromaVectorStore(
                    path=runtime_settings.vector_db_path,
                    collection_name=runtime_settings.vector_collection,
                )
                application.state.vector_store = vector_store
                _record_vector_status(rag_status, vector_store)
            except Exception:
                rag_status["vector_store"].update(status="error", vector_count=None)
            rag_status["pipeline"].update(
                status="not_ready", reason=application.state.rag_configuration_error
            )
        else:
            try:
                runtime = runtime_builder(runtime_settings)
            except Exception as exc:
                application.state.rag_pipeline = None
                application.state.patentability_engine = None
                application.state.prior_art_engine = None
                if isinstance(exc, RAGInitializationError):
                    reason = exc.public_message
                    rag_status[exc.component]["status"] = "unavailable"
                    if exc.component != "vector_store":
                        try:
                            vector_store = ChromaVectorStore(
                                path=runtime_settings.vector_db_path,
                                collection_name=runtime_settings.vector_collection,
                            )
                            application.state.vector_store = vector_store
                            _record_vector_status(rag_status, vector_store)
                        except Exception:
                            rag_status["vector_store"].update(
                                status="error", vector_count=None
                            )
                else:
                    reason = "RAG components could not be initialized."
                application.state.rag_configuration_error = reason
                rag_status["pipeline"].update(status="not_ready", reason=reason)
            else:
                application.state.rag_pipeline = runtime.pipeline
                application.state.patentability_engine = runtime.patentability_engine
                application.state.prior_art_engine = runtime.prior_art_engine
                application.state.rag_configuration_error = None
                rag_status["embedding_model"]["status"] = "available"
                vector_store = _vector_store_from_runtime(runtime)
                if vector_store is None:
                    rag_status["vector_store"]["status"] = "unavailable"
                    rag_status["pipeline"].update(
                        status="ready",
                        reason="RAG pipeline initialized; vector count is unavailable.",
                    )
                else:
                    application.state.vector_store = vector_store
                    try:
                        vector_count = _record_vector_status(rag_status, vector_store)
                    except Exception:
                        rag_status["vector_store"].update(
                            status="error", vector_count=None
                        )
                        rag_status["pipeline"].update(
                            status="not_ready",
                            reason="Vector store status could not be read.",
                        )
                    else:
                        if vector_count == 0:
                            rag_status["pipeline"].update(
                                status="not_ready",
                                reason="Knowledge base is empty. Please ingest documents first.",
                            )
                        else:
                            rag_status["pipeline"].update(
                                status="ready",
                                reason="RAG pipeline and indexed knowledge base are available.",
                            )

        _log_rag_status(rag_status)

        # Patent-provider configuration is independent of the Gemini lifecycle.
        independent_prior = None
        if application.state.prior_art_engine is None:
            try:
                independent_prior = build_prior_art_engine(
                    runtime_settings, BGEEmbeddingService(model_name=runtime_settings.embedding_model)
                )
                application.state.prior_art_engine = independent_prior
            except Exception:
                application.state.services.configuration_errors.append("Prior-art configuration could not be initialized.")
        try:
            yield
        finally:
            application.state.rag_pipeline = None
            application.state.patentability_engine = None
            application.state.prior_art_engine = None
            application.state.vector_store = None
            application.state.services.close()
            application.state.services = None
            if independent_prior is not None:
                close = getattr(independent_prior.provider, "close", None)
                if callable(close):
                    close()
            if runtime is not None:
                if runtime.prior_art_engine is not None:
                    close = getattr(runtime.prior_art_engine.provider, "close", None)
                    if callable(close):
                        close()
                runtime.llm_service.close()

    application = FastAPI(
        title=runtime_settings.app_name,
        version="1.0.0",
        description="Trustworthy source-cited RAG for Ayurveda IP intelligence",
        lifespan=lifespan,
    )
    application.state.settings = runtime_settings
    application.state.services = None
    application.state.rag_status = _initial_rag_status(runtime_settings)
    application.state.vector_store = None
    application.add_middleware(CORSMiddleware, allow_origins=runtime_settings.cors_origins,
                               allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"],
                               allow_headers=["Content-Type", "Authorization"])

    @application.exception_handler(Exception)
    async def unexpected_error(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Processing failed. No successful assessment is asserted."})
    application.state.rag_pipeline = None
    application.state.patentability_engine = None
    application.state.prior_art_engine = None
    if runtime_settings.gemini_api_key.get_secret_value().strip():
        application.state.rag_configuration_error = (
            "The RAG pipeline has not been initialized."
        )
    else:
        application.state.rag_configuration_error = (
            "Gemini API key not configured - full RAG chat is unavailable."
        )

    @application.get("/")
    def root() -> dict[str, str]:
        return {
            "application": runtime_settings.app_name,
            "status": "running",
            "version": "1.0.0",
        }

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    application.include_router(auth_router, prefix="/api")
    application.include_router(api_router)
    return application


app = create_app()
