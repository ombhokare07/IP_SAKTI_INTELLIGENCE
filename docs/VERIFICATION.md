# Final Verification Record

Date: 2026-09-07 (UTC)

Environment: Python 3.12.13, Node.js 24.19.0, npm 11.9.0.

## Backend

The complete suite was run with a newly created writable `--basetemp` directory:

- Passed: **243**
- Failed: **0**
- Errors: **0**
- Skipped: **0**
- Warnings: **2**
- Duration: 2.14 seconds

The warnings are dependency deprecations in the installed FastAPI/Starlette test stack: Starlette's current `httpx` TestClient compatibility path and the `anyio.abc.BlockingPortal` alias. They do not represent application test failures.

The exact 27 original test modules from the supplied ZIP were also run separately with a fresh writable temp directory:

- Passed: **97**
- Failed: **0**
- Errors: **0**
- Skipped: **0**
- Warnings: **2**
- Duration: 1.04 seconds

This confirms the original 97-test regression baseline remains intact.

## Frontend

`npm install --no-audit --no-fund`, `npm run build`, `npm run typecheck`, and `npm test` completed successfully.

- Next.js 15.5.24 production build: passed
- TypeScript typecheck: passed
- Frontend protocol tests: 7 passed, 0 failed, 0 skipped
- Separate lint script: not configured
- Next build's configured lint/type validity stage: passed

The production build generated all requested routes: Dashboard, Ask IP-SAKTI, Patentability Check, Prior-Art Intelligence, Traditional Knowledge Risk, Global Regulation Compare, Document Compliance, Regulation Changes, Compliance Journey, Knowledge Library, Regulatory Alerts, Reports, and Settings.

npm emitted one environment-level warning that the inherited `http-proxy` npm configuration will be unsupported in a future major npm version. It did not affect installation, build, typecheck, or tests.

## Credential-free startup

An actual Uvicorn process was started from a temporary working directory with Gemini, EPO OPS, TK, regulation, translation, STT, TTS, API-token, and mock configuration removed from the process environment.

- `GET /health`: 200
- `GET /api/status`: 200
- RAG, prior art, TK, regulations, translation, STT, and TTS: `unconfigured`
- Unconfigured `POST /api/chat`: controlled 503
- Startup result: passed

## Gemini

`GEMINI_API_KEY` was not configured in the verification environment, so no live Gemini call was attempted and no live-success claim is made. Fourteen focused RAG/API/LLM tests passed with injected offline clients/pipelines. The credential-free behavior was separately confirmed to leave the application running and `/api/chat` safely unavailable.

## Offline API verification

Sixty-seven focused integration tests passed for the API matrix, including health/status, chat, patentability, prior-art fixture search, TK assessment, regulation comparison/version/diff/change APIs, compliance checking, compliance journeys, deterministic orchestration, documents/ingestion, reports/exports, alerts, provider status, bearer authentication, production mock disabling, and graceful credential absence.

Tests use explicit injected/local fixtures and block unexpected external network access. Fixture prior-art identifiers are prefixed `TEST-FIXTURE-`; fixture modes and limitations remain visible.

## Evidence safety

The complete passing suite asserts:

- no evidence produces no definitive conclusion;
- no real prior-art search produces no final novelty claim;
- no authorized TK search produces no TK clearance;
- synthetic/mock evidence is labelled and has zero real-world trust;
- configured provider state is not represented as verified access;
- unsupported citations and conflicting evidence fail closed;
- screening/trust scores are never represented as legal correctness or patent-grant probability.

## Secret scan

The project source scan examined 323 text files outside dependency, build, cache, and runtime directories. It found zero high-confidence API-key/token/private-key signatures and zero non-empty sensitive assignments in `.env`, `.env.example`, `frontend/.env.local`, or `frontend/.env.example`. Environment files containing local defaults are excluded from packaging; only `.env.example` templates are retained.
