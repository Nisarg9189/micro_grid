"""Serve the interactive console.

    PYTHONPATH=src .venv/bin/python scripts/serve.py

Then open http://127.0.0.1:8000 . API docs are at /api/docs.

Bound to localhost only: the endpoints run unbounded-ish CPU work and there is no
authentication, so this is a review tool for one machine, not something to expose.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"GramUrja console on http://127.0.0.1:{port}   (API docs at /api/docs)")
    uvicorn.run("gramurja.api:app", host="127.0.0.1", port=port, log_level="warning")
