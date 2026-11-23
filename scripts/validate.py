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
from public_rules import parse_routing_rules  # noqa: E402
from public_policy_groups import read_policy_group_model  # noqa: E402

BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "PASS"}
QQ_MUSIC_CONTROLS = frozenset({
    "qq.com", "gtimg.com", "gtimg.cn", "qqmusic.com", "imgcache.qq.com",
    "dldir1.qq.com", "dldir1v6.qq.com", "dlied6.qq.com", "service.qq.com",
    "www.qq.com", "www.tencent.com", "hr.tencent.com", "adver.qq.com",
    "monitor.music.qq.com", "stat.y.qq.com", "game.qq.com", "wegame.gtimg.com",
    "music.163.com", "u.y.qq.com", "example.org",
})
DOUYIN_CONTROLS = frozenset({
    "douyin.com", "douyinstatic.com", "douyinvod.com", "live.douyin.com",
    "api.amemv.com", "v3-web.douyinvod.com", "v26-web.douyinvod.com",
    "www.tiktok.com", "p16-sign-va.tiktokcdn.com", "p16-va.tiktokcdn.com",
    "p16-sg.tiktokcdn.com", "p1.ibyteimg.com", "byteimg.com", "example.org",
})
PINDUODUO_CONTROLS = frozenset({
    "pinduoduo.com", "yangkeduo.com", "pddpic.com", "www.pinduoduo.com",
    "cdn.pinduoduo.com", "images.pinduoduo.com", "promotion.pddpic.com",
    "api.pinduoduo.com", "api.yangkeduo.com", "log.pinduoduo.com",
    "log.yangkeduo.com", "www.temu.com", "pftk.temu.com", "thtk.temu.com",
    "m.jd.com", "www.meituan.com", "www.douyin.com", "guzzoni.apple.com",
    "example.org",
})


def parse_policy_groups(root: Path = ROOT) -> tuple[set[str], dict[str, list[str]]]:
    """Read the project-owned policy-group template without a YAML dependency."""
    groups = read_policy_group_model(root / "config" / "proxy-groups.yaml")
    names = {group['name'] for group in groups}
    members = {group['name']: list(group.get('proxies', [])) for group in groups}
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
    for rule in parse_routing_rules(text):
        fields = rule.split(",")
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

    referenced = {fields[1] for rule in ordered_rules
                  if len(fields := rule.split(",")) >= 3 and fields[0] == "RULE-SET"}
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
    parse_policy_groups(root)
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
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    referenced = {rule.split(",")[1] for rule in ordered if rule.startswith("RULE-SET,")}
    missing = referenced - set(manifests)
    if missing:
        raise ValueError("Douyin routing references missing providers: " + ", ".join(sorted(missing)))
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
    controls = DOUYIN_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_douyin=True):
            raise ValueError("Douyin changed non-target routing: " + host)


