#!/usr/bin/env python3
"""Check the working tree for common public-release mistakes."""

from __future__ import annotations

import re
import struct
import subprocess
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
    "@gmail.com": "personal email address",
}
PLACEHOLDER = "YOUR_GITHUB_USERNAME"
SKIP_DIRS = {".git", "__pycache__"}
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
SECRET_PATTERNS = {
    "GitHub token": re.compile(r"\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "signed URL": re.compile(
        r"https?://\S+[?&](?:token|sig|signature|auth|key|expires)=",
        re.IGNORECASE,
    ),
}


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
        for description, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                problems.append(f"{relative}: possible {description}")
        for email in EMAIL_PATTERN.findall(text):
            if not email.lower().endswith("@users.noreply.github.com"):
                problems.append(f"{relative}: public email address {email}")
        if PLACEHOLDER in text:
            placeholders.append(str(relative))

    if missing:
        problems.append(f"missing required public files: {', '.join(missing)}")
    social_preview = ROOT / "assets" / "social-preview.png"
    if not social_preview.is_file():
        problems.append("missing social preview: assets/social-preview.png")
    else:
        data = social_preview.read_bytes()
        if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
            width, height = struct.unpack(">II", data[16:24])
            if (width, height) != (1280, 640):
                problems.append(
                    f"social preview must be 1280x640, got {width}x{height}"
                )
        else:
            problems.append("social preview is not a valid PNG")
        if len(data) >= 1_000_000:
            problems.append(
                f"social preview must be under 1 MB, got {len(data)} bytes"
            )
    if release_mode and placeholders:
        problems.append(
            "repository owner placeholder remains in: "
            + ", ".join(sorted(placeholders))
        )
    if release_mode:
        metadata = subprocess.run(
            ["git", "log", "--format=%ae%n%ce", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        exposed = sorted(
            {
                email
                for email in metadata
                if email and not email.lower().endswith("@users.noreply.github.com")
            }
        )
        if exposed:
            problems.append(
                "public branch commit metadata exposes email: " + ", ".join(exposed)
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
