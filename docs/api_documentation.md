# API Reference

The FastAPI service defaults to `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `/docs`, and the machine-readable schema is at `/openapi.json`.

Every `/api/*` route is protected when `API_AUTH_REQUIRED=true` or `APP_ENV=production`:

```http
Authorization: Bearer <application-token>
Content-Type: application/json
```

`/` and `/health` remain minimal process/health endpoints. Provider configuration is reported separately by `/api/status`.

## Routes

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Application name, version, and running status. |
| `GET` | `/health` | Credential-independent liveness check. |
| `GET` | `/api/status` | Provider, authentication, sync, document, report, and configuration status. |
| `POST` | `/api/chat` | Run the configured source-grounded RAG pipeline. Returns `503` when RAG is unavailable. |
| `POST` | `/api/patentability/check` | Run the original configured patentability pre-screen. |
| `POST` | `/api/patentability/screen` | Run the extended pre-screen, with an evidence-safe fallback when the full RAG runtime is unavailable. |
| `POST` | `/api/prior-art/search` | Search the configured EPO OPS, gateway, or explicit test-fixture provider. |
| `POST` | `/api/traditional-knowledge/assess` | Extract product features and assess TK similarity/risk against configured evidence. |
| `GET` | `/api/regulations/jurisdictions` | List the India, USA, EU, and UK architecture descriptors. |
| `POST` | `/api/regulations/compare` | Compare requirements for selected jurisdictions/product fields. |
| `POST` | `/api/regulations/sync` | Import versions from the configured regulation provider. |
| `GET` | `/api/regulations/versions` | Return stored versions for the active provider mode. |
| `GET` | `/api/regulations/changes` | Return tracked regulatory changes. |
| `POST` | `/api/regulations/diff` | Diff two stored versions and analyze supplied-field impacts. |
| `POST` | `/api/compliance/check` | Extract requirements, detect missing fields, and return an evidence-grounded screening score. |
| `POST` | `/api/compliance/journey` | Generate an ordered compliance journey from the same evidence base. |
| `POST` | `/api/agents/run` | Classify/rout a question, run bounded agents, and apply citation/evidence/contradiction gates. |
| `POST` | `/api/languages/detect` | Detect English, Hindi, Marathi, or undetermined input. |
| `POST` | `/api/languages/normalize` | Normalize AYUSH terminology without changing citations. |
| `POST` | `/api/languages/translate` | Translate using dictionaries or the configured gateway; otherwise retain original text. |
| `POST` | `/api/voice/transcribe` | Transcribe base64 audio through the configured STT gateway. |
| `POST` | `/api/voice/synthesize` | Synthesize speech through the configured TTS gateway. |
| `POST` | `/api/voice/query` | Transcribe, orchestrate, and optionally synthesize one bounded request. |
| `GET`, `POST` | `/api/documents` | List or upload PDF/TXT/MD documents. Upload content is base64 encoded. |
| `GET` | `/api/documents/{id}` | Retrieve stored document metadata. |
| `GET` | `/api/documents/{id}/file` | Download the immutable stored file. |
| `POST` | `/api/documents/{id}/ingest` | Ingest a stored PDF into the preserved Phase-1 vector pipeline. |
| `GET`, `POST` | `/api/reports` | List reports or create a report from a saved/new screening. |
| `GET` | `/api/reports/{id}` | Retrieve a report record. |
| `GET` | `/api/reports/{id}/export?format=json|markdown|html` | Export a report in a safe supported format. |
| `GET` | `/api/alerts` | List generated regulation alerts. |
| `POST` | `/api/alerts/{id}/acknowledge` | Acknowledge an alert. |

## Core request examples

RAG:

```json
{"question": "What evidence supports this requirement?"}
```

Patentability/prior art:

```json
{
  "title": "Example formulation",
  "abstract": "A described formulation and manufacturing process.",
  "claims": ["A formulation comprising ..."],
  "jurisdictions": ["IN"],
  "limit": 10
}
```

Traditional knowledge:

```json
{
  "product_name": "Example product",
  "description": "A topical preparation containing turmeric for wound care.",
  "ingredients": ["turmeric"],
  "therapeutic_uses": ["wound care"],
  "processes": ["aqueous extraction"]
}
```

Regulation/compliance:

```json
{
  "product_name": "Example product",
  "product_type": "ayurvedic medicinal product",
  "jurisdictions": ["IN", "US", "EU", "UK"],
  "fields": {"ingredients": ["turmeric"], "intended_use": "wound care"}
}
```

Agent orchestration:

```json
{
  "question": "Compare regulatory requirements in India and the EU",
  "language": "en",
  "intent": "international"
}
```

Refer to `/docs` for the authoritative generated field constraints and response schemas.

## Status and evidence semantics

- `mode=live` means a configured provider returned a validated response; it does not mean a legal conclusion is correct.
- `mode=local` identifies operator-supplied local sources.
- `mode=mock` identifies explicitly enabled synthetic fixtures.
- `mode=unconfigured` means no evidence source was available.
- `configured_not_verified` means configuration exists but no successful request has established connectivity.
- `insufficient_evidence`, unavailable responses, and zero trust scores are expected safety outcomes.

Provider failures use controlled `401`, `422`, `429`, `502`, `503`, or `504` responses as applicable. Raw provider response bodies and secrets are not forwarded.
