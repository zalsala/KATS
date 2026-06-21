"""Build KATS executable with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    """Run PyInstaller using the release spec file."""
    root = project_root()
    spec_path = root / "release" / "kats.spec"
    if not spec_path.is_file():
        print(f"Spec file not found: {spec_path}")
        return 1

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(spec_path),
        "--noconfirm",
        "--distpath",
        str(root / "dist"),
        "--workpath",
        str(root / "build"),
    ]
    print(f">>> {' '.join(command)}")
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode != 0:
        return result.returncode
    print(f"Build completed: {root / 'dist' / 'KATS'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
