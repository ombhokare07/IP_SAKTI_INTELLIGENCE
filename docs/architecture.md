# Architecture

IP-SAKTI is a modular FastAPI and Next.js application. Cloud-backed services are optional adapters rather than startup dependencies.

## Runtime layers

1. `backend/` exposes validated HTTP routes, bearer-token enforcement, lifecycle management, and safe error responses.
2. `services/` owns application persistence, documents, reports, notifications, external JSON gateways, voice adapters, and the credential-independent service registry.
3. `rag/` preserves the original source-cited RAG, document ingestion, retrieval, generation, and citation pipeline.
4. `intelligence/` contains patentability, prior-art, TK, regulatory, compliance, and trust/evidence screening modules.
5. `agents/` classifies requests deterministically, delegates bounded analysis, and applies citation, evidence, and contradiction gates.
6. `multilingual/` and `voice/` provide English/Hindi/Marathi detection, normalization, translation, and speech pipeline interfaces.
7. `frontend/` is the 13-page Next.js dashboard and consumes the `/api` routes through one validated client.

SQLite persists document metadata, immutable assessment snapshots, report records, regulation versions, and alerts under `APP_DATA_DIR`. Uploaded files are stored under the same runtime root. Chroma remains the optional Phase-1 vector store. Runtime databases and user documents are excluded from the final archive.

## Startup behavior

`backend.main.create_app()` always creates the API. During lifespan startup, `Services` initializes local persistence and each independent provider in a guarded mode. Missing Gemini, EPO OPS, TK, regulation, translation, STT, or TTS credentials do not abort startup. `GET /api/status` reports their state.

The RAG and patentability runtime is initialized only when Gemini is configured. Prior-art configuration is handled independently so EPO OPS can be used without requiring Gemini. Provider construction or request failures fail closed and never become successful evidence.

## Evidence flow

A request is validated, routed to a bounded service/agent, and returns structured evidence with identifiers, excerpts, locators or URLs, mode, and retrieval metadata. Citation validation rejects unsupported references. Evidence scoring measures traceability and coverage. Contradictions lower trust and force a review state. Mock evidence has zero real-world trust and cannot support a definitive conclusion.

## Security boundaries

- Every `/api/*` route shares optional bearer-token enforcement; production always requires a configured token.
- External gateway endpoints require HTTPS except loopback development and reject embedded URL credentials and fragments.
- Provider secrets remain backend-only `SecretStr` settings.
- Responses expose controlled error codes/messages, not provider bodies, credentials, or stack traces.
- HTTP fixture clients are injected in tests, and the test suite disables unexpected outbound network access.

See `AUTHENTICATION_SETUP.md`, `docs/api_documentation.md`, and `docs/rag_design.md` for operational details.
