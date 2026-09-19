"""Prior-Art Semantic Similarity Score using the existing embedding service."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class SimilarityEmbeddingService(Protocol):
    def embed_documents(self, texts: Sequence[str], *, batch_size: int = 32) -> list[list[float]]: ...


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
    if denominator == 0:
        return 0.0
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(left, right, strict=True)) / denominator))


def cosine_to_presentation_score(cosine_similarity: float) -> int:
    """Convert cosine similarity to 0-100 by clamping negatives to zero."""
    return round(max(0.0, min(1.0, cosine_similarity)) * 100)


def invention_text(invention: Mapping[str, Any]) -> str:
    values: list[str] = [str(invention.get("title") or "")]
    values.extend(str(item) for item in invention.get("ingredients_components") or [])
    values.extend(
        str(invention.get(field) or "")
        for field in (
            "manufacturing_preparation_process",
            "therapeutic_purpose",
            "claimed_novelty",
            "technical_advantage",
        )
    )
    values.extend(str(item) for item in invention.get("technical_features") or [])
    return " ".join(value for value in values if value.strip())


def analyze_semantic_similarity(
    invention: Mapping[str, Any],
    record: Mapping[str, Any],
    embedding_service: SimilarityEmbeddingService,
) -> dict[str, int | str]:
    source = invention_text(invention)
    fields = {
        "title_similarity": str(record.get("title") or "").strip(),
        "abstract_similarity": str(record.get("abstract") or "").strip(),
        "claims_similarity": " ".join(str(item) for item in record.get("claims") or []).strip(),
    }
    available = [(name, text) for name, text in fields.items() if text]
    if not source or not available:
        return {
            "name": "Prior-Art Semantic Similarity Score",
            "overall_similarity": 0,
            "title_similarity": 0,
            "abstract_similarity": 0,
            "claims_similarity": 0,
        }
    vectors = embedding_service.embed_documents([source, *(text for _, text in available)])
    source_vector = vectors[0]
    scores = {name: 0 for name in fields}
    for (name, _), vector in zip(available, vectors[1:], strict=True):
        scores[name] = cosine_to_presentation_score(_cosine(source_vector, vector))

    weights = {"title_similarity": 0.25, "abstract_similarity": 0.45, "claims_similarity": 0.30}
    weight_total = sum(weights[name] for name, _ in available)
    overall = round(sum(scores[name] * weights[name] for name, _ in available) / weight_total)
    return {
        "name": "Prior-Art Semantic Similarity Score",
        "overall_similarity": overall,
        **scores,
    }


semantic_similarity = analyze_semantic_similarity
