"""
Starts the FastAPI backend in a background thread so that Streamlit Cloud
(which only runs one process) can host both frontend and backend together.

Import this module at the top of app.py with:
    import start_backend  # noqa: F401  — starts backend thread
"""
import threading
import time
import logging

logger = logging.getLogger(__name__)

def _run():
    import uvicorn
    # Give Streamlit a moment to bind port 8501 first
    time.sleep(2)
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )

_thread = threading.Thread(target=_run, daemon=True, name="fastapi-backend")
_thread.start()
