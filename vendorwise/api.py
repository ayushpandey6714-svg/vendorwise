"""Run with: python -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000"""
from uuid import UUID

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool

from .config import Settings
from .errors import VendorWiseError
from .report import markdown_report
from .schemas import (AnalysisSummary, Answer, AskRequest, Comparison, Document, Health,
                      Quote, Requirements, WhatIfRequest, WhatIfResult)
from .service import Service


def create_app(settings: Settings | None = None):
    service = Service(settings or Settings.from_env())
    app = FastAPI(title="VendorWise", version="1.0.0",
                  description="Laptop quotation auditor. INR only. Shared request budgets; no user authentication.")
    app.state.service = service

    @app.exception_handler(VendorWiseError)
    async def vendor_error(request, exc):
        headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after is not None else None
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)}, headers=headers)

    @app.middleware("http")
    async def upload_limit(request, call_next):
        # Reject oversize bodies even without Content-Length. Multipart parsing itself
        # happens before the endpoint, so endpoint-only limits are insufficient.
        limit = service.settings.max_request_bytes
        if request.method == "POST":
            length = request.headers.get("content-length")
            if length and (not length.isdigit() or int(length) > limit):
                return JSONResponse(status_code=413, content={"detail": f"Request body exceeds {limit} bytes or has invalid length."})
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > limit:
                    return JSONResponse(status_code=413, content={"detail": f"Request body exceeds {limit} bytes."})
            request._body = bytes(body)
        return await call_next(request)

    @app.get("/health", response_model=Health)
    def health():
        s = service.settings
        return Health(status="ok", mode=s.mode, embedding_backend=s.embedding_backend,
                      provider_configured=bool(s.api_key and not s.api_key.startswith("your-")), public_demo=s.public_demo,
                      ai_requests_per_minute=s.ai_requests_per_minute, ai_requests_per_day=s.ai_requests_per_day)

    @app.post("/analyses", response_model=AnalysisSummary, status_code=201)
    def create(requirements: Requirements):
        with service.repo.lock:
            limit = service.settings.max_demo_analyses if service.settings.public_demo else service.settings.max_analyses
            if len(list(service.repo.root.glob("*/analysis.json"))) >= limit:
                raise VendorWiseError("Analysis storage is full. Existing analyses still work. The owner must clear expired data before new analyses can be created.", 503)
            a = service.repo.create(requirements, service.settings.mode, service.settings.embedding_backend)
        return AnalysisSummary(**a.model_dump(exclude={"quotes"}))

    @app.post("/analyses/{analysis_id}/documents", response_model=list[Document], status_code=201)
    async def upload(analysis_id: UUID, files: list[UploadFile] = File(...)):
        try:
            if not 1 <= len(files) <= service.settings.max_documents:
                raise VendorWiseError("Upload one to five PDFs.")
            uploads = []
            for file in files:
                data = await file.read(service.settings.max_upload_bytes + 1)
                if len(data) > service.settings.max_upload_bytes:
                    raise VendorWiseError("Each PDF must be 10 MiB or smaller.", 413)
                uploads.append((file.filename or "quotation.pdf", data))
            return await run_in_threadpool(service.upload, analysis_id, uploads)
        finally:
            for file in files:
                await file.close()

    @app.post("/analyses/{analysis_id}/extract", response_model=list[Quote])
    def extract(analysis_id: UUID):
        return service.extract(analysis_id)

    @app.get("/analyses/{analysis_id}/quotes", response_model=list[Quote])
    def quotes(analysis_id: UUID):
        return service.load(analysis_id).quotes

    @app.post("/analyses/{analysis_id}/compare", response_model=Comparison)
    def comparison(analysis_id: UUID):
        return service.compare(analysis_id)

    @app.post("/analyses/{analysis_id}/ask", response_model=Answer)
    def question(analysis_id: UUID, request: AskRequest):
        return service.ask(analysis_id, request)

    @app.post("/analyses/{analysis_id}/what-if", response_model=WhatIfResult)
    def scenario(analysis_id: UUID, request: WhatIfRequest):
        return service.what_if(analysis_id, request)

    @app.get("/analyses/{analysis_id}/report", response_class=PlainTextResponse)
    def report(analysis_id: UUID):
        return PlainTextResponse(markdown_report(service.ready(analysis_id)), media_type="text/markdown",
                                 headers={"Content-Disposition": 'attachment; filename="vendorwise-report.md"'})

    return app


app = create_app()
