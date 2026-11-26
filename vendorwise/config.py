"""Configuration is read at startup; keys are never sent to the frontend."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    mode: str = "live"
    embedding_backend: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    api_key: str = ""
    model: str = "gpt-4.1-mini"
    base_url: str = "https://api.openai.com/v1"
    llm_provider: str = "openai"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_pages: int = 20
    timeout_seconds: float = 45.0
    max_tool_calls: int = 4
    public_demo: bool = False
    max_demo_analyses: int = 200
    max_analyses: int = 50
    max_documents: int = 5
    ai_requests_per_minute: int = 20
    ai_requests_per_day: int = 100

    @property
    def max_request_bytes(self):
        # Allow every advertised file plus bounded multipart framing overhead.
        return self.max_documents * self.max_upload_bytes + 1024 * 1024

    @classmethod
    def from_env(cls):
        load_dotenv(ROOT / ".env", override=False)
        mode = os.getenv("VENDORWISE_MODE", "live")
        backend = os.getenv("EMBEDDING_BACKEND", "fastembed")
        provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if provider not in ("openai", "gemini", "openrouter"):
            raise ValueError("LLM_PROVIDER must be openai, gemini or openrouter")
        defaults = {
            "openai": ("gpt-4.1-mini", os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")),
            "gemini": ("gemini-3.5-flash-lite", "https://generativelanguage.googleapis.com/v1beta/openai/"),
            "openrouter": ("openrouter/free", "https://openrouter.ai/api/v1"),
        }
        default_model, base_url = defaults[provider]
        public_demo = os.getenv("VENDORWISE_PUBLIC_DEMO", "false").lower() == "true"
        if public_demo and mode != "fixture":
            raise ValueError("Public sample demo must use fixture mode. Use public_demo=false for live uploads.")
        if mode not in ("live", "fixture") or backend not in ("fastembed", "tfidf"):
            raise ValueError("VENDORWISE_MODE must be live/fixture; EMBEDDING_BACKEND must be fastembed/tfidf")
        return cls(data_dir=Path(os.getenv("VENDORWISE_DATA_DIR", str(ROOT / "data"))).resolve(),
                   mode=mode, embedding_backend=backend,
                   embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"),
                   llm_provider=provider,
                   api_key=os.getenv(provider.upper() + "_API_KEY", "").strip(),
                   model=os.getenv(provider.upper() + "_MODEL", default_model),
                   base_url=base_url,
                   public_demo=public_demo,
                   max_analyses=positive_env("VENDORWISE_MAX_ANALYSES", 50),
                   ai_requests_per_minute=positive_env("VENDORWISE_AI_REQUESTS_PER_MINUTE", 20),
                   ai_requests_per_day=positive_env("VENDORWISE_AI_REQUESTS_PER_DAY", 100))


def positive_env(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return value
