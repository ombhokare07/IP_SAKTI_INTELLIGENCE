# Authentication and Provider Setup

No real credentials are included in this repository. Copy `.env.example` to `.env`, enter only credentials issued to you, keep `.env` out of source control, and restart the backend after changing environment variables.

The backend starts without any optional provider. `GET /api/status` distinguishes `unconfigured`, mock, authorization-required, and configured-but-not-yet-verified states. A provider is not considered operational until an actual request succeeds.

## Credential matrix

| Provider | Environment variables | Required? | Feature | Behavior when absent |
| --- | --- | --- | --- | --- |
| Gemini | `GEMINI_API_KEY`; optional `GEMINI_MODEL` | Optional | Source-grounded `/api/chat` generation and the configured RAG-backed patentability runtime | The application starts; RAG reports `unconfigured`; `/api/chat` returns a controlled `503` unless a test/runtime pipeline was explicitly injected. No answer is fabricated. |
| EPO Open Patent Services | `PRIOR_ART_PROVIDER=epo_ops`, `EPO_OPS_CONSUMER_KEY`, `EPO_OPS_CONSUMER_SECRET`; optional `PRIOR_ART_TIMEOUT`, `PRIOR_ART_CACHE_TTL` | Optional | Live EPO OPS prior-art search | The application starts; prior art reports `unconfigured`; the API returns an unavailable/insufficient-evidence screening result rather than a final novelty claim. |
| Operator prior-art gateway | `PRIOR_ART_PROVIDER=http_json`, `PRIOR_ART_API_URL`, `PRIOR_ART_API_KEY`; optional `PRIOR_ART_TIMEOUT`, `PRIOR_ART_CACHE_TTL` | Optional alternative | Prior-art search through an operator-managed JSON service | The application starts and no live search occurs. Configured status does not verify that the gateway is reachable or authoritative. |
| Authorized TK local corpus | `TK_PROVIDER=local`, `TK_CORPUS_PATH`, `TK_SEARCH_AUTHORIZED=true` | Optional | Evidence-backed traditional-knowledge screening using a corpus the operator is legally authorized to use | The application starts. Without both an authorized provider and evidence, no TK clearance is produced. |
| Authorized TK gateway | `TK_PROVIDER=http_json`, `TK_API_URL`, `TK_API_KEY`, `TK_SEARCH_AUTHORIZED=true` | Optional alternative | Traditional-knowledge search through an operator-managed gateway | The application starts; status is `authorization_required` or `unconfigured`; no TK clearance is produced. This is not a TKDL credential or TKDL integration. |
| Regulation local corpus | `REGULATION_PROVIDER=local`, `REGULATION_CORPUS_PATH` | Optional | Regulation comparison, versions, changes, impacts, and compliance screening based on an operator-supplied corpus | The application starts. Without evidence, legal compliance remains undetermined. |
| Regulation gateway | `REGULATION_PROVIDER=http_json`, `REGULATION_API_URL`, `REGULATION_API_KEY` | Optional alternative | India/USA/EU/UK regulatory intelligence through an operator-managed gateway | The application starts; live comparison/sync remains unavailable. Configured status is not proof of successful retrieval. |
| Translation gateway | `TRANSLATION_PROVIDER=http_json`, `TRANSLATION_API_URL`, `TRANSLATION_API_KEY` | Optional | Machine translation beyond the bundled English/Hindi/Marathi terminology dictionary | Original text is retained with `translation_unavailable`; no translation is invented. |
| Speech-to-text gateway | `STT_PROVIDER=http_json`, `STT_API_URL`, `STT_API_KEY` | Optional | Voice transcription | Returns `unconfigured` with no transcript; typed input remains available. |
| Text-to-speech gateway | `TTS_PROVIDER=http_json`, `TTS_API_URL`, `TTS_API_KEY` | Optional | Voice synthesis | Returns `unconfigured` with no audio; text remains available. |
| IP-SAKTI API bearer token | `API_AUTH_REQUIRED`, `API_AUTH_TOKEN`; `APP_ENV` controls production enforcement | Optional in local development; mandatory in production | Protects every `/api/*` route | In development with authentication disabled, local requests continue. If required but the token is empty, routes return `503`; a missing or incorrect bearer token returns `401`. |

## Gemini

1. Create or obtain a Gemini API key under your own Google account and usage policy.
2. Set `GEMINI_API_KEY` in `.env`.
3. Optionally change `GEMINI_MODEL`.
4. Restart the backend and make a real `/api/chat` request against an indexed local knowledge base.

Official setup documentation: [Google AI Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key).

Do not expose the key in frontend environment variables, browser storage, logs, screenshots, or reports.

## EPO OPS OAuth

1. Register for EPO Open Patent Services and obtain a consumer key and consumer secret from EPO.
2. Set:

   ```dotenv
   PRIOR_ART_PROVIDER=epo_ops
   EPO_OPS_CONSUMER_KEY=
   EPO_OPS_CONSUMER_SECRET=
   ```

3. Restart the backend and issue a prior-art search.

The adapter performs OAuth client-credentials token acquisition, keeps the token in memory, renews it when needed, validates responses, and fails closed on authentication, rate-limit, network, or parsing errors. The token is never written to the repository. See the [EPO developer portal](https://developers.epo.org/) for account terms, quotas, and current service documentation.

## Operator gateway contract

Prior-art, TK, regulation, translation, speech-to-text, and text-to-speech HTTP providers are **operator-managed gateway contracts**. They are not claims that any public authority exposes the same JSON interface. Each gateway URL must be HTTPS outside explicitly allowed loopback development, and the backend sends its corresponding key as a bearer token.

Use a different least-privilege key for each service. The gateway must preserve genuine source identifiers and metadata. Regulatory evidence should include the authority, jurisdiction, effective/version dates, retrieval time, and an actual source URL. TK evidence must come only from sources the operator is authorized to search.

## API bearer-token authentication

For local development, authentication defaults to disabled:

```dotenv
APP_ENV=development
API_AUTH_REQUIRED=false
API_AUTH_TOKEN=
```

For production:

```dotenv
APP_ENV=production
API_AUTH_REQUIRED=true
API_AUTH_TOKEN=
```

Generate a strong random token outside the repository and inject it through the deployment platform's secret manager. Never reuse a provider key as the application token. Production mode enforces bearer authentication even if `API_AUTH_REQUIRED=false` was accidentally supplied.

Clients send:

```http
Authorization: Bearer <application-token>
```

The frontend Settings page can retain this **application** token in `sessionStorage` for the current browser tab. Provider credentials must never be entered into the frontend.

## Explicit offline/demo fixtures

Offline fixtures require deliberate opt-in and are disabled in production:

```dotenv
APP_ENV=development
ALLOW_MOCK_DATA=true
PRIOR_ART_PROVIDER=mock
PRIOR_ART_ALLOW_MOCK=true
TK_PROVIDER=mock
REGULATION_PROVIDER=mock
```

These fixtures are synthetic test data. Responses remain labelled `mock`, `synthetic`, or `TEST DATA`; they cannot support a final novelty conclusion, TK clearance, or legal-compliance conclusion.

## Rotation and incident response

- Revoke and replace any key that appears in a shell transcript, log, source file, browser bundle, or report.
- Restart the backend after rotation so in-memory OAuth and gateway clients use new credentials.
- Keep production secrets in the deployment platform's secret store, not Docker images or checked-in compose files.
- Restrict gateway permissions and network access to only the required operations.
