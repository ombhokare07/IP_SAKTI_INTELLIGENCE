"""Patent Readiness Pre-Screen Score calculation."""

from collections.abc import Mapping, Sequence
from typing import Any


WEIGHTS = {
    "invention_completeness": 0.20,
    "novelty_clarity": 0.20,
    "technical_advancement": 0.20,
    "evidence_support": 0.20,
    "patentability_risk": 0.20,
}


def readiness_level(score: int) -> str:
    if score < 40:
        return "high_risk_or_incomplete"
    if score < 60:
        return "weak"
    if score < 75:
        return "promising_but_review_required"
    if score < 90:
        return "strong_preliminary_case"
    return "very_strong_preliminary_case"


def _clamp(value: Any) -> int:
    try:
        return round(max(0.0, min(100.0, float(value))))
    except (TypeError, ValueError):
        return 0


def score_readiness_factors(
    factors: Mapping[str, Any],
    *,
    limitations: Sequence[str] = (),
) -> dict[str, Any]:
    normalized = {name: _clamp(factors.get(name, 0)) for name in WEIGHTS}
    score = round(sum(normalized[name] * weight for name, weight in WEIGHTS.items()))
    return {
        "name": "Patent Readiness Pre-Screen Score",
        "score": score,
        "level": readiness_level(score),
        "factors": normalized,
        "limitations": list(limitations),
    }


def calculate_readiness_score(
    invention: Mapping[str, Any] | None = None,
    novelty: Mapping[str, Any] | None = None,
    inventive_step: Mapping[str, Any] | None = None,
    evidence_strength: Mapping[str, Any] | None = None,
    risks: Sequence[Mapping[str, Any]] = (),
    *,
    factors: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if factors is not None:
        return score_readiness_factors(factors)

    invention = invention or {}
    present = sum(
        bool(invention.get(field))
        for field in (
            "title",
            "ingredients_components",
            "manufacturing_preparation_process",
            "claimed_novelty",
            "technical_advantage",
        )
    )
    completeness = round(present / 5 * 100)
    # A high preliminary exclusion signal must materially constrain readiness,
    # even when the invention narrative is otherwise complete.
    severity_penalty = {"low": 10, "medium": 25, "high": 60}
    risk_score = max(
        0,
        100 - sum(severity_penalty.get(str(risk.get("severity")), 20) for risk in risks),
    )
    computed = {
        "invention_completeness": completeness,
        "novelty_clarity": _clamp((novelty or {}).get("score", 0)),
        "technical_advancement": _clamp((inventive_step or {}).get("score", 0)),
        "evidence_support": _clamp((evidence_strength or {}).get("evidence_score", 0)),
        "patentability_risk": risk_score,
    }
    return score_readiness_factors(
        computed,
        limitations=(
            "This score is a deterministic readiness pre-screen, not a probability of patent grant.",
            "Prior-art and traditional-knowledge searches are outside this phase.",
        ),
    )


patent_readiness_score = calculate_readiness_score
