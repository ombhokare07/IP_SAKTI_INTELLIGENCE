"""Focused, conclusion-free patent search query construction."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any


_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "of", "or", "the", "to", "using", "with", "improved", "claimed",
}


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = " ".join(value.replace("_", " ").split())
    return value or None


def _terms(values: Sequence[Any]) -> list[str]:
    output: list[str] = []
    for value in values:
        cleaned = _clean(value)
        if not cleaned:
            continue
        for term in re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", cleaned):
            if len(term) > 2 and term.casefold() not in _STOP:
                normalized = term.casefold()
                if normalized not in output:
                    output.append(normalized)
    return output


def build_prior_art_queries(invention: Mapping[str, Any]) -> dict[str, list[str]]:
    ingredients = [str(item) for item in invention.get("ingredients_components") or []]
    features = [str(item) for item in invention.get("technical_features") or []]
    purpose = _clean(invention.get("therapeutic_purpose"))
    process = _clean(invention.get("manufacturing_preparation_process"))
    advantage = _clean(invention.get("technical_advantage"))
    claimed = _clean(invention.get("claimed_novelty"))
    invention_type = _clean(invention.get("invention_type"))
    category = _clean(invention.get("invention_category"))

    technical_terms = _terms(ingredients + features + [process, purpose, advantage, claimed])
    key_features = list(dict.fromkeys(ingredients + features + [x for x in (process, advantage) if x]))

    queries: list[str] = []

    def add(parts: Sequence[str | None]) -> None:
        words = _terms([part for part in parts if part])
        query = " ".join(words[:12])
        if len(words) >= 2 and query not in queries:
            queries.append(query)

    add([*ingredients[:4], purpose, invention_type])
    add([process, advantage])
    add([category, purpose, invention_type, *ingredients[:2]])
    add([claimed, process])
    if not queries:
        add([_clean(invention.get("title")), invention_type])

    return {
        "queries": queries[:4],
        "technical_terms": technical_terms,
        "key_features": key_features,
    }


generate_search_queries = build_prior_art_queries
