<div align="center">

# 🧾 VendorWise

### **AI-Powered Quotation Auditor & Multi-Vendor Comparison System**

A portfolio application that audits INR laptop quotations, checks buyer requirements, and answers document questions with source citations. Python calculates totals from validated extracted inputs; AI interpretations still require review.

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-vendorwise.onrender.com-00D4A0?style=for-the-badge)](https://vendorwise.onrender.com)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-181717?style=for-the-badge&logo=github)](https://github.com/ayushpandey6714-svg/vendorwise)

<br/>

[![Python 3.14 tested](https://img.shields.io/badge/Python-3.14_tested-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.165-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Qdrant](https://img.shields.io/badge/Vector_DB-Qdrant-DC244C?style=flat)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Tests and Docker](https://github.com/ayushpandey6714-svg/vendorwise/actions/workflows/docker-check.yml/badge.svg)](https://github.com/ayushpandey6714-svg/vendorwise/actions/workflows/docker-check.yml)

</div>

---

## 🌟 Overview

When procurement teams buy hardware or services, comparing multiple vendor PDF quotes is tedious, error-prone, and slow. Hidden charges, misleading tax structures, mathematical discrepancies, and warranty caveats often slip past human review.

**VendorWise** automates this end-to-end:
1. **Upload up to 5 quotation PDFs** together, or select the three built-in synthetic quotations. Live mode calls the AI provider even for sample PDFs; fixture mode uses predefined sample extractions.
2. **Deterministic Arithmetic Audit**: Uses Python's `Decimal` arithmetic to check totals. Incorrectly interpreted source inputs can still produce incorrect conclusions; review the evidence.
3. **Requirement Compliance Engine**: Checks strict constraints (Budget, RAM, SSD, Warranty, Delivery) returning structured `PASS`, `FAIL`, or `UNKNOWN` verdicts with exact citations.
4. **Interactive "What-If" Matrix**: Change delivery deadlines or budget sliders to see which vendor becomes the new optimal winner in real time.
5. **RAG-Powered Document Q&A**: Asks questions across all proposals (e.g., *"Is battery replacement covered under warranty?"*) with exact page-level citations.

---

## ⚡ Live Deployment

Experience VendorWise live in your browser:

👉 **[https://vendorwise.onrender.com](https://vendorwise.onrender.com)** 👈

### Try the sample workflow

1. Select **Use the 3 synthetic sample PDFs (Vendors A, B and C)** and keep the default requirements.
2. Click **Create analysis and extract** once. Live extraction can take several minutes; keep the page open while it runs.
3. Expect **Vendor C**: Vendor A fails the warranty requirement and Vendor B fails the delivery deadline.
4. Open **What if?**, change maximum delivery from **10 to 14 days**, and apply. Expect **Vendor B** and **INR 30,000 savings**.
5. Ask **Does Vendor B include battery replacement?** in Document Q&A. Inspect the page-2 evidence: manufacturing defects are covered for 12 months.
6. Return to Comparison, prepare the Markdown report, and download it.

These expectations apply to the supplied synthetic samples. Review extracted facts and citations before using an answer to make a decision.

| Mode | Documents | AI calls | Typical use |
|---|---|---|---|
| Live | Your supported quotations or the samples | Yes; provider key required | Demonstrating real extraction and generated answers |
| Fixture | Exact supplied sample PDFs | None | Repeatable local demonstration and regression tests |

One observed public live run took about **123 seconds** for three-PDF extraction/comparison, **2.5 seconds** for what-if, and **7 seconds** for Q&A. These are single-run observations, not a performance guarantee. Extraction is sequential and concurrent analyses share a backend lock. Provider response times and hosting startup can add delays. See [validation evidence](docs/VALIDATION.md).

---

## 🎯 Key Features

| Capability | Technical Detail |
|---|---|
| 📑 **Multi-PDF Intake** | Ingests up to 5 vendor PDFs (10 MiB, 20 pages max per document) |
| 🧮 **Deterministic arithmetic** | Stated totals vs calculated sums checked via Python `Decimal` (`ROUND_HALF_UP` to ₹0.01) |
| 🔍 **RAG retrieval** | Local Qdrant with either TF-IDF lexical vectors or BGE semantic embeddings; the two are not fused into hybrid search |
| 🤖 **Multi-LLM support** | OpenRouter and Gemini use Chat Completions; OpenAI uses the Responses API |
| 🛠️ **Bounded Tool-Calling** | Assistant restricted to 3 server-controlled tools (`search_documents`, `calculate_quote_total`, `compare_vendors`) |
| 🌙 **Dark UI** | Streamlit frontend with comparison tables and source evidence |
| 📊 **Audit Export** | Export a downloadable, audit-ready Markdown report complete with source evidence passages |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([👤 User / Buyer]) <--> UI[🖥️ Streamlit Frontend - Dark Theme]
    UI <-->|REST API / JSON| API[⚡ FastAPI Backend Service]
    
    subgraph Data Processing Pipeline
        API --> PDF[📄 PDF Parser - pypdf]
        PDF --> Chunks[✂️ Page-Preserving Text Chunks]
        Chunks --> Embeddings[🔢 Embeddings: TF-IDF / BGE Local]
        Embeddings --> Qdrant[(🗄️ Qdrant Vector Store)]
    end

    subgraph Core Intelligence
        API --> LLM[🤖 LLM Engine: OpenRouter / Gemini / OpenAI]
        LLM <--> Tools[🛠️ Bounded Assistant Tools]
        Tools --> Qdrant
        Tools --> Engine[🧮 Pure Decimal Audit Engine - logic.py]
    end

    Engine --> Results[📊 Comparison Matrix & PASS/FAIL Verdicts]
    Results --> UI
```

---

## 🛠️ Tech Stack

| Layer | Technologies Used |
|---|---|
| **AI & RAG Pipeline** | **RAG** (Page-Preserving Chunking), **Tool-Calling Agent**, OpenRouter / Google Gemini / OpenAI |
| **Embeddings & Vector DB** | **Qdrant** Vector Database, **FastEmbed (`BAAI/bge-small-en-v1.5`)**, **TF-IDF (`scikit-learn`)** |
| **Backend & Validation** | **FastAPI**, **Uvicorn**, **Pydantic v2**, Python `Decimal`, `pypdf` |
| **Frontend UI** | **Streamlit** (Custom Dark Theme), `httpx` |
| **DevOps & Testing** | **Docker**, **Render Cloud**, **GitHub Actions CI**, **Pytest**, **ty** |

---

## 🚀 Quick Start Guide

### Option 1: Local development (Windows PowerShell, Python 3.14)

Use **Python 3.14** to reproduce the tested environment. Project metadata allows Python 3.12–3.14; the pinned dependencies require at least 3.12, and 3.12/3.13 have not been verified by this project's CI.

#### 1. Clone the repository
```bash
git clone https://github.com/ayushpandey6714-svg/vendorwise.git
cd vendorwise
```

#### 2. Create virtual environment & install dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt
```

#### 3. Run in Demo Mode (Zero API Keys Required)
**Terminal 1 — Start Backend:**
```powershell
$env:VENDORWISE_MODE = 'fixture'
$env:EMBEDDING_BACKEND = 'tfidf'
.\.venv\Scripts\python -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Start Frontend:**
```powershell
.\.venv\Scripts\python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open your browser at **[http://localhost:8501](http://localhost:8501)**.

Select the synthetic sample checkbox before submitting in fixture mode. Keep both terminals open. For live local setup, follow [OpenRouter setup](docs/OPENROUTER_SETUP.md); store your key in `.env`, never in GitHub.

---

### Option 2: Docker Deployment

Run both backend and frontend isolated in a single Docker container:

```bash
docker compose up --build -d
```
Access the application on **`http://localhost:7860`**.

Compose starts the sample-only fixture demo without an API key. The Render blueprint starts live mode; set `OPENROUTER_API_KEY` privately in Render's environment settings. See [deployment instructions](docs/DEPLOYMENT.md).

On Linux/macOS, virtual-environment commands use `.venv/bin/python` and environment variables use `export NAME=value`.

---

## 📡 API Reference

Interactive Swagger documentation is available locally at `http://127.0.0.1:8000/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Runtime status, provider setup, and embedding mode |
| `POST` | `/analyses` | Initialize a new isolated procurement analysis session |
| `POST` | `/analyses/{id}/documents` | Multipart upload for up to 5 PDF quotes |
| `POST` | `/analyses/{id}/extract` | Structured LLM / fixture quotation extraction |
| `GET` | `/analyses/{id}/quotes` | Retrieve extracted pricing and spec facts |
| `POST` | `/analyses/{id}/compare` | Deterministic compliance check & cost comparison |
| `POST` | `/analyses/{id}/what-if` | Dynamic constraint sensitivity & savings analysis |
| `POST` | `/analyses/{id}/ask` | Grounded question answering with validated citations |
| `GET` | `/analyses/{id}/report` | Generate downloadable Markdown audit report |

---

## 📂 Project Organization

```
vendorwise/
├── streamlit_app.py          # Modern Dark-themed Streamlit UI
├── vendorwise/               # Core application package
│   ├── api.py                # FastAPI HTTP routing & middleware
│   ├── schemas.py            # Pydantic data schemas & contracts
│   ├── logic.py              # Deterministic Decimal math & audit
│   ├── assistant.py          # Bounded AI agent with tool execution
│   ├── retrieval.py          # Chunking, vector indexing & Qdrant RAG
│   ├── pdf.py                # Text extraction from PDF documents
│   ├── provider.py           # Unified client for OpenAI / Gemini / OpenRouter
│   ├── service.py            # Workflow orchestration layer
│   ├── storage.py            # Persistent session & analysis repository
│   ├── usage.py              # Atomic shared AI request budgets in SQLite
│   ├── config.py             # Strongly-typed environment configuration
│   └── report.py             # Formatted Markdown report builder
├── samples/                  # Pre-generated synthetic PDF quotations (A, B, C)
├── tests/                    # Unit, API, UI and mocked-provider regression tests
├── evaluation/               # Accuracy benchmarks & held-out datasets
├── scripts/                  # Container supervisors and smoke test scripts
├── Dockerfile                # Single-stage container running as a non-root user
├── render.yaml               # Cloud deployment blueprint
└── requirements-lock.txt     # Reproducible dependency lockfile
```

---

## 🧪 Testing & Validation

CI runs the complete test suite and type checker before building the Linux image and exercising its sample workflow. Tests cover arithmetic, source validation, five-file uploads, shared usage limits, and provider contracts:

```powershell
.\.venv\Scripts\python -m pytest -v
```

Mocked provider tests and fixture results are not live AI accuracy measurements. The Docker smoke check uses synthetic samples and requires no key. See [validation records](docs/VALIDATION.md).

## Troubleshooting

| Symptom | What to do |
|---|---|
| Live AI is not configured | Set the selected provider's API key in the backend environment, then restart or redeploy. |
| Extraction takes several minutes | Wait for the current request; repeatedly creating analyses adds work. Try one PDF first. Use fixture mode for a repeatable demonstration without provider calls. |
| HTTP 429 | Read the error: the app's shared request budget or the provider's quota was reached. Wait for the applicable reset; comparisons and reports on completed analyses do not call the model. |
| HTTP 503 says analysis storage is full | Existing analyses remain available. The operator must clear expired analysis data as described in the deployment guide. |
| Scanned, encrypted, or malformed PDF rejected | Export an unlocked text-based PDF containing one INR laptop offer. OCR is not implemented. |
| Analysis disappears after hosting restart | Storage may be ephemeral. Start a new analysis and download reports you need to keep. |

## Understand the project

Read [the architecture guide](docs/ARCHITECTURE.md), then follow `streamlit_app.py` → `vendorwise/api.py` → `vendorwise/service.py`. Study `provider.py` and `schemas.py` for extraction, `logic.py` for arithmetic and comparison, and `retrieval.py` / `assistant.py` for document Q&A. Finish with `Dockerfile`, `scripts/serve_container.py`, and the CI workflow. The [demo script](docs/DEMO_SCRIPT.md) explains how to present the project accurately.

## Public demo limits

- Live mode accepts up to **five text-based PDFs**, **10 MiB and 20 pages each**, with a 51 MiB total HTTP request cap. One laptop offer per PDF; INR only. Scans/OCR and multiple configurations in one PDF are unsupported.
- All visitors share **20 AI requests per minute** and **100 per rolling 24 hours** by default. Each extraction attempt and Q&A model step counts, including failures. Automatic SDK retries are disabled. HTTP 429 includes `Retry-After`; comparisons, what-if and reports remain usable.
- Counters are stored in SQLite in the data directory. They survive process restarts while that directory remains available. A fresh deployment or ephemeral disk replacement resets them. These are request caps, not token or monetary budgets.
- Live storage is capped at **50 analyses**; the sample-only demo allows 200. Limits are operator-configurable. There is no automatic expiry or background deletion; the operator must remove expired analysis data when the cap is reached.
- This is an anonymous, single-instance portfolio demo, with no accounts or user authentication. The container exposes only Streamlit; keep FastAPI on loopback. Do not upload confidential data. Live document text goes to the selected AI provider.
- For confidential or production use, add authenticated ownership, durable storage, retention/deletion controls, and operational monitoring. Rate limits do not provide user isolation or prevent denial of service.

---

## 🛡️ Reliability & Security Principles

- **No Float Arithmetic**: All currencies use Python `Decimal` with explicit `ROUND_HALF_UP` to eliminate floating-point drift.
- **Strict Evidence Anchoring**: Quotation facts require supporting page numbers and exact excerpt snippets.
- **Server-Owned Execution**: Calculation tools take stored document IDs rather than model-supplied prices. Extracted facts still need human review.
- **Untrusted Input Treatment**: PDFs are treated as untrusted data inputs to prevent prompt injection from affecting comparison criteria.

---

## 👤 Author

**Ayush Pandey**
- GitHub: [@ayushpandey6714-svg](https://github.com/ayushpandey6714-svg)
- Project: [VendorWise](https://github.com/ayushpandey6714-svg/vendorwise)

---

<div align="center">
<sub>Built with precision for transparent, intelligent procurement.</sub>
</div>
