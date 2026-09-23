"""EPO OPS 3.2 bibliographic search. Network access is always explicit.

Contract: EPO OPS Reference Guide 1.3.20, sections 2.3.2 and 3.1.1.
No example patent records are used as a fallback for an OPS failure.

OPS signals "no results" with HTTP 404 plus a fault body
(SERVER.EntityNotFound / \"No results found\"), not with an empty result
set; that documented behaviour is treated as a successful empty search
instead of a provider failure.
"""
from __future__ import annotations

import math
import re
import threading
import time
from xml.etree import ElementTree as ET

import httpx

from intelligence.prior_art.normalizer import normalize_prior_art_record
from intelligence.prior_art.providers.base import (
    PriorArtAuthenticationError, PriorArtConfigurationError,
    PriorArtMalformedResponseError, PriorArtProviderError,
    PriorArtRateLimitError, PriorArtRecord, PriorArtTimeoutError,
)


_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "of", "or", "the", "to", "using", "with", "improved", "claimed",
}

_MISSING_ENTITY_FAULT = re.compile(rb"SERVER\.EntityNotFound", re.I)


def _text(node: ET.Element | None) -> str | None:
    return " ".join(" ".join(node.itertext()).split()) or None if node is not None else None


def _pick_language(nodes: list[ET.Element]) -> ET.Element | None:
    return next((n for n in nodes if n.get("lang") == "en"), nodes[0] if nodes else None)


def parse_ops_xml(content: bytes, *, provider: str = "epo_ops") -> list[PriorArtRecord]:
    # Reject declarations/entities and oversized payloads before parsing untrusted XML.
    if len(content) > 8_000_000 or re.search(br"<!\s*(?:DOCTYPE|ENTITY)", content, re.I):
        raise PriorArtMalformedResponseError("OPS returned unsafe or oversized XML.")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise PriorArtMalformedResponseError("OPS returned malformed XML.") from exc
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    search = root.find(".//biblio-search")
    docs = list(root.iter("exchange-document"))
    if not docs:
        if search is not None and search.get("total-result-count") == "0":
            return []
        raise PriorArtMalformedResponseError("OPS did not return a bibliographic result set.")
    records = []
    for doc in docs:
        if doc.get("status") == "not found":
            raise PriorArtMalformedResponseError("An OPS bibliographic record is unavailable.")
        reference = doc.find(".//publication-reference/document-id[@document-id-type='docdb']")
        country = doc.get("country") or _text(reference.find("country") if reference is not None else None)
        number = doc.get("doc-number") or _text(reference.find("doc-number") if reference is not None else None)
        kind = doc.get("kind") or _text(reference.find("kind") if reference is not None else None)
        publication = f"{country}{number}{kind or ''}" if country and number else None
        if not publication:
            raise PriorArtMalformedResponseError("OPS returned a record without its publication identifier.")
        def names(party: str) -> list[str]:
            nodes = doc.findall(f".//{party}[@data-format='epodoc']") or doc.findall(f".//{party}")
            return list(dict.fromkeys(t for n in nodes if (t := _text(n.find(".//name")))))
        priority = [t for n in doc.findall(".//priority-claim/document-id/date") if (t := _text(n))]
        # Search results do not guarantee claims or individual record URLs. Leave absent.
        record = normalize_prior_art_record({
            "publication_number": publication,
            "title": _text(_pick_language(doc.findall(".//invention-title"))),
            "abstract": _text(_pick_language(doc.findall(".//abstract"))),
            "applicants": names("applicant"), "inventors": names("inventor"),
            "publication_date": _text(reference.find("date") if reference is not None else None),
            "filing_date": _text(doc.find(".//application-reference/document-id/date")),
            "priority_date": min(priority) if priority else None,
            "jurisdiction": country,
            "classification_codes": [t for n in doc.findall(".//classification-ipc/text") if (t := _text(n))],
        }, provider=provider)
        records.append(PriorArtRecord(**record))
    return records


