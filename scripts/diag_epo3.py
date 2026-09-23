"""Compare safe EPO query shapes without printing credentials or tokens."""
import re
import sys

import httpx

try:
    from _bootstrap import ensure_project_root
except ImportError:
    from scripts._bootstrap import ensure_project_root

ensure_project_root()


def main() -> int:
    from config import settings

    key = settings.epo_ops_consumer_key.get_secret_value()
    secret = settings.epo_ops_consumer_secret.get_secret_value()
    token_url = "https://ops.epo.org/3.2/auth/accesstoken"
    search_url = "https://ops.epo.org/3.2/rest-services/published-data/search/biblio"

    with httpx.Client(timeout=15, follow_redirects=False) as client:
        tr = client.post(token_url, auth=httpx.BasicAuth(key, secret),
                         data={"grant_type": "client_credentials"}, headers={"Accept": "application/json"})
        if tr.status_code != 200:
            print(f"token status={tr.status_code}")
            return 1
        try:
            token = tr.json()["access_token"]
        except (KeyError, TypeError, ValueError):
            print("token response category=malformed")
            return 1
        for query_index, query in enumerate([
            "ayurvedic formulation for diabetes treatment",
            "ayurvedic herbal composition",
            "antidiabetic polyherbal composition",
        ], start=1):
            terms = re.findall(r"[^\W_]+", query, flags=re.UNICODE)[:40]
            cql = " AND ".join(f'ta="{term}"' for term in terms)
            r = client.get(search_url, params={"q": cql},
                           headers={"Authorization": f"Bearer {token}",
                                    "Accept": "application/exchange+xml", "X-OPS-Range": "1-3"})
            match = re.search(rb"total-result-count=\"(\d+)\"", r.content) if r.status_code == 200 else None
            print(f"query_index={query_index} status={r.status_code} total={match.group(1).decode() if match else 'unavailable'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
