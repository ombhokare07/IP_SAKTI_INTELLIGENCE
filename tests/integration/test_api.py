import asyncio

import httpx
from pydantic import SecretStr

from backend.main import app, create_app
from config.settings import Settings
from intelligence.patentability.patentability_engine import PatentabilityEngine
from intelligence.prior_art.providers.base import PriorArtRateLimitError
from intelligence.prior_art.providers.mock_provider import MockPriorArtProvider
from intelligence.prior_art.search_engine import PriorArtSearchEngine


def test_health_is_lightweight() -> None:
    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_chat_response_includes_public_trust_schema() -> None:
    class FakePipeline:
        def run(self, question: str) -> dict:
            return {
                "question": question,
                "answer": "Grounded answer [1].",
                "status": "grounded",
                "citations": [
                    {
                        "citation_id": 1,
                        "chunk_id": "chunk-1",
                        "source": "source.pdf",
                        "page": 1,
                        "text": "Grounded evidence.",
                        "internal_debug_value": "must not leak",
                    }
                ],
                "trust": {
                    "trust_score": 88,
                    "level": "very_high",
                    "evidence_score": 90,
                    "hallucination_risk": "low",
                    "contradictions_detected": False,
                    "unsupported_claims": 0,
                    "explanation": ["Grounded."],
                    "disclaimer": "Not legal correctness.",
                    "internal_factors": {"hidden": True},
                },
            }

    async def request_chat() -> httpx.Response:
        app.state.rag_pipeline = FakePipeline()
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                return await client.post("/api/chat", json={"question": "Question?"})
        finally:
            del app.state.rag_pipeline

    response = asyncio.run(request_chat())

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "grounded"
    assert body["trust"]["trust_score"] == 88
    assert "internal_factors" not in body["trust"]
    assert "internal_debug_value" not in body["citations"][0]


def test_chat_rejects_blank_question() -> None:
    async def request_chat() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post("/api/chat", json={"question": "   "})

    response = asyncio.run(request_chat())

    assert response.status_code == 422


def test_chat_reports_missing_llm_configuration() -> None:
    application = create_app(
        Settings(_env_file=None, gemini_api_key=SecretStr(""))
    )

    async def request_chat() -> httpx.Response:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post("/api/chat", json={"question": "Question?"})

    response = asyncio.run(request_chat())

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Gemini API key not configured - full RAG chat is unavailable."
    }


def test_patentability_check_runs_full_structured_pre_screen(tmp_path) -> None:
    source = tmp_path / "ayush-guidance.pdf"
    source.write_bytes(b"source")

    class FakeRetriever:
        def retrieve(self, _question: str) -> list[dict]:
            return [
                {
                    "chunk_id": "patent-guide-1",
                    "text": (
                        "Novelty and inventive step require assessment. Traditional "
                        "knowledge and known properties may require review."
                    ),
                    "source": "ayush-guidance.pdf",
                    "page": 4,
                    "path": str(source),
                    "distance": 0.1,
                }
            ]

    async def request_check() -> httpx.Response:
        app.state.patentability_engine = PatentabilityEngine(
            FakeRetriever(),
            relevance_threshold=0.5,
            sufficiency_threshold=0.5,
            min_relevant_chunks=1,
        )
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test"
            ) as client:
                return await client.post(
                    "/api/patentability/check",
                    json={
                        "title": "Improved Herbal Wound Healing Formulation",
                        "description": (
                            "An Ayurvedic formulation containing turmeric, neem and "
                            "aloe vera prepared using a modified low-temperature "
                            "extraction process."
                        ),
                        "claimed_innovation": (
                            "The process improves retention compared with conventional "
                            "preparation."
                        ),
                        "technical_advantage": "Improved stability and retention.",
                    },
                )
        finally:
            app.state.patentability_engine = None

    response = asyncio.run(request_check())
    assert response.status_code == 200
    body = response.json()
    assert body["assessment"]["novelty"]["status"] == "prior_art_search_required"
    assert body["citations"][0]["chunk_id"] == "patent-guide-1"
    assert body["trust"]["evidence_score"] > 0
    assert "prior-art search" in body["evidence_gaps"]
    assert body["limitations"][-1] == "The score does not represent probability of patent grant."


