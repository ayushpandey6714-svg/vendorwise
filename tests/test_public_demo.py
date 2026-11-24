from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from vendorwise.api import create_app
from vendorwise.config import ROOT, Settings
from vendorwise.errors import VendorWiseError
from vendorwise.service import Service


def test_public_demo_rejects_live_mode(settings):
    with pytest.raises(VendorWiseError, match="requires fixture"):
        Service(replace(settings, public_demo=True, mode="live"))


def test_public_demo_rejects_unrecognized_bytes_before_parsing(settings, requirements, monkeypatch):
    with TestClient(create_app(replace(settings, public_demo=True))) as client:
        assert client.get("/health").json()["public_demo"]
        aid = client.post("/analyses", json=requirements.model_dump(mode="json")).json()["analysis_id"]
        def never_parse(*args):
            raise AssertionError("Unknown public uploads must not reach PDF parsing")
        monkeypatch.setattr("vendorwise.service.read_pdf", never_parse)
        result = client.post(f"/analyses/{aid}/documents", files=[("files", ("private.pdf", b"%PDF-untrusted"))])
        assert result.status_code == 422 and "synthetic" in result.json()["detail"]


def test_public_demo_sample_flow_and_session_limit(settings, requirements):
    with TestClient(create_app(replace(settings, public_demo=True, max_demo_analyses=1))) as client:
        aid = client.post("/analyses", json=requirements.model_dump(mode="json")).json()["analysis_id"]
        data = (ROOT / "samples" / "vendor_c.pdf").read_bytes()
        assert client.post(f"/analyses/{aid}/documents", files=[("files", ("c.pdf", data))]).status_code == 201
        assert client.post(f"/analyses/{aid}/extract").status_code == 200
        assert client.post(f"/analyses/{aid}/compare").json()["recommendation_ids"]
        assert client.post("/analyses", json=requirements.model_dump(mode="json")).status_code == 503


def test_container_supervisor_stops_both_children_on_service_failure(monkeypatch):
    from scripts import serve_container
    children = []
    class Process:
        def __init__(self, args, **kwargs):
            self.args, self.terminated = args, False
            self.number = len(children)
            children.append(self)
        def poll(self):
            return 1 if self.number == 1 else None
        def terminate(self):
            self.terminated = True
        def wait(self, timeout=None):
            return 0
    class Healthy:
        status = 200
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
    monkeypatch.setenv("PORT", "7860")
    monkeypatch.setattr(serve_container.subprocess, "Popen", Process)
    monkeypatch.setattr(serve_container.urllib.request, "urlopen", lambda *a, **kw: Healthy())
    monkeypatch.setattr(serve_container.signal, "signal", lambda *a: None)
    with pytest.raises(RuntimeError, match="service exited"):
        serve_container.main()
    assert children[0].terminated
    assert "127.0.0.1" in children[0].args
    assert "--server.address=0.0.0.0" in children[1].args


def test_container_supervisor_rejects_conflicting_port(monkeypatch):
    from scripts.serve_container import main
    monkeypatch.setenv("PORT", "8000")
    with pytest.raises(SystemExit, match="different"):
        main()


def test_public_frontend_uses_samples_without_upload_widget(settings, monkeypatch):
    """UI + real application logic over in-process HTTP, not a Docker test."""
    from urllib.parse import urlsplit
    import httpx
    from streamlit.testing.v1 import AppTest
    with TestClient(create_app(replace(settings, public_demo=True))) as client:
        def local_request(method, url, **kwargs):
            kwargs.pop("timeout", None)  # In-process TestClient has no socket timeout.
            return client.request(method, urlsplit(url).path, **kwargs)
        monkeypatch.setattr(httpx, "request", local_request)
        ui = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        assert not ui.exception
        assert not ui.file_uploader
        ui.button(key="create_analysis").click().run()
        assert not ui.exception and not ui.error
        comparison = ui.session_state["comparison"]
        winners = [o["vendor"] for o in comparison["offers"] if o["document_id"] in comparison["recommendation_ids"]]
        assert winners == ["Vendor C"]
