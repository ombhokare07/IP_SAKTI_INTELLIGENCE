from __future__ import annotations

import math

import pytest

from backend.api.schemas.prior_art_schema import PriorArtSearchRequest
from intelligence.patentability.invention_analyzer import InventionAnalyzer
from intelligence.patentability.patentability_engine import PatentabilityEngine
from intelligence.prior_art.cache import PriorArtSearchCache
from intelligence.prior_art.feature_matcher import match_features
from intelligence.prior_art.normalizer import normalize_prior_art_record
from intelligence.prior_art.novelty_risk import analyze_novelty_risk
from intelligence.prior_art.providers.base import (
    PriorArtConfigurationError,
    PriorArtMalformedResponseError,
    PriorArtRateLimitError,
    PriorArtRecord,
    PriorArtTimeoutError,
)
from intelligence.prior_art.providers.http_json_provider import HTTPJSONPriorArtProvider
from intelligence.prior_art.providers.mock_provider import MockPriorArtProvider
from intelligence.prior_art.query_builder import build_prior_art_queries
from intelligence.prior_art.result_ranker import rank_prior_art_results
from intelligence.prior_art.search_engine import PriorArtSearchEngine, deduplicate_records
from intelligence.prior_art.similarity import analyze_semantic_similarity


INVENTION_INPUT = {
    "title": "Improved Herbal Wound Healing Formulation",
    "description": (
        "An Ayurvedic formulation containing turmeric, neem and aloe vera prepared "
        "using a modified low-temperature extraction process for wound healing."
    ),
    "claimed_innovation": "Improved retention of heat-sensitive active constituents.",
    "technical_advantage": "Improved stability and active-compound retention.",
}
INVENTION = InventionAnalyzer().analyze(INVENTION_INPUT)


class KeywordEmbedding:
    words = (
        "turmeric", "neem", "aloe", "wound", "healing", "low", "temperature",
        "extraction", "active", "retention", "irrigation", "sensor", "water",
    )

    def embed_documents(self, texts, *, batch_size=32):
        vectors = []
        for text in texts:
            lowered = text.casefold().replace("-", " ")
            vector = [float(lowered.count(word)) for word in self.words]
            if not any(vector):
                vector[-1] = 0.01
            norm = math.sqrt(sum(value * value for value in vector)) or 1
            vectors.append([value / norm for value in vector])
        return vectors


class StaticProvider:
    name = "offline-static"
    is_test_fixture = False

    def __init__(self, records):
        self.records = records
        self.calls = 0

    def search(self, query, limit=10):
        self.calls += 1
        return self.records[:limit]


def test_search_query_generation_is_focused() -> None:
    result = build_prior_art_queries(INVENTION)
    assert 2 <= len(result["queries"]) <= 4
    assert "turmeric" in result["technical_terms"]
    assert any("wound" in query and "formulation" in query for query in result["queries"])
    assert all(len(query.split()) <= 12 for query in result["queries"])


def test_normalization_handles_missing_and_inconsistent_fields() -> None:
    result = normalize_prior_art_record(
        {
            "publicationNumber": " us 12/345 a1 ",
            "name": "  Herbal composition ",
            "applicant": "One Corp; Two Labs",
            "inventor": [{"name": "Ada Example"}],
            "publicationDate": "20240102",
            "country": "in",
        },
        provider="fixture-normalizer",
    )
    assert result["publication_number"] == "US12345A1"
    assert result["abstract"] is None
    assert result["claims"] == []
    assert result["publication_date"] == "2024-01-02"
    assert result["applicants"] == ["One Corp", "Two Labs"]
    assert result["jurisdiction"] == "IN"


def test_deduplication_uses_publication_then_title_and_priority() -> None:
    records = [
        {"publication_number": "ONE", "title": "First", "priority_date": None},
        {"publication_number": "ONE", "title": "Duplicate", "priority_date": None},
        {"publication_number": None, "title": "Same title", "priority_date": "2020-01-01"},
        {"publication_number": None, "title": "same TITLE", "priority_date": "2020-01-01"},
    ]
    assert len(deduplicate_records(records)) == 2


