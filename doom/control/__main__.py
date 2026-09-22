"""Run the DOOM control plane locally."""
from __future__ import annotations
import argparse
import uvicorn
from .server import DoomControlPlane

def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m doom.control")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    app = DoomControlPlane().create_app()
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