class EPOOPSProvider:
    name = "epo_ops"
    is_test_fixture = False
    TOKEN_URL = "https://ops.epo.org/3.2/auth/accesstoken"
    SEARCH_URL = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"

    def __init__(self, consumer_key: str = "", consumer_secret: str = "", *,
                 timeout: float = 15, client: httpx.Client | None = None,
                 clock=time.monotonic):
        self._key, self._secret = consumer_key.strip(), consumer_secret.strip()
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=False)
        self._owns_client = client is None
        self._clock = clock
        self._token, self._expires = "", 0.0
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return bool(self._key and self._secret)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            return self._client.request(method, url, timeout=self.timeout, **kwargs)
        except httpx.TimeoutException as exc:
            raise PriorArtTimeoutError("The OPS request timed out.") from exc
        except httpx.HTTPError as exc:
            raise PriorArtProviderError("The OPS request failed.") from exc

    @staticmethod
    def _check(response: httpx.Response) -> None:
        if response.status_code in (401, 403):
            raise PriorArtAuthenticationError("OPS authentication or access authorization failed.")
        if response.status_code == 429:
            raise PriorArtRateLimitError("The OPS request quota was reached.")
        if response.status_code != 200:
            raise PriorArtProviderError(f"OPS returned HTTP {response.status_code}.")

    @staticmethod
    def _is_missing_entity(response: httpx.Response) -> bool:
        """OPS reports zero matches as 404 + SERVER.EntityNotFound fault body."""
        return response.status_code == 404 and _MISSING_ENTITY_FAULT.search(response.content) is not None

    def _access_token(self) -> str:
        if not self.configured:
            raise PriorArtConfigurationError("EPO OPS consumer credentials are not configured.")
        with self._lock:
            if self._token and self._clock() < self._expires:
                return self._token
            response = self._request("POST", self.TOKEN_URL,
                auth=httpx.BasicAuth(self._key, self._secret),
                data={"grant_type": "client_credentials"}, headers={"Accept": "application/json"})
            self._check(response)
            try:
                payload = response.json()
                token = payload["access_token"]
                expires = float(payload["expires_in"])
                if not isinstance(token, str) or not token.strip() or not math.isfinite(expires) or expires <= 0:
                    raise ValueError
                if len(token)>8192 or any(ord(c)<32 for c in token):
                    raise ValueError
                if str(payload.get("token_type", "Bearer")).casefold() != "bearer":
                    raise ValueError
            except (ValueError, KeyError, TypeError) as exc:
                raise PriorArtMalformedResponseError("OPS returned an invalid OAuth token response.") from exc
            self._token = token
            self._expires = self._clock() + max(0, expires - min(30, expires / 10))
            return token

    def search(self, query: str, limit: int = 10) -> list[PriorArtRecord]:
        if not query.strip() or not 1 <= limit <= 100:
            raise ValueError("A query and a limit between 1 and 100 are required.")
        # Treat the engine's natural-language query as literal title/abstract terms,
        # dropping stop words so a single filler term cannot empty an AND query.
        terms = [t for t in re.findall(r"[^\W_]+", query, flags=re.UNICODE)[:40]
                 if t.casefold() not in _STOP]
        if not terms:
            raise ValueError("Search query contains no searchable terms.")
        cql = " AND ".join(f'ta="{term}"' for term in terms)
        for attempt in range(2):
            response = self._request("GET", self.SEARCH_URL, params={"q": cql}, headers={
                "Authorization": f"Bearer {self._access_token()}",
                "Accept": "application/exchange+xml", "X-OPS-Range": f"1-{limit}",
            })
            if response.status_code == 401 and attempt == 0:
                with self._lock:
                    self._token, self._expires = "", 0.0
                continue
            if self._is_missing_entity(response):
                return []
            self._check(response)
            return parse_ops_xml(response.content)[:limit]
        raise PriorArtAuthenticationError("OPS authentication failed after token renewal.")

    def close(self) -> None:
        self._token, self._expires = "", 0.0
        if self._owns_client:
            self._client.close()
