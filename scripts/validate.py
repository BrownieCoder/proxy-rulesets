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
from siri_ai import entries  # noqa: E402

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
    ordered_rules = entries(root / "config" / "rules.yaml")

    def position(marker: str) -> int:
        count = ordered_rules.count(marker)
        if count == 0:
            raise ValueError(f"missing expected rule: {marker}")
        if count > 1:
            raise ValueError(f"duplicate expected rule: {marker}")
        return ordered_rules.index(marker)

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
    positions = [position(marker) for marker in ordered_markers]
    if positions != sorted(positions):
        raise ValueError("rules.yaml game/provider priority order is unsafe")
    if position("DOMAIN,fastcdn.hoyoverse.com,DIRECT") > positions[0]:
        raise ValueError("fastcdn.hoyoverse.com override must precede InternationalGaming")
    geoip_position = position("GEOIP,CN,DIRECT,no-resolve")
    if not positions[-2] < geoip_position < positions[-1]:
        raise ValueError("GEOIP CN fallback must be after GlobalMedia and before ChinaMax")

    gemini_position = position("RULE-SET,Gemini,♊ Gemini")
    google_position = position("RULE-SET,Google,🔎 Google")
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

    rednote = "RULE-SET,Xiaohongshu,📕 小红书 / REDnote"
    rednote_position = position(rednote)
    for marker in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                   "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(marker) > rednote_position:
            raise ValueError("Security and gaming rules must precede Xiaohongshu")
    for marker in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,Bilibili,📺 Bilibili",
                   "RULE-SET,GlobalMedia,🛰️ International-Global",
                   "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(marker) < rednote_position:
            raise ValueError("Xiaohongshu must precede broader providers")
    options = group_members.get("📕 小红书 / REDnote", [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("Xiaohongshu must default to DIRECT and retain a proxy option")


def validate_xiaohongshu(root: Path = ROOT) -> None:
    """Validate reviewed scope and real first-match domain precedence offline."""
    from siri_ai import DomainRules, entries
    reviewed = {"xiaohongshu.com", "rednote.com", "xhscdn.com", "xhscdn.net"}
    rules = entries(root / "ruleset/Xiaohongshu.yaml")
    if len(rules) != 4 or set(rules) != {f"DOMAIN-SUFFIX,{d}" for d in reviewed}:
        raise ValueError("Xiaohongshu must contain only the four reviewed first-party roots")
    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}
    ordered = entries(root / "config/rules.yaml")

    def route(domain: str, include_rednote: bool = True) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            if fields[0] == "RULE-SET":
                if fields[1] == "Xiaohongshu" and not include_rednote:
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif fields[0] == "MATCH":
                return "MATCH", fields[1]
            elif fields[0] in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return fields[0] + "," + fields[1], fields[2]
            elif fields[0] not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                # This model has no IP/process/port metadata. Fail explicitly
                # when a new rule kind requires semantics we cannot simulate.
                raise ValueError(f"Unsupported top-level rule in domain model: {fields[0]}")
        raise ValueError("Missing MATCH rule")

    for domain in reviewed | {"www.xiaohongshu.com", "creator.rednote.com",
                              "sns-webpic-qc.xhscdn.com", "sns-video-hw.xhscdn.net"}:
        current = route(domain)
        if current not in {("Xiaohongshu", "📕 小红书 / REDnote"),
                           ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}:
            raise ValueError(f"Xiaohongshu is shadowed by an earlier domain rule: {domain}: {current}")
    controls = {"example.org", "reddit.com", "guzzoni.apple.com", "hoyoverse.com",
                "fastcdn.hoyoverse.com", "hmma.baidu.com", "cloudflare.com"}
    controls |= {name for d in reviewed for name in ("not" + d, d + ".example.org")}
    for domain in controls:
        if route(domain) != route(domain, False):
            raise ValueError(f"Xiaohongshu changed non-target domain: {domain}")


def validate_amap(root: Path = ROOT) -> None:
    """Enforce the reviewed AMap scope and security-first routing offline."""
    from siri_ai import DomainRules
    reviewed = {"ditu.amap.com", "m.amap.com", "maps.amap.com",
                "mobile.amap.com", "restapi.amap.com", "webapi.amap.com"}
    rules = entries(root / "ruleset/Amap.yaml")
    if len(rules) != len(reviewed) or set(rules) != {f"DOMAIN,{d}" for d in reviewed}:
        raise ValueError("Amap must contain only the six reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    marker = "RULE-SET,Amap,🗺️ 高德地图"
    references = [rule for rule in ordered if rule.startswith("RULE-SET,Amap,")]
    if references != [marker]:
        raise ValueError("Amap must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Amap requires exactly one active rule: {rule}")
        return ordered.index(rule)

    amap_position = position(marker)
    for rule in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                 "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(rule) > amap_position:
            raise ValueError("Security and gaming rules must precede Amap")
    for rule in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,Bilibili,📺 Bilibili",
                 "RULE-SET,GlobalMedia,🛰️ International-Global",
                 "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(rule) < amap_position:
            raise ValueError("Amap must precede broader providers and GEOIP CN")

    _, groups = parse_policy_groups(root)
    options = groups.get("🗺️ 高德地图", [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    block = re.search(r'^  - name: "🗺️ 高德地图"\n((?:    .*\n|\s*\n)*)', group_text, re.MULTILINE)
    types = re.findall(r'^    type: (\S+)\s*$', block.group(1), re.MULTILINE) if block else []
    if types != ["select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("Amap must be a DIRECT-first select group with a manual proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}

    def route(domain: str) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in Amap domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    allowed = {("Amap", "🗺️ 高德地图"), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for domain in reviewed:
        current = route(domain)
        if current not in allowed:
            raise ValueError(f"Amap host shadowed by a non-security or incorrect policy: {domain}: {current}")


def validate_netease_music(root: Path = ROOT) -> None:
    """Enforce reviewed exact hosts and security-first routing in sync candidates."""
    from siri_ai import DomainRules

    reviewed = {"music.163.com", "st.music.163.com", "y.music.163.com",
                "s1.music.126.net", "s2.music.126.net", "p1.music.126.net",
                "p3.music.126.net", "p6.music.126.net"}
    rules = entries(root / "ruleset/NetEaseMusic.yaml")
    if len(rules) != len(reviewed) or set(rules) != {f"DOMAIN,{d}" for d in reviewed}:
        raise ValueError("NetEaseMusic must contain only the eight reviewed exact hosts")

    ordered = entries(root / "config/rules.yaml")
    target = "🎵 网易云音乐"
    marker = f"RULE-SET,NetEaseMusic,{target}"
    references = [rule for rule in ordered if rule.startswith("RULE-SET,NetEaseMusic,")]
    if references != [marker]:
        raise ValueError("NetEaseMusic must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        count = ordered.count(expected)
        if count != 1:
            raise ValueError(f"NetEaseMusic requires one active expected rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for expected in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                     "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(expected) > app_position:
            raise ValueError("Security and gaming rules must precede NetEaseMusic")
    for expected in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                     "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(expected) < app_position:
            raise ValueError("NetEaseMusic must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text()
    group = re.search(r'^  - name: "🎵 网易云音乐"\n(.*?)(?=^  - name: |\Z)',
                      group_text, re.MULTILINE | re.DOTALL)
    types = [] if group is None else [line.strip() for line in group.group(1).splitlines()
                                     if line.startswith("    type:")]
    if types != ["type: select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("NetEaseMusic must be DIRECT-first select with a manual proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}

    def route(domain: str, include_app: bool = True) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if fields[1] == "NetEaseMusic" and not include_app:
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    for domain in reviewed:
        current = route(domain)
        if current not in {("NetEaseMusic", target), ("Privacy", "REJECT"),
                           ("Hijacking", "🚫 Hijacking")}:
            raise ValueError(f"NetEaseMusic is shadowed by an earlier domain rule: {domain}: {current}")
    controls = {"163.com", "126.net", "reg.163.com", "mail.163.com", "example.org",
                "clientlog.music.163.com", "sentry.music.163.com"}
    controls |= {value for domain in reviewed for value in
                 ("child." + domain, "not" + domain, domain + ".example.org")}
    for domain in controls:
        if route(domain) != route(domain, False):
            raise ValueError(f"NetEaseMusic changed non-target domain: {domain}")


def validate_zhihu(root: Path = ROOT) -> None:
    """Enforce reviewed exact hosts, configurable egress and security-first routing."""
    from siri_ai import DomainRules
    reviewed = {"www.zhihu.com", "api.zhihu.com", "zhuanlan.zhihu.com", "static.zhihu.com",
                "static.zhimg.com", "pic1.zhimg.com", "pica.zhimg.com", "picx.zhimg.com"}
    rules = entries(root / "ruleset/Zhihu.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Zhihu must contain only the eight reviewed exact hosts, without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "💡 知乎"
    marker = "RULE-SET,Zhihu," + target
    references = [r for r in ordered if r.split(",")[:2] == ["RULE-SET", "Zhihu"]]
    if references != [marker]:
        raise ValueError("Zhihu must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Zhihu requires one active rule: {rule}")
        return ordered.index(rule)

    current_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= current_position:
            raise ValueError("Security and gaming rules must precede Zhihu")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current_position:
            raise ValueError("Zhihu must precede broader providers")
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    groups_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "💡 知乎"\n((?:(?!  - name:).*\n)*)', groups_text, re.MULTILINE)
    if (len(blocks) != 1 or not re.search(r'^    type: select\s*$', blocks[0], re.MULTILINE)
            or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options):
        raise ValueError("Zhihu must be a DIRECT-first select group with a proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}

    def route(domain: str, skip_zhihu: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_zhihu and fields[1] == "Zhihu":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return kind + "," + fields[1], fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError("Unsupported top-level rule in Zhihu domain model: " + kind)
        raise ValueError("Missing MATCH rule")

    allowed = {("Zhihu", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Zhihu is shadowed by an earlier rule: {host}: {result}")
    controls = {"zhihu.com", "zhimg.com", "zhihuishu.com", "cloudflare.com", "example.org",
                "www.xiaohongshu.com", "guzzoni.apple.com", "hoyoverse.com"}
    controls |= {h for host in reviewed for h in ("probe." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_zhihu=True):
            raise ValueError("Zhihu changed non-target routing: " + host)


def validate_douban(root: Path = ROOT) -> None:
    """Check exact Douban scope and effective routing in live or staged public trees."""
    from siri_ai import DomainRules

    reviewed = {"accounts.douban.com", "asset.doubanio.com", "book.douban.com",
                "img3.doubanio.com", "img9.doubanio.com", "m.douban.com",
                "movie.douban.com", "www.douban.com"}
    rules = entries(root / "ruleset/Douban.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Douban must contain only the eight reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "📚 豆瓣"
    marker = "RULE-SET,Douban," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Douban"]]
    if references != [marker]:
        raise ValueError("Douban must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Douban requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote"):
        if position(earlier) >= app_position:
            raise ValueError("Security, gaming and Xiaohongshu rules must precede Douban")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("Douban must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text()
    group = re.search(r'^  - name: "📚 豆瓣"\n(.*?)(?=^  - name: |\Z)',
                      group_text, re.MULTILINE | re.DOTALL)
    types = [] if group is None else [line.strip() for line in group.group(1).splitlines()
                                     if line.startswith("    type:")]
    if types != ["type: select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("Douban must be a DIRECT-first select group with a proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}

    def route(domain: str, skip_douban: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_douban and fields[1] == "Douban":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in Douban domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    for host in reviewed:
        current = route(host)
        if current not in {("Douban", target), ("Privacy", "REJECT"),
                           ("Hijacking", "🚫 Hijacking")}:
            raise ValueError(f"Douban is shadowed by an earlier rule: {host}: {current}")
    controls = {"douban.com", "doubanio.com", "api.douban.com", "music.douban.com",
                "douban.fm", "cloudflare.com", "www.xiaohongshu.com", "guzzoni.apple.com"}
    controls |= {value for host in reviewed for value in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_douban=True):
            raise ValueError("Douban changed non-target routing: " + host)


def validate_douyin(root: Path = ROOT) -> None:
    """Validate only evidenced Douyin website/static hosts, preserving security and TikTok."""
    from siri_ai import DomainRules
    reviewed = {"www.douyin.com", "lf-douyin-pc-web.douyinstatic.com",
                "sf1-cdn-tos.douyinstatic.com"}
    rules = entries(root / "ruleset/Douyin.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Douyin must contain only the three reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🎶 抖音"
    marker = "RULE-SET,Douyin," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Douyin"]]
    if references != [marker]:
        raise ValueError("Douyin must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Douyin requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= current:
            raise ValueError("Security and gaming rules must precede Douyin")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,TikTok,🎵 Tiktok",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Douyin must precede broader providers and TikTok")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🎶 抖音"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    types = [] if len(blocks) != 1 else re.findall(r'^    type: (\S+)\s*$', blocks[0], re.MULTILINE)
    if types != ["select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("Douyin must be a DIRECT-first select group with a proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}

    def route(domain: str, skip_douyin: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_douyin and fields[1] == "Douyin":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return kind + "," + fields[1], fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError("Unsupported top-level rule in Douyin domain model: " + kind)
        raise ValueError("Missing MATCH rule")

    allowed = {("Douyin", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Douyin is shadowed by an earlier rule: {host}: {result}")
    controls = {"douyin.com", "douyinstatic.com", "douyinvod.com", "live.douyin.com",
                "api.amemv.com", "v3-web.douyinvod.com", "v26-web.douyinvod.com",
                "www.tiktok.com", "p16-sign-va.tiktokcdn.com", "p16-va.tiktokcdn.com",
                "p16-sg.tiktokcdn.com", "p1.ibyteimg.com", "byteimg.com", "example.org"}
    controls |= {value for host in reviewed for value in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_douyin=True):
            raise ValueError("Douyin changed non-target routing: " + host)


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
    validate_xiaohongshu(root)
    validate_douban(root)
    validate_zhihu(root)
    validate_amap(root)
    validate_netease_music(root)
    validate_douyin(root)
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
