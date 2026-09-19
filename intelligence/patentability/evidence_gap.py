"""Deterministic patentability evidence-gap analysis."""

from collections.abc import Mapping, Sequence
from typing import Any


_NEXT_STEPS = {
    "exact ingredient quantities": "Document exact ingredient quantities and units.",
    "formulation ratios": "Record formulation ratios and acceptable ranges.",
    "manufacturing steps": "Provide a reproducible step-by-step manufacturing method.",
    "technical effect": "Define the technical effect attributable to the claimed difference.",
    "comparative testing": "Run comparative testing against the conventional approach.",
    "stability data": "Generate and document stability data where relevant.",
    "experimental evidence": "Provide experimental evidence supporting the claimed advantage.",
    "prior-art search": "Perform a comprehensive prior-art search before a final novelty opinion.",
    "traditional-knowledge search": "Perform a traditional-knowledge clearance search.",
    "precise claim language": "Draft precise claim language with a qualified patent professional.",
}


def analyze_evidence_gaps(
    invention: Mapping[str, Any],
    *,
    prior_art_searched: bool = False,
    traditional_knowledge_searched: bool = False,
) -> dict[str, list[str]]:
    missing: list[str] = []
    ingredients = invention.get("ingredients_components") or []
    description_text = " ".join(
        str(value or "")
        for value in (
            " ".join(str(item) for item in ingredients),
            invention.get("manufacturing_preparation_process"),
            invention.get("claimed_novelty"),
            invention.get("technical_advantage"),
        )
    ).casefold()

    if ingredients and not any(char.isdigit() for char in description_text):
        missing.extend(["exact ingredient quantities", "formulation ratios"])
    if not invention.get("manufacturing_preparation_process"):
        missing.append("manufacturing steps")
    if not invention.get("technical_advantage"):
        missing.append("technical effect")
    if not any(
        term in description_text
        for term in (
            "comparative study",
            "comparative test",
            "versus control",
            "control group",
            "test results",
        )
    ):
        missing.append("comparative testing")
    if not any(term in description_text for term in ("stability data", "shelf life", "stability study")):
        missing.append("stability data")
    if not any(term in description_text for term in ("experiment", "study", "test data", "%", "measured")):
        missing.append("experimental evidence")
    if not prior_art_searched:
        missing.append("prior-art search")
    if not traditional_knowledge_searched:
        missing.append("traditional-knowledge search")
    missing.append("precise claim language")

    deduplicated = list(dict.fromkeys(missing))
    return {
        "missing": deduplicated,
        "recommended_next_steps": [_NEXT_STEPS[item] for item in deduplicated],
    }


detect_evidence_gaps = analyze_evidence_gaps
