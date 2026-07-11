from __future__ import annotations

import argparse
import sys

from finalert.config import provider_from_env


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="finalert", description="Send notifications for Python jobs."
    )
    parser.add_argument("--version", action="version", version="finalert 0.3.1")
    commands = parser.add_subparsers(dest="command", required=True)
    test = commands.add_parser("test", help="send a test notification")
    test.add_argument(
        "--provider",
        choices=("telegram", "email", "webhook", "pushplus"),
        default=None,
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "test":
        try:
            selected = provider_from_env(args.provider)
            selected.send(
                "🧪 Finalert test",
                "Your configuration works. Finalert can send notifications.",
            )
        except Exception as exc:
            print(f"✗ Test notification failed: {exc}", file=sys.stderr)
            return 1
        print("✓ Test notification sent")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
