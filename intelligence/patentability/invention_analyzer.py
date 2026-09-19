"""Conservative, mostly deterministic invention fact extraction."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class StructuredExtractionService(Protocol):
    def generate(self, prompt: str) -> str: ...


INVENTION_TYPES = {
    "formulation",
    "process",
    "device",
    "system",
    "product",
    "method",
    "unknown",
}

_TYPE_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("formulation", ("formulation", "composition", "blend", "mixture")),
    ("device", ("device", "apparatus", "sensor", "machine")),
    ("system", ("system", "platform", "network")),
    ("process", ("process", "extraction", "manufacturing", "preparation")),
    ("method", ("method", "procedure", "technique")),
    ("product", ("product", "kit", "article")),
)
_CATEGORY_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ayurvedic", ("ayurvedic", "ayurveda")),
    ("herbal", ("herbal", "botanical", "plant-based")),
    ("pharmaceutical", ("pharmaceutical", "drug", "medicament")),
    ("medical_device", ("medical device", "diagnostic device")),
    ("technology", ("software", "computer", "electronic", "digital")),
)
_PURPOSE = re.compile(
    r"(?i)(?:intended|used|designed|configured)\s+(?:to|for)\s+([^.;]+)|"
    r"(?:treatment|management|healing|prevention|diagnosis)\s+(?:of\s+)?([^.;]+)"
)
_JSON_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        values: Sequence[Any] = re.split(r",|;|\band\b", value, flags=re.IGNORECASE)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = value
    else:
        return []
    output: list[str] = []
    for item in values:
        cleaned = _clean(item)
        if cleaned and cleaned.casefold() not in {entry.casefold() for entry in output}:
            output.append(cleaned)
    return output


def _extract_ingredients(text: str) -> list[str]:
    patterns = (
        r"(?i)\b(?:containing|comprising|includes?|ingredients?\s*(?:are|include|:))\s+([^.;]+)",
        r"(?i)\b(?:combination|mixture|blend)\s+of\s+([^.;]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        phrase = re.split(
            r"(?i)\s+(?:prepared|produced|manufactured|made|using|wherein|intended)\b",
            match.group(1),
            maxsplit=1,
        )[0]
        ingredients = _clean_list(phrase)
        if ingredients:
            return ingredients
    return []


def _extract_process(text: str) -> str | None:
    prepared = re.search(
        r"(?i)(?:prepared|produced|manufactured|made|obtained)\s+"
        r"(?:by|using|through|via)\s+([^.;]+)",
        text,
    )
    if prepared:
        candidate = re.split(
            r"(?i)\s+(?:intended|designed|configured)\s+(?:to|for)\b",
            prepared.group(1),
            maxsplit=1,
        )[0]
        return _clean(candidate)
    match = re.search(
        r"(?i)\b((?:(?:modified|controlled|low-temperature|cold)\s+){1,3}"
        r"(?:extraction|preparation|manufacturing)\s+process)\b",
        text,
    )
    return _clean(match.group(1)) if match else None


def _extract_purpose(title: str, description: str) -> str | None:
    match = _PURPOSE.search(description)
    if match:
        candidate = _clean(next((group for group in match.groups() if group), None))
        therapeutic_terms = (
            "heal",
            "treat",
            "therap",
            "prevent",
            "diagnos",
            "disease",
            "disorder",
            "wound",
        )
        if candidate and any(term in candidate.casefold() for term in therapeutic_terms):
            return candidate
    title_match = re.search(
        r"(?i)\b((?:wound\s+healing|[a-z-]+\s+(?:treatment|therapy|prevention|diagnosis)))\b",
        title,
    )
    return _clean(title_match.group(1)) if title_match else None


def _technical_features(process: str | None, claimed: str | None) -> list[str]:
    features: list[str] = []
    if process:
        features.append(process)
    if claimed:
        for marker in ("low-temperature", "modified", "controlled", "measurable"):
            if marker in claimed.casefold() and marker not in {item.casefold() for item in features}:
                features.append(marker)
    return features


def _parse_llm_json(raw: str) -> Mapping[str, Any]:
    cleaned = _JSON_FENCE.sub("", raw.strip())
    try:
        parsed = json.loads(cleaned)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, Mapping) else {}


def _grounded_in_input(value: str, source_text: str) -> bool:
    normalized = " ".join(value.casefold().split())
    return bool(normalized) and normalized in source_text.casefold()


class InventionAnalyzer:
    """Extract supplied invention facts without filling absent technical detail."""

    def __init__(self, llm_service: StructuredExtractionService | None = None) -> None:
        self.llm_service = llm_service

    def _gemini_extract(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if self.llm_service is None:
            return {}
        prompt = (
            "Extract only facts explicitly present in the invention input. Return one "
            "JSON object with keys invention_category, invention_type, ingredients, "
            "manufacturing_process, therapeutic_purpose, technical_features, and "
            "traditional_known_elements. Use null or [] when absent. Never infer legal "
            "novelty, prior art, quantities, effects, or missing facts.\n\nINPUT:\n"
            + json.dumps(dict(payload), ensure_ascii=False)
        )
        return _parse_llm_json(self.llm_service.generate(prompt))

    def analyze(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        title = _clean(payload.get("title"))
        description = _clean(payload.get("description"))
        if not title or not description:
            raise ValueError("title and description are required")

        claimed = _clean(payload.get("claimed_innovation"))
        advantage = _clean(payload.get("technical_advantage"))
        combined = " ".join((title, description, claimed or "", advantage or ""))
        lowered = combined.casefold()

        invention_type = "unknown"
        for candidate, terms in _TYPE_TERMS:
            if any(term in lowered for term in terms):
                invention_type = candidate
                break
        category = next(
            (candidate for candidate, terms in _CATEGORY_TERMS if any(term in lowered for term in terms)),
            "unknown",
        )
        ingredients = _clean_list(payload.get("ingredients")) or _extract_ingredients(description)
        process = _clean(payload.get("process")) or _extract_process(description)
        purpose = _extract_purpose(title, description)
        features = _technical_features(process, claimed)

        known_elements: list[str] = []
        if "traditional" in lowered or "ayurved" in lowered:
            known_elements.extend(ingredients)
            known_elements.append("Ayurvedic/traditional context")
        elif "known" in lowered or "conventional" in lowered:
            known_elements.extend(ingredients)

        needs_structured_help = (
            invention_type == "unknown"
            or category == "unknown"
            or not ingredients
            or process is None
            or purpose is None
        )
        llm_data = self._gemini_extract(payload) if needs_structured_help else {}
        if invention_type == "unknown":
            candidate = _clean(llm_data.get("invention_type"))
            if candidate and candidate.casefold() in INVENTION_TYPES:
                invention_type = candidate.casefold()
        if category == "unknown":
            candidate = _clean(llm_data.get("invention_category"))
            if candidate and _grounded_in_input(candidate, combined):
                category = candidate
        for field_name, target in (
            ("ingredients", ingredients),
            ("technical_features", features),
            ("traditional_known_elements", known_elements),
        ):
            for item in _clean_list(llm_data.get(field_name)):
                if _grounded_in_input(item, combined) and item.casefold() not in {x.casefold() for x in target}:
                    target.append(item)
        if process is None:
            candidate = _clean(llm_data.get("manufacturing_process"))
            process = candidate if candidate and _grounded_in_input(candidate, combined) else None
        if purpose is None:
            candidate = _clean(llm_data.get("therapeutic_purpose"))
            purpose = candidate if candidate and _grounded_in_input(candidate, combined) else None

        missing: list[str] = []
        for field, value in (
            ("ingredients/components", ingredients),
            ("manufacturing/preparation process", process),
            ("therapeutic purpose", purpose),
            ("claimed novelty", claimed),
            ("technical advantage", advantage),
        ):
            if not value:
                missing.append(field)

        return {
            "title": title,
            "invention_category": category,
            "invention_type": invention_type,
            "ingredients_components": ingredients,
            "manufacturing_preparation_process": process,
            "therapeutic_purpose": purpose,
            "claimed_novelty": claimed,
            "technical_features": features,
            "technical_advantage": advantage,
            "traditional_known_elements_mentioned": known_elements,
            "missing_information": missing,
        }


def analyze_invention(
    payload: Mapping[str, Any],
    llm_service: StructuredExtractionService | None = None,
) -> dict[str, Any]:
    return InventionAnalyzer(llm_service).analyze(payload)
