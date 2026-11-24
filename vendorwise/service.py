"""Application layer: transactions, file isolation and orchestration."""
from uuid import uuid4
import hashlib
import json

from .config import ROOT

from .assistant import ask
from .errors import VendorWiseError
from .logic import compare, what_if
from .pdf import read_pdf
from .provider import Provider
from .retrieval import VectorIndex
from .storage import Repository


class Service:
    def __init__(self, settings):
        if settings.public_demo and settings.mode != "fixture":
            raise VendorWiseError("Public sample demo requires fixture mode.", 503)
        self.settings = settings
        self.repo = Repository(settings.data_dir)
        self.provider = Provider(settings)

    def load(self, analysis_id):
        a = self.repo.get(analysis_id)
        if a.mode != self.settings.mode or a.embedding_backend != self.settings.embedding_backend:
            raise VendorWiseError("This analysis used a different runtime mode. Restore that configuration or create a new analysis.", 409)
        return a

    def index(self, a):
        return VectorIndex(self.repo.folder(a.analysis_id) / "index", a.embedding_backend,
                           self.settings.embedding_model, self.settings.data_dir / "model_cache")

    def upload(self, analysis_id, uploads):
        with self.repo.lock:
            a = self.load(analysis_id)
            if not uploads or len(a.documents) + len(uploads) > 3:
                raise VendorWiseError("Upload between one and three PDFs per analysis.")
            staged = []
            hashes = {d.sha256 for d in a.documents}
            for filename, data in uploads:
                if len(data) > self.settings.max_upload_bytes:
                    raise VendorWiseError("Each PDF must be 10 MiB or smaller.", 413)
                if self.settings.public_demo:
                    manifest = json.loads((ROOT / "samples" / "fixture_manifest.json").read_text(encoding="utf-8"))
                    if hashlib.sha256(data).hexdigest() not in manifest:
                        raise VendorWiseError("This public demo accepts only the supplied synthetic PDFs. Personal quotation uploads are disabled.")
                doc = read_pdf(data, filename, str(uuid4()), self.settings.max_pages)
                if doc.sha256 in hashes:
                    raise VendorWiseError("Duplicate PDF in this analysis.")
                hashes.add(doc.sha256)
                staged.append((doc, data))
            for doc, data in staged:
                (self.repo.folder(a.analysis_id) / f"{doc.document_id}.pdf").write_bytes(data)
                a.documents.append(doc)
            a.quotes = []  # Never compare outdated quotes after another upload.
            self.repo.save(a)
            return a.documents

    def extract(self, analysis_id):
        with self.repo.lock:
            a = self.load(analysis_id)
            if not a.documents:
                raise VendorWiseError("Upload at least one PDF before extraction.", 409)
            if a.quotes:
                return a.quotes
            quotes = [self.provider.extract(d) for d in a.documents]
            a.quotes = quotes
            self.index(a).build(a)
            self.repo.save(a)
            return quotes

    def ready(self, analysis_id):
        a = self.load(analysis_id)
        if not a.quotes:
            raise VendorWiseError("Extract the uploaded quotations first.", 409)
        return a

    def compare(self, analysis_id):
        a = self.ready(analysis_id)
        return compare(a.quotes, a.requirements)

    def what_if(self, analysis_id, change):
        with self.repo.lock:
            a = self.ready(analysis_id)
            result = what_if(a.quotes, a.requirements, change)
            a.requirements = result.updated.requirements
            self.repo.save(a)
            return result

    def ask(self, analysis_id, request):
        with self.repo.lock:
            a = self.ready(analysis_id)
            return ask(a, request, self.index(a), self.provider)
