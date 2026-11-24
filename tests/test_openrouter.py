"""Mocked HTTP contracts, not live OpenRouter quality checks."""
from dataclasses import replace
import json
import httpx
from openai import OpenAI
import pytest
from vendorwise.config import ROOT, Settings
from vendorwise.provider import Provider
from vendorwise.pdf import read_pdf
from vendorwise.assistant import ask
from vendorwise.schemas import Extraction, AnswerDraft, AskRequest
from vendorwise.errors import VendorWiseError


def test_openrouter_config(monkeypatch, tmp_path):
    monkeypatch.setattr('vendorwise.config.load_dotenv', lambda *a, **k: None)
    monkeypatch.setenv('LLM_PROVIDER', 'openrouter')
    monkeypatch.setenv('VENDORWISE_MODE', 'live')
    monkeypatch.setenv('VENDORWISE_PUBLIC_DEMO', 'false')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'test-router-key')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-other-key')
    monkeypatch.setenv('OPENAI_BASE_URL', 'https://other.invalid')
    monkeypatch.delenv('OPENROUTER_MODEL', raising=False)
    monkeypatch.setenv('VENDORWISE_DATA_DIR', str(tmp_path))
    config = Settings.from_env()
    assert config.api_key == 'test-router-key'
    assert config.model == 'openrouter/free'
    assert config.base_url == 'https://openrouter.ai/api/v1'
    monkeypatch.delenv('OPENROUTER_API_KEY')
    with pytest.raises(VendorWiseError, match='OPENROUTER_API_KEY is not configured'):
        Provider(Settings.from_env()).client


def make_provider(settings, handler):
    settings = replace(settings, llm_provider='openrouter', mode='live',
                       api_key='test-key', model='openrouter/free', base_url='https://openrouter.ai/api/v1')
    provider = Provider(settings)
    provider._client = OpenAI(api_key='test-key', base_url=settings.base_url, max_retries=0,
                             http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    return provider


def response(message):
    return httpx.Response(200, json={'id': 'test', 'object': 'chat.completion', 'created': 1,
        'model': 'test-free-model', 'choices': [{'index': 0, 'message': message,
        'finish_reason': 'tool_calls' if message.get('tool_calls') else 'stop'}]})


@pytest.mark.mocked
def test_openrouter_extraction_and_bounded_assistant(client, ready_analysis, quote_factory):
    aid, _ = ready_analysis()
    service = client.app.state.service
    analysis = service.ready(aid)
    analysis.mode = 'live'
    quote = quote_factory()
    seen = []
    def handler(request):
        assert str(request.url) == 'https://openrouter.ai/api/v1/chat/completions'
        body = json.loads(request.content)
        seen.append(body)
        assert body['provider']['require_parameters'] is True
        assert body['model'] == 'openrouter/free'
        if body.get('response_format', {}).get('json_schema', {}).get('name') == 'Extraction':
            return response({'role': 'assistant', 'content': Extraction(supported=True, reason='', quote=quote).model_dump_json()})
        if 'response_format' in body:
            return response({'role': 'assistant', 'content': AnswerDraft(answer='CALCULATION: see comparison',
                citation_ids=[], evidence_absent=False, conflict=False).model_dump_json()})
        return response({'role': 'assistant', 'tool_calls': [{'id': f'call_{len(seen)}', 'type': 'function',
            'function': {'name': 'compare_vendors', 'arguments': '{}'}}]})
    provider = make_provider(service.settings, handler)
    doc = read_pdf((ROOT / 'samples/vendor_c.pdf').read_bytes(), quote.filename, quote.document_id)
    assert provider.extract(doc).stated_total == quote.stated_total
    result = ask(analysis, AskRequest(question='Compare vendors'), service.index(analysis), provider)
    assert result.comparison is not None
    assert len(result.activity) == 4
    assert len(seen) == 6  # extraction, four bounded tool rounds, structured final answer
    assert len([m for m in seen[-1]['messages'] if m['role'] == 'tool']) == 4


@pytest.mark.mocked
@pytest.mark.parametrize('status', [401, 429, 503])
def test_openrouter_errors_never_fall_back(settings, quote_factory, status):
    quote = quote_factory()
    provider = make_provider(settings, lambda request: httpx.Response(status,
        json={'error': {'message': 'Test error', 'code': status}}))
    doc = read_pdf((ROOT / 'samples/vendor_c.pdf').read_bytes(), quote.filename, quote.document_id)
    with pytest.raises(VendorWiseError) as error:
        provider.extract(doc)
    assert error.value.status_code == (429 if status == 429 else 502)


@pytest.mark.mocked
@pytest.mark.parametrize('repair_succeeds', [True, False])
def test_structured_extraction_repairs_at_most_once(settings, quote_factory, repair_succeeds):
    quote = quote_factory()
    valid = Extraction(supported=True, reason='', quote=quote).model_dump(mode='json')
    invalid = json.loads(json.dumps(valid))
    invalid['quote']['tax']['value']['basis'] = 'fixed'
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        data = valid if repair_succeeds and len(calls) == 2 else invalid
        return response({'role':'assistant', 'content':json.dumps(data)})
    provider = make_provider(settings, handler)
    doc = read_pdf((ROOT/'samples/vendor_c.pdf').read_bytes(),quote.filename,quote.document_id)
    if repair_succeeds:
        assert provider.extract(doc).tax == quote.tax
    else:
        with pytest.raises(VendorWiseError):
            provider.extract(doc)
    assert len(calls) == 2
    assert 'quote.tax.value' in calls[1]['messages'][-1]['content']
