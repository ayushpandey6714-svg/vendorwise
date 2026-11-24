"""Record reproducibility metadata without collecting credentials or user files."""
import hashlib
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    packages = ["fastapi", "uvicorn", "streamlit", "pydantic", "openai", "pypdf", "reportlab",
                "fastembed", "qdrant-client", "onnxruntime", "scikit-learn", "numpy", "pytest",
                "httpx", "python-multipart", "python-dotenv", "pypdfium2", "ty"]
    result = {"python":sys.version, "platform":platform.platform(),
              "packages":{name:importlib.metadata.version(name) for name in packages},
              "sample_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "samples").glob("*.pdf"))},
              "evaluation_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "evaluation").glob("*.json"))}}
    path = ROOT / "evaluation" / "results" / "environment.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
