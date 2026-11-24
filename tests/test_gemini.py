"""Real SDK over mocked HTTP: these tests do not make live Gemini requests."""
import json
from dataclasses import replace

import httpx
import pytest
from openai import OpenAI

from vendorwise.assistant import ask
from vendorwise.config import ROOT, Settings
from vendorwise.errors import VendorWiseError
from vendorwise.pdf import read_pdf
from vendorwise.provider import Provider
from vendorwise.schemas import AnswerDraft, AskRequest, Extraction


def provider_for(settings, handler):
    settings = replace(settings, mode="live", llm_provider="gemini", api_key="test-key",
                       model="gemini-3.5-flash-lite",
                       base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    provider = Provider(settings)
    provider._client = OpenAI(api_key=settings.api_key, base_url=settings.base_url, max_retries=0,
                             http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return provider


def completion(message):
    return httpx.Response(200, json={"id": "chatcmpl_mock", "object": "chat.completion",
        "created": 1, "model": "gemini-3.5-flash-lite", "choices": [{"index": 0,
        "finish_reason": "tool_calls" if message.get("tool_calls") else "stop", "message": message}]})


def configure_env(monkeypatch, tmp_path):
    monkeypatch.setattr("vendorwise.config.load_dotenv", lambda *a, **k: None)
    for name in ("LLM_PROVIDER", "GEMINI_API_KEY", "GEMINI_MODEL", "OPENAI_API_KEY",
                 "OPENAI_BASE_URL", "VENDORWISE_PUBLIC_DEMO"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VENDORWISE_MODE", "live")
    monkeypatch.setenv("VENDORWISE_DATA_DIR", str(tmp_path))


def test_gemini_config_uses_only_google_key_and_endpoint(monkeypatch, tmp_path):
    configure_env(monkeypatch, tmp_path)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-other-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://other.invalid/v1")
    settings = Settings.from_env()
    assert settings.api_key == "test-google-key"
    assert settings.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert settings.model == "gemini-3.5-flash-lite"
    monkeypatch.delenv("GEMINI_API_KEY")
    with pytest.raises(VendorWiseError, match="GEMINI_API_KEY is not configured"):
        Provider(Settings.from_env()).client


def test_invalid_provider_and_live_public_demo_are_rejected(monkeypatch, tmp_path):
    configure_env(monkeypatch, tmp_path)
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        Settings.from_env()
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("VENDORWISE_PUBLIC_DEMO", "true")
    with pytest.raises(ValueError, match="fixture mode"):
        Settings.from_env()


@pytest.mark.mocked
def test_gemini_extraction_uses_chat_structured_output(settings, quote_factory):
    quote = quote_factory()
    seen = []
    def handler(request):
        assert request.url.host == "generativelanguage.googleapis.com"
        assert request.url.path == "/v1beta/openai/chat/completions"
        seen.append(json.loads(request.content))
        return completion({"role": "assistant", "content": Extraction(
            supported=True, reason="", quote=quote).model_dump_json()})
    provider = provider_for(settings, handler)
    doc = read_pdf((ROOT / "samples/vendor_c.pdf").read_bytes(), quote.filename, quote.document_id)
    result = provider.extract(doc)
    assert result.stated_total == quote.stated_total
    assert seen[0]["response_format"]["type"] == "json_schema"
    assert json.loads(seen[0]["messages"][1]["content"])["document_id"] == doc.document_id
    assert "store" not in seen[0]  # Responses-only options must not reach Gemini.


@pytest.mark.mocked
def test_gemini_bound_tools_and_preserve_signatures(client, ready_analysis):
    aid, quotes = ready_analysis()
    service = client.app.state.service
    analysis = service.ready(aid)
    analysis.mode = "live"
    seen = []
    def handler(request):
        body = json.loads(request.content)
        seen.append(body)
        if "response_format" in body:
            return completion({"role": "assistant", "content": AnswerDraft(
                answer="CALCULATION: see verified audit", citation_ids=[], evidence_absent=False,
                conflict=False).model_dump_json()})
        return completion({"role": "assistant", "content": None, "tool_calls": [{
            "id": f"call_{len(seen)}", "type": "function", "function": {
                "name": "calculate_quote_total", "arguments": json.dumps({"document_id": quotes[2]["document_id"]})},
            "extra_content": {"google": {"thought_signature": "test-signature"}}}]})
    provider = provider_for(service.settings, handler)
    result = ask(analysis, AskRequest(question="Audit Vendor C total"), service.index(analysis), provider)
    assert len(result.activity) == provider.settings.max_tool_calls
    assert len(seen) == provider.settings.max_tool_calls + 1
    assert str(result.calculations[0].calculated_total) == "1190000.00"
    assert seen[0]["tool_choice"] == "required"
    assistant = next(m for m in seen[-1]["messages"] if m["role"] == "assistant")
    assert assistant["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == "test-signature"
    assert len([m for m in seen[-1]["messages"] if m["role"] == "tool"]) == 4


@pytest.mark.mocked
@pytest.mark.parametrize("case", ["invalid_citation", "unknown_tool", "excess_calls"])
def test_gemini_rejects_untrusted_output(client, ready_analysis, case):
    aid, quotes = ready_analysis()
    service = client.app.state.service
    analysis = service.ready(aid)
    analysis.mode = "live"
    def handler(request):
        body = json.loads(request.content)
        if "response_format" in body:
            return completion({"role": "assistant", "content": AnswerDraft(
                answer="Unverified", citation_ids=["invented"] if case == "invalid_citation" else [],
                evidence_absent=case != "invalid_citation", conflict=False).model_dump_json()})
        name = "send_email" if case == "unknown_tool" else "calculate_quote_total"
        calls = [{"id": f"c{i}", "type": "function", "function": {"name": name,
                  "arguments": json.dumps({"document_id": quotes[2]["document_id"]})}}
                 for i in range(5 if case == "excess_calls" else 1)]
        return completion({"role": "assistant", "content": None, "tool_calls": calls})
    provider = provider_for(service.settings, handler)
    if case == "unknown_tool":
        result = ask(analysis, AskRequest(question="Audit"), service.index(analysis), provider)
        assert all(a.outcome.startswith("Rejected:") for a in result.activity)
        assert not result.calculations
    else:
        with pytest.raises(VendorWiseError, match="not retrieved" if case == "invalid_citation" else "limit reached"):
            ask(analysis, AskRequest(question="Audit"), service.index(analysis), provider)


@pytest.mark.mocked
@pytest.mark.parametrize("failure", ["quota", "invalid_json", "empty", "refusal"])
def test_gemini_extraction_failure_never_returns_fixtures(settings, quote_factory, failure):
    quote = quote_factory()
    def handler(request):
        if failure == "quota":
            return httpx.Response(429, json={"error": {"message": "Test quota", "type": "rate_limit"}})
        if failure == "empty":
            return httpx.Response(200, json={"id": "mock", "choices": []})
        return completion({"role": "assistant", "content": "invalid JSON" if failure == "invalid_json" else None,
                           "refusal": "Test refusal" if failure == "refusal" else None})
    provider = provider_for(settings, handler)
    doc = read_pdf((ROOT / "samples/vendor_c.pdf").read_bytes(), quote.filename, quote.document_id)
    with pytest.raises(VendorWiseError) as error:
        provider.extract(doc)
    assert error.value.status_code == (429 if failure == "quota" else 502)
