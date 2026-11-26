from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from vendorwise.api import create_app
from vendorwise.config import ROOT, Settings
from vendorwise.errors import VendorWiseError
from vendorwise.provider import Provider
from vendorwise.usage import UsageBudget


def test_five_large_pdfs_are_accepted_together(client, requirements):
    aid = client.post("/analyses", json=requirements.model_dump(mode="json")).json()["analysis_id"]
    files = []
    # Real, readable PDFs with attachments: combined size exceeds the former 31 MiB cap.
    for i in range(5):
        writer = PdfWriter(clone_from=BytesIO((ROOT / "samples/vendor_c.pdf").read_bytes()))
        writer.add_attachment(f"padding-{i}.bin", b"x" * (8 * 1024 * 1024))
        stream = BytesIO()
        writer.write(stream)
        data = stream.getvalue()
        assert len(data) < 10 * 1024 * 1024
        files.append(("files", (f"quote-{i}.pdf", data, "application/pdf")))
    result = client.post(f"/analyses/{aid}/documents", files=files)
    assert result.status_code == 201, result.text
    assert len(result.json()) == 5
    extra = client.post(f"/analyses/{aid}/documents", files=files[:1])
    assert extra.status_code == 422 and "five" in extra.json()["detail"]
    assert len(client.app.state.service.load(aid).documents) == 5


def test_request_cap_checks_declared_and_streamed_sizes(settings):
    settings = replace(settings, max_upload_bytes=10)
    with TestClient(create_app(settings)) as client:
        cap = settings.max_request_bytes
        assert client.post("/analyses", content=b"", headers={"Content-Length": str(cap + 1)}).status_code == 413
        def chunks():
            yield b"x" * cap
            yield b"x"
        response = client.post("/analyses", content=chunks())
        assert response.status_code == 413


def test_live_storage_cap_and_existing_analysis(settings, requirements):
    with TestClient(create_app(replace(settings, mode="live", max_analyses=1))) as client:
        first = client.post("/analyses", json=requirements.model_dump(mode="json"))
        assert first.status_code == 201
        assert client.post("/analyses", json=requirements.model_dump(mode="json")).status_code == 503
        assert client.get(f"/analyses/{first.json()['analysis_id']}/quotes").status_code == 200


def test_rolling_limits_survive_restart_and_expire(settings, monkeypatch):
    settings = replace(settings, ai_requests_per_minute=1, ai_requests_per_day=2)
    now = [100000.0]
    monkeypatch.setattr("vendorwise.usage.time.time", lambda: now[0])
    UsageBudget(settings).reserve()
    with pytest.raises(VendorWiseError) as error:
        UsageBudget(settings).reserve()
    assert error.value.status_code == 429 and error.value.retry_after == 60
    now[0] += 60
    UsageBudget(settings).reserve()
    now[0] += 60
    with pytest.raises(VendorWiseError, match="24-hour"):
        UsageBudget(settings).reserve()
    now[0] = 100000 + 86400
    UsageBudget(settings).reserve()


def test_parallel_requests_cannot_overdraw_budget(settings):
    settings = replace(settings, ai_requests_per_minute=3)
    def reserve(_):
        try:
            UsageBudget(settings).reserve()
            return True
        except VendorWiseError as exc:
            assert exc.status_code == 429
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(reserve, range(12))) == 3


def test_failed_provider_call_is_charged_and_next_call_blocked(settings):
    provider = Provider(replace(settings, mode="live", api_key="test-key", ai_requests_per_day=1))
    calls = []
    def failing_request():
        calls.append(True)
        raise TimeoutError("simulated network failure")
    with pytest.raises(TimeoutError):
        provider.call(failing_request)
    with pytest.raises(VendorWiseError, match="24-hour"):
        provider.call(failing_request)
    assert len(calls) == 1
    assert provider.client.max_retries == 0


def test_limit_returns_retry_after_and_read_only_work_still_works(client, ready_analysis, monkeypatch):
    aid, _ = ready_analysis()
    service = client.app.state.service
    budget = UsageBudget(replace(service.settings, ai_requests_per_minute=1))
    budget.reserve()
    monkeypatch.setattr(service, "ask", lambda *args: budget.reserve())
    response = client.post(f"/analyses/{aid}/ask", json={"question": "Warranty?"})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert client.post(f"/analyses/{aid}/compare").status_code == 200
    assert client.get(f"/analyses/{aid}/report").status_code == 200
    assert client.post(f"/analyses/{aid}/what-if", json={"budget": "1200000", "min_warranty_months": 36, "max_delivery_days": 14}).status_code == 200


@pytest.mark.parametrize("name", ["VENDORWISE_AI_REQUESTS_PER_MINUTE", "VENDORWISE_AI_REQUESTS_PER_DAY", "VENDORWISE_MAX_ANALYSES"])
def test_zero_budget_is_rejected(name, monkeypatch, tmp_path):
    monkeypatch.setattr("vendorwise.config.load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("VENDORWISE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv(name, "0")
    with pytest.raises(ValueError, match=name):
        Settings.from_env()


def test_live_ui_keeps_uploads_and_disables_submit_without_key(settings, monkeypatch):
    from urllib.parse import urlsplit
    import httpx
    from streamlit.testing.v1 import AppTest
    with TestClient(create_app(replace(settings, mode="live"))) as client:
        def local_request(method, url, **kwargs):
            kwargs.pop("timeout", None)
            return client.request(method, urlsplit(url).path, **kwargs)
        monkeypatch.setattr(httpx, "request", local_request)
        ui = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        assert not ui.exception
        assert len(ui.file_uploader) == 1
        assert ui.button(key="create_analysis").disabled
        assert any("not configured" in warning.value for warning in ui.warning)


def test_extraction_repair_cannot_bypass_request_budget(settings, quote_factory):
    import httpx
    from openai import OpenAI
    from vendorwise.pdf import read_pdf
    quote = quote_factory()
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={"id": "mock", "object": "chat.completion", "created": 1,
            "model": "test", "choices": [{"index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": "{}"}}]})
    provider = Provider(replace(settings, mode="live", llm_provider="openrouter", api_key="test-key", ai_requests_per_day=1))
    provider._client = OpenAI(api_key="test-key", max_retries=0,
                             http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    doc = read_pdf((ROOT / "samples/vendor_c.pdf").read_bytes(), quote.filename, quote.document_id)
    with pytest.raises(VendorWiseError, match="24-hour"):
        provider.extract(doc)
    assert len(calls) == 1
