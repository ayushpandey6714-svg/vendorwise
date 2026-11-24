"""Actual per-analysis vector retrieval, with page-preserving chunks and filters."""
import json
import os
import re
from functools import lru_cache
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .config import ROOT

# Configure auxiliary download caches before Qdrant imports FastEmbed/Hugging Face.
# Keep every model artifact within operator-configured local storage, not the home directory.
_cache_root = Path(os.getenv("VENDORWISE_DATA_DIR", str(ROOT / "data"))) / "model_cache"
os.environ.setdefault("HF_HOME", str(_cache_root / "huggingface"))
os.environ.setdefault("HF_XET_CACHE", str(_cache_root / "xet"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

import numpy as np
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import TfidfVectorizer

from .errors import VendorWiseError
from .schemas import Analysis, AnswerDraft, Chunk


def chunk_documents(analysis: Analysis, size: int = 800, overlap: int = 120) -> list[Chunk]:
    chunks = []
    for doc in analysis.documents:
        for page, text in enumerate(doc.pages, 1):
            # Slice the original page so the displayed passage is always an exact source substring.
            for start in range(0, len(text), size - overlap):
                passage = text[start:start + size]
                if passage.strip():
                    chunks.append(Chunk(citation_id=f"{doc.document_id}:p{page}:c{start}",
                                        document_id=doc.document_id, filename=doc.filename,
                                        page=page, text=passage))
                if start + size >= len(text):
                    break
    return chunks


def named_document_ids(analysis: Analysis, query: str) -> set[str] | None:
    named = {q.document_id for q in analysis.quotes if q.vendor.value and
             re.search(r"(?<!\w)" + re.escape(q.vendor.value) + r"(?!\w)", query, re.IGNORECASE)}
    requested_names = set(re.findall(r"\bvendor\s+[a-z]\b", query.lower()))
    known_names = {q.vendor.value.lower() for q in analysis.quotes if q.vendor.value}
    if requested_names - known_names:
        return set()
    return named or None


@lru_cache(maxsize=2)
def embedding_model(name: str, cache_dir: str):
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=name, cache_dir=cache_dir, threads=2)


class VectorIndex:
    def __init__(self, folder: Path, backend: str, model: str, cache: Path):
        self.folder, self.backend, self.model, self.cache = folder, backend, model, cache

    def _embeddings(self, texts: list[str], query: bool = False):
        if self.backend == "fastembed":
            try:
                model = embedding_model(self.model, str(self.cache))
                return np.asarray(list(model.query_embed(texts) if query else model.passage_embed(texts)))
            except Exception as exc:
                raise VendorWiseError("Local embedding model could not load. Check network/model cache, or explicitly select EMBEDDING_BACKEND=tfidf and create a new analysis.", 503) from exc
        # Explicit lightweight lexical baseline for fully offline demos. Never labelled semantic.
        corpus = json.loads((self.folder / "chunks.json").read_text(encoding="utf-8"))
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b", max_features=6000)
        vectorizer.fit([c["text"] for c in corpus])
        return vectorizer.transform(texts).toarray().astype("float32")

    def build(self, analysis: Analysis):
        chunks = chunk_documents(analysis)
        if not chunks:
            raise VendorWiseError("No readable text to index.")
        self.folder.mkdir(parents=True, exist_ok=True)
        (self.folder / "chunks.json").write_text(json.dumps([c.model_dump() for c in chunks]), encoding="utf-8")
        vectors = self._embeddings([c.text for c in chunks])
        client = QdrantClient(path=str(self.folder / "vectors"))
        try:
            if client.collection_exists("passages"):
                client.delete_collection("passages")
            client.create_collection("passages", vectors_config=models.VectorParams(
                size=int(vectors.shape[1]), distance=models.Distance.COSINE))
            client.upsert("passages", points=[models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, c.citation_id)), vector=v.tolist(), payload=c.model_dump())
                for c, v in zip(chunks, vectors)])
        finally:
            client.close()
        (self.folder / "metadata.json").write_text(json.dumps({"backend": self.backend, "model": self.model}), encoding="utf-8")

    def search(self, analysis: Analysis, query: str, document_ids: list[str] | None = None, limit: int = 6):
        allowed = {d.document_id for d in analysis.documents}
        if document_ids is not None and (not document_ids or not set(document_ids) <= allowed):
            raise VendorWiseError("Unknown or empty document filter for this analysis.")
        named = named_document_ids(analysis, query)
        selected = set(document_ids) if document_ids is not None else allowed
        if named is not None:
            selected &= named
        # Do not answer a question about a missing synthetic vendor using another vendor's evidence.
        if not selected:
            return []
        metadata_path = self.folder / "metadata.json"
        if not metadata_path.exists():
            raise VendorWiseError("Extract quotations before asking document questions.", 409)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata != {"backend": self.backend, "model": self.model}:
            raise VendorWiseError("Embedding configuration changed. Create a new analysis to rebuild its index.", 409)
        vector = self._embeddings([query], query=True)[0]
        if not np.any(vector):
            return []
        client = QdrantClient(path=str(self.folder / "vectors"))
        try:
            # Balanced per-document search prevents one vendor crowding all others out of a comparison.
            per_doc = max(1, limit // len(selected))
            results = []
            for doc_id in sorted(selected):
                hits = client.query_points("passages", query=vector.tolist(), limit=per_doc,
                    query_filter=models.Filter(must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=doc_id))]),
                    score_threshold=0.01).points
                results.extend(Chunk.model_validate(h.payload) for h in hits)
            return results
        finally:
            client.close()


def validate_citations(draft: AnswerDraft, retrieved: list[Chunk], has_calculations: bool = False) -> list[Chunk]:
    by_id = {c.citation_id: c for c in retrieved}
    if any(cid not in by_id for cid in draft.citation_ids):
        raise VendorWiseError("Model returned a citation that was not retrieved. Answer withheld.", 502)
    if not draft.evidence_absent and not draft.citation_ids and not has_calculations:
        raise VendorWiseError("Answer lacks source citations. Answer withheld.", 502)
    if draft.conflict and len(set(draft.citation_ids)) < 2:
        raise VendorWiseError("A conflict needs at least two cited passages.", 502)
    return [by_id[cid] for cid in dict.fromkeys(draft.citation_ids)]
