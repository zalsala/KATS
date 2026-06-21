"""Run the full quality check suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run(command: list[str]) -> int:
    """Run a command and return its exit code."""
    print(f">>> {' '.join(command)}")
    result = subprocess.run(command, check=False, cwd=project_root())
    return result.returncode


def main() -> int:
    """Execute ruff, black, mypy, pytest, and release structure checks."""
    root = project_root()
    python = sys.executable
    checks = [
        [python, "-m", "ruff", "check", "app", "tests", "main.py", "scripts"],
        [python, "-m", "black", "--check", "app", "tests", "main.py", "scripts"],
        [python, "-m", "mypy", "app", "main.py"],
        [python, "-m", "pytest"],
        [python, str(root / "scripts" / "package.py"), "--verify-only"],
    ]
    for command in checks:
        code = run(command)
        if code != 0:
            return code
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
