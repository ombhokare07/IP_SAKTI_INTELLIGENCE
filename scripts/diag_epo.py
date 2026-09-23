"""Safe live diagnostic for EPO OPS. Never prints credentials or token values."""
import sys

try:
    from _bootstrap import ensure_project_root
except ImportError:
    from scripts._bootstrap import ensure_project_root

ensure_project_root()

def main() -> int:
    from config import settings
    from intelligence.prior_art.providers.epo_ops_provider import EPOOPSProvider
    from intelligence.prior_art.providers.base import (
        PriorArtAuthenticationError, PriorArtConfigurationError,
        PriorArtMalformedResponseError, PriorArtProviderError,
        PriorArtRateLimitError, PriorArtTimeoutError,
    )

    key = settings.epo_ops_consumer_key.get_secret_value() if settings.epo_ops_consumer_key else ""
    secret = settings.epo_ops_consumer_secret.get_secret_value() if settings.epo_ops_consumer_secret else ""
    provider = EPOOPSProvider(key, secret, timeout=settings.provider_timeout)
    print(f"provider={provider.name} configured={provider.configured}")
    print(f"timeout={settings.provider_timeout} provider_cfg={settings.prior_art_provider!r}")
    if not provider.configured:
        print("NOT_CONFIGURED")
        return 2
    try:
        records = provider.search("ayurvedic formulation for diabetes treatment", limit=3)
        print(f"SEARCH_OK records={len(records)}")
        for r in records[:3]:
            print({"publication_number": r.publication_number, "title": (r.title or "")[:80]})
        return 0
    except (PriorArtAuthenticationError, PriorArtConfigurationError, PriorArtMalformedResponseError,
            PriorArtProviderError, PriorArtRateLimitError, PriorArtTimeoutError) as exc:
        print(f"SEARCH_FAILED type={type(exc).__name__} message={exc}")
        return 1
    except Exception as exc:  # unexpected
        print(f"UNEXPECTED type={type(exc).__name__}")
        return 3
    finally:
        provider.close()

if __name__ == "__main__":
    sys.exit(main())
