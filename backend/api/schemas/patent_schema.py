from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.api.schemas.chat_schema import CitationResponse, TrustResponse
from backend.api.schemas.prior_art_schema import PriorArtSearchResponse


class PatentabilityRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=20_000)
    ingredients: list[str] = Field(default_factory=list, max_length=200)
    process: str | None = Field(default=None, max_length=10_000)
    claimed_innovation: str | None = Field(default=None, max_length=10_000)
    technical_advantage: str | None = Field(default=None, max_length=10_000)
    run_prior_art_search: bool = False

    @field_validator("title", "description")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned

    @field_validator("process", "claimed_innovation", "technical_advantage")
    @classmethod
    def optional_text_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return " ".join(value.split()) or None

    @field_validator("ingredients")
    @classmethod
    def clean_ingredients(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(cleaned for item in value if (cleaned := " ".join(item.split()))))


class PatentCitationResponse(CitationResponse):
    retrieval_score: float | None = Field(default=None, ge=0, le=1)


class InventionResponse(BaseModel):
    title: str
    invention_category: str
    invention_type: Literal["formulation", "process", "device", "system", "product", "method", "unknown"]
    ingredients_components: list[str]
    manufacturing_preparation_process: str | None = None
    therapeutic_purpose: str | None = None
    claimed_novelty: str | None = None
    technical_features: list[str]
    technical_advantage: str | None = None
    traditional_known_elements_mentioned: list[str]
    missing_information: list[str]


class NoveltyResponse(BaseModel):
    status: Literal[
        "potentially_novel",
        "novelty_concern",
        "insufficient_evidence",
        "prior_art_search_required",
        "potentially_novel_after_limited_search",
        "significant_prior_art_overlap",
        "insufficient_prior_art",
        "broader_search_required",
    ]
    score: int = Field(ge=0, le=100)
    positive_signals: list[str]
    concerns: list[str]
    evidence: list[PatentCitationResponse]
    limitations: list[str]


class InventiveStepResponse(BaseModel):
    status: str
    score: int = Field(ge=0, le=100)
    strengths: list[str]
    concerns: list[str]
    missing_information: list[str]
    evidence: list[PatentCitationResponse]


class ReadinessResponse(BaseModel):
    name: Literal["Patent Readiness Pre-Screen Score"]
    score: int = Field(ge=0, le=100)
    level: Literal[
        "high_risk_or_incomplete",
        "weak",
        "promising_but_review_required",
        "strong_preliminary_case",
        "very_strong_preliminary_case",
    ]
    factors: dict[str, int]
    limitations: list[str]


class AssessmentResponse(BaseModel):
    readiness_score: int = Field(ge=0, le=100)
    readiness_level: str
    readiness: ReadinessResponse
    novelty: NoveltyResponse
    inventive_step: InventiveStepResponse


class RiskResponse(BaseModel):
    type: str
    severity: Literal["low", "medium", "high"]
    reason: str
    citations: list[PatentCitationResponse]


class PatentabilityResponse(BaseModel):
    invention: InventionResponse
    assessment: AssessmentResponse
    risks: list[RiskResponse]
    evidence_gaps: list[str]
    recommended_next_steps: list[str]
    citations: list[PatentCitationResponse]
    trust: TrustResponse
    limitations: list[str]
    prior_art: PriorArtSearchResponse | None = None


PatentCheckRequest = PatentabilityRequest
PatentCheckResponse = PatentabilityResponse
