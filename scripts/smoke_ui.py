"""Real HTTP backend + Streamlit AppTest interaction. No HTTP/provider mocks."""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="smoke-", dir=work) as temp:
        env = {**os.environ, "VENDORWISE_MODE":"fixture", "EMBEDDING_BACKEND":"tfidf", "VENDORWISE_DATA_DIR":temp}
        backend = subprocess.Popen([sys.executable,"-m","uvicorn","vendorwise.api:app","--host","127.0.0.1","--port",str(port)],
                                   cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        assert backend.stderr is not None
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(120):
                if backend.poll() is not None:
                    raise RuntimeError(backend.stderr.read().decode())
                try:
                    if httpx.get(base + "/health").status_code == 200:
                        break
                except httpx.RequestError:
                    pass
                time.sleep(.25)
            else:
                raise RuntimeError("Backend did not start within 30 seconds")
            os.environ["VENDORWISE_API_URL"] = base
            app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
            assert not app.exception, app.exception
            app.checkbox[0].check()
            next(b for b in app.button if b.label == "Create analysis and extract").click().run()
            assert not app.exception, app.exception
            assert not app.error, [e.value for e in app.error]
            comparison = app.session_state["comparison"]
            winners = [o["vendor"] for o in comparison["offers"] if o["document_id"] in comparison["recommendation_ids"]]
            assert winners == ["Vendor C"], winners
            app.slider(key="wi_delivery").set_value(14)
            next(b for b in app.button if b.label == "Apply what-if requirements").click().run()
            assert not app.exception, app.exception
            assert app.session_state["what_if"]["savings"] == "30000.00"
            app.text_input[0].set_value("Does Vendor B include battery replacement?")
            next(b for b in app.button if b.label == "Ask documents").click().run()
            assert not app.exception, app.exception
            assert app.session_state["answers"][-1][1]["citations"][0]["page"] == 2
            next(b for b in app.button if b.label == "Prepare Markdown report").click().run()
            assert not app.exception, app.exception
            assert "PDF page 2" in app.session_state["report"]
            result = {"status":"passed", "backend":"real localhost HTTP", "frontend":"Streamlit AppTest (headless)",
                      "steps":["create", "upload 3 PDFs", "extract", "compare C", "what-if B saves INR 30000", "Q&A page 2 citations", "report"],
                      "mode":"fixture", "embeddings":"tfidf", "browser_visual_test":False}
            path = ROOT / "evaluation" / "results" / "ui-smoke.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result, indent=2))
        finally:
            backend.terminate()
            backend.wait(timeout=15)
            backend.stderr.close()


if __name__ == "__main__":
    main()
