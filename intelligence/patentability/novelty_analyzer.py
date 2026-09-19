"""Preliminary novelty indicators; never a final novelty determination."""

from collections.abc import Mapping, Sequence
from typing import Any


def analyze_novelty(
    invention: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]] = (),
    *,
    evidence_sufficient: bool = False,
) -> dict[str, Any]:
    claimed = str(invention.get("claimed_novelty") or "").strip()
    advantage = str(invention.get("technical_advantage") or "").strip()
    features = list(invention.get("technical_features") or [])
    known = list(invention.get("traditional_known_elements_mentioned") or [])
    guidance_text = " ".join(str(item.get("text") or "") for item in evidence).casefold()

    score = 20
    positive: list[str] = []
    concerns: list[str] = []
    limitations = [
        "This is a novelty pre-screen, not a final novelty determination.",
        "No comprehensive prior-art search has been performed.",
    ]

    if claimed:
        score += 25
        positive.append("A claimed innovation is explicitly described.")
    else:
        concerns.append("The claimed innovation is not clearly described.")
    if features:
        score += 15
        positive.append("At least one technical feature or process difference is identified.")
    else:
        concerns.append("No distinct technical feature is identified.")
    if advantage:
        score += 15
        positive.append("A technical advantage is stated.")
    else:
        concerns.append("No technical advantage is stated.")
    if known:
        score -= 10
        concerns.append("Traditional or known elements are mentioned and require comparison with prior disclosures.")
    if evidence_sufficient and evidence:
        score += 10
        if any(
            term in guidance_text
            for term in (
                "traditional knowledge",
                "known properties",
                "known ingredient",
                "mere admixture",
                "lack of novelty",
                "not novel",
            )
        ):
            score -= 10
            concerns.append(
                "Retrieved guidance raises a potential novelty-related concern that requires review."
            )
    else:
        concerns.append("Retrieved guidance is absent or insufficient for a grounded legal assessment.")

    score = round(max(0, min(100, score)))
    if not evidence_sufficient:
        status = "insufficient_evidence"
    elif not claimed or (known and not features):
        status = "novelty_concern"
    else:
        status = "prior_art_search_required"

    return {
        "status": status,
        "score": score,
        "positive_signals": positive,
        "concerns": concerns,
        "evidence": [dict(item) for item in evidence],
        "limitations": limitations,
    }


novelty_pre_screen = analyze_novelty
