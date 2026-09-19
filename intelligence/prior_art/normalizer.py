"""Normalize heterogeneous provider records without filling missing metadata."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any


def _first(record: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        value = record.get(name)
        if value not in (None, ""):
            return value
    return None


def _text(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _names(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, Mapping):
        value = list(value.values())
    if isinstance(value, str):
        values: Sequence[Any] = re.split(r"\s*[;|,]\s*", value)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        values = value
    else:
        values = [value]
    output: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            item = _first(item, "name", "full_name", "value")
        cleaned = _text(item)
        if cleaned and cleaned.casefold() not in {name.casefold() for name in output}:
            output.append(cleaned)
    return output


def _claims(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        cleaned = _text(value)
        return [cleaned] if cleaned else []
    return _names(value)


def _date(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (date, datetime)):
        return value.date().isoformat() if isinstance(value, datetime) else value.isoformat()
    cleaned = _text(value)
    if not cleaned:
        return None
    digits = re.sub(r"\D", "", cleaned)
    if len(digits) == 8:
        try:
            return date(int(digits[:4]), int(digits[4:6]), int(digits[6:])).isoformat()
        except ValueError:
            return None
    try:
        return date.fromisoformat(cleaned[:10]).isoformat()
    except ValueError:
        return None


def _publication_number(value: Any) -> str | None:
    cleaned = _text(value)
    return re.sub(r"[\s/]", "", cleaned).upper() if cleaned else None


def normalize_prior_art_record(
    raw: Any,
    *,
    provider: str | None = None,
) -> dict[str, Any]:
    if hasattr(raw, "to_dict"):
        raw = raw.to_dict()
    elif is_dataclass(raw):
        raw = asdict(raw)
    if not isinstance(raw, Mapping):
        raise TypeError("prior-art record must be a mapping or dataclass")

    normalized_provider = _text(provider) or _text(_first(raw, "provider", "source_provider"))
    jurisdiction = _text(_first(raw, "jurisdiction", "country", "office"))
    return {
        "publication_number": _publication_number(
            _first(raw, "publication_number", "publicationNumber", "publication_id", "patent_number")
        ),
        "title": _text(_first(raw, "title", "invention_title", "name")),
        "abstract": _text(_first(raw, "abstract", "summary")),
        "applicants": _names(_first(raw, "applicants", "applicant", "assignees", "assignee")),
        "inventors": _names(_first(raw, "inventors", "inventor")),
        "publication_date": _date(_first(raw, "publication_date", "publicationDate", "published")),
        "filing_date": _date(_first(raw, "filing_date", "filingDate", "application_date")),
        "priority_date": _date(_first(raw, "priority_date", "priorityDate")),
        "jurisdiction": jurisdiction.upper() if jurisdiction else None,
        "classification_codes": _names(
            _first(raw, "classification_codes", "classifications", "ipc", "cpc")
        ),
        "claims": _claims(_first(raw, "claims", "independent_claims", "claim_text")),
        "source_url": _text(_first(raw, "source_url", "url", "link")),
        "provider": normalized_provider,
    }


normalize_record = normalize_prior_art_record


def validate_prior_art_metadata(record: Mapping[str, Any]) -> dict[str, Any]:
    """Expose metadata completeness without inventing identifiers or dates."""
    issues: list[str] = []
    if not record.get("publication_number"):
        issues.append("publication_number is unavailable")
    if not record.get("title"):
        issues.append("title is unavailable")
    if not record.get("provider"):
        issues.append("provider is unavailable")
    if not record.get("source_url"):
        issues.append("source_url is unavailable")
    return {
        "valid_for_comparison": bool(record.get("publication_number") or record.get("title")),
        "issues": issues,
    }
