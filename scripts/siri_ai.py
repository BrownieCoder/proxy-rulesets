#!/usr/bin/env python3
"""离线生成并验证 SiriAI；不下载、不读取私人配置。GPL-2.0-only。"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = re.compile(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?\Z")
SOURCE = "https://support.apple.com/en-us/101555"
TARGET = "🤖 AI 服务"


def canonical(root: Path = ROOT) -> tuple[list[str], str]:
    data = (root / "rules/siri-ai-domains.txt").read_bytes()
    domains = data.decode("utf-8").splitlines()
    if not domains or len(domains) != len(set(domains)):
        raise ValueError("SiriAI：空清单或重复域名")
    if domains != sorted(domains) or data != ("\n".join(domains) + "\n").encode():
        raise ValueError("SiriAI：必须按字母排序、LF 换行并保留末尾换行")
    for domain in domains:
        if not DOMAIN.fullmatch(domain):
            raise ValueError("SiriAI：不支持的域名、通配符或规则语法")
        try:
            ipaddress.ip_address(domain)
        except ValueError:
            pass
        else:
            raise ValueError("SiriAI：不能用 IP 地址代替域名")
    records = json.loads((root / "rules/siri-ai-provenance.json").read_text())
    if not isinstance(records, list) or [r["domain"] for r in records] != domains:
        raise ValueError("SiriAI：provenance 与 canonical 不一致")
    for record in records:
        for field in ("source", "evidence_type", "user_provided_status", "verified_date", "purpose", "confidence", "notes", "target_policy"):
            if not record.get(field):
                raise ValueError(f"SiriAI：缺少来源字段 {field}")
        if record["source"] != SOURCE or record["evidence_type"] != "Apple official":
            raise ValueError("SiriAI：新来源须先审查证据合同")
        if record["target_policy"] != TARGET or "first_observed" not in record:
            raise ValueError("SiriAI：目标或观察记录缺失")
    audit = json.loads((root / "research/SiriAI-audit.json").read_text())
    identities = [(r["provided_rule_type"], r["domain"]) for r in audit]
    if len(identities) != len(set(identities)):
        raise ValueError("SiriAI：候选审计重复")
    accepted = sorted(r["domain"] for r in audit if r["status"] == "ACCEPTED")
    if accepted != domains:
        raise ValueError("SiriAI：已接受候选与 canonical 不一致")
    if any(r["production_rule_type"] != "DOMAIN" for r in audit if r["status"] == "ACCEPTED"):
        raise ValueError("SiriAI：正式规则只能精确匹配")
    return domains, hashlib.sha256(data).hexdigest()


def render(domains: list[str], digest: str) -> str:
    return ("# 由 scripts/siri_ai.py --write 生成；请修改 canonical，勿手改。\n"
            "# 来源：rules/siri-ai-domains.txt；许可证：GPL-2.0-only。\n"
            f"# canonical-sha256: {digest}\n"
            "# 仅决定出口，不保证资格、完整覆盖或服务可用。\n"
            "payload:\n" + "".join(f"  - DOMAIN,{domain}\n" for domain in domains))


def entries(path: Path) -> list[str]:
    return [line.strip()[2:].strip("\"'") for line in path.read_text().splitlines()
            if line.strip().startswith("- ")]


class DomainRules:
    """只模拟有域名、无进程/IP元数据的请求；不伪造 DNS/GeoIP/UDP 实测。"""
    def __init__(self, rules: list[str]):
        self.exact: set[str] = set()
        self.suffix: set[str] = set()
        self.keywords: list[str] = []
        for rule in rules:
            fields = rule.split(",")
            kind = fields[0]
            if kind == "DOMAIN":
                self.exact.add(fields[1])
            elif kind == "DOMAIN-SUFFIX":
                self.suffix.add(fields[1])
            elif kind == "DOMAIN-KEYWORD":
                self.keywords.append(fields[1])
            elif kind not in {"IP-CIDR", "IP-CIDR6", "IP-ASN", "PROCESS-NAME"}:
                raise ValueError(f"离线域名模型不支持规则类型：{kind}")

    def matches(self, domain: str) -> bool:
        labels = domain.split(".")
        return (domain in self.exact
                or any(".".join(labels[i:]) in self.suffix for i in range(len(labels)))
                or any(keyword in domain for keyword in self.keywords))


def routing_check(domains: list[str], root: Path = ROOT) -> tuple[list[str], int]:
    manifests = {}
    for filename in ("sources.json", "local-rulesets.json"):
        manifests.update(json.loads((root / filename).read_text()))
    providers = {name: DomainRules(entries(root / record["path"])) for name, record in manifests.items()}
    rules = entries(root / "config/rules.yaml")
    siri = f"RULE-SET,SiriAI,{TARGET}"
    if rules.count(siri) != 1:
        raise ValueError("SiriAI：必须且只能引用一次现有 AI 策略")
    if not (rules.index("RULE-SET,Privacy,REJECT") < rules.index("RULE-SET,Hijacking,🚫 Hijacking")
            < rules.index("RULE-SET,InternationalGaming,🎮 国际游戏")
            < rules.index("RULE-SET,ChinaGaming,DIRECT") < rules.index(siri)
            < rules.index("RULE-SET,Apple,🍎 Apple")):
        raise ValueError("SiriAI：安全/游戏/Apple 顺序不满足合同")

    def route(domain: str, include_siri: bool = True) -> tuple[str, str]:
        for rule in rules:
            if not include_siri and rule == siri:
                continue
            fields = rule.split(",")
            kind = fields[0]
            if kind == "RULE-SET":
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == "MATCH":
                return "MATCH", fields[1]
            elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                if DomainRules([rule]).matches(domain):
                    return fields[0] + "," + fields[1], fields[2]
            elif kind not in {"GEOIP", "IP-CIDR", "IP-CIDR6"}:
                raise ValueError(f"离线域名模型不支持顶层类型：{kind}")
        raise ValueError("缺少 MATCH 规则")

    transitions = []
    for domain in domains:
        current = route(domain)
        if current != ("SiriAI", TARGET):
            raise ValueError(f"SiriAI 目标被更早规则抢先匹配：{domain}: {current}")
        transitions.append(f"{domain}: {route(domain, False)[0]} → SiriAI")
    # 覆盖全部现有 Apple 域名规则的代表，以及候选、游戏、安全与邻近域名。
    apple = providers["Apple"]
    controls = apple.exact | apple.suffix | {"probe." + d for d in apple.suffix}
    controls |= {r["domain"] for r in json.loads((root / "research/SiriAI-audit.json").read_text())
                 if r["provided_rule_type"] != "DOMAIN-KEYWORD"}
    controls |= {"probe." + d for d in domains}
    controls |= {"siri.example.org", "example.org", "hmma.baidu.com", "hoyoverse.com",
                 "fastcdn.hoyoverse.com", "qq.com", "cloudflare.com", "fastly-edge.com"}
    controls -= set(domains)
    for domain in controls:
        if route(domain) != route(domain, False):
            raise ValueError(f"SiriAI 意外改变非目标域名：{domain}")
    if route("hmma.baidu.com") != ("Privacy", "REJECT"):
        raise ValueError("安全规则回归")
    if route("hoyoverse.com") != ("InternationalGaming", "🎮 国际游戏"):
        raise ValueError("国际游戏规则回归")
    if route("fastcdn.hoyoverse.com")[1] != "DIRECT":
        raise ValueError("国际游戏精确例外回归")
    return transitions, len(controls)


def validate(root: Path = ROOT) -> None:
    domains, digest = canonical(root)
    if (root / "ruleset/SiriAI.yaml").read_text() != render(domains, digest):
        raise ValueError("SiriAI 生成漂移：运行 python3 scripts/siri_ai.py --write")
    for filename, required in (
        ("rule-providers.local.yaml", ["type: file", "behavior: classical", "path: ./ruleset/SiriAI.yaml"]),
        ("rule-providers.remote.yaml", ["type: http", "behavior: classical",
          "url: https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/SiriAI.yaml",
          "path: ./ruleset-cache/SiriAI.yaml", "interval: 86400"]),
    ):
        text = (root / "config" / filename).read_text()
        blocks = re.findall(r"^  SiriAI:\n((?:    .+\n)+)", text, re.M)
        if len(blocks) != 1 or {line.strip() for line in blocks[0].splitlines()} != set(required):
            raise ValueError(f"SiriAI provider 配置漂移：{filename}")
    transitions, controls = routing_check(domains, root)
    print(f"SiriAI：{len(domains)} 个精确域名，0 重复，生成/hash/来源/引用一致；{controls} 个非目标域名模拟不变。")
    for transition in transitions:
        print("  " + transition)
    print("边界：以上是无 IP/进程元数据的离线域名模拟；实际 DNS、GeoIP、UDP 和设备资格未实测。")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="从已审计 canonical 生成本地规则")
    args = parser.parse_args()
    if args.write:
        domains, digest = canonical()
        (ROOT / "ruleset/SiriAI.yaml").write_text(render(domains, digest))
        print("已离线生成 SiriAI.yaml。")
    else:
        validate()


if __name__ == "__main__":
    main()
