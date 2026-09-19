"""Detected prior-art overlap risk, not a legal novelty conclusion."""

from collections.abc import Mapping, Sequence
from typing import Any


def analyze_novelty_risk(
    ranked_records: Sequence[Mapping[str, Any]],
    *,
    search_performed: bool,
) -> dict[str, Any]:
    limitations = [
        "Detected Prior-Art Overlap Risk is not a probability of rejection or lack of novelty.",
        "The result covers only records returned by the configured provider and queries.",
        "A comprehensive professional prior-art search may still be required.",
    ]
    if not search_performed:
        return {
            "name": "Detected Prior-Art Overlap Risk",
            "level": "search_required",
            "score": 0,
            "reasoning": ["No prior-art provider search was performed."],
            "high_similarity_records": [],
            "limitations": limitations,
        }
    if not ranked_records:
        return {
            "name": "Detected Prior-Art Overlap Risk",
            "level": "insufficient_prior_art",
            "score": 0,
            "reasoning": [
                "The configured search returned no records; absence of results does not establish novelty."
            ],
            "high_similarity_records": [],
            "limitations": limitations,
        }

    top_scores = [
        max(
            int(item.get("similarity", {}).get("overall_similarity", 0)),
            int(item.get("feature_overlap_score", 0)),
            int(item.get("ranking_score", 0)),
        )
        for item in ranked_records[:3]
    ]
    if len(top_scores) == 1:
        risk_score = top_scores[0]
    else:
        risk_score = max(
            top_scores[0],
            round(
                top_scores[0] * 0.7
                + (sum(top_scores[1:]) / (len(top_scores) - 1)) * 0.3
            ),
        )
    high_records = [
        {
            "publication_number": item.get("publication_number"),
            "title": item.get("title"),
            "similarity": item.get("similarity", {}).get("overall_similarity", 0),
        }
        for item in ranked_records
        if int(item.get("similarity", {}).get("overall_similarity", 0)) >= 75
    ]
    if risk_score >= 75:
        level = "high_detected_overlap"
    elif risk_score >= 50:
        level = "moderate_detected_overlap"
    else:
        level = "low_detected_overlap"
    return {
        "name": "Detected Prior-Art Overlap Risk",
        "level": level,
        "score": max(0, min(100, risk_score)),
        "reasoning": [
            f"The highest-ranked retrieved records produced a detected overlap score of {risk_score}/100.",
            "Similarity and feature matches indicate retrieval overlap only, not legal anticipation.",
        ],
        "high_similarity_records": high_records,
        "limitations": limitations,
    }


novelty_risk = analyze_novelty_risk
