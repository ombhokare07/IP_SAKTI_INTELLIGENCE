"""Configurable adapter for documented JSON patent-search APIs."""

from __future__ import annotations

from typing import Any

import httpx

from intelligence.prior_art.providers.base import (
    PriorArtAuthenticationError,
    PriorArtMalformedResponseError,
    PriorArtProviderError,
    PriorArtRateLimitError,
    PriorArtRecord,
    PriorArtTimeoutError,
)
from intelligence.prior_art.normalizer import normalize_prior_art_record
from intelligence.contracts import validate_endpoint


class HTTPJSONPriorArtProvider:
    """POST query/limit to a configured machine-readable provider endpoint.

    The endpoint must return either a JSON list or an object whose ``records``
    or ``results`` member is a list. Provider-specific field shapes are handled
    by the normalizer; credentials are sent only as a bearer token.
    """

    is_test_fixture = False

    def __init__(
        self,
        api_url: str,
        *,
        api_key: str = "",
        timeout: float = 15.0,
        name: str = "configured_json_api",
        client: Any | None = None,
    ) -> None:
        if not api_url.strip():
            raise ValueError("api_url is required")
        self.api_url = validate_endpoint(api_url.strip())
        self.api_key = api_key.strip()
        self.timeout = timeout
        self.name = name.strip() or "configured_json_api"
        self._client = client or httpx.Client(timeout=timeout)

    def search(self, query: str, limit: int = 10) -> list[PriorArtRecord]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            response = self._client.post(
                self.api_url,
                json={"query": query, "limit": limit},
                headers=headers,
                timeout=self.timeout,
            )
        except httpx.TimeoutException as exc:
            raise PriorArtTimeoutError("The prior-art provider timed out.") from exc
        except httpx.HTTPError as exc:
            raise PriorArtProviderError("The prior-art provider request failed.") from exc

        if response.status_code in (401, 403):
            raise PriorArtAuthenticationError("Prior-art provider authentication failed.")
        if response.status_code == 429:
            raise PriorArtRateLimitError("The prior-art provider rate limit was reached.")
        if response.status_code >= 400:
            raise PriorArtProviderError(
                f"The prior-art provider returned HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise PriorArtMalformedResponseError(
                "The prior-art provider returned malformed JSON."
            ) from exc
        raw_records = payload if isinstance(payload, list) else (
            payload.get("records", payload.get("results")) if isinstance(payload, dict) else None
        )
        if not isinstance(raw_records, list):
            raise PriorArtMalformedResponseError(
                "The prior-art provider response did not contain a record list."
            )
        records: list[PriorArtRecord] = []
        for raw in raw_records[:limit]:
            if not isinstance(raw, dict):
                raise PriorArtMalformedResponseError(
                    "A prior-art provider record was not an object."
                )
            normalized = normalize_prior_art_record(raw, provider=self.name)
            records.append(PriorArtRecord(**normalized))
        return records

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()
