from __future__ import annotations

import json

import pytest

from backend.api.schemas.patent_schema import PatentabilityRequest
from intelligence.patentability.evidence_gap import analyze_evidence_gaps
from intelligence.patentability.exclusion_checker import check_exclusion_risks
from intelligence.patentability.invention_analyzer import InventionAnalyzer
from intelligence.patentability.inventive_step import analyze_inventive_step
from intelligence.patentability.novelty_analyzer import analyze_novelty
from intelligence.patentability.patentability_engine import PatentabilityEngine
from intelligence.patentability.readiness_score import readiness_level, score_readiness_factors


COMPLETE = {
    "title": "Improved Herbal Wound Healing Formulation",
    "description": (
        "An Ayurvedic formulation containing turmeric, neem and aloe vera prepared "
        "using a modified low-temperature extraction process for wound healing."
    ),
    "claimed_innovation": (
        "The low-temperature extraction process improves retention compared with "
        "conventional preparation."
    ),
    "technical_advantage": "Improved stability and active-compound retention.",
}


class FakeRetriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.queries = []

    def retrieve(self, question):
        self.queries.append(question)
        return self.chunks


def test_minimal_invention_never_invents_missing_details() -> None:
    result = InventionAnalyzer().analyze(
        {"title": "New product", "description": "A product for evaluation."}
    )
    assert result["invention_type"] == "product"
    assert result["ingredients_components"] == []
    assert result["claimed_novelty"] is None
    assert "claimed novelty" in result["missing_information"]


def test_complete_invention_is_extracted_deterministically() -> None:
    result = InventionAnalyzer().analyze(COMPLETE)
    assert result["invention_type"] == "formulation"
    assert result["invention_category"] == "ayurvedic"
    assert result["ingredients_components"] == ["turmeric", "neem", "aloe vera"]
    assert "low-temperature extraction" in result["manufacturing_preparation_process"]


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        ("claimed_innovation", "claimed novelty"),
        ("technical_advantage", "technical advantage"),
    ],
)
def test_missing_core_claim_fields_are_reported(field: str, expected: str) -> None:
    payload = dict(COMPLETE)
    payload.pop(field)
    assert expected in InventionAnalyzer().analyze(payload)["missing_information"]


def test_novelty_pre_screen_requires_prior_art_search() -> None:
    invention = InventionAnalyzer().analyze(COMPLETE)
    result = analyze_novelty(invention, [{"citation_id": 1}], evidence_sufficient=True)
    assert result["status"] == "prior_art_search_required"
    assert 0 <= result["score"] <= 100


def test_inventive_step_detects_technical_advancement_indicators() -> None:
    invention = InventionAnalyzer().analyze(COMPLETE)
    result = analyze_inventive_step(
        invention, [{"citation_id": 1}], evidence_sufficient=True
    )
    assert result["status"] == "technical_advancement_indicated"
    assert result["strengths"]
    assert "Inventive step is not legally proven" in result["concerns"][-1]


def test_potential_exclusion_concern_requires_matching_evidence() -> None:
    invention = InventionAnalyzer().analyze(COMPLETE)
    chunk = {
        "chunk_id": "tk-1",
        "text": "Traditional knowledge and known properties require assessment.",
    }
    citation = {"citation_id": 1, "chunk_id": "tk-1", "text": chunk["text"]}
    risks = check_exclusion_risks(invention, [chunk], [citation])["risks"]
    grounded = next(risk for risk in risks if risk["type"] == "traditional_knowledge_concern")
    assert grounded["citations"] == [citation]


def test_evidence_gap_detection() -> None:
    gaps = analyze_evidence_gaps(InventionAnalyzer().analyze(COMPLETE))
    assert "prior-art search" in gaps["missing"]
    assert "traditional-knowledge search" in gaps["missing"]
    assert "comparative testing" in gaps["missing"]
    assert "experimental evidence" in gaps["missing"]


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0, "high_risk_or_incomplete"),
        (39, "high_risk_or_incomplete"),
        (40, "weak"),
        (59, "weak"),
        (60, "promising_but_review_required"),
        (74, "promising_but_review_required"),
        (75, "strong_preliminary_case"),
        (89, "strong_preliminary_case"),
        (90, "very_strong_preliminary_case"),
        (100, "very_strong_preliminary_case"),
    ],
)
def test_readiness_score_boundaries(score: int, level: str) -> None:
    assert readiness_level(score) == level
    factors = {
        name: score
        for name in (
            "invention_completeness",
            "novelty_clarity",
            "technical_advancement",
            "evidence_support",
            "patentability_risk",
        )
    }
    assert score_readiness_factors(factors)["score"] == score


def test_insufficient_evidence_prevents_supported_conclusions() -> None:
    result = PatentabilityEngine(FakeRetriever([]), check_source_files=False).check(COMPLETE)
    assert result["assessment"]["novelty"]["status"] == "insufficient_evidence"
    assert result["assessment"]["inventive_step"]["status"] == "insufficient_evidence"
    assert result["citations"] == []
    assert result["trust"]["hallucination_risk"] == "high"


def test_citation_preservation_and_trust_integration(tmp_path) -> None:
    source = tmp_path / "guidance.pdf"
    source.write_bytes(b"source")
    chunk = {
        "chunk_id": "guide-1",
        "text": "Traditional knowledge and novelty require careful assessment.",
        "source": "guidance.pdf",
        "page": 7,
        "path": str(source),
        "distance": 0.1,
    }
    result = PatentabilityEngine(
        FakeRetriever([chunk]),
        relevance_threshold=0.5,
        sufficiency_threshold=0.5,
        min_relevant_chunks=1,
    ).check(COMPLETE)
    citation = result["citations"][0]
    assert citation["source"] == "guidance.pdf"
    assert citation["page"] == 7
    assert citation["chunk_id"] == "guide-1"
    assert citation["retrieval_score"] == pytest.approx(0.95)
    assert result["trust"]["evidence_score"] > 0


def test_mocked_gemini_structured_extraction_is_grounded() -> None:
    class FakeLLM:
        def __init__(self):
            self.prompts = []

        def generate(self, prompt):
            self.prompts.append(prompt)
            return json.dumps(
                {
                    "invention_type": "unknown",
                    "invention_category": "unknown",
                    "ingredients": ["pulse extraction", "invented ingredient"],
                    "manufacturing_process": "pulse extraction",
                    "therapeutic_purpose": None,
                    "technical_features": ["pulse extraction"],
                    "traditional_known_elements": [],
                }
            )

    llm = FakeLLM()
    result = InventionAnalyzer(llm).analyze(
        {"title": "Experimental concept", "description": "It uses pulse extraction."}
    )
    assert len(llm.prompts) == 1
    assert result["manufacturing_preparation_process"] == "pulse extraction"
    assert "invented ingredient" not in result["ingredients_components"]


def test_api_request_schema() -> None:
    request = PatentabilityRequest(title="  A title ", description=" Description ")
    assert request.title == "A title"
    assert request.ingredients == []
    with pytest.raises(ValueError):
        PatentabilityRequest(title=" ", description="Description")
