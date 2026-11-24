"""Small JSON repository. Run one backend worker; use the service lock for transactions."""
from pathlib import Path
from threading import RLock
from uuid import UUID, uuid4

from .errors import VendorWiseError
from .schemas import Analysis, Requirements


class Repository:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()

    def folder(self, analysis_id: str | UUID) -> Path:
        try:
            safe_id = str(UUID(str(analysis_id)))
        except ValueError as exc:
            raise VendorWiseError("Invalid analysis ID.", 422) from exc
        return self.root / safe_id

    def create(self, requirements: Requirements, mode: str, backend: str) -> Analysis:
        a = Analysis.model_validate(dict(analysis_id=uuid4(), requirements=requirements, mode=mode, embedding_backend=backend))
        self.folder(a.analysis_id).mkdir()
        self.save(a)
        return a

    def get(self, analysis_id: str | UUID) -> Analysis:
        path = self.folder(analysis_id) / "analysis.json"
        if not path.exists():
            raise VendorWiseError("Analysis not found. Create a new analysis.", 404)
        return Analysis.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, analysis: Analysis):
        folder = self.folder(analysis.analysis_id)
        temp = folder / "analysis.tmp"
        temp.write_text(analysis.model_dump_json(indent=2), encoding="utf-8")
        temp.replace(folder / "analysis.json")
