"""Common provider contracts and safe failure types for prior-art search."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class PriorArtRecord:
    publication_number: str | None
    title: str | None
    abstract: str | None = None
    applicants: list[str] = field(default_factory=list)
    inventors: list[str] = field(default_factory=list)
    publication_date: str | None = None
    filing_date: str | None = None
    priority_date: str | None = None
    jurisdiction: str | None = None
    classification_codes: list[str] = field(default_factory=list)
    claims: list[str] = field(default_factory=list)
    source_url: str | None = None
    provider: str | None = None

    def to_dict(self) -> dict:
        value = asdict(self)
        for field in ("applicants", "inventors", "classification_codes", "claims"):
            value[field] = list(value[field])
        return value


class PriorArtProvider(Protocol):
    name: str
    is_test_fixture: bool

    def search(self, query: str, limit: int = 10) -> list[PriorArtRecord]: ...


class PriorArtProviderError(RuntimeError):
    """Base class for controlled provider failures."""


class PriorArtConfigurationError(PriorArtProviderError):
    """Raised when no usable provider is configured."""


class PriorArtTimeoutError(PriorArtProviderError):
    """Raised when a provider does not respond in time."""


class PriorArtAuthenticationError(PriorArtProviderError):
    """Raised when provider credentials are rejected."""


class PriorArtRateLimitError(PriorArtProviderError):
    """Raised when a provider rate limit is reached."""


class PriorArtMalformedResponseError(PriorArtProviderError):
    """Raised when a provider response cannot be normalized safely."""
