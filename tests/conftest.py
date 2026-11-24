from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from vendorwise.api import create_app
from vendorwise.config import ROOT, Settings
from vendorwise.pdf import read_pdf
from vendorwise.provider import Provider
from vendorwise.schemas import Requirements


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path / "data", mode="fixture", embedding_backend="tfidf")


@pytest.fixture
def requirements():
    return Requirements(quantity=20, budget="1200000", min_ram_gb=16, min_storage_gb=512,
                        min_warranty_months=36, max_delivery_days=10)


@pytest.fixture
def quote_factory(settings):
    def make(sample="vendor_c"):
        data = (ROOT / "samples" / f"{sample}.pdf").read_bytes()
        doc = read_pdf(data, f"{sample}.pdf", str(uuid4()))
        return Provider(settings).extract(doc)
    return make


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def ready_analysis(client, requirements):
    def create(samples=("vendor_a", "vendor_b", "vendor_c")):
        response = client.post("/analyses", json=requirements.model_dump(mode="json"))
        assert response.status_code == 201, response.text
        aid = response.json()["analysis_id"]
        files = [("files", (f"{name}.pdf", (ROOT / "samples" / f"{name}.pdf").read_bytes(), "application/pdf")) for name in samples]
        response = client.post(f"/analyses/{aid}/documents", files=files)
        assert response.status_code == 201, response.text
        response = client.post(f"/analyses/{aid}/extract")
        assert response.status_code == 200, response.text
        return aid, response.json()
    return create
