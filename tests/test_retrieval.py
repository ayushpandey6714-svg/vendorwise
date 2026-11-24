import pytest

from vendorwise.assistant import ToolRunner
from vendorwise.errors import VendorWiseError
from vendorwise.retrieval import chunk_documents


def test_chunks_preserve_pages_and_source_text(client, ready_analysis):
    aid, _ = ready_analysis()
    a = client.app.state.service.ready(aid)
    chunks = chunk_documents(a)
    for c in chunks:
        doc = next(d for d in a.documents if d.document_id == c.document_id)
        assert c.text in doc.pages[c.page - 1]
    assert {c.page for c in chunks} == {1, 2}
    assert len({c.citation_id for c in chunks}) == len(chunks)


def test_named_vendor_search_and_explicit_filter_cannot_expand(client, ready_analysis):
    aid, quotes = ready_analysis()
    service = client.app.state.service
    a = service.ready(aid)
    b_id = quotes[1]["document_id"]
    runner = ToolRunner(a, service.index(a), [b_id])
    chunks = runner.run("search_documents", {"query":"battery replacement", "document_ids":None})
    assert chunks and all(c["document_id"] == b_id for c in chunks)
    with pytest.raises(VendorWiseError, match="expand"):
        runner.run("search_documents", {"query":"battery", "document_ids":[quotes[0]["document_id"]]})
    chunks = service.index(a).search(a, "Which vendor offers onsite warranty?")
    assert {c.document_id for c in chunks} == {q["document_id"] for q in quotes}


def test_reopen_persisted_analysis_and_vectors(client, ready_analysis):
    from vendorwise.service import Service
    from vendorwise.schemas import AskRequest
    aid, _ = ready_analysis()
    restarted = Service(client.app.state.service.settings)
    answer = restarted.ask(aid, AskRequest(question="What exclusions are in Vendor C warranty?"))
    assert answer.citations and all(c.filename == "vendor_c.pdf" for c in answer.citations)
