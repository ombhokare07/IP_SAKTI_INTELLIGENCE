"""Deterministic inventive-step indicators for preliminary screening."""

from collections.abc import Mapping, Sequence
from typing import Any


def analyze_inventive_step(
    invention: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]] = (),
    *,
    evidence_sufficient: bool = False,
) -> dict[str, Any]:
    advantage = str(invention.get("technical_advantage") or "").strip()
    claimed = str(invention.get("claimed_novelty") or "").strip()
    process = str(invention.get("manufacturing_preparation_process") or "").strip()
    combined = " ".join((advantage, claimed, process)).casefold()

    score = 15
    strengths: list[str] = []
    concerns: list[str] = []
    missing: list[str] = []

    if advantage:
        score += 25
        strengths.append("A technical advantage is stated.")
    else:
        missing.append("technical advancement or advantage")
    if claimed and process:
        score += 15
        strengths.append("The claimed difference is connected to a described process or feature.")
    else:
        concerns.append("The technical difference from a conventional approach is not fully described.")
    if any(term in combined for term in ("unexpected", "surprising", "non-obvious")):
        score += 15
        strengths.append("An unexpected or non-obvious effect is asserted and requires supporting evidence.")
    else:
        missing.append("unexpected-effect rationale")
    if any(term in combined for term in ("%", "measured", "increase", "decrease", "improved", "retention", "stability")):
        score += 15
        strengths.append("A potentially measurable technical improvement is identified.")
    else:
        missing.append("measurable technical improvement")
    if any(term in combined for term in ("compared", "comparative", "conventional", "existing")):
        score += 10
    else:
        missing.append("comparison with the conventional method")
    if any(term in combined for term in ("economic", "cost", "yield", "efficiency")):
        score += 5
        strengths.append("Possible economic or efficiency significance is stated.")
    if evidence_sufficient and evidence:
        score += 5
    else:
        concerns.append("Retrieved guidance is absent or insufficient for a grounded legal assessment.")

    score = round(max(0, min(100, score)))
    if not evidence_sufficient:
        status = "insufficient_evidence"
    elif advantage and score >= 60:
        status = "technical_advancement_indicated"
    else:
        status = "inventive_step_concern"
    concerns.append("Inventive step is not legally proven by this pre-screen.")

    return {
        "status": status,
        "score": score,
        "strengths": strengths,
        "concerns": concerns,
        "missing_information": list(dict.fromkeys(missing)),
        "evidence": [dict(item) for item in evidence],
    }


inventive_step_pre_screen = analyze_inventive_step
