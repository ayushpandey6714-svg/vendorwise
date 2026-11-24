from types import SimpleNamespace
from uuid import uuid4

import pytest

from vendorwise.assistant import ToolRunner, ask
from vendorwise.errors import VendorWiseError
from vendorwise.retrieval import validate_citations
from vendorwise.schemas import AnswerDraft, AskRequest, Chunk


def test_citation_validation():
    c = Chunk(citation_id="valid", document_id="doc", filename="q.pdf", page=2, text="Warranty: 36 months")
    draft = AnswerDraft(answer="36 months", citation_ids=["fake"], evidence_absent=False, conflict=False)
    with pytest.raises(VendorWiseError, match="not retrieved"):
        validate_citations(draft, [c])
    draft.citation_ids = ["valid"]
    assert validate_citations(draft, [c]) == [c]
    draft.citation_ids = []
    with pytest.raises(VendorWiseError, match="lacks"):
        validate_citations(draft, [c])
    draft.evidence_absent = True
    assert validate_citations(draft, [c]) == []


def test_conflicts_need_multiple_citations():
    draft = AnswerDraft(answer="Conflicting", citation_ids=[], evidence_absent=True, conflict=True)
    with pytest.raises(VendorWiseError, match="two cited"):
        validate_citations(draft, [])


def test_tool_argument_validation_and_unknown_ids(client, ready_analysis):
    aid, quotes = ready_analysis()
    service = client.app.state.service
    a = service.ready(aid)
    runner = ToolRunner(a, service.index(a))
    with pytest.raises(VendorWiseError, match="Invalid arguments"):
        runner.run("calculate_quote_total", {"document_id": quotes[0]["document_id"], "unit_price":1})
    with pytest.raises(VendorWiseError, match="Unknown document"):
        runner.run("calculate_quote_total", {"document_id": str(uuid4())})
    with pytest.raises(VendorWiseError, match="Unknown assistant tool"):
        runner.run("send_email", {})
    with pytest.raises(VendorWiseError, match="Invalid arguments"):
        runner.run("compare_vendors", {"budget":1})
    result = runner.run("calculate_quote_total", {"document_id":quotes[0]["document_id"]})
    assert result["calculated_total"] == "1080000.00"
    assert runner.activity[-1].tool == "calculate_quote_total"


@pytest.mark.mocked
def test_real_sdk_structured_output_contract(settings, quote_factory):
    """Exercise SDK serialization/parsing over MockTransport, not a live model."""
    import httpx
    from openai import OpenAI
    from vendorwise.provider import Provider
    from vendorwise.schemas import Extraction
    from dataclasses import replace
    from vendorwise.pdf import read_pdf
    from vendorwise.config import ROOT
    q = quote_factory()
    seen = []
    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"id":"resp_mock", "object":"response", "created_at":1,
            "status":"completed", "model":"test", "output":[{"id":"msg_mock", "type":"message", "role":"assistant", "status":"completed",
            "content":[{"type":"output_text", "text":Extraction(supported=True, reason="", quote=q).model_dump_json(), "annotations":[]}]}]})
    provider = Provider(replace(settings, mode="live", api_key="test-key"))
    provider._client = OpenAI(api_key="test-key", http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    doc = read_pdf((ROOT / "samples" / "vendor_c.pdf").read_bytes(), q.filename, q.document_id)
    assert provider.extract(doc).stated_total.value == q.stated_total.value
    assert seen and b'json_schema' in seen[0].content


@pytest.mark.mocked
def test_bounded_loop_actual_tools_and_invalid_citation(client, ready_analysis):
    aid, quotes = ready_analysis()
    service = client.app.state.service
    a = service.ready(aid)
    a.mode = "live"
    calls = []
    class Responses:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(output=[SimpleNamespace(type="function_call", name="calculate_quote_total",
                arguments='{"document_id":"' + quotes[2]["document_id"] + '"}', call_id=f"c{len(calls)}")])
        def parse(self, **kwargs):
            return SimpleNamespace(output_parsed=AnswerDraft(answer="CALCULATION: see audit", citation_ids=[], evidence_absent=False, conflict=False))
    provider = SimpleNamespace(client=SimpleNamespace(responses=Responses()), settings=service.settings)
    result = ask(a, AskRequest(question="Audit Vendor C total"), service.index(a), provider)
    assert len(calls) == service.settings.max_tool_calls
    assert len(result.activity) == len(calls)
    assert all(x.tool == "calculate_quote_total" for x in result.activity)


def test_missing_credentials_never_falls_back(settings):
    from dataclasses import replace
    from vendorwise.provider import Provider
    with pytest.raises(VendorWiseError, match="not configured"):
        Provider(replace(settings, mode="live", api_key="")).client
