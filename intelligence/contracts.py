"""Shared provenance and screening semantics for phases 3–7."""
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

Mode = Literal["unconfigured", "mock", "local", "live"]
SCREENING_NOTICE = "Scores measure screening, evidence or grounding quality, not legal correctness or probability of patent grant."
NO_EVIDENCE = "No reliable evidence is available for a definitive conclusion."


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_endpoint(value: str) -> str:
    url = urlsplit(value)
    if (url.scheme != "https" and not (url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1"})) or not url.hostname or url.username or url.password or url.fragment:
        raise ValueError("Use an HTTPS endpoint without embedded credentials (HTTP localhost is allowed).")
    return value


class Evidence(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    title: str = Field(min_length=1, max_length=1000)
    excerpt: str = Field(min_length=1, max_length=100_000)
    source_url: str | None = None
    locator: str | None = None
    page: int | None = Field(default=None, gt=0)
    mode: Mode = "local"
    authority: str | None = None
    retrieved_at: str = Field(default_factory=now_iso)

    @field_validator("source_url")
    @classmethod
    def source_is_web_url(cls, value):
        return validate_endpoint(value) if value else None


def screening_trust(evidence: list[dict], *, mode: str, coverage: float = 1) -> dict:
    # This measures traceability/completeness only; mock evidence never earns real trust.
    valid = [e for e in evidence if e.get("excerpt") and (e.get("source_url") or e.get("locator"))]
    score = round(100 * len(valid) / len(evidence) * max(0, min(1, coverage))) if evidence and mode not in {"mock", "unconfigured"} else 0
    return {"trust_score": score, "evidence_score": score,
            "evidence_strength": "none" if not score else "limited" if score < 75 else "traceable",
            "disclaimer": SCREENING_NOTICE}
