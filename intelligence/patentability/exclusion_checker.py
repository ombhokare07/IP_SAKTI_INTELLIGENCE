"""Evidence-grounded eligibility and exclusion risk indicators."""

from collections.abc import Mapping, Sequence
from typing import Any

from rag.citations.citation_generator import chunk_value


_RISK_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "traditional_knowledge_concern",
        ("traditional knowledge", "traditionally known", "known properties"),
        "Retrieved guidance indicates a potential traditional-knowledge concern that requires review.",
    ),
    (
        "known_ingredients_or_aggregation_concern",
        ("known ingredient", "mere admixture", "aggregation", "known substance"),
        "Retrieved guidance indicates that known ingredients or an aggregation may require further assessment.",
    ),
    (
        "therapeutic_method_concern",
        ("method of treatment", "therapeutic treatment", "treatment of human"),
        "Retrieved guidance indicates a potential concern for therapeutic-method claim language.",
    ),
)


def check_exclusion_risks(
    invention: Mapping[str, Any],
    evidence_chunks: Sequence[Mapping[str, Any]],
    citations: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    citation_by_chunk = {
        str(chunk_value(citation, "chunk_id")): dict(citation)
        for citation in citations
        if chunk_value(citation, "chunk_id") not in (None, "")
    }
    risks: list[dict[str, Any]] = []
    for risk_type, terms, reason in _RISK_PATTERNS:
        matched: list[dict[str, Any]] = []
        for chunk in evidence_chunks:
            text = str(chunk_value(chunk, "text") or "").casefold()
            if not any(term in text for term in terms):
                continue
            citation = citation_by_chunk.get(str(chunk_value(chunk, "chunk_id")))
            if citation:
                matched.append(citation)
        if matched:
            severity = "high" if risk_type == "traditional_knowledge_concern" else "medium"
            risks.append(
                {
                    "type": risk_type,
                    "severity": severity,
                    "reason": reason,
                    "citations": matched,
                }
            )

    if invention.get("traditional_known_elements_mentioned") and not any(
        risk["type"] == "traditional_knowledge_concern" for risk in risks
    ):
        risks.append(
            {
                "type": "traditional_elements_review_required",
                "severity": "medium",
                "reason": (
                    "Traditional or known elements are mentioned. This is a potential concern; "
                    "traditional-knowledge clearance requires a separate search."
                ),
                "citations": [],
            }
        )
    return {"risks": risks}


check_patentability_exclusions = check_exclusion_risks
