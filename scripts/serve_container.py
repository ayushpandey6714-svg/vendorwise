"""Supervise both services in one container; only Streamlit is publicly exposed."""
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

from vendorwise.config import ROOT


def main():
    port = int(os.getenv("PORT", "7860"))
    if not 1024 <= port <= 65535 or port == 8000:
        raise SystemExit("PORT must be 1024-65535 and different from internal backend port 8000.")
    env = dict(os.environ)
    env["VENDORWISE_API_URL"] = "http://127.0.0.1:8000"
    children: list[subprocess.Popen] = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "vendorwise.api:app",
                                    "--host", "127.0.0.1", "--port", "8000", "--workers", "1"], cwd=ROOT, env=env)
        children.append(backend)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline and not stopping:
            if backend.poll() is not None:
                raise RuntimeError("FastAPI exited during startup; check the preceding logs.")
            try:
                with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (urllib.error.URLError, TimeoutError):
                time.sleep(.5)
        else:
            if stopping:
                return 0
            raise RuntimeError("FastAPI did not become healthy within 90 seconds.")
        frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
                                     "--server.address=0.0.0.0", f"--server.port={port}",
                                     "--server.headless=true", "--server.enableAgentApi=false"], cwd=ROOT, env=env)
        children.append(frontend)
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError("An application service exited; stopping the container so hosting can restart it.")
            time.sleep(.5)
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    raise SystemExit(main())
