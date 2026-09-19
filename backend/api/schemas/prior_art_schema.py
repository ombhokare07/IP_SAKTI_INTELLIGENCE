from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PriorArtSearchRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=20_000)
    ingredients: list[str] = Field(default_factory=list, max_length=200)
    process: str | None = Field(default=None, max_length=10_000)
    claimed_innovation: str | None = Field(default=None, max_length=10_000)
    technical_advantage: str | None = Field(default=None, max_length=10_000)
    limit: int = Field(default=10, ge=1, le=100)

    @field_validator("title", "description")
    @classmethod
    def required_text_not_blank(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned


class SimilarityResponse(BaseModel):
    name: Literal["Prior-Art Semantic Similarity Score"]
    overall_similarity: int = Field(ge=0, le=100)
    title_similarity: int = Field(ge=0, le=100)
    abstract_similarity: int = Field(ge=0, le=100)
    claims_similarity: int = Field(ge=0, le=100)


class FeatureOverlapResponse(BaseModel):
    matching_features: list[str]
    partially_matching_features: list[str]
    apparently_distinct_features: list[str]
    unsupported_comparisons: list[str]


class PriorArtResultResponse(BaseModel):
    rank: int = Field(gt=0)
    ranking_score: int = Field(ge=0, le=100)
    feature_overlap_score: int = Field(ge=0, le=100)
    query_relevance_score: int = Field(ge=0, le=100)
    publication_number: str | None = None
    title: str | None = None
    abstract: str | None = None
    applicants: list[str]
    inventors: list[str]
    publication_date: str | None = None
    filing_date: str | None = None
    priority_date: str | None = None
    jurisdiction: str | None = None
    classification_codes: list[str]
    claims: list[str]
    source_url: str | None = None
    provider: str | None = None
    similarity: SimilarityResponse
    feature_overlap: FeatureOverlapResponse
    reason_for_ranking: str
    metadata_validation: dict


class PriorArtRiskResponse(BaseModel):
    name: Literal["Detected Prior-Art Overlap Risk"]
    level: Literal[
        "low_detected_overlap",
        "moderate_detected_overlap",
        "high_detected_overlap",
        "insufficient_prior_art",
        "search_required",
    ]
    score: int = Field(ge=0, le=100)
    reasoning: list[str]
    high_similarity_records: list[dict]
    limitations: list[str]


class PriorArtSearchSummaryResponse(BaseModel):
    queries_run: list[str]
    provider: str
    provider_mode: Literal["mock", "live"]
    configuration_status: Literal["mock_test_data", "live_configured"]
    records_found: int = Field(ge=0)
    records_analyzed: int = Field(ge=0)
    cache_hits: int = Field(ge=0)
    retrieval_timestamp: str


class PriorArtTopResultResponse(BaseModel):
    publication_number: str | None = None
    title: str | None = None
    similarity: int = Field(ge=0, le=100)
    matching_features: list[str]
    distinct_features: list[str]
    source_url: str | None = None
    provider: str | None = None


class PriorArtSearchResponse(BaseModel):
    assessment_id: str | None = None
    search_summary: PriorArtSearchSummaryResponse
    risk: PriorArtRiskResponse
    results: list[PriorArtResultResponse]
    top_results: list[PriorArtTopResultResponse]
    limitations: list[str]


PriorArtRequest = PriorArtSearchRequest
PriorArtResponse = PriorArtSearchResponse
