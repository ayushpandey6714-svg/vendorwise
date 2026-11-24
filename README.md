# VendorWise 🧾

**AI-powered Quotation Auditor & Vendor Comparison Tool**

> Compare up to **3 vendor PDF quotations**, audit arithmetic, check requirements, ask questions with cited evidence — all in one clean web interface.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.165-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.67-red?logo=streamlit)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-ready-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🌐 Live Demo

> 🚀 **[Live Demo on Render →](https://vendorwise.onrender.com)** *(deploy karne ke baad yahan real link ayega)*

---

## ✨ What It Does

| Feature | Description |
|---|---|
| 📄 **PDF Extraction** | Pulls price, RAM, warranty, delivery, taxes from vendor PDFs |
| 🧮 **Arithmetic Audit** | Verifies stated totals using Python `Decimal` — catches rounding errors |
| ✅ **Requirement Check** | PASS / FAIL / UNKNOWN for budget, RAM, storage, warranty, delivery |
| 🔄 **What-If Analysis** | Change requirements → instantly see who qualifies, how much you save |
| 💬 **Cited Q&A** | Ask questions about documents — answers cite exact PDF pages |
| 📊 **Report Download** | Full Markdown audit report with evidence |

---

## 🖥️ Screenshots

```
[ Vendor A ]  PASS ✅  INR 10,80,000  Verified  ⭐ Recommended
[ Vendor B ]  FAIL ❌  INR 11,60,000  Verified  (warranty too short)
[ Vendor C ]  PASS ✅  INR 11,90,000  Verified
```

---

## 🏗️ Architecture

```
Browser (Streamlit UI)
        │  HTTP
        ▼
FastAPI Backend (port 8000)
   ├── PDF Parsing (pypdf)
   ├── LLM Extraction (Gemini / OpenAI / OpenRouter)
   ├── Deterministic Audit (Python Decimal — no AI)
   ├── RAG Search (Qdrant + TF-IDF / BGE embeddings)
   └── Bounded AI Assistant (3 tools, citation validation)
```

---

## 🚀 Quick Start (Local)

### 1. Clone & Setup

```powershell
git clone https://github.com/ayushpandey6714-svg/vendorwise.git
cd vendorwise
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-lock.txt
```

### 2. Run Demo (No API key needed)

**Terminal 1 — Backend:**
```powershell
$env:VENDORWISE_MODE = 'fixture'
$env:EMBEDDING_BACKEND = 'tfidf'
.\.venv\Scripts\python -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend:**
```powershell
.\.venv\Scripts\python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

**Open:** [http://localhost:8501](http://localhost:8501) → Select **"Use the three synthetic demo PDFs"** → **Create analysis and extract**

> API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🤖 Live AI Mode (Real LLM)

Edit `.env` (copy from `.env.example`):

```dotenv
VENDORWISE_MODE=live
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-2.0-flash-lite
EMBEDDING_BACKEND=fastembed
```

Supported providers: **Gemini** · **OpenAI** · **OpenRouter**

> ⚠️ Never commit your `.env` file or paste API keys in chat.

---

## 🐳 Docker (Local)

```powershell
docker compose up --build -d
```

Open [http://localhost:7860](http://localhost:7860)

---

## ☁️ Deploy to Render (Free)

1. Push this repo to your GitHub account
2. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Set:
   - **Runtime:** Docker
   - **Health Check Path:** `/_stcore/health`
   - **Environment Variable:** `PORT = 7860`
5. Click **Create Web Service** — done! 🎉

> Free tier sleeps when idle; first visit after sleep takes ~30 seconds to wake up.

---

## 📁 Project Structure

```
vendorwise/
├── streamlit_app.py          # UI (Streamlit frontend)
├── vendorwise/
│   ├── api.py                # REST API (FastAPI)
│   ├── schemas.py            # Data models (Pydantic)
│   ├── logic.py              # Deterministic audit & comparison
│   ├── assistant.py          # AI assistant with tool calling
│   ├── retrieval.py          # RAG search (Qdrant)
│   ├── pdf.py                # PDF text extraction
│   ├── provider.py           # LLM provider setup
│   ├── service.py            # Business logic coordinator
│   ├── storage.py            # Disk persistence
│   ├── config.py             # Settings from .env
│   └── report.py             # Markdown report generator
├── samples/                  # Synthetic demo PDFs (Vendor A/B/C)
├── tests/                    # Automated test suite (64 tests)
├── evaluation/               # Retrieval quality benchmarks
├── scripts/                  # Helper scripts
├── docs/                     # Architecture & setup docs
├── Dockerfile                # Production container
├── render.yaml               # Render deployment config
└── requirements-lock.txt     # Pinned dependencies
```

---

## 🔌 API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Runtime mode, embeddings, provider status |
| `POST` | `/analyses` | Create a new analysis session |
| `POST` | `/analyses/{id}/documents` | Upload 1–3 PDF quotations |
| `POST` | `/analyses/{id}/extract` | Extract facts from PDFs |
| `GET` | `/analyses/{id}/quotes` | Get extracted quote data |
| `POST` | `/analyses/{id}/compare` | Run deterministic comparison |
| `POST` | `/analyses/{id}/ask` | Ask a question (RAG + AI) |
| `POST` | `/analyses/{id}/what-if` | Change requirements & recompare |
| `GET` | `/analyses/{id}/report` | Download Markdown audit report |

---

## 🧪 Tests

```powershell
.\.venv\Scripts\python -m pytest -q
```

64 tests covering: arithmetic audit · requirement checks · RAG retrieval · API endpoints · public demo restrictions · provider contracts

---

## 📄 Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [OpenRouter Setup](docs/OPENROUTER_SETUP.md)
- [Validation Evidence](docs/VALIDATION.md)
- [Dependencies](docs/DEPENDENCIES.md)

---

## ⚠️ Limitations

- **INR only** — no multi-currency
- **Text PDFs only** — no OCR for scanned docs
- **1 laptop config per PDF** — no multi-product baskets
- **Local single-user** — no authentication or multi-user support
- **Demo data only** in Docker public mode — no personal PDF uploads

---

## 🛠️ Built With

- [FastAPI](https://fastapi.tiangolo.com) — Backend API
- [Streamlit](https://streamlit.io) — Frontend UI
- [Pydantic](https://docs.pydantic.dev) — Data validation
- [Qdrant](https://qdrant.tech) — Local vector search
- [pypdf](https://pypdf.readthedocs.io) — PDF parsing
- [FastEmbed](https://github.com/qdrant/fastembed) — Local embeddings (BGE)
- [OpenAI SDK](https://github.com/openai/openai-python) — LLM provider interface

---

## 👨‍💻 Author

**Ayush Pandey**
- GitHub: [@ayushpandey6714-svg](https://github.com/ayushpandey6714-svg)

---

*This is a portfolio/learning project. Inspect the evidence before relying on any AI interpretation.*
