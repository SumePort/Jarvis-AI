"""DOOM command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
from .vault import LocalProtectedVault
from .workers import ResourceManager, Worker, WorkerType

def main() -> None:
    parser = argparse.ArgumentParser(prog="doom")
    sub = parser.add_subparsers(dest="command")
    init = sub.add_parser("init", help="initialize the local DOOM protected vault")
    init.add_argument("--root", default="data/doom")
    sub.add_parser("status", help="show the local DOOM foundation status")
    args = parser.parse_args()
    if args.command == "init":
        root = Path(args.root).expanduser().resolve()
        LocalProtectedVault(root / "protected_vault").initialize()
        print(f"DOOM initialized: {root}")
        print("Protected vault: local PC only")
        return
    manager = ResourceManager()
    manager.register(Worker(id="local-pc", type=WorkerType.LOCAL, capabilities={"cpu", "filesystem", "browser"}))
    print("DOOM 0.1.0")
    print(f"Workers: {len(manager.workers)}")
    print("Protected vault policy: LOCAL_ONLY")
    print("Distributed workspace: READY")

if __name__ == "__main__":
    main()
