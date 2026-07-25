#!/usr/bin/env python3
"""Validate the committed mirror without network access."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from sync import validate  # noqa: E402


def validate_config_references(provider_names: set[str]) -> None:
    provider_pattern = re.compile(r"^  ([A-Za-z0-9_-]+):$", re.MULTILINE)
    for filename in ("rule-providers.local.yaml", "rule-providers.remote.yaml"):
        text = (ROOT / "config" / filename).read_text(encoding="utf-8")
        defined = set(provider_pattern.findall(text))
        if defined != provider_names:
            raise ValueError(
                f"{filename}: provider mismatch: "
                f"missing={provider_names-defined}, extra={defined-provider_names}"
            )

    rules_text = (ROOT / "config" / "rules.yaml").read_text(encoding="utf-8")
    referenced = set(
        re.findall(r"^\s*-\s*RULE-SET,([^,]+),", rules_text, re.MULTILINE)
    )
    if not referenced <= provider_names:
        raise ValueError(
            f"rules.yaml references undefined providers: {referenced-provider_names}"
        )

    ordered_markers = (
        "RULE-SET,InternationalGaming,🧭 Final",
        "RULE-SET,ChinaGaming,DIRECT",
        "RULE-SET,Bilibili,📺 Bilibili",
        "RULE-SET,SteamCN,🕹️ Steam",
        "RULE-SET,GlobalMedia,🛰️ International-Global",
        "RULE-SET,ChinaMax,🇨🇳 China-Global",
    )
    positions = [rules_text.index(marker) for marker in ordered_markers]
    if positions != sorted(positions):
        raise ValueError("rules.yaml game/provider priority order is unsafe")
    if rules_text.index("DOMAIN,fastcdn.hoyoverse.com,DIRECT") > positions[0]:
        raise ValueError("fastcdn.hoyoverse.com override must precede InternationalGaming")
    geoip_position = rules_text.index("GEOIP,CN,DIRECT,no-resolve")
    if not positions[-2] < geoip_position < positions[-1]:
        raise ValueError("GEOIP CN fallback must be after GlobalMedia and before ChinaMax")


def main() -> int:
    sources = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
    local_sources = json.loads((ROOT / "local-rulesets.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
    expected_paths = {
        entry["path"] for entry in list(sources.values()) + list(local_sources.values())
    }
    actual_paths = {str(path.relative_to(ROOT)) for path in (ROOT / "ruleset").glob("*.yaml")}
    if expected_paths != actual_paths:
        raise ValueError(f"ruleset file mismatch: missing={expected_paths-actual_paths}, extra={actual_paths-expected_paths}")
    for name, source in sources.items():
        data = (ROOT / source["path"]).read_bytes()
        validate(name, data)
        digest = hashlib.sha256(data).hexdigest()
        if digest != lock["rulesets"][name]["sha256"]:
            raise ValueError(f"{name}: SHA-256 does not match sources.lock.json")
    for name, source in local_sources.items():
        data = (ROOT / source["path"]).read_bytes()
        validate(name, data)
        rules = [
            line.strip()
            for line in data.decode("utf-8").splitlines()
            if line.strip().startswith("- ")
        ]
        if len(rules) != len(set(rules)):
            raise ValueError(f"{name}: local ruleset contains duplicate entries")
    validate_config_references(set(sources) | set(local_sources))
    print(
        f"Validated {len(sources)} mirrored rulesets/checksums "
        f"and {len(local_sources)} local rulesets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
