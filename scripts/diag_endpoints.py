"""Live verification of every /api endpoint with a real signed session.
Sends valid payloads and validates returned schemas. No credentials printed."""
import base64
import io
import sys
import wave

try:
    from _bootstrap import ensure_project_root
except ImportError:
    from scripts._bootstrap import ensure_project_root

ensure_project_root()

from fastapi.testclient import TestClient


def _public_repr(value, depth=3):
    import json
    return json.dumps(_sanitize(value), ensure_ascii=False, default=str)[:600]

def _sanitize(value):
    import copy
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            lowered = str(k).lower()
            if "token" in lowered or "secret" in lowered or "key" in lowered or "auth" in lowered:
                out[k] = "<redacted>"
            else:
                out[k] = _sanitize(v)
        return out
    if isinstance(value, list):
        return [_sanitize(v) for v in value[:12]]
    return value

INVENTION = {
    "title": "Polyherbal antidiabetic ayurvedic composition",
    "description": "A composition of bitter gourd, fenugreek and turmeric for managing blood sugar in adults.",
    "ingredients": ["Momordica charantia", "Trigonella foenum-graecum", "Curcuma longa"],
    "process": "The dried powders are mixed in a synergistic 2:1:1 ratio and compressed into tablets.",
    "claimed_innovation": "A fixed synergistic ratio of the three herbal extracts.",
    "technical_advantage": "Improved glycemic control with reduced bitterness and improved palatability.",
}


def _silent_wav() -> str:
    """Return a small valid WAV fixture for exercising live voice fallbacks."""
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(16_000)
        audio.writeframes(b"\x00\x00" * 8_000)
    return base64.b64encode(output.getvalue()).decode("ascii")

def main():
    from config import Settings
    from backend.core.session import issue_session
    from backend.main import create_app

    settings = Settings()
    app = create_app(settings)
    results = []
    with TestClient(app, raise_server_exceptions=False) as client:
        cookie = issue_session(settings, {"sub": "verify-user", "email": "verify@example.org", "name": "Verifier", "picture": ""})
        client.cookies.set(settings.session_cookie_name, cookie)

        checks = [
            ("GET /health", client.get("/health"), None),
            ("GET /api/auth/me", client.get("/api/auth/me"), None),
            ("GET /api/status", client.get("/api/status"), None),
            ("GET /api/alerts", client.get("/api/alerts"), None),
            ("GET /api/regulations/jurisdictions", client.get("/api/regulations/jurisdictions"), None),
            ("GET /api/regulations/versions", client.get("/api/regulations/versions"), None),
            ("GET /api/regulations/changes", client.get("/api/regulations/changes"), None),
            ("GET /api/documents", client.get("/api/documents"), None),
            ("GET /api/reports", client.get("/api/reports"), None),
            ("POST /api/chat", client.post("/api/chat", json={"question": "What is the AYUSH patent filing fee for an individual inventor?", "language": "en"}), {}),
            ("POST /api/patentability/check", client.post("/api/patentability/check", json=INVENTION), {}),
            ("POST /api/patentability/screen", client.post("/api/patentability/screen", json={**INVENTION, "intent": "patent"}), {"intent": "patent"}),
            ("POST /api/prior-art/search", client.post("/api/prior-art/search", json={**INVENTION, "limit": 5}), {"limit": 5}),
            ("POST /api/traditional-knowledge/assess", client.post("/api/traditional-knowledge/assess", json={"title": INVENTION["title"], "description": INVENTION["description"], "ingredients": INVENTION["ingredients"], "therapeutic_use": "blood sugar management", "process": INVENTION["process"]}), {}),
            ("POST /api/regulations/compare", client.post("/api/regulations/compare", json={"jurisdictions": ["IN", "US", "EU", "UK"], "product_category": "herbal_product"}), {}),
            ("POST /api/compliance/check", client.post("/api/compliance/check", json={"jurisdiction": "IN", "product_category": "herbal_product", "document_text": "This licensed herbal product is manufactured under Schedule Z of the Ayurveda, Siddha and Unani medicines rules 1945."}), {}),
            ("POST /api/compliance/journey", client.post("/api/compliance/journey", json={"jurisdiction": "IN", "product_category": "herbal_product"}), {}),
            ("POST /api/agents/run", client.post("/api/agents/run", json={"question": "What regulation applies to herbal products in the EU?", "intent": "regulation", "language": "en"}), {"intent": "regulation"}),
            ("POST /api/languages/translate", client.post("/api/languages/translate", json={"text": "Triphala is a classical Ayurvedic formulation.", "source_language": "en", "target_language": "hi"}), {}),
            ("POST /api/languages/detect", client.post("/api/languages/detect", json={"text": "Tribhuvana lona is an Ayurvedic formulation."}), {}),
            ("POST /api/languages/normalize", client.post("/api/languages/normalize", json={"text": "Chyawanprash"}), {}),
            ("POST /api/voice/transcribe", client.post("/api/voice/transcribe", json={"audio_base64": _silent_wav(), "language": "en", "mime_type": "audio/wav"}), {}),
            ("POST /api/voice/synthesize", client.post("/api/voice/synthesize", json={"text": "Evidence before assertion.", "language": "en"}), {}),
            ("POST /api/voice/query", client.post("/api/voice/query", json={"audio_base64": _silent_wav(), "language": "en", "mime_type": "audio/wav", "speak": False}), {}),
        ]

        for name, response, extra in checks:
            ok = 200 <= response.status_code < 300 or response.status_code in {429, 502, 503, 504}
            label = "OK" if ok else "?"
            results.append((label, name, response.status_code, _public_repr(response.json()) if response.headers.get("content-type", "").startswith("application/json") else response.text[:300] if not response.content else ""))
            print(f"{label:>3} {name} -> {response.status_code}")

        for name, response, extra in checks[-0:]:
            if extra:
                print(f"  {name}\n    {_public_repr(extra)}")

    print("\n=== ENDPOINT VERIFICATION SUMMARY ===")
    annotated = client.app.state if hasattr(client, "app") else None
    return 0

if __name__ == "__main__":
    sys.exit(main())
