# Deployment

## Public live app on Render

The existing app is linked from the repository README. Keep its GitHub source on `main` and enable deployment after CI checks pass when that option is available.

The `render.yaml` blueprint describes a single Docker service. For an existing manually created service, confirm these settings in its dashboard:

| Variable | Value |
|---|---|
| `PORT` | `7860` |
| `VENDORWISE_MODE` | `live` |
| `VENDORWISE_PUBLIC_DEMO` | `false` |
| `LLM_PROVIDER` | `openrouter` |
| `OPENROUTER_MODEL` | `openrouter/free` |
| `OPENROUTER_API_KEY` | Your private key, stored only as a service secret |
| `EMBEDDING_BACKEND` | `tfidf` |
| `VENDORWISE_AI_REQUESTS_PER_MINUTE` | `20` |
| `VENDORWISE_AI_REQUESTS_PER_DAY` | `100` |
| `VENDORWISE_MAX_ANALYSES` | `50` |

The last three limits have these defaults in code, so existing services receive them without new environment variables. They must be positive integers. The quota is shared across visitors, and each Q&A may use several requests. The app keeps FastAPI on `127.0.0.1:8000`; publish only the Streamlit port.

Use `/_stcore/health` as the hosting health path. A healthy page does not prove the AI provider is available. After deployment, select the synthetic sample checkbox, create an analysis, inspect the comparison, change delivery from 10 to 14 days, ask about Vendor B's battery terms, and download the report. Free provider availability can cause quota or structured-output errors; live mode never substitutes canned fixture answers.

## Sample-only mode

Set `VENDORWISE_MODE=fixture` and `VENDORWISE_PUBLIC_DEMO=true` for an offline demonstration. The uploader is hidden, sample hashes are checked before parsing, and no AI requests are made. `docker compose up --build -d` uses this mode locally at `http://localhost:7860`.

## Data and limits

PDFs, extracted data and indexes are stored under `VENDORWISE_DATA_DIR` (`/app/data` in Docker). Treat storage as temporary unless you explicitly attach persistent storage. Analyses and quota counters can disappear when an ephemeral service is replaced; download reports promptly.

`usage.sqlite3` contains only outbound-request timestamps, never keys or document text. Preserve it when clearing old analysis folders if you need the rolling budget to survive. Once the analysis cap is reached, existing analyses remain readable but new ones return HTTP 503. Review and delete expired UUID analysis folders while the backend is stopped, or use fresh temporary storage when appropriate. There is no automatic retention job.

The app uses one backend worker and one instance. The shared request budget limits API use but is not authentication, a token budget, or a guarantee against overload. This portfolio deployment is not intended for confidential procurement documents.