def test_semantic_similarity_scores_exact_text_above_unrelated_text() -> None:
    close = analyze_semantic_similarity(
        INVENTION,
        {"title": "Turmeric neem aloe wound healing", "abstract": "low temperature extraction active retention", "claims": []},
        KeywordEmbedding(),
    )
    distant = analyze_semantic_similarity(
        INVENTION,
        {"title": "Irrigation sensor", "abstract": "water controller", "claims": []},
        KeywordEmbedding(),
    )
    assert close["overall_similarity"] > distant["overall_similarity"]
    assert close["name"] == "Prior-Art Semantic Similarity Score"
    assert 0 <= distant["overall_similarity"] <= 100


def test_feature_overlap_uses_nonlegal_distinct_wording() -> None:
    overlap = match_features(
        INVENTION,
        {
            "title": "Turmeric neem wound healing formulation",
            "abstract": "A herbal composition.",
            "claims": [],
        },
    )
    assert "turmeric" in overlap["matching_features"]
    assert any("not identified in this retrieved record" in item for item in overlap["apparently_distinct_features"])


def test_result_ranking_uses_documented_weights() -> None:
    candidates = [
        {
            "publication_number": "LOW",
            "title": "unrelated",
            "abstract": "",
            "claims": [],
            "similarity": {"overall_similarity": 10},
            "feature_overlap": {"matching_features": [], "partially_matching_features": [], "apparently_distinct_features": ["x"]},
        },
        {
            "publication_number": "HIGH",
            "title": "turmeric wound formulation",
            "abstract": "",
            "claims": [],
            "similarity": {"overall_similarity": 90},
            "feature_overlap": {"matching_features": ["turmeric"], "partially_matching_features": [], "apparently_distinct_features": []},
        },
    ]
    ranked = rank_prior_art_results(candidates, ["turmeric wound formulation"])
    assert ranked[0]["publication_number"] == "HIGH"
    assert ranked[0]["rank"] == 1
    assert "Weighted semantic similarity" in ranked[0]["reason_for_ranking"]


def test_mock_provider_requires_explicit_test_mode() -> None:
    with pytest.raises(PriorArtConfigurationError):
        PriorArtSearchEngine(MockPriorArtProvider(), KeywordEmbedding())


def test_mock_records_are_visibly_synthetic() -> None:
    records = MockPriorArtProvider().search("turmeric wound", limit=3)
    assert all(record.publication_number.startswith("TEST-FIXTURE-") for record in records)
    assert all(record.provider == "TEST DATA / MOCK PROVIDER" for record in records)


def test_search_engine_empty_result_is_insufficient_not_novel() -> None:
    report = PriorArtSearchEngine(StaticProvider([]), KeywordEmbedding()).search(INVENTION)
    assert report["risk"]["level"] == "insufficient_prior_art"
    assert report["results"] == []
    assert report["search_summary"]["search_status"] == "complete"
    assert report["search_summary"]["queries_failed"] == 0


def test_search_engine_deduplicates_and_preserves_partial_metadata() -> None:
    record = PriorArtRecord(
        publication_number="TEST-ONE",
        title="Turmeric neem wound healing",
        abstract=None,
        publication_date=None,
        claims=(),
        provider="offline-static",
    )
    report = PriorArtSearchEngine(StaticProvider([record, record]), KeywordEmbedding()).search(INVENTION)
    assert report["search_summary"]["records_found"] > 1
    assert report["search_summary"]["records_analyzed"] == 1
    assert report["results"][0]["abstract"] is None
    assert report["results"][0]["publication_date"] is None
    assert report["results"][0]["claims"] == []
    assert report["results"][0]["metadata_validation"]["valid_for_comparison"] is True


def test_high_similarity_prior_art_produces_high_overlap_risk() -> None:
    text = "turmeric neem aloe wound healing low temperature extraction active retention"
    record = PriorArtRecord("TEST-HIGH", text, abstract=text, claims=(text,), provider="offline-static")
    report = PriorArtSearchEngine(StaticProvider([record]), KeywordEmbedding()).search(INVENTION)
    assert report["risk"]["level"] == "high_detected_overlap"
    assert report["risk"]["high_similarity_records"]


def test_low_similarity_prior_art_produces_low_overlap_risk() -> None:
    record = PriorArtRecord(
        "TEST-LOW", "Irrigation sensor", abstract="water controller", provider="offline-static"
    )
    report = PriorArtSearchEngine(StaticProvider([record]), KeywordEmbedding()).search(INVENTION)
    assert report["risk"]["level"] == "low_detected_overlap"


