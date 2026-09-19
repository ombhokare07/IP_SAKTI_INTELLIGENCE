"""Provider-based prior-art search, normalization, comparison, and ranking."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from intelligence.prior_art.cache import PriorArtSearchCache
from intelligence.prior_art.feature_matcher import match_features
from intelligence.prior_art.normalizer import normalize_prior_art_record, validate_prior_art_metadata
from intelligence.prior_art.novelty_risk import analyze_novelty_risk
from intelligence.prior_art.prior_art_report import build_prior_art_report
from intelligence.prior_art.providers.base import (
    PriorArtConfigurationError,
    PriorArtMalformedResponseError,
    PriorArtProvider,
    PriorArtProviderError,
)
from intelligence.prior_art.query_builder import build_prior_art_queries
from intelligence.prior_art.result_ranker import rank_prior_art_results
from intelligence.prior_art.similarity import SimilarityEmbeddingService, analyze_semantic_similarity


def _deduplication_key(record: Mapping[str, Any], fallback: int) -> str:
    publication = str(record.get("publication_number") or "").strip().casefold()
    if publication:
        return f"publication:{publication}"
    title = " ".join(re.findall(r"[a-z0-9]+", str(record.get("title") or "").casefold()))
    date_value = record.get("priority_date") or record.get("filing_date")
    if title and date_value:
        return f"secondary:{title}|{date_value}"
    return f"unidentified:{fallback}"


def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        key = _deduplication_key(record, index)
        if key not in unique:
            unique[key] = record
    return list(unique.values())


class PriorArtSearchEngine:
    def __init__(
        self,
        provider: PriorArtProvider,
        embedding_service: SimilarityEmbeddingService,
        *,
        allow_test_provider: bool = False,
        cache: PriorArtSearchCache | None = None,
        cache_ttl_seconds: float = 900.0,
    ) -> None:
        if getattr(provider, "is_test_fixture", False) and not allow_test_provider:
            raise PriorArtConfigurationError(
                "Synthetic prior-art fixtures require explicit offline/test mode."
            )
        self.provider = provider
        self.embedding_service = embedding_service
        self.cache = cache or PriorArtSearchCache(cache_ttl_seconds)

    def search(self, invention: Mapping[str, Any], limit: int = 10) -> dict[str, Any]:
        if limit <= 0 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        query_data = build_prior_art_queries(invention)
        queries = query_data["queries"]
        if not queries:
            raise ValueError("The invention did not contain enough information for a search query.")

        raw_records: list[Any] = []
        failures: list[str] = []
        first_failure: PriorArtProviderError | None = None
        successful_queries = 0
        cache_hits = 0
        for query in queries:
            cached = self.cache.get(self.provider.name, query, limit)
            if cached is not None:
                records = cached
                cache_hits += 1
                successful_queries += 1
            else:
                try:
                    records = list(self.provider.search(query, limit=limit))
                except PriorArtProviderError as exc:
                    failures.append(str(exc))
                    if first_failure is None:
                        first_failure = exc
                    continue
                self.cache.put(self.provider.name, query, limit, records)
                successful_queries += 1
            raw_records.extend(records)

        if successful_queries == 0 and failures:
            # Preserve the controlled type so the API can select a stable status
            # without exposing credentials or provider response bodies.
            assert first_failure is not None
            raise first_failure

        normalized: list[dict[str, Any]] = []
        for raw in raw_records:
            try:
                normalized.append(normalize_prior_art_record(raw, provider=self.provider.name))
            except (TypeError, ValueError) as exc:
                raise PriorArtMalformedResponseError(
                    "The prior-art provider returned a malformed record."
                ) from exc
        unique = deduplicate_records(normalized)
        candidates: list[dict[str, Any]] = []
        for record in unique:
            candidates.append(
                {
                    **record,
                    "metadata_validation": validate_prior_art_metadata(record),
                    "similarity": analyze_semantic_similarity(
                        invention, record, self.embedding_service
                    ),
                    "feature_overlap": match_features(invention, record),
                }
            )
        ranked = rank_prior_art_results(candidates, queries)[:limit]
        risk = analyze_novelty_risk(ranked, search_performed=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        warnings = []
        if failures:
            warnings.append(
                f"{len(failures)} query request(s) failed; the returned search is partial."
            )
        return build_prior_art_report(
            queries=queries,
            provider=self.provider.name,
            provider_mode="mock" if getattr(self.provider, "is_test_fixture", False) else "live",
            records_found=len(raw_records),
            ranked_records=ranked,
            risk=risk,
            retrieval_timestamp=timestamp,
            cache_hits=cache_hits,
            warnings=warnings,
        )


def search_prior_art(
    invention: Mapping[str, Any],
    provider: PriorArtProvider,
    embedding_service: SimilarityEmbeddingService,
    *,
    limit: int = 10,
    allow_test_provider: bool = False,
) -> dict[str, Any]:
    return PriorArtSearchEngine(
        provider,
        embedding_service,
        allow_test_provider=allow_test_provider,
    ).search(invention, limit=limit)
