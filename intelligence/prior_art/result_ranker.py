"""Deterministic ranking for normalized prior-art candidates."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


RANKING_WEIGHTS = {
    "semantic_similarity": 0.50,
    "feature_overlap": 0.30,
    "query_relevance": 0.20,
}


def feature_overlap_score(overlap: Mapping[str, Any]) -> int:
    matching = len(overlap.get("matching_features") or [])
    partial = len(overlap.get("partially_matching_features") or [])
    distinct = len(overlap.get("apparently_distinct_features") or [])
    total = matching + partial + distinct
    return round((matching + partial * 0.5) / total * 100) if total else 0


def query_relevance_score(queries: Sequence[str], record: Mapping[str, Any]) -> int:
    text = " ".join(
        [str(record.get("title") or ""), str(record.get("abstract") or "")]
        + [str(item) for item in record.get("claims") or []]
    ).casefold()
    text_terms = set(re.findall(r"[a-z0-9]+", text))
    best = 0.0
    for query in queries:
        terms = {term for term in re.findall(r"[a-z0-9]+", query.casefold()) if len(term) > 2}
        if terms:
            best = max(best, len(terms & text_terms) / len(terms))
    return round(best * 100)


def rank_prior_art_results(
    candidates: Sequence[Mapping[str, Any]],
    queries: Sequence[str],
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        semantic = int(item.get("similarity", {}).get("overall_similarity", 0))
        overlap = feature_overlap_score(item.get("feature_overlap", {}))
        relevance = query_relevance_score(queries, item)
        score = round(
            semantic * RANKING_WEIGHTS["semantic_similarity"]
            + overlap * RANKING_WEIGHTS["feature_overlap"]
            + relevance * RANKING_WEIGHTS["query_relevance"]
        )
        item["ranking_score"] = score
        item["feature_overlap_score"] = overlap
        item["query_relevance_score"] = relevance
        item["reason_for_ranking"] = (
            f"Weighted semantic similarity {semantic}/100, feature overlap "
            f"{overlap}/100, and query relevance {relevance}/100."
        )
        ranked.append(item)
    ranked.sort(
        key=lambda item: (
            -int(item["ranking_score"]),
            str(item.get("publication_number") or ""),
            str(item.get("title") or ""),
        )
    )
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank
    return ranked


rank_results = rank_prior_art_results
