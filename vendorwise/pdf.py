"""PDF parsing and mechanical provenance checks; these do not prove interpretation."""
import hashlib
import io
import re
from pypdf import PdfReader

from .errors import VendorWiseError
from .schemas import Document, Quote


def normalized(text: str) -> str:
    return " ".join(text.split())


def safe_filename(name: str) -> str:
    # Display name only: storage always uses a server-generated UUID.
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"[^\w .()-]", "_", name)[:150] or "quotation.pdf"


def read_pdf(data: bytes, filename: str, document_id: str, max_pages: int = 20) -> Document:
    if not filename.lower().endswith(".pdf") or not data.startswith(b"%PDF-"):
        raise VendorWiseError("Only text-based PDF quotation files are supported.")
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise VendorWiseError("Encrypted PDFs are unsupported. Upload an unlocked text-based PDF.")
        if not 1 <= len(reader.pages) <= max_pages:
            raise VendorWiseError(f"PDF must have 1-{max_pages} pages.")
        pages = []
        for number, page in enumerate(reader.pages, 1):
            content = page.get_contents()
            if content is not None and len(content.get_data()) > 5_000_000:
                raise VendorWiseError(f"Page {number} is too complex to process locally.")
            text = (page.extract_text() or "").strip()
            if len(text) < 20:
                raise VendorWiseError(f"Page {number} has insufficient readable text. Scans/OCR and empty pages are unsupported.")
            if len(text) > 30_000:
                raise VendorWiseError(f"Page {number} exceeds the 30,000-character extraction limit.")
            pages.append(text)
        if sum(map(len, pages)) > 120_000:
            raise VendorWiseError("Document exceeds the 120,000-character analysis limit.")
    except VendorWiseError:
        raise
    except Exception as exc:
        raise VendorWiseError("Unreadable or malformed PDF. Export a valid text-based PDF and try again.") from exc
    return Document(document_id=document_id, filename=safe_filename(filename),
                    sha256=hashlib.sha256(data).hexdigest(), pages=pages)


def validate_provenance(quote: Quote, doc: Document) -> Quote:
    if quote.document_id != doc.document_id or quote.filename != doc.filename:
        raise VendorWiseError("Extraction returned an inconsistent document identity.", 502)
    count = 0
    for name in Quote.model_fields:
        fact = getattr(quote, name)
        if not hasattr(fact, "evidence"):
            continue
        for evidence in fact.evidence:
            if not normalized(evidence.text):
                raise VendorWiseError(f"Empty supporting text for {name}.", 502)
            if not 1 <= evidence.page <= len(doc.pages):
                raise VendorWiseError(f"Invalid source page for {name}.", 502)
            if normalized(evidence.text) not in normalized(doc.pages[evidence.page - 1]):
                raise VendorWiseError(f"Supporting text for {name} does not exist on its cited page.", 502)
            if evidence.document_id not in ("", doc.document_id) or evidence.filename not in ("", doc.filename):
                raise VendorWiseError(f"Invalid source document for {name}.", 502)
            evidence.document_id, evidence.filename = doc.document_id, doc.filename
            count += 1
    if not count or not any(getattr(quote, n).value for n in ("vendor", "manufacturer", "model")):
        raise VendorWiseError("No usable laptop quotation details were extracted.", 422)
    if quote.currency.value != "INR":
        raise VendorWiseError("Currency must be explicitly INR; missing or other currencies are unsupported.")
    return quote
