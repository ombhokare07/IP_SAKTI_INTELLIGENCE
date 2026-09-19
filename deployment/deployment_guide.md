# Deployment Guide

Use this guide after completing `AUTHENTICATION_SETUP.md`. No deployment credentials are bundled.

## Local production build

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:APP_ENV = "production"
$env:API_AUTH_REQUIRED = "true"
$env:API_AUTH_TOKEN = "<inject-with-your-secret-manager>"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL = "https://api.example.invalid"
npm run build
npm run start
```

`NEXT_PUBLIC_API_BASE_URL` is public browser configuration. Never place any provider key, OAuth secret, or backend bearer token in a `NEXT_PUBLIC_*` variable.

## Docker Compose

1. Copy `.env.example` to an untracked `.env`.
2. Set `APP_ENV=production`, `API_AUTH_REQUIRED=true`, a strong injected `API_AUTH_TOKEN`, allowed `CORS_ORIGINS`, and only the provider credentials you use.
3. Review the frontend `NEXT_PUBLIC_API_BASE_URL` build argument in `docker-compose.yml`; replace loopback for a non-local deployment.
4. Build and start:

   ```bash
   docker compose up --build -d
   docker compose ps
   ```

5. Check `GET /health` and authenticated `GET /api/status`.

The default backend image installs `requirements-offline.txt`. Set Docker build argument `INSTALL_FULL=true` when the deployment requires the full BGE/Chroma RAG stack. The compose file persists `data/runtime` and `chroma_db` in named volumes and binds service ports to loopback by default.

## Production checklist

- Terminate TLS at a trusted proxy/load balancer and expose only HTTPS.
- Restrict `CORS_ORIGINS` to the real frontend origins.
- Require the API bearer token and store all secrets in the platform's secret manager.
- Run the containers as the non-root users defined in the Dockerfiles.
- Back up the runtime SQLite/document volume and vector-store volume according to data-retention policy.
- Do not bake `.env`, source documents, runtime databases, or provider tokens into an image.
- Add network egress controls so the backend can contact only configured providers.
- Set request/body limits at the proxy consistent with the application's 10 MB document and 5 MB audio limits.
- Monitor provider authentication, timeout, rate-limit, and malformed-response errors without logging secrets or full sensitive payloads.
- Verify official source terms, TK authorization, EPO OPS quota/terms, and data-processing requirements before enabling live providers.

## Health and readiness

`GET /health` reports process liveness without contacting optional providers. `GET /api/status` reports configuration and sync state but deliberately labels configured gateways `configured_not_verified` until used. A successful health response is not proof that Gemini, EPO OPS, TK, regulation, translation, or voice providers are available.

## Updates and rollback

Build immutable images from the reviewed archive/commit, run backend and frontend test/build checks before rollout, back up persistent volumes, and retain the previous image tag for rollback. Regulatory version records and assessment/report snapshots should not be silently rewritten during deployment.

## Render template

`deployment/render.yaml` is a starting template only. Review its service URLs, secret injection, persistent storage, health checks, and region before use. Do not commit values entered in the deployment dashboard.
