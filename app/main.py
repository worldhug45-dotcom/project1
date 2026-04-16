"""Command line entry point for the first MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.infrastructure.settings import ConfigurationError, load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project1",
        description="AI, infrastructure, SI opportunity notice collector MVP.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to a TOML settings file. Defaults are used when omitted.",
    )
    parser.add_argument(
        "--env",
        choices=["local", "dev", "prod"],
        default=None,
        help="Runtime environment override.",
    )
    parser.add_argument(
        "--action",
        choices=["collect", "export", "all"],
        default=None,
        help="Runtime action override.",
    )
    parser.add_argument(
        "--mode",
        choices=["normal", "dry_run"],
        default=None,
        help="Runtime mode override.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    overrides = {
        key: value
        for key, value in {
            "action": args.action,
            "mode": args.mode,
            "env": args.env,
        }.items()
        if value is not None
    }

    try:
        settings = load_settings(args.config, cli_overrides=overrides)
    except ConfigurationError as exc:
        parser.exit(status=2, message=f"Configuration error:\n{exc}\n")

    action = settings.runtime.action
    print(
        f"project1 action={action} env={settings.app.env} mode={settings.runtime.mode}"
    )
    print("CLI skeleton is ready; source, storage, export, and logging work follow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

