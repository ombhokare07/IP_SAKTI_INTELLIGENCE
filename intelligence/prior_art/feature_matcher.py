"""Conservative lexical feature overlap analysis."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


_STOP = {"a", "an", "and", "for", "in", "of", "or", "the", "to", "with", "using"}


def _normalized(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold().replace("-", " ")))


def _tokens(value: Any) -> set[str]:
    return {term for term in _normalized(value).split() if len(term) > 2 and term not in _STOP}


def invention_features(invention: Mapping[str, Any]) -> list[str]:
    candidates: list[Any] = []
    candidates.extend(invention.get("ingredients_components") or [])
    candidates.extend(invention.get("technical_features") or [])
    candidates.extend(
        invention.get(field)
        for field in (
            "manufacturing_preparation_process",
            "therapeutic_purpose",
            "technical_advantage",
        )
    )
    output: list[str] = []
    for candidate in candidates:
        cleaned = " ".join(str(candidate or "").split())
        if cleaned and cleaned.casefold() not in {item.casefold() for item in output}:
            output.append(cleaned)
    return output


def match_features(
    invention: Mapping[str, Any],
    record: Mapping[str, Any],
) -> dict[str, list[str]]:
    record_text = " ".join(
        [str(record.get("title") or ""), str(record.get("abstract") or "")]
        + [str(item) for item in record.get("claims") or []]
    )
    normalized_record = _normalized(record_text)
    record_terms = _tokens(record_text)
    matching: list[str] = []
    partial: list[str] = []
    distinct: list[str] = []
    unsupported: list[str] = []

    if not normalized_record:
        unsupported.append("The retrieved record has no title, abstract, or claims to compare.")
    for feature in invention_features(invention):
        normalized_feature = _normalized(feature)
        terms = _tokens(feature)
        if not terms:
            unsupported.append(f"Feature could not be compared reliably: {feature}")
            continue
        coverage = len(terms & record_terms) / len(terms)
        if normalized_feature in normalized_record or coverage >= 0.8:
            matching.append(feature)
        elif coverage >= 0.4:
            partial.append(feature)
        else:
            distinct.append(f"{feature} — not identified in this retrieved record")
    return {
        "matching_features": matching,
        "partially_matching_features": partial,
        "apparently_distinct_features": distinct,
        "unsupported_comparisons": unsupported,
    }


analyze_feature_overlap = match_features
