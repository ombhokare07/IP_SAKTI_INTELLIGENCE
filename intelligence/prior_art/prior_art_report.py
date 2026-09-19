"""Stable report assembly for prior-art API and patentability integration."""

from collections.abc import Mapping, Sequence
from typing import Any


def build_prior_art_report(
    *,
    queries: Sequence[str],
    provider: str,
    provider_mode: str,
    records_found: int,
    ranked_records: Sequence[Mapping[str, Any]],
    risk: Mapping[str, Any],
    retrieval_timestamp: str,
    cache_hits: int = 0,
    warnings: Sequence[str] = (),
) -> dict[str, Any]:
    results = [dict(item) for item in ranked_records]
    top_results = [
        {
            "publication_number": item.get("publication_number"),
            "title": item.get("title"),
            "similarity": item.get("similarity", {}).get("overall_similarity", 0),
            "matching_features": item.get("feature_overlap", {}).get("matching_features", []),
            "distinct_features": item.get("feature_overlap", {}).get(
                "apparently_distinct_features", []
            ),
            "source_url": item.get("source_url"),
            "provider": item.get("provider"),
        }
        for item in results
    ]
    limitations = [
        "This is a limited prior-art intelligence search, not a legal novelty opinion.",
        "No result, low similarity, or an apparently distinct feature establishes novelty.",
        "Patent metadata is preserved as received; unavailable values remain null or empty.",
    ]
    if provider_mode == "mock":
        limitations.insert(0, "TEST DATA ONLY: all returned patent records are synthetic fixtures.")
    limitations.extend(warnings)
    return {
        "search_summary": {
            "queries_run": list(queries),
            "provider": provider,
            "provider_mode": provider_mode,
            "configuration_status": "mock_test_data" if provider_mode == "mock" else "live_configured",
            "records_found": records_found,
            "records_analyzed": len(results),
            "cache_hits": cache_hits,
            "retrieval_timestamp": retrieval_timestamp,
        },
        "risk": dict(risk),
        "results": results,
        "top_results": top_results,
        "limitations": limitations,
    }


create_prior_art_report = build_prior_art_report
