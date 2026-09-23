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
from siri_ai import validate as validate_siri_ai  # noqa: E402

BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "PASS"}


def parse_policy_groups(root: Path = ROOT) -> tuple[set[str], dict[str, list[str]]]:
    """Read the project-owned policy-group template without a YAML dependency."""
    text = (root / "config" / "proxy-groups.yaml").read_text(encoding="utf-8")
    names: set[str] = set()
    members: dict[str, list[str]] = {}
    current: str | None = None
    in_proxies = False

    for line in text.splitlines():
        name_match = re.match(r'^  - name: "([^"]+)"\s*$', line)
        if name_match:
            current = name_match.group(1)
            if current in names:
                raise ValueError(f"proxy-groups.yaml defines duplicate group: {current}")
            names.add(current)
            members[current] = []
            in_proxies = False
            continue
        if current is None:
            continue
        if re.match(r"^    proxies:\s*$", line):
            in_proxies = True
            continue
        if in_proxies:
            member_match = re.match(r'^      - (?:"([^"]+)"|([^#\s][^#]*?))\s*$', line)
            if member_match:
                member = (member_match.group(1) or member_match.group(2)).strip()
                members[current].append(member)
            elif line.strip() and not line.lstrip().startswith("#"):
                in_proxies = False

    if not names:
        raise ValueError("proxy-groups.yaml defines no policy groups")
    referenced = {member for values in members.values() for member in values}
    missing = referenced - names - BUILTIN_POLICIES
    if missing:
        raise ValueError(f"proxy-groups.yaml references undefined groups: {missing}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ValueError(f"proxy-groups.yaml contains a group cycle at: {name}")
        if name in visited:
            return
        visiting.add(name)
        for member in members[name]:
            if member in names:
                visit(member)
        visiting.remove(name)
        visited.add(name)

    for name in names:
        visit(name)
    return names, members


def parse_rule_targets(text: str) -> set[str]:
    targets: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\s*-\s*([^#].*)$", line)
        if not match:
            continue
        fields = [field.strip() for field in match.group(1).split(",")]
        if fields[0] == "MATCH" and len(fields) >= 2:
            targets.add(fields[1])
        elif len(fields) >= 3:
            targets.add(fields[2])
    return targets


def validate_config_references(provider_names: set[str], root: Path = ROOT) -> None:
    provider_pattern = re.compile(r"^  ([A-Za-z0-9_-]+):$", re.MULTILINE)
    for filename in ("rule-providers.local.yaml", "rule-providers.remote.yaml"):
        text = (root / "config" / filename).read_text(encoding="utf-8")
        defined = set(provider_pattern.findall(text))
        if defined != provider_names:
            raise ValueError(
                f"{filename}: provider mismatch: "
                f"missing={provider_names-defined}, extra={defined-provider_names}"
            )

    rules_text = (root / "config" / "rules.yaml").read_text(encoding="utf-8")
    referenced = set(
        re.findall(r"^\s*-\s*RULE-SET,([^,]+),", rules_text, re.MULTILINE)
    )
    if not referenced <= provider_names:
        raise ValueError(
            f"rules.yaml references undefined providers: {referenced-provider_names}"
        )

    ordered_markers = (
        "RULE-SET,InternationalGaming,🎮 国际游戏",
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

    gemini_position = rules_text.index("RULE-SET,Gemini,♊ Gemini")
    google_position = rules_text.index("RULE-SET,Google,🔎 Google")
    if gemini_position > google_position:
        raise ValueError("Gemini must be matched before the broader Google provider")

    group_names, group_members = parse_policy_groups(root)
    custom_targets = parse_rule_targets(rules_text) - BUILTIN_POLICIES
    missing_groups = custom_targets - group_names
    if missing_groups:
        raise ValueError(
            f"rules.yaml references undefined policy groups: {missing_groups}"
        )
    def reaches_direct(name: str, seen: set[str] | None = None) -> bool:
        seen = set() if seen is None else seen
        if name in seen:
            return False
        seen.add(name)
        for member in group_members[name]:
            if member == "DIRECT":
                return True
            if member in group_members and reaches_direct(member, seen):
                return True
        return False

    if reaches_direct("🎮 国际游戏"):
        raise ValueError("🎮 国际游戏 must not offer DIRECT, including transitively")


def validate_tree(root: Path = ROOT) -> int:
    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local_sources = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    lock = json.loads((root / "sources.lock.json").read_text(encoding="utf-8"))
    expected_paths = {
        entry["path"] for entry in list(sources.values()) + list(local_sources.values())
    }
    actual_paths = {str(path.relative_to(root)) for path in (root / "ruleset").glob("*.yaml")}
    if expected_paths != actual_paths:
        raise ValueError(f"ruleset file mismatch: missing={expected_paths-actual_paths}, extra={actual_paths-expected_paths}")
    for name, source in sources.items():
        data = (root / source["path"]).read_bytes()
        validate(name, data)
        digest = hashlib.sha256(data).hexdigest()
        if digest != lock["rulesets"][name]["sha256"]:
            raise ValueError(f"{name}: SHA-256 does not match sources.lock.json")
    for name, source in local_sources.items():
        data = (root / source["path"]).read_bytes()
        validate(name, data)
        rules = [
            line.strip()
            for line in data.decode("utf-8").splitlines()
            if line.strip().startswith("- ")
        ]
        if len(rules) != len(set(rules)):
            raise ValueError(f"{name}: local ruleset contains duplicate entries")
    validate_config_references(set(sources) | set(local_sources), root)
    from generate_catalog import generate
    generate(root)
    validate_siri_ai(root)
    print(
        f"Validated {len(sources)} mirrored rulesets/checksums "
        f"and {len(local_sources)} local rulesets."
    )
    return 0


def main() -> int:
    return validate_tree(ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
