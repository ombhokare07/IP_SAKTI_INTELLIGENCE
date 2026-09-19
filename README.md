# IP-SAKTI Intelligence

IP-SAKTI Intelligence is an evidence-first screening workspace for Ayurveda-related intellectual-property and regulatory research. The project extends the original Trustworthy RAG, patentability pre-screening, and prior-art intelligence implementation with provider-ready patent search, traditional-knowledge risk screening, deterministic agent orchestration, global regulatory comparison, multilingual/voice interfaces, reports, and a 13-page Next.js dashboard.

It is a decision-support system, not a legal opinion service.

## Safety rules

- **No evidence -> no definitive conclusion.**
- **No real prior-art search -> no final novelty claim.**
- **No authorized traditional-knowledge search -> no TK clearance.**
- Mock and synthetic records are labelled as test data and never represented as live search results.
- Scores measure screening quality, evidence coverage, and grounding quality. They are not measures of legal correctness or patent-grant probability.

## Implemented phases

- Phase 1: trustworthy RAG with source/page citations, evidence sufficiency, contradiction checks, trust scoring, PDF ingestion, and Chroma integration.
- Phase 2A: patentability pre-screening with invention analysis, evidence gaps, novelty/inventive-step screening, exclusions, and readiness scoring.
- Phase 2B/2C: prior-art query building, ranking, feature matching, caching, reports, provider contracts, EPO OPS OAuth adapter, generic HTTP adapter, and explicit offline fixtures.
- Phase 3: ingredient, therapeutic-use, and process extraction; TK similarity and risk scoring; evidence-backed assessment; authorized/local/gateway/mock provider modes.
- Phase 4: deterministic intent routing and patent, AYUSH, international, prior-art, TK, evidence, citation, contradiction, compliance, regulation, translation, and report agents.
- Phase 5: India, USA, EU, and UK regulation comparison architecture; version tracking, diffs, impact analysis, compliance requirements, missing fields, screening score, change feeds, and compliance journeys.
- Phase 6: English, Hindi, and Marathi language detection, translation gateways, AYUSH terminology normalization, and offline-safe speech-to-text/text-to-speech interfaces.
- Phase 7: responsive Next.js dashboard with all 13 requested pages, API integration, source cards, citations, trust/evidence/risk displays, reports, and loading/error/empty states.

## Prerequisites

- Python 3.11 or 3.12
- Node.js 22 or 24 LTS with npm
- PowerShell for the commands below (bash equivalents are also provided)

The application starts without optional cloud credentials. Provider-backed features report `unconfigured` or a controlled unavailable response until configured. Startup also initializes a missing Chroma directory safely and reports Gemini, embedding-model, vector-store, indexed-document, vector-count, and RAG-readiness status without exposing credentials.

## Backend setup (Windows PowerShell)

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn backend.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive OpenAPI documentation is at `http://127.0.0.1:8000/docs`.

## Backend setup (macOS/Linux)

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn backend.main:app --reload
```

`requirements.txt` installs the complete RAG stack. `requirements-offline.txt` provides a reproducible pinned environment for API, fixture, and automated-test workflows.

The Windows-tested dependency set pins Pydantic and its surrounding FastAPI stack. Pydantic itself selects the exact compatible `pydantic-core` native wheel for the active CPython version; no platform-specific wheel filename is stored in this repository.

## Frontend setup

Open a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

On macOS/Linux, replace the copy command with `cp .env.example .env.local`. The dashboard is available at `http://127.0.0.1:3000`.

## Production build commands

Backend:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Set `APP_ENV=production` and a strong `API_AUTH_TOKEN` before starting a production instance.

Frontend:

```powershell
cd frontend
npm install
npm run build
npm run start
```

For repeatable setup, `python scripts/setup.py --mode offline` creates local environment files from templates, installs dependencies, builds the frontend, and runs tests. Add `--demo` only when explicitly opting into clearly labelled synthetic fixtures.

