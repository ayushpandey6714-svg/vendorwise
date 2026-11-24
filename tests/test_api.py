from io import BytesIO
from uuid import uuid4

import pytest
from pypdf import PdfWriter

from vendorwise.config import ROOT
from vendorwise.errors import VendorWiseError
from vendorwise.pdf import read_pdf, validate_provenance

pytestmark = pytest.mark.integration


def test_api_full_flow_and_report(client, ready_analysis):
    aid, quotes = ready_analysis()
    prefix = f"/analyses/{aid}"
    assert client.get("/health").json()["mode"] == "fixture"
    assert len(client.get(prefix + "/quotes").json()) == 3
    before = client.post(prefix + "/compare").json()
    assert before["recommendation_ids"] == [quotes[2]["document_id"]]
    result = client.post(prefix + "/what-if", json={"budget": "1200000", "min_warranty_months": 36, "max_delivery_days": 14})
    assert result.status_code == 200, result.text
    assert result.json()["savings"] == "30000.00"
    report = client.get(prefix + "/report")
    assert "Vendor B" in report.text and "PDF page 2" in report.text
    assert "SYNTHETIC" in report.text


def test_whatif_and_reextract_do_not_call_provider(client, ready_analysis, monkeypatch):
    aid, original = ready_analysis()
    def forbidden(*args):
        raise AssertionError("Unexpected LLM/extraction call")
    monkeypatch.setattr(client.app.state.service.provider, "extract", forbidden)
    assert client.post(f"/analyses/{aid}/extract").json() == original
    assert client.post(f"/analyses/{aid}/what-if", json={"budget":"1200000", "min_warranty_months":36,"max_delivery_days":14}).status_code == 200


def test_isolation_and_vendor_filters(client, ready_analysis):
    first, a_quotes = ready_analysis(("vendor_a",))
    second, b_quotes = ready_analysis(("vendor_b",))
    foreign = client.post(f"/analyses/{first}/ask", json={"question":"Warranty?", "document_ids":[b_quotes[0]["document_id"]]})
    assert foreign.status_code == 422
    answer = client.post(f"/analyses/{second}/ask", json={"question":"Does Vendor B include battery replacement?"})
    assert answer.status_code == 200, answer.text
    assert answer.json()["citations"]
    assert all(c["document_id"] == b_quotes[0]["document_id"] and c["page"] == 2 for c in answer.json()["citations"])
    absent = client.post(f"/analyses/{first}/ask", json={"question":"Does Vendor B include battery replacement?"})
    assert absent.json()["evidence_absent"]


def test_missing_battery_is_not_exclusion(client, ready_analysis):
    aid, _ = ready_analysis(("missing_battery",))
    result = client.post(f"/analyses/{aid}/ask", json={"question":"Does Vendor B include battery replacement?"}).json()
    assert result["evidence_absent"] and "not covered" in result["answer"]


def test_invalid_inputs_and_status_codes(client, requirements):
    raw = requirements.model_dump(mode="json")
    assert client.post("/analyses", json={**raw, "quantity":0}).status_code == 422
    assert client.post("/analyses", json={**raw, "budget":"NaN"}).status_code == 422
    assert client.post("/analyses", json={**raw, "unexpected":"value"}).status_code == 422
    assert client.get("/analyses/not-a-uuid/quotes").status_code == 422
    assert client.get(f"/analyses/{uuid4()}/quotes").status_code == 404
    aid = client.post("/analyses", json=raw).json()["analysis_id"]
    assert client.post(f"/analyses/{aid}/extract").status_code == 409
    assert client.post(f"/analyses/{aid}/compare").status_code == 409
    assert client.post(f"/analyses/{aid}/ask", json={"question":""}).status_code == 422


def test_safe_upload_duplicate_limits_and_transaction(client, requirements):
    aid = client.post("/analyses", json=requirements.model_dump(mode="json")).json()["analysis_id"]
    path = f"/analyses/{aid}/documents"
    pdf = (ROOT / "samples" / "vendor_a.pdf").read_bytes()
    response = client.post(path, files=[("files", ("../../evil.pdf", pdf, "application/pdf"))])
    assert response.status_code == 201
    assert response.json()[0]["filename"] == "evil.pdf"
    stored = list(client.app.state.service.repo.folder(aid).glob("*.pdf"))
    assert len(stored) == 1 and stored[0].name != "evil.pdf"
    assert client.post(path, files=[("files", ("a.pdf", pdf))]).status_code == 422
    assert client.post(path, files=[("files", ("a.pdf", pdf))] * 4).status_code == 422
    assert client.post(path, files=[("files", ("a.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024)))]).status_code == 413
    # Validation of every file precedes writes: a bad second PDF leaves no new documents.
    b = (ROOT / "samples" / "vendor_b.pdf").read_bytes()
    assert client.post(path, files=[("files", ("b.pdf", b)), ("files", ("bad.pdf", b"broken"))]).status_code == 422
    assert len(client.app.state.service.repo.get(aid).documents) == 1


def test_unsupported_unreadable_and_encrypted_pdf():
    for name, data in [("bad.pdf", b"broken"), ("bad.txt", b"%PDF-"), ("bad.pdf", b"%PDF-broken")]:
        with pytest.raises(VendorWiseError):
            read_pdf(data, name, str(uuid4()))
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(VendorWiseError, match="insufficient readable text"):
        read_pdf(stream.getvalue(), "scan.pdf", str(uuid4()))
    writer.encrypt("secret")
    stream = BytesIO()
    writer.write(stream)
    with pytest.raises(VendorWiseError, match="Encrypted"):
        read_pdf(stream.getvalue(), "locked.pdf", str(uuid4()))


def test_provenance_rejects_fake_page_and_passage(quote_factory):
    q = quote_factory()
    doc = read_pdf((ROOT / "samples" / "vendor_c.pdf").read_bytes(), q.filename, q.document_id)
    q.warranty_months.evidence[0].page = 99
    with pytest.raises(VendorWiseError, match="Invalid source page"):
        validate_provenance(q, doc)
    q.warranty_months.evidence[0].page = 2
    q.warranty_months.evidence[0].text = "Made up lifetime warranty"
    with pytest.raises(VendorWiseError, match="does not exist"):
        validate_provenance(q, doc)


def test_fixture_mode_rejects_unknown_document(client, requirements):
    aid = client.post("/analyses", json=requirements.model_dump(mode="json")).json()["analysis_id"]
    # Even equivalent-looking bytes outside the exact manifest are not silently treated as fixtures.
    data = (ROOT / "samples" / "vendor_c.pdf").read_bytes() + b"\n% changed\n"
    assert client.post(f"/analyses/{aid}/documents", files=[("files", ("changed.pdf", data))]).status_code == 201
    assert client.post(f"/analyses/{aid}/extract").status_code == 422
