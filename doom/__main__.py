"""DOOM command-line entry point."""
from __future__ import annotations
import argparse
from pathlib import Path
from .vault import LocalProtectedVault
from .workers import ResourceManager, Worker, WorkerType
from .workspace import WorkspaceManifest

def main() -> None:
    parser = argparse.ArgumentParser(prog="doom")
    sub = parser.add_subparsers(dest="command")
    init = sub.add_parser("init", help="initialize the local DOOM protected vault")
    init.add_argument("--root", default="data/doom")
    workspace = sub.add_parser("workspace", help="manage a DOOM project workspace")
    workspace_sub = workspace.add_subparsers(dest="workspace_command")
    workspace_init = workspace_sub.add_parser("init", help="create a workspace manifest")
    workspace_init.add_argument("project_id")
    workspace_init.add_argument("root")
    args = parser.parse_args()

    if args.command == "init":
        root = Path(args.root).expanduser().resolve()
        LocalProtectedVault(root / "protected_vault").initialize()
        print(f"DOOM initialized: {root}")
        print("Protected vault: local PC only")
        return

    if args.command == "workspace" and args.workspace_command == "init":
        root = Path(args.root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        manifest = WorkspaceManifest(args.project_id)
        manifest.save(root / ".doom" / "manifest.json")
        print(f"Workspace initialized: {root}")
        print(f"Manifest: {root / '.doom' / 'manifest.json'}")
        return

    manager = ResourceManager()
    manager.register(Worker(id="local-pc", type=WorkerType.LOCAL, capabilities={"cpu", "filesystem", "browser"}))
    print("DOOM 0.1.0")
    print(f"Workers: {len(manager.workers)}")
    print("Protected vault policy: LOCAL_ONLY")
    print("Distributed workspace: READY")

if __name__ == "__main__":
    main()
