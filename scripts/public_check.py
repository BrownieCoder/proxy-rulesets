#!/usr/bin/env python3
"""Check the working tree for common public-release mistakes."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "THIRD_PARTY_NOTICES.md",
    "PUBLICATION_CHECKLIST.md",
    "research/ChinaGaming-audit.md",
    "research/ChinaGaming-audit.en.md",
}
FORBIDDEN = {
    "/Users/": "absolute local user path",
    "libradns.com": "removed private hostname",
    "gt2-rs-weissach.pro": "removed private hostname",
    "rainbose/Config": "source without confirmed redistribution license",
    "supreme4local@gmail.com": "personal email address",
}
PLACEHOLDER = "YOUR_GITHUB_USERNAME"
SKIP_DIRS = {".git", "__pycache__"}


def public_files() -> list[Path]:
    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.resolve() != Path(__file__).resolve()
        and not any(part in SKIP_DIRS for part in path.parts)
    ]


def main() -> int:
    release_mode = "--release" in sys.argv[1:]
    missing = sorted(name for name in REQUIRED if not (ROOT / name).is_file())
    problems: list[str] = []
    placeholders: list[str] = []

    for path in public_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(ROOT)
        for value, description in FORBIDDEN.items():
            if value in text:
                problems.append(f"{relative}: {description}")
        if PLACEHOLDER in text:
            placeholders.append(str(relative))

    if missing:
        problems.append(f"missing required public files: {', '.join(missing)}")
    if release_mode and placeholders:
        problems.append(
            "repository owner placeholder remains in: "
            + ", ".join(sorted(placeholders))
        )

    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 1

    print(f"Public working-tree check passed ({len(public_files())} files).")
    if placeholders:
        print(
            "Release warning: replace YOUR_GITHUB_USERNAME before public push "
            "(enforced by --release)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