def validate_qq_music(root: Path = ROOT) -> None:
    """Validate the three reviewed QQ Music hosts without widening shared Tencent scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules
    reviewed = {"y.qq.com", "c.y.qq.com", "dldir.y.qq.com"}
    rules = entries(root / "ruleset/QQMusic.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("QQMusic must contain only the three reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    for rule in ordered:
        kind = rule.split(",")[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in QQMusic domain model: " + kind)
    target = "🎧 QQ 音乐"
    marker = "RULE-SET,QQMusic," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "QQMusic"]]
    if references != [marker]:
        raise ValueError("QQMusic must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"QQMusic requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for rule in ordered[:current]:
        if rule.split(",")[0] in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("QQMusic domain-only model cannot validate preceding IP conditions: " + rule)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= current:
            raise ValueError("Security and gaming rules must precede QQMusic")
    for later in ("RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("QQMusic must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🎧 QQ 音乐"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = ("QQMusic must be a DIRECT-first select group with a proxy option; "
             "use supported simple select/type and proxies template syntax")
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    referenced = {rule.split(",")[1] for rule in ordered if rule.startswith("RULE-SET,")}
    missing = referenced - set(manifests)
    if missing:
        raise ValueError("QQMusic routing references missing providers: " + ", ".join(sorted(missing)))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}

    def route(domain: str, skip_qq_music: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_qq_music and fields[1] == "QQMusic":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return kind + "," + fields[1], fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError("Unsupported top-level rule in QQMusic domain model: " + kind)
        raise ValueError("Missing MATCH rule")

    allowed = {("QQMusic", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"QQMusic is shadowed by an earlier rule: {host}: {result}")
    controls = QQ_MUSIC_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_qq_music=True):
            raise ValueError("QQMusic changed non-target routing: " + host)


def validate_baidu_pan(root: Path = ROOT) -> None:
    """Check exact BaiduPan scope and effective routing in live or staged public trees."""
    from siri_ai import DomainRules

    reviewed = {"pan.baidu.com", "nd-static.bdstatic.com"}
    rules = entries(root / "ruleset/BaiduPan.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("BaiduPan must contain only the two reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "☁️ 百度网盘"
    marker = "RULE-SET,BaiduPan," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "BaiduPan"]]
    if references != [marker]:
        raise ValueError("BaiduPan must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"BaiduPan requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote"):
        if position(earlier) >= app_position:
            raise ValueError("Security, gaming and Xiaohongshu rules must precede BaiduPan")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("BaiduPan must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    group = re.search(r'^  - name: "☁️ 百度网盘"\n(.*?)(?=^  - name: |\Z)',
                      group_text, re.MULTILINE | re.DOTALL)
    types = [] if group is None else [line.strip() for line in group.group(1).splitlines()
                                     if line.startswith("    type:")]
    if types != ["type: select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("BaiduPan must be a DIRECT-first select group with a proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}

    def route(domain: str, skip_baidu_pan: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_baidu_pan and fields[1] == "BaiduPan":
                    continue
                if fields[1] not in providers:
                    raise ValueError(f"Unknown provider in rules.yaml: {fields[1]}")
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in BaiduPan domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    for host in reviewed:
        current = route(host)
        if current not in {("BaiduPan", target), ("Privacy", "REJECT"),
                           ("Hijacking", "🚫 Hijacking")}:
            raise ValueError(f"BaiduPan is shadowed by an earlier rule: {host}: {current}")
    controls = {"baidu.com", "bdstatic.com", "baidupcs.com", "www.baidu.com",
                "passport.baidu.com", "webpush.pan.baidu.com", "hm.baidu.com",
                "example.org", "guzzoni.apple.com", "www.douban.com"}
    controls |= {value for host in reviewed for value in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_baidu_pan=True):
            raise ValueError("BaiduPan changed non-target routing: " + host)


def validate_meituan(root: Path = ROOT) -> None:
    """Check reviewed public hosts and safe precedence in live or staged trees."""
    from siri_ai import DomainRules

    reviewed = {"www.meituan.com", "i.meituan.com", "waimai.meituan.com",
                "img.meituan.net", "p0.meituan.net", "p1.meituan.net", "s3plus.meituan.net"}
    rules = entries(root / "ruleset/Meituan.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Meituan must contain only the seven reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🍜 美团"
    marker = "RULE-SET,Meituan," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Meituan"]]
    if references != [marker]:
        raise ValueError("Meituan must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Meituan requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= app_position:
            raise ValueError("Security and gaming rules must precede Meituan")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("Meituan must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    group = re.search(r'^  - name: "🍜 美团"\n(.*?)(?=^  - name: |\Z)',
                      group_text, re.MULTILINE | re.DOTALL)
    types = [] if group is None else [line.strip() for line in group.group(1).splitlines()
                                     if line.startswith("    type:")]
    if types != ["type: select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("Meituan must be a DIRECT-first select group with a proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}
    for rule in ordered:
        fields = rule.split(",")
        if fields[0] == "RULE-SET" and fields[1] not in providers:
            raise ValueError(f"Meituan references undefined provider: {fields[1]}")

    def route(domain: str, skip_app: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_app and fields[1] == "Meituan":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in Meituan domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    for host in reviewed:
        current = route(host)
        if current not in {("Meituan", target), ("Privacy", "REJECT"),
                           ("Hijacking", "🚫 Hijacking")}:
            raise ValueError(f"Meituan is shadowed by an earlier rule: {host}: {current}")
    controls = {"meituan.com", "meituan.net", "sankuai.com", "www.dpfile.com",
                "www.dianping.com", "report.meituan.com", "analytics.meituan.net",
                "verify.meituan.com", "www.xiaohongshu.com", "guzzoni.apple.com"}
    controls |= {value for host in reviewed for value in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_app=True):
            raise ValueError("Meituan changed non-target routing: " + host)


def validate_jd(root: Path = ROOT) -> None:
    """Enforce the evidenced JD host and policy contract in public candidate trees."""
    from siri_ai import DomainRules

    reviewed = {"app.jd.com", "h5.m.jd.com", "img12.360buyimg.com",
                "img14.360buyimg.com", "img20.360buyimg.com", "m.360buyimg.com",
                "m.jd.com", "storage.360buyimg.com"}
    rules = entries(root / "ruleset/JD.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + d for d in reviewed}:
        raise ValueError("JD must contain only the eight reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🛒 京东"
    marker = "RULE-SET,JD," + target
    references = [r for r in ordered if r.split(",")[:2] == ["RULE-SET", "JD"]]
    if references != [marker]:
        raise ValueError("JD must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"JD requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= app_position:
            raise ValueError("Security and gaming rules must precede JD")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("JD must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    group = re.search(r'^  - name: "🛒 京东"\n(.*?)(?=^  - name: |\Z)',
                      group_text, re.MULTILINE | re.DOTALL)
    types = [] if group is None else [line.strip() for line in group.group(1).splitlines()
                                     if line.startswith("    type:")]
    if types != ["type: select"] or not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError("JD must be a DIRECT-first select group with a manual proxy option")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}
    for rule in ordered:
        fields = rule.split(",")
        if fields[0] == "RULE-SET" and fields[1] not in providers:
            raise ValueError(f"JD routing references missing provider: {fields[1]}")

    def route(domain: str, skip_jd: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_jd and fields[1] == "JD":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in JD domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    allowed = {("JD", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        current = route(host)
        if current not in allowed:
            raise ValueError(f"JD host shadowed by a non-security or incorrect policy: {host}: {current}")
    controls = {"jd.com", "360buyimg.com", "www.jd.com", "passport.jd.com",
                "api.m.jd.com", "m.jr.jd.com", "jdpay.com", "aliyun.com",
                "www.xiaohongshu.com", "guzzoni.apple.com", "hoyoverse.com"}
    controls |= {name for host in reviewed for name in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_jd=True):
            raise ValueError("JD changed non-target routing: " + host)


def validate_pinduoduo(root: Path = ROOT) -> None:
    """Enforce reviewed Pinduoduo exact hosts in live and staged public trees."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.yangkeduo.com", "mobile.yangkeduo.com", "commimg.pddpic.com",
                "img.pddpic.com", "t13img.yangkeduo.com"}
    rules = entries(root / "ruleset/Pinduoduo.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Pinduoduo must contain only the five reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🛍️ 拼多多"
    marker = "RULE-SET,Pinduoduo," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Pinduoduo"]]
    if references != [marker]:
        raise ValueError("Pinduoduo must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Pinduoduo requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,Douyin,🎶 抖音", "RULE-SET,Amap,🗺️ 高德地图",
                    "RULE-SET,Zhihu,💡 知乎", "RULE-SET,Xiaohongshu,📕 小红书 / REDnote",
                    "RULE-SET,NetEaseMusic,🎵 网易云音乐", "RULE-SET,Douban,📚 豆瓣",
                    "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘"):
        if position(earlier) >= app_position:
            raise ValueError("Security, gaming and existing App rules must precede Pinduoduo")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,Bilibili,📺 Bilibili", "RULE-SET,TikTok,🎵 Tiktok",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("Pinduoduo must precede SiriAI and broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🛍️ 拼多多"\n(.*?)(?=^  - name: |\Z)',
                        group_text, re.MULTILINE | re.DOTALL)
    group_error = "Pinduoduo must be a DIRECT-first select group with a manual proxy option"
    if len(blocks) != 1:
        raise ValueError(group_error)
    validate_select_group(blocks[0], group_error)
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError(group_error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    allowed_types = {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                     "GEOIP", "IP-CIDR", "IP-CIDR6"}
    for rule_index, rule in enumerate(ordered):
        fields = rule.split(",")
        if fields[0] not in allowed_types:
            raise ValueError("Unsupported top-level rule in Pinduoduo domain-only model: " + fields[0]
                             + "; process/port or compound conditions are intentionally rejected (fail closed)")
        if fields[0] in {"GEOIP", "IP-CIDR", "IP-CIDR6"} and rule_index < app_position:
            raise ValueError("Pinduoduo domain-only model limitation: IP/GeoIP rules before Pinduoduo "
                             "cannot be evaluated without IP metadata: " + rule)
        if fields[0] == "RULE-SET":
            if len(fields) < 3:
                raise ValueError("Pinduoduo encountered an incomplete RULE-SET reference")
            if fields[1] not in manifests:
                raise ValueError("Pinduoduo references undefined provider: " + fields[1])
    providers = {name: DomainRules(entries(root / source["path"]))
                 for name, source in manifests.items()}

    def route(domain: str, skip_app: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_app and fields[1] == "Pinduoduo":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # Only IP/GeoIP conditions remain; this domain-only model has no IP metadata.
        raise ValueError("Missing MATCH rule")

    allowed = {("Pinduoduo", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Pinduoduo is shadowed by an earlier rule: {host}: {result}")
    controls = PINDUODUO_CONTROLS | {value for host in reviewed for value in
                                   ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_app=True):
            raise ValueError("Pinduoduo changed non-target routing: " + host)


CTRIP_CONTROLS = {
    "ctrip.com", "c-ctrip.com", "trip.com", "tripcdn.com", "www.trip.com",
    "english.ctrip.com", "www.tieyou.com", "www.tujia.com", "my.ctrip.com",
    "sec.ctrip.com", "ct.ctrip.com", "s.c-ctrip.com", "webresource.c-ctrip.com",
    "static.tripcdn.com", "hm.baidu.com", "api.ctrip.com", "guzzoni.apple.com",
    "www.jd.com", "www.meituan.com", "example.org",
}


def validate_ctrip(root: Path = ROOT) -> None:
    """Enforce the exact official Ctrip entry scope in public candidate trees."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.ctrip.com", "m.ctrip.com", "app.ctrip.com", "hotels.ctrip.com",
                "flights.ctrip.com", "trains.ctrip.com", "vacations.ctrip.com"}
    rules = entries(root / "ruleset/Ctrip.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Ctrip must contain only the seven reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🧳 携程"
    marker = "RULE-SET,Ctrip," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Ctrip"]]
    if references != [marker]:
        raise ValueError("Ctrip must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Ctrip requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT"):
        if position(earlier) >= app_position:
            raise ValueError("Security and gaming rules must precede Ctrip")
    for later in ("RULE-SET,Apple,🍎 Apple", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("Ctrip must precede broader providers")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🧳 携程"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Ctrip must be a DIRECT-first select group with a manual proxy option"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Ctrip manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    missing = {rule.split(",")[1] for rule in ordered if rule.startswith("RULE-SET,")} - set(manifests)
    if missing:
        raise ValueError("Ctrip routing references missing providers: " + ", ".join(sorted(missing)))
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_ctrip: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_ctrip and fields[1] == "Ctrip":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"Unsupported top-level rule in Ctrip domain model: {kind}")
        raise ValueError("Missing MATCH rule")

    allowed = {("Ctrip", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        current = route(host)
        if current not in allowed:
            raise ValueError(f"Ctrip is shadowed by an earlier rule: {host}: {current}")
    controls = CTRIP_CONTROLS | {value for host in reviewed for value in
                               ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_ctrip=True):
            raise ValueError("Ctrip changed non-target routing: " + host)


def validate_taobao(root: Path = ROOT) -> None:
    """Enforce exact public Taobao entries in live and staged public trees."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.taobao.com", "m.taobao.com", "pc.taobao.com", "pcdetail.taobao.com"}
    rules = entries(root / "ruleset/Taobao.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Taobao must contain only the four reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🛍️ 淘宝"
    marker = "RULE-SET,Taobao," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Taobao"]]
    if references != [marker]:
        raise ValueError("Taobao must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Taobao requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,BaiduPan,☁️ 百度网盘"):
        if position(earlier) >= app_position:
            raise ValueError("Security, gaming and existing app rules must precede Taobao")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,Bilibili,📺 Bilibili", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("Taobao must precede broader providers and SiriAI")

    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    group_text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🛍️ 淘宝"\n(.*?)(?=^  - name: |\Z)',
                        group_text, re.MULTILINE | re.DOTALL)
    error = "Taobao must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text(encoding="utf-8")))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}
    for rule in ordered:
        fields = rule.split(",")
        if fields[0] == "RULE-SET" and fields[1] not in providers:
            raise ValueError(f"Taobao routing references missing provider: {fields[1]}")
        if fields[0] not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                             "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError(f"Unsupported top-level rule in Taobao domain model: {fields[0]}")

    def route(domain: str, skip_taobao: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_taobao and fields[1] == "Taobao":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # Remaining IP/GeoIP conditions fall through: this domain-only model has no IP metadata.
        raise ValueError("Missing MATCH rule")

    allowed = {("Taobao", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        current = route(host)
        if current not in allowed:
            raise ValueError(f"Taobao host shadowed by a non-security or incorrect policy: {host}: {current}")
    controls = {"taobao.com", "alicdn.com", "taobaocdn.com", "g.alicdn.com", "o.alicdn.com",
                "img.alicdn.com", "gw.alicdn.com", "g-search1.alicdn.com", "g-search2.alicdn.com",
                "g-search3.alicdn.com", "gm.mmstat.com", "log.mmstat.com", "res.mmstat.com",
                "dfhs.tanx.com", "ecpm.tanx.com", "login.taobao.com", "h5api.m.taobao.com",
                "www.tmall.com", "www.alipay.com", "goods.taobao.com", "bk.taobao.com",
                "item.taobao.com", "s.taobao.com",
                "www.jd.com", "guzzoni.apple.com", "fastcdn.hoyoverse.com", "example.org"}
    controls |= {name for host in reviewed for name in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_taobao=True):
            raise ValueError("Taobao changed non-target routing: " + host)


def validate_baidu_map(root: Path = ROOT) -> None:
    """Validate only evidenced Baidu Map hosts in live or staged public trees."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"map.baidu.com", "api.map.baidu.com", "webmap0.bdimg.com", "webmap1.bdimg.com"}
    rules = entries(root / "ruleset/BaiduMap.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("BaiduMap must contain only the four reviewed exact hosts without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🗺️ 百度地图"
    marker = "RULE-SET,BaiduMap," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "BaiduMap"]]
    if references != [marker]:
        raise ValueError("BaiduMap must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"BaiduMap requires one active rule: {expected}")
        return ordered.index(expected)

    app_position = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝"):
        if position(earlier) >= app_position:
            raise ValueError("Security, gaming and existing app rules must precede BaiduMap")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,Bilibili,📺 Bilibili", "RULE-SET,TikTok,🎵 Tiktok",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= app_position:
            raise ValueError("BaiduMap must precede broader providers and SiriAI")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🗺️ 百度地图"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "BaiduMap must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options or "🧭 Final" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("BaiduMap manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    allowed_types = {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                     "GEOIP", "IP-CIDR", "IP-CIDR6"}
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in allowed_types:
            raise ValueError("Unsupported top-level rule in BaiduMap domain-only model: " + kind)
        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} and index < app_position:
            raise ValueError("BaiduMap domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if len(fields) != 3:
                raise ValueError("BaiduMap encountered an unsupported RULE-SET reference: " + rule)
            if fields[1] not in manifests:
                raise ValueError("BaiduMap routing references missing provider: " + fields[1])
        elif kind == "MATCH" and len(fields) != 2:
            raise ValueError("BaiduMap encountered an unsupported MATCH rule: " + rule)
        elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"} and len(fields) != 3:
            raise ValueError("BaiduMap encountered an unsupported domain rule: " + rule)
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_baidu_map: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_baidu_map and fields[1] == "BaiduMap":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # This domain-only model does not evaluate IP/GeoIP conditions after the App rule.
        raise ValueError("Missing MATCH rule")

    allowed = {("BaiduMap", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        current = route(host)
        if current not in allowed:
            raise ValueError(f"BaiduMap host shadowed by a non-security or incorrect policy: {host}: {current}")
    controls = {"baidu.com", "bdimg.com", "bdstatic.com", "bcebos.com", "www.baidu.com",
                "ss0.bdstatic.com", "map-mobile-static.cdn.bcebos.com", "lbs.baidu.com",
                "lbsyun.baidu.com", "hm.baidu.com", "log.map.baidu.com",
                "mapopen-website-wiki.cdn.bcebos.com", "mapopen-docs-assets.bj.bcebos.com",
                "pan.baidu.com", "nd-static.bdstatic.com", "webapi.amap.com", "restapi.amap.com",
                "guzzoni.apple.com", "fastcdn.hoyoverse.com", "music.163.com", "example.org"}
    controls |= {name for host in reviewed for name in
                 ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_baidu_map=True):
            raise ValueError("BaiduMap changed non-target routing: " + host)


KUAISHOU_CONTROLS = frozenset({
    "kuaishou.com", "yximgs.com", "yximg.com", "kwimgs.com", "wskwai.com", "kwai.com",
    "static.yximgs.com", "s2-11673.kwimgs.com", "p1-plat.wskwai.com", "p2-plat.wskwai.com",
    "live.kuaishou.com", "liveopen.kuaishou.com", "cp.kuaishou.com", "jigou.kuaishou.com",
    "e.kuaishou.com", "tuiguang.kuaishou.com", "pay.ssl.kuaishou.com", "game.kuaishou.com",
    "klingai.kuaishou.com", "music.kuaishou.com", "www.acfun.cn", "www.kwaixiaodian.com",
    "www.kwai.com", "wlog.kuaishou.com", "www.douyin.com", "y.qq.com",
    "guzzoni.apple.com", "example.org",
})

def validate_kuaishou(root: Path = ROOT) -> None:
    """Validate only the two evidenced public Kuaishou entry hosts and their policy."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.kuaishou.com", "m.kuaishou.com"}
    rules = entries(root / "ruleset/Kuaishou.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Kuaishou must contain only the two reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "📹 快手"
    marker = "RULE-SET,Kuaishou," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Kuaishou"]]
    if references != [marker]:
        raise ValueError("Kuaishou must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"Kuaishou requires one active rule: {expected}")
        return ordered.index(expected)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing App rules must precede Kuaishou")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,Bilibili,📺 Bilibili", "RULE-SET,TikTok,🎵 Tiktok",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Kuaishou must precede SiriAI and broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "📹 快手"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Kuaishou must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options or "🧭 Final" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Kuaishou manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    allowed_types = {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                     "GEOIP", "IP-CIDR", "IP-CIDR6"}
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in allowed_types:
            raise ValueError("Kuaishou domain-only model limitation: unsupported top-level rule " + kind)
        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} and index < current:
            raise ValueError("Kuaishou domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if len(fields) < 3:
                raise ValueError("Kuaishou encountered an incomplete RULE-SET reference")
            if fields[1] not in manifests:
                raise ValueError("Kuaishou routing references missing provider: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_kuaishou: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_kuaishou and fields[1] == "Kuaishou":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # Only supported IP conditions remain; the model has no IP metadata.
        raise ValueError("Missing MATCH rule")

    allowed = {("Kuaishou", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Kuaishou is shadowed by an earlier rule: {host}: {result}")
    controls = KUAISHOU_CONTROLS | {value for host in reviewed for value in
                                  ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_kuaishou=True):
            raise ValueError("Kuaishou changed non-target routing: " + host)


TENCENT_VIDEO_CONTROLS = frozenset({
    "qq.com", "video.qq.com", "gtimg.com", "gtimg.cn", "qpic.cn",
    "vfiles.gtimg.cn", "vm.gtimg.cn", "midas.gtimg.cn", "tv.puui.qpic.cn",
    "puui.qpic.cn", "imgcache.qq.com", "dcm.qq.com", "dldir1.qq.com",
    "pbaccess.video.qq.com", "vd6.l.qq.com", "staticfile.qq.com",
    "res.ab.qq.com", "config.ab.qq.com", "cc.v.qq.com", "mp.v.qq.com",
    "y.qq.com", "c.y.qq.com", "dldir.y.qq.com", "game.qq.com", "wegame.gtimg.com",
    "iwan.video.qq.com", "iwan-s.video.qq.com", "iwan.qq.com", "stat.y.qq.com",
    "live.qq.com", "www.iqiyi.com", "www.youku.com", "example.org",
})

def validate_tencent_video(root: Path = ROOT) -> None:
    """Validate four exact public Tencent Video entries without widening shared Tencent scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules
    reviewed = {"v.qq.com", "m.v.qq.com", "film.qq.com", "film.video.qq.com"}
    rules = entries(root / "ruleset/TencentVideo.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("TencentVideo must contain only the four reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    for rule in ordered:
        kind = rule.split(",")[0]
        if kind == "RULE-SET" and len(rule.split(",")) < 3:
            raise ValueError("TencentVideo encountered an incomplete RULE-SET reference")
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in TencentVideo domain model: " + kind)
    target = "📺 腾讯视频"
    marker = "RULE-SET,TencentVideo," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "TencentVideo"]]
    if references != [marker]:
        raise ValueError("TencentVideo must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"TencentVideo requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for rule in ordered[:current]:
        if rule.split(",")[0] in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("TencentVideo domain-only model cannot validate preceding IP conditions: " + rule)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手"):
        if position(earlier) >= current:
            raise ValueError("Security and gaming rules and existing App rules must precede TencentVideo")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("TencentVideo must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "📺 腾讯视频"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = ("TencentVideo must be a DIRECT-first select group with proxy and Final options; "
             "use supported simple select/type and proxies template syntax")
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options or "🧭 Final" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        records = json.loads((root / filename).read_text(encoding="utf-8"))
        duplicates = set(manifests) & set(records)
        if duplicates:
            raise ValueError("TencentVideo manifests contain duplicate providers: " + ", ".join(sorted(duplicates)))
        manifests.update(records)
    referenced = {rule.split(",")[1] for rule in ordered if rule.startswith("RULE-SET,")}
    missing = referenced - set(manifests)
    if missing:
        raise ValueError("TencentVideo routing references missing providers: " + ", ".join(sorted(missing)))
    providers = {name: DomainRules(entries(root / item["path"]))
                 for name, item in manifests.items()}

    def route(domain: str, skip_tencent_video: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_tencent_video and fields[1] == "TencentVideo":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return kind + "," + fields[1], fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError("Unsupported top-level rule in TencentVideo domain model: " + kind)
        raise ValueError("Missing MATCH rule")

    allowed = {("TencentVideo", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"TencentVideo is shadowed by an earlier rule: {host}: {result}")
    controls = TENCENT_VIDEO_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_tencent_video=True):
            raise ValueError("TencentVideo changed non-target routing: " + host)


ALIPAN_CONTROLS = frozenset({
    "alipan.com", "aliyundrive.com", "aliyundrive.net", "alicdn.com", "aliyun.com",
    "api.alipan.com", "api.aliyundrive.com", "auth.aliyundrive.com", "cdn.aliyundrive.net",
    "pages.aliyundrive.com", "stg.aliyundrive.com", "g.alicdn.com", "img.alicdn.com",
    "appdownload.alicdn.com", "arms-retcode.aliyuncs.com", "retcode.alicdn.com",
    "pan.baidu.com", "nd-static.bdstatic.com", "www.taobao.com", "www.dingtalk.com",
    "guzzoni.apple.com", "fastcdn.hoyoverse.com", "example.org",
})

def validate_alipan(root: Path = ROOT) -> None:
    """Enforce the two evidenced public entries without expanding Alibaba shared scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.alipan.com", "www.aliyundrive.com"}
    rules = entries(root / "ruleset/AliPan.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("AliPan must contain only the two reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "📁 阿里云盘"
    marker = "RULE-SET,AliPan," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "AliPan"]]
    if references != [marker]:
        raise ValueError("AliPan must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"AliPan requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede AliPan")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("AliPan must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "📁 阿里云盘"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "AliPan must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("AliPan manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in AliPan domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field for field in fields[:required]):
            raise ValueError("AliPan domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("AliPan domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("AliPan routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_alipan: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_alipan and fields[1] == "AliPan":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("AliPan", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"AliPan is shadowed by an earlier rule: {host}: {result}")
    controls = ALIPAN_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_alipan=True):
            raise ValueError("AliPan changed non-target routing: " + host)


IQIYI_CONTROLS = frozenset({
    "iqiyi.com", "qiyi.com", "iqiyipic.com", "qy.net", "static.iqiyi.com",
    "mesh.if.iqiyi.com", "pic0.iqiyipic.com", "pic1.iqiyipic.com", "pic2.iqiyipic.com",
    "pic3.iqiyipic.com", "dl-static.iqiyi.com", "static-d.iqiyi.com", "mbdapp.iqiyi.com",
    "app.iqiyi.com", "privacy.iqiyi.com", "creator.iqiyi.com", "g.iqiyi.com",
    "game.iqiyi.com", "iq.com", "www.iq.com", "msg.qy.net", "apps.apple.com",
    "itunes.apple.com", "appgallery.huawei.com", "beian.miit.gov.cn",
    "v.qq.com", "m.v.qq.com", "film.qq.com", "film.video.qq.com",
    "y.qq.com", "c.y.qq.com", "dldir.y.qq.com", "www.bilibili.com",
    "www.youtube.com", "www.tiktok.com", "www.disneyplus.com", "www.netflix.com",
    "www.alipan.com", "www.aliyundrive.com", "guzzoni.apple.com",
    "fastcdn.hoyoverse.com", "example.org",
})


def validate_iqiyi(root: Path = ROOT) -> None:
    """Enforce the single evidenced iQIYI portal host and its restricted policy contract."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.iqiyi.com"}
    rules = entries(root / "ruleset/IQIYI.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("IQIYI must contain only the one reviewed exact host without duplicates")

    ordered = entries(root / "config/rules.yaml")
    target = "🎬 爱奇艺"
    marker = "RULE-SET,IQIYI," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "IQIYI"]]
    if references != [marker]:
        raise ValueError("IQIYI must have exactly one dedicated policy reference")

    def position(expected: str) -> int:
        if ordered.count(expected) != 1:
            raise ValueError(f"IQIYI requires one active rule: {expected}")
        return ordered.index(expected)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede IQIYI")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("IQIYI must precede broader providers and SiriAI")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🎬 爱奇艺"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "IQIYI must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if not options or options[0] != "DIRECT" or "🚀 节点选择" not in options or "🧭 Final" not in options:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("IQIYI manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in IQIYI domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("IQIYI domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("IQIYI domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET" and fields[1] not in manifests:
            raise ValueError("IQIYI routing references missing provider: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_iqiyi: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_iqiyi and fields[1] == "IQIYI":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # Supported IP conditions after this App remain outside the domain-only model.
        raise ValueError("Missing MATCH rule")

    allowed = {("IQIYI", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"IQIYI host shadowed by a non-security or incorrect policy: {host}: {result}")
    controls = IQIYI_CONTROLS | {value for host in reviewed for value in
                               ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_iqiyi=True):
            raise ValueError("IQIYI changed non-target routing: " + host)


XIANYU_CONTROLS = frozenset({
    "goofish.cn", "h5.m.goofish.com", "m.goofish.com", "api.goofish.com",
    "alicdn.com", "g.alicdn.com", "gw.alicdn.com", "img.alicdn.com", "o.alicdn.com",
    "terms.alicdn.com", "gm.mmstat.com", "log.mmstat.com", "taobao.com", "www.taobao.com",
    "login.taobao.com", "h5api.m.taobao.com", "alipay.com", "www.alipay.com",
    "www.alipan.com", "pan.baidu.com", "map.baidu.com", "www.kuaishou.com",
    "v.qq.com", "www.jd.com", "guzzoni.apple.com", "fastcdn.hoyoverse.com", "example.org",
})


def validate_xianyu(root: Path = ROOT) -> None:
    """Enforce three official public Xianyu entries without expanding shared Alibaba scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"goofish.com", "www.goofish.com", "terms.goofish.com"}
    rules = entries(root / "ruleset/Xianyu.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Xianyu must contain only the three reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🐟 闲鱼"
    marker = "RULE-SET,Xianyu," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Xianyu"]]
    if references != [marker]:
        raise ValueError("Xianyu must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Xianyu requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Xianyu")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Xianyu must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🐟 闲鱼"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Xianyu must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Xianyu manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Xianyu domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Xianyu domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Xianyu domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Xianyu routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_xianyu: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_xianyu and fields[1] == "Xianyu":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Xianyu", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Xianyu is shadowed by an earlier rule: {host}: {result}")
    controls = XIANYU_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_xianyu=True):
            raise ValueError("Xianyu changed non-target routing: " + host)


RAILWAY_12306_CONTROLS = frozenset({
    "12306.cn", "mobile.12306.cn", "95306.cn", "www.95306.cn",
    "g.alicdn.com", "www.taobao.com", "www.alipay.com", "www.alipan.com",
    "www.jd.com", "www.meituan.com", "www.pinduoduo.com", "www.ctrip.com",
    "pan.baidu.com", "map.baidu.com", "restapi.amap.com", "www.zhihu.com", "www.douban.com",
    "www.xiaohongshu.com", "www.kuaishou.com", "v.qq.com", "y.qq.com", "music.163.com",
    "www.douyin.com", "www.bilibili.com", "guzzoni.apple.com", "fastcdn.hoyoverse.com",
    "wlog.kuaishou.com", "msg.qy.net", "example.org",
})


def validate_railway_12306(root: Path = ROOT) -> None:
    """Enforce only the three evidenced Railway12306 public entry hosts."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.12306.cn", "kyfw.12306.cn", "dynamic.12306.cn"}
    rules = entries(root / "ruleset/Railway12306.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Railway12306 must contain only the three reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🚄 铁路12306"
    marker = "RULE-SET,Railway12306," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Railway12306"]]
    if references != [marker]:
        raise ValueError("Railway12306 must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Railway12306 requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Railway12306")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Railway12306 must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🚄 铁路12306"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Railway12306 must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Railway12306 manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Railway12306 domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Railway12306 domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Railway12306 domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Railway12306 routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_railway_12306: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_railway_12306 and fields[1] == "Railway12306":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Railway12306", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Railway12306 is shadowed by an earlier rule: {host}: {result}")
    controls = RAILWAY_12306_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_railway_12306=True):
            raise ValueError("Railway12306 changed non-target routing: " + host)


YOUKU_CONTROLS = frozenset({
    "youku.com", "m.youku.com", "v.youku.com", "t.youku.com", "acg.youku.com",
    "jingrui-ai-competition.youku.com", "ykimg.com", "alicdn.com", "aliyun.com",
    "g.alicdn.com", "img.alicdn.com", "gw.alicdn.com", "ykimg.alicdn.com",
    "liangcang-material.alicdn.com", "qzs.gdtimg.com", "wy.668wan.com",
    "www.youku.tv", "www.kumiao.com", "api.youku.com", "ups.youku.com",
    "www.taobao.com", "www.alipan.com", "v.qq.com", "www.kuaishou.com",
    "www.iqiyi.com", "game.qq.com", "guzzoni.apple.com", "fastcdn.hoyoverse.com",
    "example.org",
})

def validate_youku(root: Path = ROOT) -> None:
    """Enforce the one evidenced public entry without expanding shared Alibaba scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.youku.com"}
    rules = entries(root / "ruleset/Youku.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Youku must contain only the one reviewed exact host without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🎞️ 优酷"
    marker = "RULE-SET,Youku," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Youku"]]
    if references != [marker]:
        raise ValueError("Youku must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Youku requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Youku")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Youku must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🎞️ 优酷"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Youku must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Youku manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Youku domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Youku domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Youku domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Youku routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_youku: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_youku and fields[1] == "Youku":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Youku", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Youku is shadowed by an earlier rule: {host}: {result}")
    controls = YOUKU_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_youku=True):
            raise ValueError("Youku changed non-target routing: " + host)


WPS_OFFICE_CONTROLS = frozenset({
    "wps.cn", "wpscdn.cn", "kdocs.cn", "365.wps.cn", "ai.wps.cn", "comate.wps.cn",
    "docer.wps.cn", "www.kdocs.cn", "ep.wps.cn", "mo.wps.cn", "helpdesk.wps.cn",
    "open.wps.cn", "bbs.wps.cn", "vip.wps.cn", "aippt.wps.cn", "rili.wps.cn",
    "qn.cache.wpscdn.cn", "kdocs-om.wpscdn.cn", "volcengine-kdocs-cache.wpscdn.cn",
    "www.iciba.com", "www.lingxi.cn", "www.kimxz.com", "www.wpspdf.cn",
    "www.dingtalk.com", "www.feishu.cn", "www.youku.com", "www.iqiyi.com",
    "www.goofish.com", "www.12306.cn", "www.taobao.com", "www.alipan.com",
    "www.jd.com", "www.meituan.com", "www.ctrip.com", "www.pinduoduo.com",
    "pan.baidu.com", "map.baidu.com", "www.zhihu.com", "www.douban.com",
    "www.xiaohongshu.com", "www.kuaishou.com", "v.qq.com", "y.qq.com",
    "music.163.com", "www.douyin.com", "guzzoni.apple.com", "fastcdn.hoyoverse.com",
    "hoyoverse.com", "hmma.baidu.com", "app.datadoghq.com", "api.anthropic.com", "example.org",
})


def validate_wps_office(root: Path = ROOT) -> None:
    """Enforce only four evidenced public WPS Office product entry hosts."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.wps.cn", "platform.wps.cn", "mac.wps.cn", "linux.wps.cn"}
    rules = entries(root / "ruleset/WPSOffice.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("WPSOffice must contain only the four reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "📝 WPS Office"
    marker = "RULE-SET,WPSOffice," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "WPSOffice"]]
    if references != [marker]:
        raise ValueError("WPSOffice must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"WPSOffice requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede WPSOffice")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix", "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("WPSOffice must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "📝 WPS Office"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "WPSOffice must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("WPSOffice manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in WPSOffice domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("WPSOffice domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("WPSOffice domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET" and fields[1] not in manifests:
            raise ValueError("WPSOffice routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_wps_office: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_wps_office and fields[1] == "WPSOffice":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # Later IP/GeoIP conditions have no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("WPSOffice", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"WPSOffice is shadowed by an earlier rule: {host}: {result}")
    controls = WPS_OFFICE_CONTROLS | {value for host in reviewed for value in
                                   ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_wps_office=True):
            raise ValueError("WPSOffice changed non-target routing: " + host)


FEISHU_CONTROLS = frozenset({
    "feishu.cn", "www.larksuite.com", "larksuite.com", "apps.apple.com",
    "y.qq.com", "www.douyin.com", "restapi.amap.com", "www.zhihu.com",
    "www.xiaohongshu.com", "music.163.com", "www.douban.com", "www.jd.com",
    "www.meituan.com", "pan.baidu.com", "www.ctrip.com", "www.pinduoduo.com",
    "www.taobao.com", "map.baidu.com", "www.kuaishou.com", "v.qq.com", "m.v.qq.com",
    "www.alipan.com", "www.aliyundrive.com", "www.iqiyi.com", "goofish.com",
    "www.goofish.com", "terms.goofish.com", "www.12306.cn", "kyfw.12306.cn",
    "dynamic.12306.cn", "www.youku.com", "guzzoni.apple.com", "msg.qy.net",
    "hmma.baidu.com", "fastcdn.hoyoverse.com", "hoyoverse.com", "game.qq.com",
    "www.bilibili.com", "www.youtube.com", "www.tiktok.com", "www.netflix.com",
    "www.disneyplus.com", "www.google.com", "www.microsoft.com", "www.datadoghq.com",
    "example.org",
})


def validate_feishu(root: Path = ROOT) -> None:
    """Enforce one Feishu entry without expanding international or tenant scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.feishu.cn"}
    rules = entries(root / "ruleset/Feishu.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Feishu must contain only the one reviewed exact host without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "💼 飞书"
    marker = "RULE-SET,Feishu," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Feishu"]]
    if references != [marker]:
        raise ValueError("Feishu must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Feishu requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Feishu")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Feishu must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "💼 飞书"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Feishu must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Feishu manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Feishu domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Feishu domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Feishu domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Feishu routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_feishu: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_feishu and fields[1] == "Feishu":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Feishu", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Feishu is shadowed by an earlier rule: {host}: {result}")
    controls = FEISHU_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_feishu=True):
            raise ValueError("Feishu changed non-target routing: " + host)


DINGTALK_CONTROLS = frozenset({
    "dingtalk.com", "gw.alicdn.com", "img.alicdn.com", "cloud.video.taobao.com",
    "alicdn.com", "taobao.com", "www.taobao.com", "www.alipan.com",
    "www.goofish.com", "www.youku.com", "www.feishu.cn", "work.weixin.qq.com",
    "guzzoni.apple.com", "fastcdn.hoyoverse.com", "generativelanguage.googleapis.com",
    "app.datadoghq.com", "example.org",
})

def validate_dingtalk(root: Path = ROOT) -> None:
    """Enforce the one evidenced public entry without expanding shared Alibaba scope."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.dingtalk.com"}
    rules = entries(root / "ruleset/DingTalk.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("DingTalk must contain only the one reviewed exact host without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "💬 钉钉"
    marker = "RULE-SET,DingTalk," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "DingTalk"]]
    if references != [marker]:
        raise ValueError("DingTalk must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"DingTalk requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede DingTalk")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix", "RULE-SET,Gemini,♊ Gemini",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("DingTalk must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "💬 钉钉"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "DingTalk must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("DingTalk manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in DingTalk domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("DingTalk domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("DingTalk domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("DingTalk routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_dingtalk: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_dingtalk and fields[1] == "DingTalk":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("DingTalk", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"DingTalk is shadowed by an earlier rule: {host}: {result}")
    controls = DINGTALK_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_dingtalk=True):
            raise ValueError("DingTalk changed non-target routing: " + host)

QUARK_CONTROLS = frozenset({
    'quark.cn', 'sm.cn', 'alicdn.com', 'www.myquark.cn',
    'scan.quark.cn', 'talent.quark.cn', 'blm.sm.cn', 'img.alicdn.com',
    'g.alicdn.com', 'api.quark.cn', 'api-drive.quark.cn', 'www.uc.cn',
    'www.baidu.com', 'www.google.com', 'www.dingtalk.com', 'www.feishu.cn',
    'www.wps.cn', 'www.iqiyi.com', 'www.youku.com', 'www.goofish.com',
    'www.12306.cn', 'www.alipan.com', 'www.aliyundrive.com', 'v.qq.com',
    'apps.apple.com', 'guzzoni.apple.com', 'fastcdn.hoyoverse.com', 'api.anthropic.com',
    'app.datadoghq.com', 'api.datadoghq.com', 'agent-http-intake.logs.datadoghq.com', 'example.org',
})

def validate_quark(root: Path = ROOT) -> None:
    """Enforce two public Quark entry hosts without absorbing shared resources."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.quark.cn", "pan.quark.cn"}
    rules = entries(root / "ruleset/Quark.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Quark must contain only the two reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🔍 夸克"
    marker = "RULE-SET,Quark," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Quark"]]
    if references != [marker]:
        raise ValueError("Quark must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Quark requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Quark")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,Gemini,♊ Gemini", "RULE-SET,Google,🔎 Google",
                  "RULE-SET,Microsoft,🪟 Microsoft",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Quark must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🔍 夸克"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Quark must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Quark manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Quark domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Quark domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Quark domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Quark routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_quark: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_quark and fields[1] == "Quark":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Quark", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Quark is shadowed by an earlier rule: {host}: {result}")
    controls = QUARK_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_quark=True):
            raise ValueError("Quark changed non-target routing: " + host)


BOSS_ZHIPIN_CONTROLS = frozenset({
    "zhipin.com", "bosszhipin.com", "kanzhun.com", "about.zhipin.com",
    "ir.zhipin.com", "static.zhipin.com", "img.bosszhipin.com",
    "youle.zhipin.com", "hi.zhipin.com", "gongyi.zhipin.com",
    "www.dianzhangzhipin.com", "www.offertoday.com", "www.quark.cn",
    "pan.quark.cn", "www.feishu.cn", "www.dingtalk.com", "www.wps.cn",
    "weixin.qq.com", "weibo.com", "www.sf-express.com", "guzzoni.apple.com",
    "fastcdn.hoyoverse.com", "hmma.baidu.com", "example.org",
})


def validate_boss_zhipin(root: Path = ROOT) -> None:
    """Validate only the evidenced BOSS Zhipin homepage and public app landing host."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.zhipin.com", "app.zhipin.com"}
    rules = entries(root / "ruleset/BossZhipin.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("BossZhipin must contain only the two reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "💼 BOSS直聘"
    marker = "RULE-SET,BossZhipin," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "BossZhipin"]]
    if references != [marker]:
        raise ValueError("BossZhipin must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"BossZhipin requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷",
                    "RULE-SET,WPSOffice,📝 WPS Office", "RULE-SET,Feishu,💼 飞书",
                    "RULE-SET,DingTalk,💬 钉钉", "RULE-SET,Quark,🔍 夸克"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede BossZhipin")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,Gemini,♊ Gemini", "RULE-SET,Google,🔎 Google",
                  "RULE-SET,Microsoft,🪟 Microsoft",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("BossZhipin must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "💼 BOSS直聘"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "BossZhipin must be a DIRECT-first select group with exactly the manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if options != ["DIRECT", "🚀 节点选择", "🧭 Final"]:
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("BossZhipin manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in BossZhipin domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("BossZhipin domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("BossZhipin domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("BossZhipin routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_boss_zhipin: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_boss_zhipin and fields[1] == "BossZhipin":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("BossZhipin", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"BossZhipin is shadowed by an earlier rule: {host}: {result}")
    controls = BOSS_ZHIPIN_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_boss_zhipin=True):
            raise ValueError("BossZhipin changed non-target routing: " + host)


WECHAT_CONTROLS = frozenset({
    "qq.com", "wx.qq.com", "wechat.com",
    "www.wechat.com", "www.weixin.qq.com", "ad.weixin.qq.com",
    "car.weixin.qq.com", "channels.weixin.qq.com", "cover.weixin.qq.com",
    "developers.weixin.qq.com", "filehelper.weixin.qq.com", "fuwu.weixin.qq.com",
    "game.weixin.qq.com", "iot.weixin.qq.com", "kids.weixin.qq.com",
    "linux.weixin.qq.com", "mac.weixin.qq.com", "mp.weixin.qq.com",
    "open.weixin.qq.com", "openai.weixin.qq.com", "pay.weixin.qq.com",
    "pc.weixin.qq.com", "search.weixin.qq.com", "sticker.weixin.qq.com",
    "store.weixin.qq.com", "work.weixin.qq.com", "z.weixin.qq.com",
    "kf.qq.com", "weixin110.qq.com", "wechat.design",
    "www.tencent.com", "res.wx.qq.com", "res.wxqcloud.qq.com.cn",
    "y.qq.com", "v.qq.com", "beacon.qq.com",
    "www.douyin.com", "restapi.amap.com", "www.zhihu.com",
    "www.xiaohongshu.com", "music.163.com", "www.douban.com",
    "www.jd.com", "www.meituan.com", "pan.baidu.com",
    "www.ctrip.com", "www.pinduoduo.com", "www.taobao.com",
    "map.baidu.com", "www.kuaishou.com", "www.alipan.com",
    "www.iqiyi.com", "www.goofish.com", "www.12306.cn",
    "www.youku.com", "www.wps.cn", "www.feishu.cn",
    "www.dingtalk.com", "www.quark.cn", "guzzoni.apple.com",
    "fastcdn.hoyoverse.com", "api.anthropic.com", "app.datadoghq.com",
    "example.org"
})

def validate_wechat(root: Path = ROOT) -> None:
    """Enforce the single official WeChat portal without absorbing other Tencent hosts."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"weixin.qq.com"}
    rules = entries(root / "ruleset/WeChat.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("WeChat must contain only the one reviewed exact host without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "💬 微信"
    marker = "RULE-SET,WeChat," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "WeChat"]]
    if references != [marker]:
        raise ValueError("WeChat must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"WeChat requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷",
                    "RULE-SET,WPSOffice,📝 WPS Office", "RULE-SET,Feishu,💼 飞书",
                    "RULE-SET,DingTalk,💬 钉钉", "RULE-SET,Quark,🔍 夸克"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede WeChat")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,Gemini,♊ Gemini", "RULE-SET,Google,🔎 Google",
                  "RULE-SET,Microsoft,🪟 Microsoft",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("WeChat must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "💬 微信"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "WeChat must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("WeChat manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in WeChat domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("WeChat domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("WeChat domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("WeChat routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_wechat: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_wechat and fields[1] == "WeChat":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("WeChat", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"WeChat is shadowed by an earlier rule: {host}: {result}")
    controls = WECHAT_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_wechat=True):
            raise ValueError("WeChat changed non-target routing: " + host)


SF_EXPRESS_CONTROLS = frozenset({
    "sf-express.com", "www-static.sf-express.com", "www.sf-international.com",
    "sf-international.com", "www.sf-laas.com", "www.sf-airlines.com",
    "www.wps.cn", "platform.wps.cn", "mac.wps.cn", "linux.wps.cn",
    "www.feishu.cn", "www.dingtalk.com", "www.quark.cn", "pan.quark.cn",
    "www.goofish.com", "www.youku.com", "www.12306.cn", "www.taobao.com",
    "www.alipan.com", "www.meituan.com", "pan.baidu.com",
    "guzzoni.apple.com", "fastcdn.hoyoverse.com", "hoyoverse.com", "hmma.baidu.com",
    "generativelanguage.googleapis.com", "app.datadoghq.com", "api.anthropic.com", "example.org",
})

def validate_sf_express(root: Path = ROOT) -> None:
    """Enforce one public portal without expanding resources or other group businesses."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"www.sf-express.com"}
    rules = entries(root / "ruleset/SFExpress.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("SFExpress must contain only the one reviewed exact host without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "📦 顺丰速运"
    marker = "RULE-SET,SFExpress," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "SFExpress"]]
    if references != [marker]:
        raise ValueError("SFExpress must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"SFExpress requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷",
                    "RULE-SET,WPSOffice,📝 WPS Office", "RULE-SET,Feishu,💼 飞书",
                    "RULE-SET,DingTalk,💬 钉钉", "RULE-SET,Quark,🔍 夸克"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede SFExpress")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix", "RULE-SET,Gemini,♊ Gemini",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("SFExpress must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "📦 顺丰速运"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "SFExpress must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("SFExpress manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in SFExpress domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("SFExpress domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("SFExpress domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("SFExpress routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_sf_express: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_sf_express and fields[1] == "SFExpress":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("SFExpress", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"SFExpress is shadowed by an earlier rule: {host}: {result}")
    controls = SF_EXPRESS_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_sf_express=True):
            raise ValueError("SFExpress changed non-target routing: " + host)



WEIBO_CONTROLS = frozenset({
    'm.weibo.cn', 'weibo.cn', 'm.weibo.com', 'visitor.passport.weibo.cn',
    'passport.weibo.com', 'api.weibo.com', 'd.weibo.com', 's.weibo.com',
    'vip.weibo.com', 'photo.weibo.com', 'game.weibo.com', 'data.weibo.com',
    'kefu.weibo.com', 'new.vip.weibo.cn', 'ir.weibo.com',
    'sina.com.cn', 'www.sina.com.cn', 'sinaimg.cn', 'wx1.sinaimg.cn',
    'tva1.sinaimg.cn', 'h5.sinaimg.cn', 'sinajs.cn', 'js.t.sinajs.cn', 'weibocdn.com',
    'www.wps.cn', 'www.feishu.cn', 'www.dingtalk.com', 'www.quark.cn', 'pan.quark.cn',
    'www.youku.com', 'www.xiaohongshu.com', 'www.bilibili.com', 'www.google.com',
    'guzzoni.apple.com', 'hmma.baidu.com', 'fastcdn.hoyoverse.com',
    'app.datadoghq.com', 'example.org',
})


def validate_weibo(root: Path = ROOT) -> None:
    """Enforce two public Weibo entries without absorbing visitor or Sina resources."""
    from app_policy import validate_select_group
    from siri_ai import DomainRules

    reviewed = {"weibo.com", "www.weibo.com"}
    rules = entries(root / "ruleset/Weibo.yaml")
    if len(rules) != len(reviewed) or set(rules) != {"DOMAIN," + host for host in reviewed}:
        raise ValueError("Weibo must contain only the two reviewed exact hosts without duplicates")
    ordered = entries(root / "config/rules.yaml")
    target = "🟠 微博"
    marker = "RULE-SET,Weibo," + target
    references = [rule for rule in ordered if rule.split(",")[:2] == ["RULE-SET", "Weibo"]]
    if references != [marker]:
        raise ValueError("Weibo must have exactly one dedicated policy reference")

    def position(rule: str) -> int:
        if ordered.count(rule) != 1:
            raise ValueError(f"Weibo requires one active rule: {rule}")
        return ordered.index(rule)

    current = position(marker)
    for earlier in ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                    "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT",
                    "RULE-SET,QQMusic,🎧 QQ 音乐", "RULE-SET,Douyin,🎶 抖音",
                    "RULE-SET,Amap,🗺️ 高德地图", "RULE-SET,Zhihu,💡 知乎",
                    "RULE-SET,Xiaohongshu,📕 小红书 / REDnote", "RULE-SET,NetEaseMusic,🎵 网易云音乐",
                    "RULE-SET,Douban,📚 豆瓣", "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
                    "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
                    "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
                    "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
                    "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
                    "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
                    "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷",
                    "RULE-SET,WPSOffice,📝 WPS Office", "RULE-SET,Feishu,💼 飞书",
                    "RULE-SET,DingTalk,💬 钉钉", "RULE-SET,Quark,🔍 夸克"):
        if position(earlier) >= current:
            raise ValueError("Security, gaming and existing app rules must precede Weibo")
    for later in ("RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
                  "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
                  "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
                  "RULE-SET,Netflix,🎞️ Netflix",
                  "RULE-SET,Gemini,♊ Gemini", "RULE-SET,Google,🔎 Google",
                  "RULE-SET,Microsoft,🪟 Microsoft",
                  "RULE-SET,GlobalMedia,🛰️ International-Global",
                  "GEOIP,CN,DIRECT,no-resolve", "RULE-SET,ChinaMax,🇨🇳 China-Global"):
        if position(later) <= current:
            raise ValueError("Weibo must precede broader providers")

    text = (root / "config/proxy-groups.yaml").read_text(encoding="utf-8")
    blocks = re.findall(r'^  - name: "🟠 微博"\n(.*?)(?=^  - name: |\Z)',
                        text, re.MULTILINE | re.DOTALL)
    error = "Weibo must be a DIRECT-first select group with manual proxy and Final options"
    if len(blocks) != 1:
        raise ValueError(error)
    validate_select_group(blocks[0], error)
    _, members = parse_policy_groups(root)
    options = members.get(target, [])
    if (not options or options[0] != "DIRECT"
            or "🚀 节点选择" not in options or "🧭 Final" not in options):
        raise ValueError(error)

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        collisions = set(manifests) & set(loaded)
        if collisions:
            raise ValueError("Weibo manifests contain duplicate providers: " + ", ".join(sorted(collisions)))
        manifests.update(loaded)
    for index, rule in enumerate(ordered):
        fields = rule.split(",")
        kind = fields[0]
        if kind not in {"RULE-SET", "MATCH", "DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD",
                        "GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Unsupported top-level rule in Weibo domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = (len(fields) in {3, 4} and (len(fields) == 3 or fields[3] == "no-resolve")
                        if kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"} else len(fields) == required)
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Weibo domain-only model requires complete supported rules: " + kind)
        if index < current and kind in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
            raise ValueError("Weibo domain-only model cannot validate preceding IP conditions: " + rule)
        if kind == "RULE-SET":
            if fields[1] not in manifests:
                raise ValueError("Weibo routing references missing providers: " + fields[1])
    providers = {name: DomainRules(entries(root / item["path"])) for name, item in manifests.items()}

    def route(domain: str, skip_weibo: bool = False) -> tuple[str, str]:
        for rule in ordered:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_weibo and fields[1] == "Weibo":
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return ",".join(fields[:2]), fields[2]
            # IP/GeoIP is only allowed after this App and has no domain-only verdict.
        raise ValueError("Missing MATCH rule")

    allowed = {("Weibo", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in reviewed:
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Weibo is shadowed by an earlier rule: {host}: {result}")
    controls = WEIBO_CONTROLS | {value for host in reviewed for value in
                                ("child." + host, "not" + host, host + ".example.org")}
    for host in controls:
        if route(host) != route(host, skip_weibo=True):
            raise ValueError("Weibo changed non-target routing: " + host)


TENCENT_QQ_CONTROLS = frozenset({
    "qq.com", "www.qq.com", "child.im.qq.com", "notim.qq.com", "im.qq.com.example.org",
    "v.qq.com", "y.qq.com", "music.qq.com", "weixin.qq.com", "game.qq.com",
    "mail.qq.com", "qzone.qq.com", "qun.qq.com", "connect.qq.com", "ssl.ptlogin2.qq.com",
    "dldir1.qq.com", "imgcache.qq.com", "gtimg.com", "gtimg.cn", "www.tencent.com",
    "weibo.com", "www.bilibili.com", "guzzoni.apple.com", "hmma.baidu.com",
    "fastcdn.hoyoverse.com", "example.org",
})


def validate_tencent_qq(root: Path = ROOT) -> None:
    """Protect the QQ public site without taking over the shared Tencent namespace."""
    from siri_ai import DomainRules

    provider = "TencentQQ"
    host = "im.qq.com"
    target = "🐧 腾讯 QQ"
    if entries(root / "ruleset/TencentQQ.yaml") != ["DOMAIN," + host]:
        raise ValueError("TencentQQ requires only the reviewed exact host im.qq.com")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [f for f in ordered if f[:2] == ["RULE-SET", provider]] != [marker]:
        raise ValueError("TencentQQ requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(f[0] == "MATCH" for f in ordered) != 1:
        raise ValueError("TencentQQ domain-only model requires a single terminal MATCH")

    # Keep all existing App, security and gaming providers before this entry.
    earlier = (
        "Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "QQMusic", "Douyin",
        "Amap", "Zhihu", "Xiaohongshu", "NetEaseMusic", "Douban", "JD", "Meituan", "BaiduPan",
        "Ctrip", "Pinduoduo", "Taobao", "BaiduMap", "Kuaishou", "TencentVideo", "AliPan",
        "IQIYI", "Xianyu", "Railway12306", "Youku", "WPSOffice", "Feishu", "DingTalk",
        "Quark", "BossZhipin", "WeChat", "SFExpress", "Weibo",
    )
    later = (
        "SiriAI", "Apple", "Bilibili", "YouTube", "TikTok", "Disney", "Netflix",
        "OpenAI", "Gemini", "Claude", "Google", "Microsoft", "GlobalMedia", "ChinaMax",
    )
    for names, before in ((earlier, True), (later, False)):
        for name in names:
            indices = [i for i, f in enumerate(ordered) if f[:2] == ["RULE-SET", name]]
            if len(indices) != 1 or (indices[0] < current) != before:
                raise ValueError("TencentQQ rule order relative to " + name + " is unsafe")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError("TencentQQ requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    manifests = {}
    for name in ("sources.json", "local-rulesets.json"):
        records = json.loads((root / name).read_text(encoding="utf-8"))
        if set(manifests) & set(records):
            raise ValueError("TencentQQ domain-only model found duplicate providers")
        manifests.update(records)
    if manifests.get(provider) != {"path": "ruleset/TencentQQ.yaml", "behavior": "classical"}:
        raise ValueError("TencentQQ requires its reviewed classical provider path")

    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}

    def domain_rule(fields: list[str]) -> str:
        # Mihomo uses Go's simple lowercase. Python's Unicode lowercase expands
        # dotted capital I instead of mapping it to ASCII i; handle that here.
        return fields[0] + "," + fields[1].replace("\u0130", "i").lower()

    for index, fields in enumerate(ordered):
        kind = fields[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError("Unsupported rule in TencentQQ domain-only model: " + kind)
        if not (len(fields) == required or
                (kind in ip_kinds and len(fields) == 4 and fields[3] == "no-resolve")) or any(
                    not value.strip() for value in fields[:required]):
            raise ValueError("TencentQQ domain-only model requires complete rules: " + kind)
        if index < current and kind in ip_kinds:
            raise ValueError("TencentQQ domain-only model cannot verify preceding IP conditions")
        if kind == "RULE-SET" and fields[1] not in manifests:
            raise ValueError("TencentQQ domain-only model found missing provider: " + fields[1])

    def provider_model(path: Path) -> DomainRules:
        rules = entries(path)
        return DomainRules([
            domain_rule(rule.split(",")) if rule.split(",", 1)[0] in domain_kinds else rule
            for rule in rules
        ])

    providers = {name: provider_model(root / item["path"]) for name, item in manifests.items()}
    def route(domain: str, skip_qq: bool = False) -> tuple[str, str]:
        for fields in ordered:
            kind = fields[0]
            if kind == "RULE-SET":
                if not (skip_qq and fields[1] == provider) and providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind in domain_kinds and DomainRules([domain_rule(fields)]).matches(domain):
                return ",".join(fields[:2]), fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
        raise ValueError("TencentQQ domain-only model did not reach MATCH")

    if route(host) not in {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}:
        raise ValueError("TencentQQ is shadowed by an earlier rule: " + host)
    for control in TENCENT_QQ_CONTROLS:
        if route(control) != route(control, skip_qq=True):
            raise ValueError("TencentQQ changed non-target routing: " + control)


MANGO_TV_CONTROLS = frozenset({
    "mgtv.com", "w.mgtv.com", "corp.mgtv.com", "app.mgtv.com", "img.mgtv.com",
    "i.mgtv.com", "7.mgtv.com", "club.mgtv.com", "order.mgtv.com", "log.mgtv.com",
    "download.hitv.com", "download.imgo.tv", "download.hunantv.com",
    "ugc.hitv.com", "ossimg.hitv.com", "i2.hitv.com", "www.hunantv.com",
    "www.iqiyi.com", "www.youku.com", "v.qq.com", "www.bilibili.com",
    "weibo.com", "game.qq.com", "guzzoni.apple.com", "example.org",
})


def validate_mango_tv(root: Path = ROOT) -> None:
    """Keep the one reviewed public Mango TV host within its dedicated policy."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target, host = "MangoTV", "🥭 芒果TV", "www.mgtv.com"
    reviewed_path = "ruleset/MangoTV.yaml"
    payload = read_rules((root / reviewed_path).read_text(encoding="utf-8"))
    if payload != ["DOMAIN," + host]:
        raise ValueError("MangoTV must contain only the reviewed exact host")

    ordered = [line.split(",") for line in entries(root / "config/rules.yaml")]
    reference = ["RULE-SET", provider, target]
    if [fields for fields in ordered if fields[:2] == ["RULE-SET", provider]] != [reference]:
        raise ValueError("MangoTV needs exactly one dedicated policy reference")
    index = ordered.index(reference)

    prior = (
        "RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
        "DOMAIN,fastcdn.hoyoverse.com,DIRECT", "RULE-SET,InternationalGaming,🎮 国际游戏",
        "RULE-SET,ChinaGaming,DIRECT", "RULE-SET,QQMusic,🎧 QQ 音乐",
        "RULE-SET,Douyin,🎶 抖音", "RULE-SET,Amap,🗺️ 高德地图",
        "RULE-SET,Zhihu,💡 知乎", "RULE-SET,Xiaohongshu,📕 小红书 / REDnote",
        "RULE-SET,NetEaseMusic,🎵 网易云音乐", "RULE-SET,Douban,📚 豆瓣",
        "RULE-SET,JD,🛒 京东", "RULE-SET,Meituan,🍜 美团",
        "RULE-SET,BaiduPan,☁️ 百度网盘", "RULE-SET,Ctrip,🧳 携程",
        "RULE-SET,Pinduoduo,🛍️ 拼多多", "RULE-SET,Taobao,🛍️ 淘宝",
        "RULE-SET,BaiduMap,🗺️ 百度地图", "RULE-SET,Kuaishou,📹 快手",
        "RULE-SET,TencentVideo,📺 腾讯视频", "RULE-SET,AliPan,📁 阿里云盘",
        "RULE-SET,IQIYI,🎬 爱奇艺", "RULE-SET,Xianyu,🐟 闲鱼",
        "RULE-SET,Railway12306,🚄 铁路12306", "RULE-SET,Youku,🎞️ 优酷",
        "RULE-SET,WPSOffice,📝 WPS Office", "RULE-SET,Feishu,💼 飞书",
        "RULE-SET,DingTalk,💬 钉钉", "RULE-SET,Quark,🔍 夸克",
        "RULE-SET,BossZhipin,💼 BOSS直聘", "RULE-SET,WeChat,💬 微信",
        "RULE-SET,SFExpress,📦 顺丰速运", "RULE-SET,Weibo,🟠 微博",
    )
    later = (
        "RULE-SET,SiriAI,🤖 AI 服务", "RULE-SET,Apple,🍎 Apple",
        "RULE-SET,YouTube,📼 YouTube", "RULE-SET,Bilibili,📺 Bilibili",
        "RULE-SET,TikTok,🎵 Tiktok", "RULE-SET,Disney,🏰 Disney",
        "RULE-SET,Netflix,🎞️ Netflix", "RULE-SET,Gemini,♊ Gemini",
        "RULE-SET,Google,🔎 Google", "RULE-SET,Microsoft,🪟 Microsoft",
        "RULE-SET,GlobalMedia,🛰️ International-Global", "GEOIP,CN,DIRECT,no-resolve",
        "RULE-SET,ChinaMax,🇨🇳 China-Global",
    )

    def require(markers: tuple[str, ...], segment: list[list[str]], error: str) -> None:
        for marker in markers:
            fields = marker.split(",")
            if ordered.count(fields) != 1 or fields not in segment:
                raise ValueError(f"MangoTV {error}: {marker}")

    require(prior, ordered[:index], "must follow security, gaming and existing app rules")
    require(later, ordered[index + 1:], "must precede broader providers")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    group = next((group for group in groups if group["name"] == target), None)
    if group != {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}:
        raise ValueError("MangoTV needs a DIRECT-first select group with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys():
        raise ValueError("MangoTV manifests cannot contain duplicate providers")
    if local.get(provider) != {"path": reviewed_path, "behavior": "classical"}:
        raise ValueError("MangoTV needs the reviewed classical local provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"GEOIP", "IP-CIDR", "IP-CIDR6"}
    for position, fields in enumerate(ordered):
        kind = fields[0]
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"Unsupported top-level rule in MangoTV domain-only model: {kind}")
        width = 2 if kind == "MATCH" else 3
        lengths = {width, width + 1} if kind in ip_kinds and fields[-1] == "no-resolve" else {width}
        if len(fields) not in lengths or any(not value.strip() for value in fields[:width]):
            raise ValueError(f"MangoTV domain-only model requires complete supported rules: {kind}")
        if kind in ip_kinds and position < index:
            raise ValueError(f"MangoTV domain-only model cannot validate preceding IP conditions: {kind}")
        if kind == "RULE-SET" and fields[1] not in manifests:
            raise ValueError(f"MangoTV routing references missing providers: {fields[1]}")

    # Mihomo normalizes rule operands; apply the ASCII part here without changing shared models.
    lower_ascii = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")

    def fold_operand(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        return kind + sep + operand.translate(lower_ascii) if kind in domain_kinds else rule

    models = {
        name: DomainRules([fold_operand(rule) for rule in entries(root / item["path"])])
        for name, item in manifests.items()
    }
    literals = {
        position: DomainRules([fold_operand(",".join(fields[:2]))])
        for position, fields in enumerate(ordered) if fields[0] in domain_kinds
    }

    def route(domain: str, skip_mango: bool = False) -> tuple[str, str]:
        for position, fields in enumerate(ordered):
            kind = fields[0]
            if kind == "RULE-SET":
                if skip_mango and fields[1] == provider:
                    continue
                if models[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
            elif kind in domain_kinds and literals[position].matches(domain):
                return ",".join(fields[:2]), fields[2]
        raise ValueError("MangoTV domain-only model needs a MATCH fallback")

    result = route(host)
    if result not in {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}:
        raise ValueError(f"MangoTV is shadowed by an earlier rule: {host}: {result}")
    controls = MANGO_TV_CONTROLS | {"child." + host, "not" + host, host + ".example.org"}
    for domain in controls:
        if route(domain) != route(domain, skip_mango=True):
            raise ValueError(f"MangoTV changed non-target routing: {domain}")


DIDI_CONTROLS = frozenset({
    "didichuxing.com", "didiglobal.com", "diditaxi.com", "didiglobal.com.cn",
    "hk.didiglobal.com", "mexico.didiglobal.com", "ir.didiglobal.com",
    "page.udache.com", "s.didi.cn", "img0.didiglobal.com", "www6.didiglobal.com",
    "www.weibo.com", "www.sf-express.com", "www.quark.cn", "www.amap.com",
    "guzzoni.apple.com", "hmma.baidu.com", "hoyoverse.com", "fastcdn.hoyoverse.com",
    "example.org",
})


def validate_didi(root: Path = ROOT) -> None:
    """Limit DiDi's selectable policy to its two attributed public website entries."""
    from siri_ai import DomainRules

    hosts = {"www.didichuxing.com", "www.didiglobal.com"}
    path = "ruleset/Didi.yaml"
    reviewed = entries(root / path)
    if len(reviewed) != len(hosts) or set(reviewed) != {"DOMAIN," + host for host in hosts}:
        raise ValueError("Didi must contain only the two reviewed exact hosts without duplicates")

    target = "🚕 滴滴出行"
    groups = read_policy_group_model(root / "config" / "proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if next((group for group in groups if group["name"] == target), None) != expected:
        raise ValueError("Didi must be a DIRECT-first select group with manual proxy and Final options")
    parse_policy_groups(root)

    ordered = [rule.split(",") for rule in entries(root / "config" / "rules.yaml")]
    priority = {"Privacy": "REJECT", "Hijacking": "🚫 Hijacking",
                "InternationalGaming": "🎮 国际游戏", "ChinaGaming": "DIRECT"}
    earlier_apps = (
        "QQMusic", "Douyin", "Amap", "Zhihu", "Xiaohongshu", "NetEaseMusic", "Douban",
        "JD", "Meituan", "BaiduPan", "Ctrip", "Pinduoduo", "Taobao", "BaiduMap",
        "Kuaishou", "TencentVideo", "AliPan", "IQIYI", "Xianyu", "Railway12306",
        "Youku", "WPSOffice", "Feishu", "DingTalk", "Quark", "BossZhipin",
        "WeChat", "SFExpress", "Weibo",
    )
    later_providers = (
        "SiriAI", "Apple", "YouTube", "Bilibili", "TikTok", "Disney", "Netflix",
        "Gemini", "Google", "Microsoft", "GlobalMedia", "ChinaMax",
    )

    def provider_position(provider: str, policy: str | None = None) -> int:
        found = [idx for idx, fields in enumerate(ordered)
                 if fields[:2] == ["RULE-SET", provider]]
        if len(found) != 1 or (policy is not None and ordered[found[0]] != ["RULE-SET", provider, policy]):
            raise ValueError(f"Didi requires exactly one valid {provider} policy reference")
        return found[0]

    current = provider_position("Didi", target)
    if (any(provider_position(name, policy) >= current for name, policy in priority.items())
            or any(provider_position(name) >= current for name in earlier_apps)):
        raise ValueError("Security, gaming and existing app rules must precede Didi")
    if any(provider_position(name) <= current for name in later_providers):
        raise ValueError("Didi must precede broader providers")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        duplicates = set(manifests) & set(loaded)
        if duplicates:
            raise ValueError("Didi manifests contain duplicate providers: " + ", ".join(sorted(duplicates)))
        manifests.update(loaded)
    if (manifests.get("Didi", {}).get("path") != path
            or manifests["Didi"].get("behavior") != "classical"):
        raise ValueError("Didi must reference its dedicated classical payload")

    domain_rules = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    network_rules = {"GEOIP", "IP-CIDR", "IP-CIDR6"}
    for idx, fields in enumerate(ordered):
        kind = fields[0]
        if kind not in domain_rules | network_rules | {"RULE-SET", "MATCH"}:
            raise ValueError("Unsupported top-level rule in Didi domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        valid_length = len(fields) == required or (
            kind in network_rules and len(fields) == 4 and fields[3] == "no-resolve"
        )
        if not valid_length or any(not field.strip() for field in fields[:required]):
            raise ValueError("Didi domain-only model requires complete supported rules: " + kind)
        if idx < current and kind in network_rules | {"MATCH"}:
            raise ValueError("Didi domain-only model cannot validate preceding IP conditions or MATCH")
        if kind == "RULE-SET" and fields[1] not in manifests:
            raise ValueError("Didi routing references missing providers: " + fields[1])
    if sum(fields[0] == "MATCH" for fields in ordered) != 1:
        raise ValueError("Didi domain-only model requires exactly one MATCH")

    def normalize_domain_rule(rule: str) -> str:
        fields = rule.split(",")
        if len(fields) < 2 or fields[0] not in domain_rules:
            return rule
        # Mihomo's strings.ToLower uses simple per-rune lowercase. Python's
        # full lowercase expands U+0130 to i + combining dot; Go maps it to i.
        operand = fields[1]
        fields[1] = operand.lower() if operand.isascii() else "".join(
            "i" if char == "\u0130" else char.lower() for char in operand
        )
        return ",".join(fields)

    providers = {
        name: DomainRules([normalize_domain_rule(rule) for rule in entries(root / item["path"])])
        for name, item in manifests.items()
    }
    inline_domains = {idx: DomainRules([normalize_domain_rule(",".join(fields))])
                      for idx, fields in enumerate(ordered) if fields[0] in domain_rules}

    def route(host: str, include_didi: bool = True) -> tuple[str, str]:
        for idx, fields in enumerate(ordered):
            kind = fields[0]
            if kind == "RULE-SET":
                name = fields[1]
                if (include_didi or name != "Didi") and providers[name].matches(host):
                    return name, fields[2]
            elif kind in domain_rules and inline_domains[idx].matches(host):
                return ",".join(fields[:2]), fields[2]
            elif kind == "MATCH":
                return kind, fields[1]
        raise ValueError("Missing MATCH rule")

    allowed = {("Didi", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        result = route(host)
        if result not in allowed:
            raise ValueError(f"Didi is shadowed by an earlier rule: {host}: {result}")
    controls = DIDI_CONTROLS | {candidate for host in hosts
                               for candidate in ("child." + host, "not" + host, host + ".example.org")}
    for host in sorted(controls):
        if route(host) != route(host, False):
            raise ValueError("Didi changed non-target routing: " + host)


DEWU_HOSTS = frozenset({"dewu.com", "www.dewu.com"})
DEWU_CONTROLS = frozenset({
    "agreement.dewu.com", "cdn.dewu.com", "cdn-fast.dewu.com", "dewucdn.com", "www.dewucdn.com",
    "poizon.com", "www.poizon.com", "stark.dewu.com", "open.dewu.com", "creator.dewu.com",
    "livemcn.dewu.com", "liveplatform.dewu.com", "mcn.dewu.com", "poizon.jobs.feishu.cn",
    "www.weibo.com", "www.xiaohongshu.com", "www.taobao.com", "www.bilibili.com",
    "www.google.com", "guzzoni.apple.com", "hmma.baidu.com", "fastcdn.hoyoverse.com",
    "app.datadoghq.com", "example.org",
})


def validate_dewu(root: Path = ROOT) -> None:
    """Check the two public Dewu portals and their domain-only first matches."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    target = "👟 得物"
    payload = read_rules((root / "ruleset/Dewu.yaml").read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in DEWU_HOSTS}:
        raise ValueError("Dewu must contain only the two reviewed exact hosts")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    group = next((row for row in groups if row["name"] == target), None)
    if group != {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}:
        raise ValueError("Dewu must be a DIRECT-first select group with manual proxy and Final options")
    parse_policy_groups(root)

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    refs = [index for index, fields in enumerate(ordered) if fields[:2] == ["RULE-SET", "Dewu"]]
    if len(refs) != 1 or ordered[refs[0]] != ["RULE-SET", "Dewu", target]:
        raise ValueError("Dewu must have exactly one dedicated policy reference")
    current = refs[0]

    security = ("RULE-SET,Privacy,REJECT", "RULE-SET,Hijacking,🚫 Hijacking",
                "RULE-SET,InternationalGaming,🎮 国际游戏", "RULE-SET,ChinaGaming,DIRECT")
    apps = ("QQMusic", "Douyin", "Amap", "Zhihu", "Xiaohongshu", "NetEaseMusic", "Douban", "JD",
            "Meituan", "BaiduPan", "Ctrip", "Pinduoduo", "Taobao", "BaiduMap", "Kuaishou",
            "TencentVideo", "AliPan", "IQIYI", "Xianyu", "Railway12306", "Youku", "WPSOffice",
            "Feishu", "DingTalk", "Quark", "BossZhipin", "WeChat", "SFExpress", "Weibo")
    broader = ("SiriAI", "Apple", "YouTube", "Bilibili", "TikTok", "Disney", "Netflix",
               "Gemini", "Google", "Microsoft", "GlobalMedia", "ChinaMax")
    for rule in security:
        fields = rule.split(",")
        if ordered.count(fields) != 1 or ordered.index(fields) >= current:
            raise ValueError("Security and gaming rules must precede Dewu")
    for names, must_precede in ((apps, True), (broader, False)):
        for name in names:
            positions = [index for index, fields in enumerate(ordered)
                         if fields[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != must_precede:
                raise ValueError(f"Dewu has an invalid routing position relative to {name}")
    if ordered.count(["GEOIP", "CN", "DIRECT", "no-resolve"]) != 1 or not (
        current < ordered.index(["GEOIP", "CN", "DIRECT", "no-resolve"])
    ):
        raise ValueError("Dewu must precede the CN GeoIP fallback")

    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        loaded = json.loads((root / filename).read_text(encoding="utf-8"))
        if manifests.keys() & loaded.keys():
            raise ValueError("Dewu manifests contain duplicate providers")
        manifests.update(loaded)
    if manifests.get("Dewu") != {"path": "ruleset/Dewu.yaml", "behavior": "classical"}:
        raise ValueError("Dewu is missing its dedicated local classical provider")

    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"GEOIP", "IP-CIDR", "IP-CIDR6"}

    def domain_operand(rule: str) -> str:
        kind, separator, value = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo uses Go's simple lowercase. Keep valid non-ASCII operands
            # (such as unrelated mirror keywords); dotted I maps to ASCII i.
            return kind + separator + value.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model_rows: list[tuple[str, str, DomainRules | None]] = []
    matches = 0
    for index, fields in enumerate(ordered):
        kind = fields[0]
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError("Unsupported top-level rule in Dewu domain-only model: " + kind)
        required = 2 if kind == "MATCH" else 3
        if (not (len(fields) == required or
                 (kind in ip_kinds and len(fields) == 4 and fields[3] == "no-resolve"))
                or any(not part.strip() for part in fields[:required])):
            raise ValueError("Dewu domain-only model requires complete supported rules: " + kind)
        if kind in ip_kinds:
            if index < current:
                raise ValueError("Dewu domain-only model cannot validate preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = fields[1]
            if name not in manifests:
                raise ValueError("Dewu routing references missing provider: " + name)
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_operand(rule) for rule in rules])
            model_rows.append((name, fields[2], providers[name]))
        elif kind == "MATCH":
            matches += 1
            model_rows.append((kind, fields[1], None))
        else:
            label = ",".join(fields[:2])
            # These are public inline routing fields, not catalog provider payloads.
            # Model first match without imposing the catalog's narrower DNS grammar.
            model_rows.append((label, fields[2], DomainRules([domain_operand(label)])))
    if matches != 1 or ordered[-1][0] != "MATCH":
        raise ValueError("Dewu requires exactly one final MATCH rule")

    def route(host: str, include_dewu: bool = True) -> tuple[str, str]:
        for label, policy, matcher in model_rows:
            if (include_dewu or label != "Dewu") and (matcher is None or matcher.matches(host)):
                return label, policy
        raise ValueError("Missing MATCH rule")

    allowed = {("Dewu", target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in DEWU_HOSTS:
        verdict = route(host)
        if verdict not in allowed:
            raise ValueError(f"Dewu is shadowed by an earlier rule: {host}: {verdict}")
    shape_controls = {value for host in DEWU_HOSTS for value in
                      ("child." + host, "not" + host, host + ".example.org")}
    for host in DEWU_CONTROLS | shape_controls:
        if route(host) != route(host, include_dewu=False):
            raise ValueError("Dewu changed non-target routing: " + host)


WE_COM_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com", "hmma.baidu.com",
    "hoyoverse.com", "im.qq.com", "login.work.weixin.qq.com", "mp.weixin.qq.com",
    "open.work.weixin.qq.com", "v.qq.com", "wecom.com", "weixin.qq.com",
    "www.bilibili.com", "www.douyin.com", "www.google.com", "www.taobao.com",
    "www.youku.com", "y.qq.com",
})


def validate_wecom(root: Path = ROOT) -> None:
    """Maintain the exact public WeCom scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "WeCom", "🏢 企业微信"
    hosts = set(["work.weixin.qq.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in WE_COM_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


TENCENT_MEETING_CONTROLS = frozenset({
    "cdn.meeting.tencent.com", "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com",
    "hmma.baidu.com", "hoyoverse.com", "im.qq.com", "qq.com",
    "tencent.com", "v.qq.com", "voovmeeting.com", "weixin.qq.com",
    "work.weixin.qq.com", "www.bilibili.com", "www.douyin.com", "www.google.com",
    "www.taobao.com", "www.voovmeeting.com", "www.youku.com", "wx.wemeet.tencent.com",
    "y.qq.com",
})


def validate_tencent_meeting(root: Path = ROOT) -> None:
    """Maintain the exact public Tencent Meeting scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "TencentMeeting", "🎥 腾讯会议"
    hosts = set(["meeting.tencent.com","meeting.qq.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in TENCENT_MEETING_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


TENCENT_MAP_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com", "hmma.baidu.com",
    "hoyoverse.com", "im.qq.com", "lbs.qq.com", "map.baidu.com",
    "map.wap.qq.com", "open.map.qq.com", "qq.com", "ugc.map.qq.com",
    "v.qq.com", "weixin.qq.com", "www.amap.com", "www.bilibili.com",
    "www.douyin.com", "www.google.com", "www.taobao.com", "www.youku.com",
    "y.qq.com",
})


def validate_tencent_map(root: Path = ROOT) -> None:
    """Maintain the exact public Tencent Map scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "TencentMap", "🗺️ 腾讯地图"
    hosts = set(["map.qq.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in TENCENT_MAP_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


MEITU_XIU_XIU_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com", "hmma.baidu.com",
    "hoyoverse.com", "im.qq.com", "meitu.com", "meituxiuxiu.com",
    "pc.meitu.com", "v.qq.com", "weixin.qq.com", "wink.cn",
    "www.bilibili.com", "www.designkit.com", "www.douyin.com", "www.google.com",
    "www.meitu.com", "www.meiyan.com", "www.taobao.com", "www.youku.com",
    "y.qq.com",
})


def validate_meitu_xiuxiu(root: Path = ROOT) -> None:
    """Maintain the exact public Meitu Xiuxiu scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "MeituXiuXiu", "🎨 美图秀秀"
    hosts = set(["xiuxiu.meitu.com","www.meituxiuxiu.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in MEITU_XIU_XIU_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


FRESHIPPO_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "freshhema.com", "freshippo.com",
    "guzzoni.apple.com", "hmma.baidu.com", "hoyoverse.com", "im.qq.com",
    "terms.alicdn.com", "v.qq.com", "weixin.qq.com", "www.bilibili.com",
    "www.douyin.com", "www.google.com", "www.taobao.com", "www.tmall.com",
    "www.youku.com", "y.qq.com",
})


def validate_freshippo(root: Path = ROOT) -> None:
    """Maintain the exact public Freshippo scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "Freshippo", "🛒 盒马"
    hosts = set(["www.freshhema.com","www.freshippo.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in FRESHIPPO_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


HUOLALA_CONTROLS = frozenset({
    "dappweb.huolala.cn", "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com",
    "hmma.baidu.com", "hoyoverse.com", "huolala.cn", "huolala.co",
    "im.qq.com", "open.huolala.cn", "v.qq.com", "weixin.qq.com",
    "wuliu.huolala.cn", "www.bilibili.com", "www.douyin.com", "www.google.com",
    "www.hllep.com", "www.lalamove.com", "www.taobao.com", "www.youku.com",
    "y.qq.com",
})


def validate_huolala(root: Path = ROOT) -> None:
    """Maintain the exact public Huolala scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "Huolala", "🚚 货拉拉"
    hosts = set(["www.huolala.cn"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in HUOLALA_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


FLIGGY_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "fliggy.com", "guzzoni.apple.com",
    "hmma.baidu.com", "hoyoverse.com", "im.qq.com", "login.taobao.com",
    "m.alitrip.com", "m.fliggy.com", "rule.fliggy.com", "terms.alicdn.com",
    "v.qq.com", "weixin.qq.com", "www.bilibili.com", "www.ctrip.com",
    "www.douyin.com", "www.fliggy.hk", "www.fliggy.net", "www.google.com",
    "www.taobao.com", "www.youku.com", "y.qq.com",
})


def validate_fliggy(root: Path = ROOT) -> None:
    """Maintain the exact public Fliggy scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "Fliggy", "✈️ 飞猪"
    hosts = set(["www.fliggy.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in FLIGGY_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


NET_EASE_MAIL_MASTER_CONTROLS = frozenset({
    "163.com", "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com",
    "hmma.baidu.com", "hoyoverse.com", "im.qq.com", "imap.163.com",
    "maas.mail.163.com", "mail.126.com", "mail.163.com", "mail.qq.com",
    "music.163.com", "pop.163.com", "reg.163.com", "smtp.163.com",
    "v.qq.com", "weixin.qq.com", "www.bilibili.com", "www.douyin.com",
    "www.google.com", "www.taobao.com", "www.youku.com", "y.qq.com",
})


def validate_netease_mail_master(root: Path = ROOT) -> None:
    """Maintain the exact public NetEase Mail Master scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "NetEaseMailMaster", "📧 网易邮箱大师"
    hosts = set(["dashi.163.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in NET_EASE_MAIL_MASTER_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


MAOYAN_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com", "hmma.baidu.com",
    "hoyoverse.com", "im.qq.com", "ir.maoyan.com", "m.maoyan.com",
    "maoyan.com", "piaofang.maoyan.com", "v.qq.com", "weixin.qq.com",
    "www.bilibili.com", "www.dianping.com", "www.douyin.com", "www.google.com",
    "www.meituan.com", "www.taobao.com", "www.youku.com", "y.qq.com",
})


def validate_maoyan(root: Path = ROOT) -> None:
    """Maintain the exact public Maoyan scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "Maoyan", "🎟️ 猫眼"
    hosts = set(["www.maoyan.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                rules = entries(root / manifests[name]["path"])
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in MAOYAN_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


WE_CHAT_READING_CONTROLS = frozenset({
    "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com", "hmma.baidu.com",
    "hoyoverse.com", "im.qq.com", "mp.weixin.qq.com", "myqcloud.com",
    "qq.com", "v.qq.com", "weixin.qq.com", "www.bilibili.com",
    "www.douyin.com", "www.google.com", "www.taobao.com", "www.youku.com",
    "y.qq.com", "yuedu.qq.com",
})


def validate_wechat_reading(root: Path = ROOT) -> None:
    """Maintain the exact public WeRead scope and its domain-only precedence."""
    from generate_catalog import read_rules
    from siri_ai import DomainRules

    provider, target = "WeChatReading", "📚 微信读书"
    hosts = set(["weread.qq.com"])
    path = f"ruleset/{provider}.yaml"
    payload = read_rules((root / path).read_text(encoding="utf-8"))
    if set(payload) != {"DOMAIN," + host for host in hosts}:
        raise ValueError(f"{provider} requires only its reviewed exact hosts")

    ordered = [rule.split(",") for rule in entries(root / "config/rules.yaml")]
    marker = ["RULE-SET", provider, target]
    if [row for row in ordered if row[:2] == marker[:2]] != [marker]:
        raise ValueError(f"{provider} requires exactly one dedicated policy reference")
    current = ordered.index(marker)
    before = ("Privacy", "Hijacking", "InternationalGaming", "ChinaGaming", "Weibo",
              "TencentQQ", "MangoTV", "Didi", "Dewu")
    after = ("SiriAI", "Apple", "Bilibili", "Gemini", "Google", "GlobalMedia", "ChinaMax")
    for names, earlier in ((before, True), (after, False)):
        for name in names:
            positions = [i for i, row in enumerate(ordered) if row[:2] == ["RULE-SET", name]]
            if len(positions) != 1 or (positions[0] < current) != earlier:
                raise ValueError(f"{provider} has an invalid routing position relative to {name}")

    groups = read_policy_group_model(root / "config/proxy-groups.yaml")
    expected = {"name": target, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]}
    if [group for group in groups if group["name"] == target] != [expected]:
        raise ValueError(f"{provider} requires a DIRECT-first select with manual proxy and Final")
    parse_policy_groups(root)

    sources = json.loads((root / "sources.json").read_text(encoding="utf-8"))
    local = json.loads((root / "local-rulesets.json").read_text(encoding="utf-8"))
    if sources.keys() & local.keys() or local.get(provider) != {"path": path, "behavior": "classical"}:
        raise ValueError(f"{provider} requires its own registered classical provider")
    manifests = sources | local
    domain_kinds = {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}
    ip_kinds = {"IP-CIDR", "IP-CIDR6", "GEOIP"}
    if ordered[-1] != ["MATCH", "🧭 Final"] or sum(row[0] == "MATCH" for row in ordered) != 1:
        raise ValueError(f"{provider} domain-only model requires a single terminal MATCH")

    def domain_rule(rule: str) -> str:
        kind, sep, operand = rule.partition(",")
        if kind in domain_kinds:
            # Mihomo lowercases domain operands. Go simple lowercase maps dotted I to i.
            return kind + sep + operand.replace("\u0130", "i").lower()
        return rule

    providers = {}
    model = []
    for position, row in enumerate(ordered):
        kind = row[0]
        required = 2 if kind == "MATCH" else 3
        if kind not in domain_kinds | ip_kinds | {"RULE-SET", "MATCH"}:
            raise ValueError(f"{provider} domain-only model does not support {kind}")
        if (not (len(row) == required or
                 (kind in ip_kinds and len(row) == 4 and row[3] == "no-resolve"))
                or any(not field.strip() for field in row[:required])):
            raise ValueError(f"{provider} domain-only model requires complete rules: {kind}")
        if kind in ip_kinds:
            if position < current:
                raise ValueError(f"{provider} domain-only model cannot verify preceding IP conditions")
            continue
        if kind == "RULE-SET":
            name = row[1]
            if name not in manifests:
                raise ValueError(f"{provider} routing references missing provider: {name}")
            if name not in providers:
                try:
                    rules = read_rules((root / manifests[name]["path"]).read_text(encoding="utf-8"))
                except ValueError as exc:
                    raise ValueError(f"{provider}: invalid rules in {name}: {exc}") from exc
                providers[name] = DomainRules([domain_rule(rule) for rule in rules])
            model.append((name, row[2], providers[name]))
        elif kind == "MATCH":
            model.append((kind, row[1], None))
        else:
            label = ",".join(row[:2])
            model.append((label, row[2], DomainRules([domain_rule(label)])))

    def route(host: str, skip_app: bool = False) -> tuple[str, str]:
        for name, policy, matcher in model:
            if not (skip_app and name == provider) and (matcher is None or matcher.matches(host)):
                return name, policy
        raise ValueError(f"{provider} domain-only model did not reach MATCH")

    allowed = {(provider, target), ("Privacy", "REJECT"), ("Hijacking", "🚫 Hijacking")}
    for host in sorted(hosts):
        if route(host) not in allowed:
            raise ValueError(f"{provider} is shadowed by an earlier rule: {host}")
    shapes = {variant for host in hosts for variant in
              ("child." + host, "not" + host, host + ".example.org")}
    for host in WE_CHAT_READING_CONTROLS | shapes:
        if route(host) != route(host, skip_app=True):
            raise ValueError(f"{provider} changed non-target routing: {host}")


def validate_dingdong_maicai(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="DingdongMaicai", target="🥬 叮咚买菜",
        host="www.100.me",
        controls=(
            "100.me", "maicai.api.ddxq.mobi", "www.freshippo.com",
            "www.pupumall.com",
        ),
    )


def validate_douyu(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="DouYu", target="🐟 斗鱼",
        host="m.douyu.com",
        controls=(
            "douyu.com", "www.douyu.com", "v.douyu.com",
            "wan.douyu.com", "staticlive.douyucdn.cn",
        ),
    )


def validate_tongcheng_travel(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="TongchengTravel", target="🧳 同程旅行",
        host="m.ly.com",
        controls=(
            "ly.com", "www.ly.com", "m.17u.cn",
            "tmc.ly.com", "passport.ly.com", "pic5.40017.cn", "www.12306.cn", "m.ctrip.com",
        ),
    )


def validate_tencent_docs(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="TencentDocs", target="📝 腾讯文档",
        host="docs.qq.com",
        controls=(
            "qq.com", "im.qq.com", "meeting.tencent.com",
            "work.weixin.qq.com", "beacon.qq.com", "weread.qq.com", "gtimg.com",
        ),
    )


def validate_ximalaya(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="Ximalaya", target="🎧 喜马拉雅",
        host="m.ximalaya.com",
        controls=(
            "ximalaya.com", "www.ximalaya.com", "passport.ximalaya.com",
            "live.ximalaya.com", "studio.ximalaya.com", "open.ximalaya.com",
            "everest-ai.ximalaya.com",
        ),
    )


def validate_kfc_china(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="KFCChina", target="🍗 肯德基中国",
        host="www.kfc.com.cn",
        controls=(
            "kfc.com.cn", "www.kfc.com", "www.yumchina.com",
            "www.4008823823.com.cn", "www.mcdonalds.com.cn", "appcommon.kfc.com.cn",
        ),
    )


def validate_fanqie_novel(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="FanqieNovel", target="🍅 番茄小说",
        host="fanqienovel.com",
        controls=(
            "www.fanqienovel.com", "www.changdunovel.com", "reading.snssdk.com",
            "lf-organic-growth.bytecdn.cn", "www.douyin.com",
        ),
    )


def validate_sogou_mobile_ime(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="SogouMobileIME", target="⌨️ 搜狗输入法手机版",
        host="shouji.sogou.com",
        controls=(
            "sogou.com", "pinyin.sogou.com", "shurufa.sogou.com",
            "account.sogou.com", "indivi-cdn.shouji.sogou.com", "img.shouji.sogou.com",
            "apkdl.sogouimecdn.com", "pb.i.sogou.com",
        ),
    )


def validate_vipshop(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="Vipshop", target="🛍️ 唯品会",
        host="www.vip.com",
        controls=(
            "vip.com", "m.vip.com", "help.vip.com",
            "myi.vip.com", "vis.vip.com", "www.vipshop.com",
            "www.vpal.com", "a.vpimg2.com", "mst.vip.com",
        ),
    )


def validate_mcdonalds_china(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="McDonaldsChina", target="🍔 麦当劳中国",
        host="www.mcdonalds.com.cn",
        controls=(
            "mcdonalds.com.cn", "www.mcdonalds.com", "www.mcd.cn",
            "www.4008-517-517.cn", "www.kfc.com.cn",
        ),
    )


def validate_huya_live(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="HuyaLive", target="🐯 虎牙直播",
        host="hd.huya.com",
        controls=(
            "huya.com", "www.huya.com", "m.huya.com",
            "api.m.huya.com", "app-agreements.huya.com", "dev.huya.com",
            "rel.huya.com", "metric.huya.com",
        ),
    )


def validate_xigua_video(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="XiguaVideo", target="🍉 西瓜视频",
        host="m.ixigua.com",
        controls=(
            "ixigua.com", "www.ixigua.com", "studio.ixigua.com",
            "live.ixigua.com", "p3.bdxiguaimg.com", "p3-sign.douyinpic.com", "www.douyin.com",
            "reading.snssdk.com",
        ),
    )


def validate_youdao_dictionary(root: Path = ROOT) -> None:
    from public_app import validate_public_app

    parse_policy_groups(root)
    validate_public_app(
        root, provider="YoudaoDictionary", target="📖 网易有道词典",
        host="dict.youdao.com",
        controls=(
            "youdao.com", "www.youdao.com", "fanyi.youdao.com",
            "cidian.youdao.com", "account.youdao.com", "ke.youdao.com",
            "note.youdao.com", "ydlunacommon.nosdn.127.net", "rlogs.youdao.com",
            "mail.163.com",
        ),
    )


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
    validate_baidu_pan(root)
    validate_zhihu(root)
    validate_amap(root)
    validate_netease_music(root)
    validate_douyin(root)
    validate_qq_music(root)
    validate_jd(root)
    validate_meituan(root)
    validate_ctrip(root)
    validate_pinduoduo(root)
    validate_taobao(root)
    validate_baidu_map(root)
    validate_kuaishou(root)
    validate_tencent_video(root)
    validate_alipan(root)
    validate_iqiyi(root)
    validate_xianyu(root)
    validate_railway_12306(root)
    validate_youku(root)
    validate_wps_office(root)
    validate_feishu(root)
    validate_dingtalk(root)
    validate_quark(root)
    validate_boss_zhipin(root)
    validate_wechat(root)
    validate_sf_express(root)
    validate_weibo(root)
    validate_tencent_qq(root)
    validate_mango_tv(root)
    validate_didi(root)
    validate_dewu(root)
    validate_wecom(root)
    validate_tencent_meeting(root)
    validate_tencent_map(root)
    validate_meitu_xiuxiu(root)
    validate_freshippo(root)
    validate_huolala(root)
    validate_fliggy(root)
    validate_netease_mail_master(root)
    validate_maoyan(root)
    validate_wechat_reading(root)
    validate_dingdong_maicai(root)
    validate_douyu(root)
    validate_tongcheng_travel(root)
    validate_tencent_docs(root)
    validate_ximalaya(root)
    validate_kfc_china(root)
    validate_fanqie_novel(root)
    validate_sogou_mobile_ime(root)
    validate_vipshop(root)
    validate_mcdonalds_china(root)
    validate_huya_live(root)
    validate_xigua_video(root)
    validate_youdao_dictionary(root)
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
