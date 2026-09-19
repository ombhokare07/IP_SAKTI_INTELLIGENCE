"""Phase-2A patentability pre-screen orchestration."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from intelligence.patentability.evidence_gap import analyze_evidence_gaps
from intelligence.patentability.exclusion_checker import check_exclusion_risks
from intelligence.patentability.invention_analyzer import InventionAnalyzer
from intelligence.patentability.inventive_step import analyze_inventive_step
from intelligence.patentability.novelty_analyzer import analyze_novelty
from intelligence.patentability.readiness_score import calculate_readiness_score
from intelligence.trust.confidence_score import calculate_evidence_strength
from intelligence.trust.contradiction_detector import detect_contradictions
from intelligence.trust.evidence_checker import check_evidence, retrieval_similarity
from intelligence.trust.source_validator import validate_sources
from intelligence.trust.trust_score import calculate_trust_score
from rag.citations.citation_generator import build_citations, chunk_value
from intelligence.prior_art.providers.base import PriorArtConfigurationError


class PatentabilityRetriever(Protocol):
    def retrieve(self, question: str) -> Sequence[Mapping[str, Any]]: ...


FOCUSED_RETRIEVAL_QUERIES = (
    "patentability of Ayurvedic formulation",
    "novelty requirement",
    "inventive step requirement",
    "traditional knowledge exclusion",
    "known ingredients patentability",
    "modified extraction process patentability",
    "therapeutic formulation patent requirements",
)

STANDARD_LIMITATIONS = [
    "This is a preliminary AI-assisted patentability screening.",
    "A comprehensive prior-art search has not yet been performed.",
    "Traditional-knowledge clearance has not yet been performed.",
    "The score does not represent probability of patent grant.",
]


def _novelty_with_prior_art(
    novelty: Mapping[str, Any], prior_art: Mapping[str, Any]
) -> dict[str, Any]:
    updated = dict(novelty)
    updated["positive_signals"] = list(novelty.get("positive_signals") or [])
    updated["concerns"] = list(novelty.get("concerns") or [])
    updated["limitations"] = list(novelty.get("limitations") or [])
    risk = prior_art.get("risk") or {}
    summary = prior_art.get("search_summary") or {}
    level = risk.get("level")
    overlap_score = int(risk.get("score", 0))

    if level == "high_detected_overlap":
        updated["status"] = "significant_prior_art_overlap"
        updated["score"] = min(int(updated.get("score", 0)), max(10, 100 - overlap_score))
        updated["concerns"].append(
            "Significant overlap was detected in the retrieved prior-art set and requires professional review."
        )
    elif level == "moderate_detected_overlap":
        updated["status"] = "novelty_concern"
        updated["score"] = min(int(updated.get("score", 0)), 50)
        updated["concerns"].append(
            "Moderate overlap was detected in the retrieved prior-art set."
        )
    elif level == "low_detected_overlap":
        if int(summary.get("records_analyzed", 0)) >= 3:
            updated["status"] = "potentially_novel_after_limited_search"
            updated["score"] = min(75, int(updated.get("score", 0)) + 5)
            updated["positive_signals"].append(
                "No significant overlap was identified in the retrieved prior-art set. "
                "A comprehensive professional search may still be required."
            )
        else:
            updated["status"] = "broader_search_required"
            updated["concerns"].append(
                "Too few records were analyzed to reduce prior-art uncertainty."
            )
    else:
        updated["status"] = "insufficient_prior_art"
        updated["score"] = min(int(updated.get("score", 0)), 40)
        updated["concerns"].append(
            "The configured search returned insufficient prior art for a supported novelty view."
        )

    updated["limitations"] = [
        limitation
        for limitation in updated["limitations"]
        if limitation != "No comprehensive prior-art search has been performed."
    ]
    updated["limitations"].append(
        "Only a limited configured-provider search was performed; this is not a final novelty determination."
    )
    if summary.get("provider_mode") == "mock":
        updated["limitations"].append(
            "The prior-art integration used synthetic TEST DATA / MOCK PROVIDER records."
        )
    return updated


def _normalized_chunk(chunk: Mapping[str, Any], query: str) -> dict[str, Any]:
    normalized = dict(chunk)
    for field in ("chunk_id", "source", "page", "path", "text"):
        value = chunk_value(chunk, field)
        if value not in (None, ""):
            normalized[field] = value
    score = retrieval_similarity(query, chunk)
    normalized["retrieval_score"] = round(score, 4)
    normalized["relevance_score"] = round(score, 4)
    normalized["retrieval_query"] = query
    return normalized


def retrieve_patentability_evidence(
    retriever: PatentabilityRetriever,
    invention: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    queries = list(FOCUSED_RETRIEVAL_QUERIES)
    invention_type = str(invention.get("invention_type") or "unknown")
    claimed = str(invention.get("claimed_novelty") or "").strip()
    if claimed:
        queries.insert(0, f"{invention_type} patentability claimed technical difference {claimed}")

    by_identity: dict[str, dict[str, Any]] = {}
    for query in queries:
        for raw in retriever.retrieve(query):
            chunk = _normalized_chunk(raw, query)
            identity = str(
                chunk_value(chunk, "chunk_id")
                or f"{chunk_value(chunk, 'source')}:{chunk_value(chunk, 'page')}:{chunk_value(chunk, 'text')}"
            )
            previous = by_identity.get(identity)
            if previous is None or chunk["retrieval_score"] > previous["retrieval_score"]:
                by_identity[identity] = chunk

    ranked = sorted(
        by_identity.values(), key=lambda item: float(item["retrieval_score"]), reverse=True
    )
    evidence_question = " ".join(queries)
    return ranked, evidence_question


def _citations_with_scores(chunks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    citations = build_citations(chunks)
    for citation, chunk in zip(citations, chunks, strict=True):
        citation["retrieval_score"] = chunk.get("retrieval_score")
    return citations


def _trust_summary(
    chunks: Sequence[Mapping[str, Any]],
    citations: Sequence[Mapping[str, Any]],
    *,
    evidence_sufficient: bool,
    question: str,
    check_source_files: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contradictions = detect_contradictions(chunks)
    scored_chunks = [
        {**dict(chunk), "citation_id": citation["citation_id"]}
        for chunk, citation in zip(chunks, citations, strict=True)
    ]
    evidence_strength = calculate_evidence_strength(
        scored_chunks, question=question, contradictions=contradictions
    )
    citation_validation = validate_sources(
        citations,
        retrieved_chunks=chunks,
        check_file_exists=check_source_files,
    )
    hallucination = {
        "risk": "low" if evidence_sufficient and citation_validation["valid"] else "high",
        "score": 0 if evidence_sufficient and citation_validation["valid"] else 60,
        "issues": [] if evidence_sufficient else ["Retrieved evidence was insufficient."],
    }
    claims = {"claims": [], "unsupported_claims": [], "invalid_citation_ids": []}
    trust = calculate_trust_score(
        evidence_strength,
        citation_validation,
        claims,
        hallucination,
        contradictions,
    )
    trust.update(
        {
            "evidence_score": evidence_strength["evidence_score"],
            "hallucination_risk": hallucination["risk"],
            "contradictions_detected": bool(contradictions["detected"]),
            "unsupported_claims": 0,
        }
    )
    return trust, evidence_strength


class PatentabilityEngine:
    """Compose Phase-1 retrieval and trust services into a Phase-2A pre-screen."""

    def __init__(
        self,
        retriever: PatentabilityRetriever,
        *,
        llm_service: Any | None = None,
        relevance_threshold: float | None = None,
        sufficiency_threshold: float | None = None,
        min_relevant_chunks: int | None = None,
        check_source_files: bool = True,
        prior_art_engine: Any | None = None,
    ) -> None:
        self.retriever = retriever
        self.invention_analyzer = InventionAnalyzer(llm_service)
        self.relevance_threshold = relevance_threshold
        self.sufficiency_threshold = sufficiency_threshold
        self.min_relevant_chunks = min_relevant_chunks
        self.check_source_files = check_source_files
        self.prior_art_engine = prior_art_engine

    def check(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        invention = self.invention_analyzer.analyze(payload)
        retrieved, question = retrieve_patentability_evidence(self.retriever, invention)
        checked = check_evidence(
            question,
            retrieved,
            relevance_threshold=self.relevance_threshold,
            sufficiency_threshold=self.sufficiency_threshold,
            min_relevant_chunks=self.min_relevant_chunks,
        )
        relevant = list(checked["relevant_chunks"])
        citations = _citations_with_scores(relevant)
        evidence_sufficient = bool(checked["sufficient"])

        novelty = analyze_novelty(
            invention, citations, evidence_sufficient=evidence_sufficient
        )
        run_prior_art = bool(payload.get("run_prior_art_search", False))
        prior_art_result: dict[str, Any] | None = None
        if run_prior_art:
            if self.prior_art_engine is None:
                raise PriorArtConfigurationError(
                    "Live prior-art provider is not configured."
                )
            prior_art_result = self.prior_art_engine.search(invention, limit=10)
            novelty = _novelty_with_prior_art(novelty, prior_art_result)
        inventive_step = analyze_inventive_step(
            invention, citations, evidence_sufficient=evidence_sufficient
        )
        risks = check_exclusion_risks(invention, relevant, citations)["risks"]
        gaps = analyze_evidence_gaps(
            invention, prior_art_searched=prior_art_result is not None
        )
        trust, evidence_strength = _trust_summary(
            relevant,
            citations,
            evidence_sufficient=evidence_sufficient,
            question=question,
            check_source_files=self.check_source_files,
        )
        readiness = calculate_readiness_score(
            invention,
            novelty,
            inventive_step,
            evidence_strength,
            risks,
        )
        if prior_art_result is not None:
            readiness["limitations"] = [
                "This score is a deterministic readiness pre-screen, not a probability of patent grant.",
                "Prior-art input was limited to the configured provider, generated queries, and returned records.",
                "Traditional-knowledge clearance remains outside this phase.",
            ]

        result = {
            "invention": invention,
            "assessment": {
                "readiness_score": readiness["score"],
                "readiness_level": readiness["level"],
                "readiness": readiness,
                "novelty": novelty,
                "inventive_step": inventive_step,
            },
            "risks": risks,
            "evidence_gaps": gaps["missing"],
            "recommended_next_steps": gaps["recommended_next_steps"],
            "citations": citations,
            "trust": trust,
            "limitations": list(STANDARD_LIMITATIONS),
        }
        if prior_art_result is not None:
            result["prior_art"] = prior_art_result
        return result

    run = check


def check_patentability(
    payload: Mapping[str, Any],
    retriever: PatentabilityRetriever,
    **kwargs: Any,
) -> dict[str, Any]:
    return PatentabilityEngine(retriever, **kwargs).check(payload)
