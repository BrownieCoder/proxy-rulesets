"""Offline domain-only validation for opt-in exact public App entries."""

from __future__ import annotations

import json
from pathlib import Path

from generate_catalog import read_rules
from public_policy_groups import read_policy_group_model
from public_rules import read_routing_rules
from siri_ai import DomainRules, entries

_DOMAIN = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
_IP = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
_EARLIER = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "WeChatReading")
_LATER = ("SiriAI", "Apple", "Bilibili", "GlobalMedia", "ChinaMax")


def _normalize(rule: str) -> str:
    kind, sep, operand = rule.partition(",")
    # Mihomo's Go lowercase maps capital dotted I to a single lowercase i.
    return kind + sep + operand.replace("\u0130", "i").lower() if kind in _DOMAIN else rule


def validate_public_app(
    root: Path, *, provider: str, target: str, host: str, controls: tuple[str, ...]
) -> None:
    """Check one opt-in provider without applying stricter rules to legacy Apps."""
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if payload != [f"DOMAIN,{host}"]:
        raise ValueError(f"{provider} requires its reviewed exact host")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    ordered = [rule.split(",") for rule in read_routing_rules(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    for names, earlier in ((_EARLIER, True), (_LATER, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in _DOMAIN | _IP | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in _IP and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in _IP:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            # No IP or GeoIP inputs are inferred for these hostname probes.
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([_normalize(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([_normalize(label)])))

    def first_match(domain: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(domain)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    # Changes to the mirrored security lists may intentionally block this host.
    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    if first_match(host) not in allowed:
        raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = ("child." + host, "not" + host, host + ".example.org")
    for domain in (*controls, *shapes):
        if first_match(domain) != first_match(domain, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {domain}")
