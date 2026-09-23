"""End-to-end check of /api/prior-art/search using a real signed session cookie.
Never prints credentials or token values."""
import sys

try:
    from _bootstrap import ensure_project_root
except ImportError:
    from scripts._bootstrap import ensure_project_root

ensure_project_root()

from backend.core.session import issue_session

def main() -> int:
    import json
    from config import Settings
    from fastapi.testclient import TestClient
    from backend.main import create_app

    settings = Settings()
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=False) as client:
        user = {"sub": "diag-user", "email": "diag@example.org", "name": "Diag", "picture": ""}
        cookie = issue_session(settings, user)
        client.cookies.set(settings.session_cookie_name, cookie)
        payload = {
            "title": "Polyherbal antidiabetic ayurvedic composition",
            "description": "A composition of bitter gourd, fenugreek and turmeric for blood sugar management.",
            "ingredients": ["bitter gourd", "fenugreek", "turmeric"],
            "process": "aqueous extraction and roller drying",
            "claimed_innovation": "synergistic ratio of the three herbal extracts",
            "technical_advantage": "improved glycemic control with reduced bitterness",
            "limit": 5,
        }
        r = client.post("/api/prior-art/search", json=payload)
        print(f"status={r.status_code}")
        if r.status_code != 200:
            print(f"body={r.text[:500]}")
            return 1
        data = r.json()
        summary = data["search_summary"]
        risk = data["risk"]
        print(f"provider={summary['provider']} mode={summary['provider_mode']} records_found={summary['records_found']}")
        print(f"records_analyzed={summary['records_analyzed']} cache_hits={summary['cache_hits']}")
        print(f"risk_level={risk['level']} risk_score={risk['score']}")
        for res in data["results"][:3]:
            print(f"  {res['publication_number']} sim={res['similarity']['overall_similarity']} title={(res['title'] or '')[:70]}")
        print(f"queries={summary['queries_run']}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
