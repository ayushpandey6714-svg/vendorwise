# OpenRouter setup

Keep your API key in the backend's local `.env` file. Do not paste it into chat, screenshots, frontend inputs, or GitHub.

Create a key at https://openrouter.ai/settings/keys. In the project folder, copy `.env.example` to `.env` only if `.env` does not already exist. Set these entries once:

```dotenv
VENDORWISE_MODE=live
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=openrouter/free
VENDORWISE_PUBLIC_DEMO=false
EMBEDDING_BACKEND=tfidf
```

Replace the key placeholder locally. This selects the free-model router; no paid model fallback is configured. The router selects models based on request capabilities, so outputs can vary between requests. Availability and quotas can block calls. A fixed model supporting tools and structured output is better for repeatable evaluations; check its pricing before changing `OPENROUTER_MODEL`. Source: [OpenRouter free router](https://openrouter.ai/openrouter/free), checked 24 November 2026.

The integration uses the existing OpenAI SDK against `https://openrouter.ai/api/v1/chat/completions`. Requests require providers to support the supplied parameters; extracted data, provenance, tool arguments and citations are validated locally. Provider errors do not substitute fixture responses. See [structured output documentation](https://openrouter.ai/docs/guides/features/structured-outputs).

If dependencies are not installed, run `python -m venv .venv`, then `.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt` from the project directory. Python 3.14 was used for recorded tests.

Start the backend in one PowerShell window:

```powershell
cd D:\VendorWise\vendorwise
$env:VENDORWISE_MODE = 'live'
$env:LLM_PROVIDER = 'openrouter'
$env:VENDORWISE_PUBLIC_DEMO = 'false'
$env:EMBEDDING_BACKEND = 'tfidf'
.\.venv\Scripts\python.exe -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000
```

Start the UI in a second window:

```powershell
cd D:\VendorWise\vendorwise
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501. Keep both windows open. Restart the backend after changing `.env`; existing shell environment variables take precedence. Create a new analysis in live mode, select the three synthetic PDFs, extract, inspect evidence and compare. Ask about Vendor B's battery terms and inspect citations. Change delivery from 10 to 14 days and inspect the recommendation. Live mode sends document text to OpenRouter and the routed provider; use synthetic samples for the first checks.

## Completion checks still required

- Completed locally on synthetic samples: real API extraction, cited battery answer, comparison, what-if and report. This is not a general accuracy measurement.
- Docker image build/run; Docker was not installed during earlier checks.
- Public hosting and a verified public URL. Existing Docker/Render configuration serves only a fixture sample demo; it does not expose unrestricted live API access. Public live AI needs access and quota controls.

Automated mocked tests are not proof of live model quality. A key alone does not make the app deployed or production-ready.
