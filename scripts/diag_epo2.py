"""Deeper live diagnostics for EPO OPS 404. Never prints credentials/tokens."""
import sys

try:
    from _bootstrap import ensure_project_root
except ImportError:
    from scripts._bootstrap import ensure_project_root

ensure_project_root()

def main() -> int:
    from config import settings
    import httpx

    key = settings.epo_ops_consumer_key.get_secret_value() if settings.epo_ops_consumer_key else ""
    secret = settings.epo_ops_consumer_secret.get_secret_value() if settings.epo_ops_consumer_secret else ""
    token_url = "https://ops.epo.org/3.2/auth/accesstoken"
    search_url = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"

    with httpx.Client(timeout=15, follow_redirects=False) as client:
        print("=== token request ===")
        tr = client.post(token_url, auth=httpx.BasicAuth(key, secret),
                         data={"grant_type": "client_credentials"},
                         headers={"Accept": "application/json"})
        print(f"token status={tr.status_code} content_type={tr.headers.get('content-type')} len={len(tr.content)}")
        if tr.status_code != 200:
            return 1
        try:
            token_payload = tr.json()
            token = token_payload.get("access_token", "")
            token_type = token_payload.get("token_type")
        except ValueError:
            print("token response category=malformed_json")
            return 1
        print(f"token obtained={bool(token)} type={token_type}")

        print("=== biblio search (raw) ===")
        try:
            r = client.get(search_url,
                           params={"q": 'ta="ayurvedic"'},
                           headers={"Authorization": f"Bearer {token}",
                                    "Accept": "application/exchange+xml",
                                    "X-OPS-Range": "1-3"})
            print(f"search status={r.status_code} reason={r.reason_phrase} ctype={r.headers.get('content-type')}")
            body = r.content[:300]
            print(f"body-snippet={body!r}")
            print(f"location={r.headers.get('location')} server={r.headers.get('server')}")
        except Exception as exc:
            print(f"search transport error type={type(exc).__name__} message={exc}")

        print("=== biblio search base (no /biblio) ===")
        try:
            r2 = client.get("https://ops.epo.org/3.2/rest-services/published-data/search",
                            params={"q": "ayurvedic"},
                            headers={"Authorization": f"Bearer {token}", "Accept": "application/exchange+xml"})
            print(f"base status={r2.status_code} body-snippet={r2.content[:200]!r}")
        except Exception as exc:
            print(f"base transport error type={type(exc).__name__} message={exc}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
