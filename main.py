"""KATS entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from app.release.cli import parse_args, run_cli


def main(argv: list[str] | None = None) -> int:
    """Initialize and start KATS.

    Returns:
        Process exit code. Zero on success.
    """
    project_root = Path(__file__).resolve().parent
    options = parse_args(argv)
    return run_cli(project_root=project_root, options=options)


if __name__ == "__main__":
    sys.exit(main())