def test_patentability_check_requires_title_and_description() -> None:
    async def request_check() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.post(
                "/api/patentability/check", json={"title": "Missing description"}
            )

    response = asyncio.run(request_check())
    assert response.status_code == 422


class _OfflineEmbedding:
    def embed_documents(self, texts, *, batch_size=32):
        vocabulary = ("turmeric", "neem", "aloe", "wound", "extraction", "sensor")
        return [
            [float(text.casefold().replace("-", " ").count(word)) for word in vocabulary]
            for text in texts
        ]


def test_prior_art_search_api_uses_explicit_mock_provider() -> None:
    async def request_search() -> httpx.Response:
        app.state.prior_art_engine = PriorArtSearchEngine(
            MockPriorArtProvider(), _OfflineEmbedding(), allow_test_provider=True
        )
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post(
                    "/api/prior-art/search",
                    json={
                        "title": "Improved Herbal Wound Healing Formulation",
                        "description": (
                            "An Ayurvedic formulation containing turmeric, neem and aloe "
                            "vera using low-temperature extraction."
                        ),
                        "claimed_innovation": "Improved active constituent retention.",
                        "technical_advantage": "Improved stability.",
                        "limit": 3,
                    },
                )
        finally:
            app.state.prior_art_engine = None

    response = asyncio.run(request_search())
    assert response.status_code == 200
    body = response.json()
    assert body["search_summary"]["provider_mode"] == "mock"
    assert body["search_summary"]["configuration_status"] == "mock_test_data"
    assert body["results"][0]["publication_number"].startswith("TEST-FIXTURE-")
    assert "TEST DATA ONLY" in body["limitations"][0]


def test_prior_art_api_reports_missing_live_configuration() -> None:
    async def request_search() -> httpx.Response:
        app.state.prior_art_engine = None
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/api/prior-art/search",
                json={"title": "Title", "description": "Description"},
            )

    response = asyncio.run(request_search())
    assert response.status_code == 503
    assert response.json()["detail"] == "Live prior-art provider is not configured."


def test_prior_art_api_maps_rate_limit_to_controlled_error() -> None:
    class RateLimitedEngine:
        def search(self, invention, limit=10):
            raise PriorArtRateLimitError("secret provider response")

    async def request_search() -> httpx.Response:
        app.state.prior_art_engine = RateLimitedEngine()
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post(
                    "/api/prior-art/search",
                    json={"title": "Title", "description": "Description"},
                )
        finally:
            app.state.prior_art_engine = None

    response = asyncio.run(request_search())
    assert response.status_code == 429
    assert response.json() == {"detail": "The prior-art provider rate limit was reached."}
    assert "secret" not in response.text


def test_patentability_api_optional_prior_art_integration(tmp_path) -> None:
    source = tmp_path / "guidance.pdf"
    source.write_bytes(b"source")

    class Retriever:
        def retrieve(self, question):
            return [{
                "chunk_id": "guide",
                "text": "Patent novelty and inventive step require assessment.",
                "source": "guidance.pdf",
                "page": 1,
                "path": str(source),
                "distance": 0.1,
            }]

    prior_engine = PriorArtSearchEngine(
        MockPriorArtProvider(), _OfflineEmbedding(), allow_test_provider=True
    )

    async def request_check() -> httpx.Response:
        app.state.patentability_engine = PatentabilityEngine(
            Retriever(),
            relevance_threshold=0.5,
            sufficiency_threshold=0.5,
            min_relevant_chunks=1,
            prior_art_engine=prior_engine,
        )
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.post(
                    "/api/patentability/check",
                    json={
                        "title": "Herbal wound formulation",
                        "description": "A formulation containing turmeric and neem for wound healing.",
                        "claimed_innovation": "A modified extraction process.",
                        "technical_advantage": "Improved retention.",
                        "run_prior_art_search": True,
                    },
                )
        finally:
            app.state.patentability_engine = None

    response = asyncio.run(request_check())
    assert response.status_code == 200
    body = response.json()
    assert body["prior_art"]["search_summary"]["provider_mode"] == "mock"
    assert body["assessment"]["novelty"]["status"] != "prior_art_search_required"
