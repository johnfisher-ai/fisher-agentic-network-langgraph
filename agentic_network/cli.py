"""Headless runner. This is the path that works in a notebook and in Colab.

    python3 -m agentic_network.cli "My bookings for November are down 20%."
    python3 -m agentic_network.cli --config config/config_agency.xml "ESG rules are coming."
    python3 -m agentic_network.cli --verbose --yes "Should I match my competitor?"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .channels import ConsoleChannel
from .config import load_config
from .graph import build_network

DEFAULT_CONFIG = "config/config_travel.xml"


def load_env() -> None:
    """Read .env if python-dotenv is available. Never fails on its absence."""
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    for candidate in (Path.cwd(), *Path(__file__).resolve().parents):
        env = candidate / ".env"
        if env.exists():
            load_dotenv(env)
            return


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ask the agent network a question.")
    p.add_argument("question", help="the business problem to put to the broker")
    p.add_argument("-c", "--config", default=DEFAULT_CONFIG, help=f"XML config (default: {DEFAULT_CONFIG})")
    p.add_argument("-v", "--verbose", action="store_true", help="show the per-agent trace")
    p.add_argument("--scenario", type=int, help="force a scenario id instead of keyword matching")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--yes", action="store_true", help="approve the human gate without asking")
    group.add_argument("--no", action="store_true", help="reject the human gate without asking")
    args = p.parse_args(argv)

    load_env()

    auto = True if args.yes else (False if args.no else None)
    channel = ConsoleChannel(verbose=args.verbose, auto_approve=auto)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        network = build_network(config, channel=channel)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    network.run(args.question, scenario_id=args.scenario)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
