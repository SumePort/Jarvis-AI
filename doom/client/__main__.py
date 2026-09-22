"""Run the DOOM PC client."""
from __future__ import annotations
import argparse
from pathlib import Path
from .client import DoomClient
from .config import ClientConfig

def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m doom.client")
    parser.add_argument("command", choices=["enroll","register","heartbeat","status","start"])
    parser.add_argument("--control-url", default=None)
    parser.add_argument("--name", default=None)
    parser.add_argument("--config", default="data/doom/client.json")
    args = parser.parse_args()

    path = Path(args.config).expanduser().resolve()
    config = ClientConfig.load(path)
    if args.control_url: config.control_url = args.control_url
    if args.name: config.device_name = args.name
    client = DoomClient(config, path)

    if args.command == "enroll":
        client.enroll()
        print(f"DOOM device enrolled: {client.config.device_id}")
        print(f"Credentials saved locally: {path}")
    elif args.command == "register":
        print(client.register_local_worker())
    elif args.command == "heartbeat":
        print(client.heartbeat())
    elif args.command == "start":
        print(client.run_once())
    else:
        print(client.status())

if __name__ == "__main__":
    main()