## Automated verification

Use a fresh writable pytest temporary directory when the host's default temp directory has restrictive permissions:

```powershell
New-Item -ItemType Directory -Force .pytest_tmp\final | Out-Null
python -m pytest -q --basetemp=.pytest_tmp\final
cd frontend
npm test
npm run typecheck
npm run build
```

The finalized baseline contains 243 passing backend tests, including all 97 tests from the supplied base project, plus 7 passing frontend protocol tests. The frontend has no separate `lint` script; `next build` performs its configured validity checks and `npm run typecheck` runs TypeScript directly.

## Provider modes

All live providers are optional and configured only with environment variables. See [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md) and [.env.example](.env.example).

- Gemini powers the configured RAG answer generator.
- EPO OPS or an operator-controlled HTTP gateway provides real prior-art search.
- Traditional-knowledge sources can be an explicitly authorized local corpus or operator gateway. This repository does **not** include or claim TKDL access.
- Regulatory sources can be an operator-provided local corpus or gateway.
- Translation, speech-to-text, and text-to-speech use separately configured gateways.
- Mock providers require explicit opt-in, are disabled in production, and mark outputs as synthetic/test data.

Provider status is available at `GET /api/status`.

## RAG knowledge-base lifecycle

The source package deliberately excludes `chroma_db/`. On first startup, the backend creates an empty local collection if the configured path does not exist. An empty collection does not crash startup and does not load the embedding model merely to answer a request: when Gemini is configured, `POST /api/chat` returns HTTP 503 with `Knowledge base is empty. Please ingest documents first.` When Gemini is not configured, it returns the existing credential-specific unavailable response. In both cases, `GET /api/status` reports each component separately.

The official AYUSH examination PDF is included at `data/raw/india/patents/ayush_patent_guidelines_2025.pdf`. A clean checkout must build its local vector data reproducibly:

```powershell
python -m scripts.test_pdf_processing
python -m scripts.ingest_documents
python -m scripts.verify_vector_store
python -m scripts.test_retrieval
```

Re-ingestion is required after every clean extraction because runtime Chroma data is intentionally not packaged. The first embedding run may download the configured `BAAI/bge-base-en-v1.5` model; it does not download or invent knowledge documents.

## API and project documentation

- [API documentation](docs/api_documentation.md)
- [Architecture](docs/architecture.md)
- [Agent design](docs/agent_design.md)
- [RAG and evidence design](docs/rag_design.md)
- [Dataset/source policy](docs/dataset_sources.md)
- [Deployment guide](deployment/deployment_guide.md)
- [Verification record](docs/VERIFICATION.md)
- [Original base-project README](docs/ORIGINAL_README.md)

## Known limitations

- Live provider credentials and authorization are not bundled; configured status is not proof of access until a request succeeds.
- EPO OPS coverage and availability depend on the account and the upstream service. A real search is required for a substantive novelty review.
- No TKDL connector or content is included. TK clearance requires an independently authorized search and qualified professional review.
- Regulatory fixtures are illustrative and cannot substitute for current official texts. Live regulation gateways must preserve authority URLs, jurisdiction, effective dates, versions, and retrieval timestamps.
- Offline translation is limited to deterministic AYUSH terminology normalization and safe pass-through behavior; offline voice input/output is unavailable.
- RAG quality depends on documents ingested into the local vector collection. An empty collection yields no definitive answer.
- Reports are screening artifacts and should be reviewed by qualified patent and regulatory professionals.

## Data and secret handling

Never commit `.env`, bearer tokens, OAuth secrets, provider keys, generated runtime databases, or user documents. Only placeholder templates such as `.env.example` belong in source control. The packaging script excludes credentials, caches, dependency directories, runtime databases, and temporary test data:

```powershell
python scripts/package_project.py ..\IP-SAKTI-Intelligence-FINAL.zip
```
