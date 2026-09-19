"""Small in-memory, expiring prior-art query cache."""

from __future__ import annotations

import time
from typing import Any


class PriorArtSearchCache:
    def __init__(self, ttl_seconds: float = 900.0) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds cannot be negative")
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, tuple[float, list[Any]]] = {}

    @staticmethod
    def key(provider: str, query: str, limit: int) -> str:
        return f"{provider.casefold().strip()}|{' '.join(query.casefold().split())}|{limit}"

    def get(self, provider: str, query: str, limit: int) -> list[Any] | None:
        key = self.key(provider, query, limit)
        item = self._items.get(key)
        if item is None:
            return None
        created, records = item
        if time.monotonic() - created > self.ttl_seconds:
            self._items.pop(key, None)
            return None
        return list(records)

    def put(self, provider: str, query: str, limit: int, records: list[Any]) -> None:
        self._items[self.key(provider, query, limit)] = (time.monotonic(), list(records))
