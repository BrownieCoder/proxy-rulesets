"""Public-entry first-match and full-tree regressions for Huolala."""
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate
from generate_catalog import generate
from siri_ai import DomainRules

HOSTS = ["www.huolala.cn"]
PROVIDER = "Huolala"
TARGET = "🚚 货拉拉"
MARKER = f"  - RULE-SET,{PROVIDER},{TARGET}\n"
ROUTES = "config/rules.yaml"
GROUPS = "config/proxy-groups.yaml"
PAYLOAD = f"ruleset/{PROVIDER}.yaml"
CONTROLS = ["dappweb.huolala.cn","example.org","fastcdn.hoyoverse.com","guzzoni.apple.com","hmma.baidu.com","hoyoverse.com","huolala.cn","huolala.co","im.qq.com","open.huolala.cn","v.qq.com","weixin.qq.com","wuliu.huolala.cn","www.bilibili.com","www.douyin.com","www.google.com","www.hllep.com","www.lalamove.com","www.taobao.com","www.youku.com","y.qq.com"]


class HuolalaContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ("config", "ruleset", "catalog", "rules", "research", "services"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ("README.md", "sources.json", "sources.lock.json", "local-rulesets.json"):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, path):
        return (self.root / path).read_text(encoding="utf-8")

    def write(self, path, text):
        (self.root / path).write_text(text, encoding="utf-8")

    def test_exact_scope_and_real_first_matches(self):
        entries = yaml.safe_load(self.read(PAYLOAD))["payload"]
        self.assertEqual(entries, ["DOMAIN," + host for host in HOSTS])
        group, = [group for group in yaml.safe_load(self.read(GROUPS))["proxy-groups"]
                  if group["name"] == TARGET]
        self.assertEqual(group, {"name": TARGET, "type": "select",
                                 "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]})
        manifests = json.loads(self.read("sources.json")) | json.loads(self.read("local-rulesets.json"))
        models = {key: DomainRules(yaml.safe_load(self.read(record["path"]))["payload"])
                  for key, record in manifests.items()}
        ordered = yaml.safe_load(self.read(ROUTES))["rules"]

        def route(host, skip_app=False):
            for rule in ordered:
                kind, operand, *policy = rule.split(",")
                if kind == "RULE-SET":
                    if not (skip_app and operand == PROVIDER) and models[operand].matches(host):
                        return operand, policy[0]
                elif kind.startswith("DOMAIN") and DomainRules([rule]).matches(host):
                    return kind + "," + operand, policy[0]
                elif kind == "MATCH":
                    return kind, operand
            self.fail("Missing MATCH")

        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(route(host), (PROVIDER, TARGET))
                self.assertEqual(route(host, True), ("ChinaMax", "🇨🇳 China-Global"))
        shapes = {item for host in HOSTS for item in ("child." + host, "not" + host, host + ".example.org")}
        for host in shapes | set(CONTROLS):
            with self.subTest(control=host):
                self.assertFalse(models[PROVIDER].matches(host))
                self.assertEqual(route(host), route(host, True))
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_rejects_broader_payload(self):
        original = self.read(PAYLOAD)
        self.write(PAYLOAD, original.replace("DOMAIN,", "DOMAIN-SUFFIX,", 1))
        with self.assertRaisesRegex(ValueError, "reviewed exact hosts"):
            validate.validate_huolala(self.root)

    def test_inline_shadowing_matches_case_fold_without_rejecting_later_rule(self):
        original = self.read(ROUTES)
        host = HOSTS[0]
        spellings = dict.fromkeys((host, host.upper(), host.upper().replace("I", "\u0130")))
        for name in spellings:
            with self.subTest(spelling=name):
                row = f"  - DOMAIN,{name},DIRECT\n"
                self.write(ROUTES, original.replace(MARKER, row + MARKER))
                with self.assertRaisesRegex(ValueError, f"{PROVIDER} is shadowed"):
                    validate.validate_huolala(self.root)
        with self.assertRaisesRegex(ValueError, f"{PROVIDER} is shadowed"):
            validate.validate_tree(self.root)
        self.write(ROUTES, original.replace(MARKER, MARKER + row))
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_refuses_unknown_or_unsupported_preceding_conditions(self):
        original = self.read(ROUTES)
        rows = (("RULE-SET,MissingProvider,DIRECT", "missing provider"),
                ("DST-PORT,443,DIRECT", "does not support"),
                ("DOMAIN,,DIRECT", "requires complete rules"),
                ("IP-CIDR,192.0.2.0/24,DIRECT,no-resolve", "preceding IP conditions"))
        for text, reason in rows:
            with self.subTest(rule=text):
                self.write(ROUTES, original.replace(MARKER, f"  - {text}\n" + MARKER))
                with self.assertRaisesRegex(ValueError, reason):
                    validate.validate_huolala(self.root)

    def test_refuses_duplicate_rule_wrong_position_and_invalid_default_group(self):
        original = self.read(ROUTES)
        for text, reason in (
            (original.replace(MARKER, MARKER * 2), "exactly one dedicated policy"),
            (original.replace(MARKER, "").replace("  - MATCH,", MARKER + "  - MATCH,"), "invalid routing position"),
        ):
            with self.subTest(reason=reason):
                self.write(ROUTES, text)
                with self.assertRaisesRegex(ValueError, reason):
                    validate.validate_huolala(self.root)
        self.write(ROUTES, original)
        source = self.read(GROUPS)
        group = f'  - name: "{TARGET}"\n    type: select\n    proxies:\n      - DIRECT\n'
        self.assertIn(group, source)
        self.write(GROUPS, source.replace(group, group.removesuffix("      - DIRECT\n")))
        with self.assertRaisesRegex(ValueError, "DIRECT-first"):
            validate.validate_huolala(self.root)

    def test_full_tree_and_independent_gate_reject_cycles_and_unknown_groups(self):
        original = self.read(GROUPS)
        final = '  - name: "🧭 Final"\n    type: select\n    proxies:\n'
        self.assertEqual(original.count(final), 1)
        for member, reason in ((TARGET, "contains a group cycle"),
                               ("MissingPublicGroup", "references undefined groups")):
            self.write(GROUPS, original.replace(final, final + f'      - "{member}"\n'))
            for gate in (validate.validate_huolala, validate.validate_tree):
                with self.subTest(member=member, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, reason):
                        gate(self.root)

    def test_legal_security_precedence_holds(self):
        manifests = json.loads(self.read("sources.json"))
        original_lock = self.read("sources.lock.json")
        for provider in ("Privacy", "Hijacking"):
            with self.subTest(provider=provider):
                path = manifests[provider]["path"]
                original = self.read(path)
                data = (original + f"  - DOMAIN,{HOSTS[0]}\n").encode("utf-8")
                (self.root / path).write_bytes(data)
                lock = json.loads(original_lock)
                digest = hashlib.sha256(data).hexdigest()
                lock["rulesets"][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                self.write("sources.lock.json", json.dumps(lock, ensure_ascii=False))
                generate(self.root, write=True)
                self.assertEqual(validate.validate_tree(self.root), 0)
                self.write(path, original)
                self.write("sources.lock.json", original_lock)


if __name__ == "__main__":
    unittest.main()
