"""Create a clean KATS release package layout."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FORBIDDEN_PACKAGE_PARTS: tuple[str, ...] = (
    "data/auth",
    "data/database",
    "logs",
    "token",
    ".env",
)

REQUIRED_RELEASE_ITEMS: tuple[str, ...] = (
    "config",
    "plugins",
    "README.txt",
    ".env.example",
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def validate_release_structure(root: Path) -> list[str]:
    """Validate that a release directory contains required items and no forbidden paths."""
    errors: list[str] = []
    for item in REQUIRED_RELEASE_ITEMS:
        if not (root / item).exists():
            errors.append(f"Missing required release item: {item}")

    for path in root.rglob("*"):
        if not path.is_file() and not path.is_dir():
            continue
        relative = path.relative_to(root).as_posix()
        for forbidden in FORBIDDEN_PACKAGE_PARTS:
            if relative == forbidden or relative.startswith(f"{forbidden}/"):
                errors.append(f"Forbidden release path present: {relative}")
    return errors


def package_release(*, source_dir: Path, output_dir: Path) -> None:
    """Copy build output into a clean release package directory."""
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(source_dir, output_dir)

    readme_src = project_root() / "release" / "README.txt"
    env_example_src = project_root() / ".env.example"
    shutil.copy2(readme_src, output_dir / "README.txt")
    shutil.copy2(env_example_src, output_dir / ".env.example")

    for forbidden in FORBIDDEN_PACKAGE_PARTS:
        target = output_dir / forbidden
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Package KATS release artifacts")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Validate repository release layout definitions only",
    )
    parser.add_argument(
        "--source",
        default="dist/KATS",
        help="PyInstaller output directory relative to project root",
    )
    parser.add_argument(
        "--output",
        default="release/dist/KATS",
        help="Release package output directory relative to project root",
    )
    args = parser.parse_args()

    root = project_root()
    if args.verify_only:
        staging = root / "release" / "dist" / "KATS"
        if staging.is_dir():
            errors = validate_release_structure(staging)
            if errors:
                for error in errors:
                    print(error)
                return 1
        print("Release structure verification passed.")
        return 0

    source_dir = root / args.source
    output_dir = root / args.output
    if not source_dir.is_dir():
        print(f"Build output not found: {source_dir}")
        print("Run scripts/build.py first.")
        return 1

    package_release(source_dir=source_dir, output_dir=output_dir)
    errors = validate_release_structure(output_dir)
    if errors:
        for error in errors:
            print(error)
        return 1

    print(f"Release package created: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
