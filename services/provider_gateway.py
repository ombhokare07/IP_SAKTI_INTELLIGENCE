"""Small injectable JSON gateway for an operator's authorized providers.

This is our gateway contract, not a claim that an authority exposes this API.
"""
import httpx
from intelligence.contracts import validate_endpoint


class ProviderUnavailable(RuntimeError):
    def __init__(self, code: str = "provider_unavailable"):
        self.code = code
        super().__init__(code)


class JSONGateway:
    def __init__(self, endpoint: str, token: str = "", *, timeout: float = 15, client=None):
        self.endpoint = validate_endpoint(endpoint) if endpoint else ""
        self._token = token
        self.timeout = timeout
        self._client = client or httpx.Client(timeout=timeout, follow_redirects=False)
        self._owns_client = client is None

    @property
    def configured(self):
        return bool(self.endpoint and self._token)

    def call(self, payload: dict) -> dict:
        if not self.configured:
            raise ProviderUnavailable("provider_not_configured")
        try:
            response = self._client.post(self.endpoint, json=payload, timeout=self.timeout,
                headers={"Authorization": f"Bearer {self._token}", "Accept": "application/json"})
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable("provider_timeout") from exc
        except httpx.HTTPError as exc:
            raise ProviderUnavailable("provider_network_error") from exc
        if response.status_code in (401, 403):
            raise ProviderUnavailable("provider_authentication_failed")
        if response.status_code == 429:
            raise ProviderUnavailable("provider_rate_limited")
        if response.status_code != 200:
            raise ProviderUnavailable("provider_http_error")
        try:
            value = response.json()
            if not isinstance(value, dict) or len(response.content) > 8_000_000:
                raise ValueError
        except ValueError as exc:
            raise ProviderUnavailable("provider_malformed_response") from exc
        return value

    def close(self):
        if self._owns_client:
            self._client.close()