@pytest.mark.parametrize("error", [PriorArtTimeoutError("timeout"), PriorArtRateLimitError("rate")])
def test_provider_failures_are_controlled(error) -> None:
    class FailingProvider(StaticProvider):
        def search(self, query, limit=10):
            raise error

    with pytest.raises(type(error)):
        PriorArtSearchEngine(FailingProvider([]), KeywordEmbedding()).search(INVENTION)


def test_partial_provider_search_is_explicitly_labelled() -> None:
    class PartiallyFailingProvider(StaticProvider):
        def __init__(self):
            super().__init__([])
            self.calls = 0

        def search(self, query, limit=10):
            self.calls += 1
            if self.calls == 1:
                raise PriorArtTimeoutError("timeout")
            return []

    report = PriorArtSearchEngine(PartiallyFailingProvider(), KeywordEmbedding()).search(INVENTION)
    summary = report["search_summary"]

    assert summary["search_status"] == "partial"
    assert summary["queries_failed"] == 1
    assert summary["queries_succeeded"] == summary["queries_total"] - 1
    assert any("partial" in limitation for limitation in report["limitations"])


def test_malformed_provider_record_is_controlled() -> None:
    with pytest.raises(PriorArtMalformedResponseError):
        PriorArtSearchEngine(StaticProvider(["bad-record"]), KeywordEmbedding()).search(INVENTION)


def test_novelty_risk_without_search_requires_search() -> None:
    risk = analyze_novelty_risk([], search_performed=False)
    assert risk["level"] == "search_required"
    assert "not a probability" in risk["limitations"][0]


def test_cache_is_keyed_by_provider_query_and_limit() -> None:
    cache = PriorArtSearchCache(ttl_seconds=30)
    cache.put("provider", "Some Query", 10, ["record"])
    assert cache.get("PROVIDER", " some   query ", 10) == ["record"]
    assert cache.get("provider", "some query", 5) is None


def test_http_json_provider_rejects_malformed_response() -> None:
    class Response:
        status_code = 200

        def json(self):
            return {"unexpected": []}

    class Client:
        def post(self, *args, **kwargs):
            return Response()

    provider = HTTPJSONPriorArtProvider("https://provider.invalid", client=Client())
    with pytest.raises(PriorArtMalformedResponseError):
        provider.search("query")


def test_prior_art_api_schema() -> None:
    request = PriorArtSearchRequest(title=" Title ", description="Description", limit=10)
    assert request.title == "Title"
    with pytest.raises(ValueError):
        PriorArtSearchRequest(title="Title", description=" ")


def test_patentability_prior_art_flag_is_opt_in_and_reduces_readiness_on_overlap() -> None:
    class GuidanceRetriever:
        def retrieve(self, question):
            return [
                {
                    "chunk_id": "guide",
                    "text": "Patent novelty and inventive step require assessment.",
                    "source": "guidance.pdf",
                    "page": 1,
                    "path": "guidance.pdf",
                    "distance": 0.1,
                }
            ]

    class HighOverlapEngine:
        def __init__(self):
            self.calls = 0

        def search(self, invention, limit=10):
            self.calls += 1
            return {
                "search_summary": {
                    "queries_run": ["focused query"],
                    "provider": "offline-static",
                    "provider_mode": "live",
                    "configuration_status": "live_configured",
                    "records_found": 1,
                    "records_analyzed": 1,
                    "cache_hits": 0,
                    "retrieval_timestamp": "2026-01-01T00:00:00+00:00",
                },
                "risk": {
                    "name": "Detected Prior-Art Overlap Risk",
                    "level": "high_detected_overlap",
                    "score": 90,
                    "reasoning": [],
                    "high_similarity_records": [],
                    "limitations": [],
                },
                "results": [],
                "top_results": [],
                "limitations": [],
            }

    prior_engine = HighOverlapEngine()
    engine = PatentabilityEngine(
        GuidanceRetriever(),
        check_source_files=False,
        relevance_threshold=0.5,
        sufficiency_threshold=0.5,
        min_relevant_chunks=1,
        prior_art_engine=prior_engine,
    )
    baseline = engine.check(INVENTION_INPUT)
    assert prior_engine.calls == 0
    assert "prior_art" not in baseline

    searched = engine.check({**INVENTION_INPUT, "run_prior_art_search": True})
    assert prior_engine.calls == 1
    assert searched["assessment"]["novelty"]["status"] == "significant_prior_art_overlap"
    assert searched["assessment"]["readiness_score"] < baseline["assessment"]["readiness_score"]
    assert "prior-art search" not in searched["evidence_gaps"]
