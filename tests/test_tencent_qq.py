"""QQ exact public-entry routing with real public-tree fixtures."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate
from siri_ai import DomainRules

HOST = "im.qq.com"
TARGET = "🐧 腾讯 QQ"
MARKER = f"  - RULE-SET,TencentQQ,{TARGET}\n"
CONTROLS = {
    "y.qq.com", "v.qq.com", "weixin.qq.com", "game.qq.com", "mail.qq.com", "qzone.qq.com",
    "qq.com", "www.qq.com", "gtimg.cn", "dldir1.qq.com", "connect.qq.com", "qun.qq.com",
    "child.im.qq.com", "notim.qq.com", "im.qq.com.example.org", "guzzoni.apple.com",
    "hmma.baidu.com", "fastcdn.hoyoverse.com", "www.bilibili.com", "example.org",
}


class TencentQQContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for folder in ("config", "ruleset", "research", "catalog", "services", "rules"):
            shutil.copytree(ROOT / folder, self.root / folder)
        for file in ("README.md", "sources.json", "sources.lock.json", "local-rulesets.json"):
            shutil.copyfile(ROOT / file, self.root / file)

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def gate(self):
        validate.validate_tencent_qq(self.root)

    def test_independent_yaml_model_and_real_first_matches(self):
        raw = yaml.safe_load(self.read("ruleset/TencentQQ.yaml"))["payload"]
        self.assertEqual(raw, ["DOMAIN," + HOST])
        self.assertLessEqual(CONTROLS, validate.TENCENT_QQ_CONTROLS)
        self.assertFalse(any(DomainRules(raw).matches(host) for host in CONTROLS))
        groups = yaml.safe_load(self.read("config/proxy-groups.yaml"))["proxy-groups"]
        self.assertEqual([group for group in groups if group["name"] == TARGET], [
            {"name": TARGET, "type": "select", "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]},
        ])
        manifests = json.loads(self.read("local-rulesets.json")) | json.loads(self.read("sources.json"))
        data = {key: DomainRules(yaml.safe_load(self.read(value["path"]))["payload"])
                for key, value in manifests.items()}
        ordered = yaml.safe_load(self.read("config/rules.yaml"))["rules"]

        def route(host, skip=False):
            for rule in ordered:
                fields = rule.split(",")
                kind = fields[0]
                if kind == "RULE-SET":
                    if not (skip and fields[1] == "TencentQQ") and data[fields[1]].matches(host):
                        return fields[1], fields[2]
                elif kind.startswith("DOMAIN") and DomainRules([rule]).matches(host):
                    return ",".join(fields[:2]), fields[2]
                elif kind == "MATCH":
                    return kind, fields[1]
            self.fail("Missing MATCH")

        self.assertEqual(route(HOST), ("TencentQQ", TARGET))
        self.assertEqual(route(HOST, True), ("ChinaMax", "🇨🇳 China-Global"))
        for host in CONTROLS:
            with self.subTest(host=host):
                self.assertEqual(route(host), route(host, True))
        self.assertEqual(route("y.qq.com"), ("QQMusic", "🎧 QQ 音乐"))
        self.assertEqual(route("v.qq.com"), ("TencentVideo", "📺 腾讯视频"))
        self.assertEqual(route("weixin.qq.com"), ("WeChat", "💬 微信"))
        self.assertEqual(route("game.qq.com"), ("ChinaGaming", "DIRECT"))

    def test_real_tree_calls_app_gate(self):
        with patch.object(validate, "validate_tencent_qq", wraps=validate.validate_tencent_qq) as gate:
            self.assertEqual(validate.validate_tree(self.root), 0)
            gate.assert_called_once_with(self.root)

    def test_payload_scope_and_hidden_comment_controls(self):
        rel = "ruleset/TencentQQ.yaml"
        original = self.read(rel)
        for text in (original.replace("DOMAIN,", "DOMAIN-SUFFIX,"),
                     original.replace(HOST, "qq.com"),
                     original.replace("  - DOMAIN," + HOST + "\n", ""),
                     original + "  - DOMAIN," + HOST + "\n"):
            with self.subTest(text=text):
                self.write(rel, text)
                with self.assertRaisesRegex(ValueError, "reviewed exact host"):
                    self.gate()
        self.write(rel, original + "# bad\x0b control\n")
        with self.assertRaisesRegex(ValueError, "U\\+000B"):
            self.gate()

    def test_routes_fail_closed_for_shadowing_and_invalid_reference_fields(self):
        rel = "config/rules.yaml"
        original = self.read(rel)
        for rule, reason in {
            f"DOMAIN,{HOST},DIRECT": "shadowed",
            "DOMAIN,IM.QQ.COM,DIRECT": "shadowed",
            "DOMAIN,\u0130M.QQ.COM,DIRECT": "shadowed",
            "DOMAIN-SUFFIX,QQ.COM,DIRECT": "shadowed",
            "DOMAIN-KEYWORD,IM.QQ,DIRECT": "shadowed",
            "DOMAIN,,DIRECT": "complete rules",
            "RULE-SET,QQMissingProvider,DIRECT": "missing provider",
            "IP-CIDR,192.0.2.0/24,DIRECT,no-resolve": "preceding IP conditions",
            "GEOSITE,CN,DIRECT": "Unsupported rule",
        }.items():
            with self.subTest(rule=rule):
                self.write(rel, original.replace(MARKER, "  - " + rule + "\n" + MARKER))
                with self.assertRaisesRegex(ValueError, reason):
                    self.gate()
        # Go simple lowercase maps dotted capital I to ASCII i in this operand.
        self.write(rel, original.replace(MARKER, "  - DOMAIN,\u0130M.QQ.COM,DIRECT\n" + MARKER))
        with self.assertRaisesRegex(ValueError, "TencentQQ is shadowed"):
            validate.validate_tree(self.root)

    def test_missing_duplicate_wrong_and_misordered_marker(self):
        rel = "config/rules.yaml"
        original = self.read(rel)
        moved_before_weibo = original.replace(MARKER, "").replace(
            "  - RULE-SET,Weibo,", MARKER + "  - RULE-SET,Weibo,")
        for route, reason in (
            (original.replace(MARKER, ""), "dedicated policy reference"),
            (original.replace(MARKER, MARKER * 2), "dedicated policy reference"),
            (original.replace(MARKER, "  - RULE-SET,TencentQQ,DIRECT\n"), "dedicated policy reference"),
            (moved_before_weibo, "order relative to Weibo"),
            (original.replace(MARKER, "").replace("  - MATCH,", MARKER + "  - MATCH,"), "order relative"),
            (original.replace(MARKER, "  - MATCH,DIRECT\n" + MARKER), "terminal MATCH"),
        ):
            with self.subTest(reason=reason):
                self.write(rel, route)
                with self.assertRaisesRegex(ValueError, reason):
                    self.gate()

    def test_legal_security_priority_and_non_targets(self):
        manifests = json.loads(self.read("sources.json"))
        paths = [manifests[key]["path"] for key in ("Privacy", "Hijacking")]
        original = {rel: self.read(rel) for rel in paths}
        for rel in paths:
            with self.subTest(provider=rel):
                self.write(rel, original[rel] + "  - DOMAIN,IM.QQ.COM\n")
                self.gate()
                self.write(rel, original[rel])

    def test_group_uses_typed_structure_and_enforces_exact_members(self):
        rel = "config/proxy-groups.yaml"
        original = self.read(rel)
        anchor = f'  - name: "{TARGET}"\n    type: select\n    proxies:\n'
        self.write(rel, original.replace(anchor, anchor.replace('"', "'").replace(
            "type: select", "'type': 'select' # literal")))
        self.gate()
        for before, after, reason in (
            (anchor, anchor.replace("type: select", "type: url-test"), "DIRECT-first select"),
            (anchor + "      - DIRECT\n", anchor, "DIRECT-first select"),
            (anchor, anchor.replace("    proxies:\n", "    include-all: true\n    proxies:\n"), "DIRECT-first select"),
            (anchor, anchor.replace("    type: select\n", "    type: select\n    'type': select\n"), "Public config/proxy-groups.yaml"),
        ):
            with self.subTest(reason=reason):
                self.assertIn(before, original)
                self.write(rel, original.replace(before, after))
                with self.assertRaisesRegex(ValueError, reason):
                    self.gate()

    def test_direct_gate_uses_ordered_rule_structure(self):
        rel = "config/rules.yaml"
        original = self.read(rel)
        for text in (original + "rules: []\n", original.replace("rules:", "wrong:", 1),
                     original.replace(MARKER, f"  - \"RULE-SET,TencentQQ, {TARGET}\"\n")):
            with self.subTest(text=text.splitlines()[0]):
                self.write(rel, text)
                with self.assertRaisesRegex(ValueError, "Public config/rules.yaml"):
                    self.gate()
