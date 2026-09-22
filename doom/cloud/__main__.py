"""Run the reference DOOM worker service."""
from __future__ import annotations
import argparse
import os
import uvicorn
from .server import create_worker_app

def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m doom.cloud")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8890)
    args = parser.parse_args()
    token = os.getenv("DOOM_WORKER_TOKEN", "")
    if not token:
        raise SystemExit("Set DOOM_WORKER_TOKEN before starting a worker.")
    uvicorn.run(create_worker_app(token), host=args.host, port=args.port)

if __name__ == "__main__":
    main()
