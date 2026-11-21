"""Mango TV exact public hostname, precedence and real full-tree regressions."""

import contextlib
import hashlib
import io
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

HOST = "www.mgtv.com"
TARGET = "🥭 芒果TV"
MARKER = "  - RULE-SET,MangoTV,🥭 芒果TV\n"
ROUTES = "config/rules.yaml"
GROUPS = "config/proxy-groups.yaml"
PAYLOAD = "ruleset/MangoTV.yaml"
FINAL = "  - MATCH,🧭 Final\n"
GROUP = (
    '  - name: "🥭 芒果TV"\n'
    '    type: select\n'
    '    proxies:\n'
    '      - DIRECT\n'
    '      - "🚀 节点选择"\n'
    '      - "🧭 Final"\n'
)
CONTROLS = {
    "mgtv.com", "w.mgtv.com", "corp.mgtv.com", "app.mgtv.com", "img.mgtv.com", "i.mgtv.com",
    "7.mgtv.com", "club.mgtv.com", "order.mgtv.com", "log.mgtv.com", "download.hitv.com",
    "download.imgo.tv", "download.hunantv.com", "ugc.hitv.com", "ossimg.hitv.com", "i2.hitv.com",
    "www.hunantv.com", "www.iqiyi.com", "www.youku.com", "v.qq.com", "www.bilibili.com",
    "weibo.com", "game.qq.com", "guzzoni.apple.com", "example.org",
}
LOOKALIKES = {"child.www.mgtv.com", "notwww.mgtv.com", "www.mgtv.com.example.org"}


class MangoTVContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for directory in ("config", "ruleset", "catalog", "rules", "research", "services"):
            shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ("sources.json", "local-rulesets.json", "sources.lock.json", "README.md"):
            shutil.copyfile(ROOT / filename, self.root / filename)

    def read(self, path):
        return (self.root / path).read_text(encoding="utf-8")

    def write(self, path, text):
        (self.root / path).write_text(text, encoding="utf-8")

    def check_tree(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate.validate_tree(self.root), 0)

    def rejected(self, reason, tree_reason=None):
        with self.assertRaisesRegex(ValueError, reason):
            validate.validate_mango_tv(self.root)
        if tree_reason is not None:
            with self.assertRaisesRegex(ValueError, tree_reason):
                validate.validate_tree(self.root)

    def test_real_public_fixture_passes(self):
        validate.validate_mango_tv(self.root)
        self.check_tree()

    def test_literal_rules_and_selected_group_match_yaml_oracle(self):
        self.assertEqual(yaml.safe_load(self.read(PAYLOAD)), {"payload": ["DOMAIN,www.mgtv.com"]})
        group, = (group for group in yaml.safe_load(self.read(GROUPS))["proxy-groups"]
                  if group["name"] == "🥭 芒果TV")
        self.assertEqual(group, {"name": "🥭 芒果TV", "type": "select",
                                "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]})

    def test_first_match_and_unchanged_international_and_other_controls(self):
        manifest = json.loads(self.read("sources.json")) | json.loads(self.read("local-rulesets.json"))
        models = {
            name: DomainRules(yaml.safe_load(self.read(row["path"]))["payload"])
            for name, row in manifest.items()
        }
        ordered = yaml.safe_load(self.read(ROUTES))["rules"]

        def route(host, include=True):
            for text in ordered:
                kind, *fields = text.split(",")
                if kind == "RULE-SET":
                    provider, target = fields
                    if (include or provider != "MangoTV") and models[provider].matches(host):
                        return provider, target
                elif kind == "MATCH":
                    return kind, fields[0]
                elif kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"}:
                    if DomainRules([kind + "," + fields[0]]).matches(host):
                        return kind + "," + fields[0], fields[1]
            self.fail("Expected MATCH as fallback")

        self.assertEqual(route(HOST), ("MangoTV", TARGET))
        self.assertEqual(route(HOST, include=False), ("ChinaMax", "🇨🇳 China-Global"))
        self.assertEqual(route("w.mgtv.com"), ("ChinaMax", "🇨🇳 China-Global"))
        self.assertEqual(route("log.mgtv.com"), ("Privacy", "REJECT"))
        self.assertEqual(route("www.youku.com"), ("Youku", "🎞️ 优酷"))
        self.assertEqual(route("v.qq.com"), ("TencentVideo", "📺 腾讯视频"))
        self.assertEqual(route("game.qq.com"), ("ChinaGaming", "DIRECT"))
        self.assertEqual(route("example.org"), ("MATCH", "🧭 Final"))
        self.assertEqual(CONTROLS, validate.MANGO_TV_CONTROLS)
        for control in CONTROLS | LOOKALIKES:
            with self.subTest(control=control):
                self.assertEqual(route(control), route(control, include=False))

    def test_rejects_other_exact_hosts_or_broad_rule(self):
        for rule in ("DOMAIN,w.mgtv.com", "DOMAIN-SUFFIX,mgtv.com", "DOMAIN-KEYWORD,mgtv",
                     "DOMAIN,www.mgtv.com\n  - DOMAIN,download.hitv.com"):
            with self.subTest(rule=rule):
                self.write(PAYLOAD, "payload:\n  - " + rule + "\n")
                self.rejected("only the reviewed exact host", "only the reviewed exact host")

    def test_duplicate_and_invalid_yaml_payload_rejected(self):
        original = self.read(PAYLOAD)
        self.write(PAYLOAD, original + "  - DOMAIN,www.mgtv.com\n")
        self.rejected("duplicate rules", "local ruleset contains duplicate entries")
        self.write(PAYLOAD, original + "payload: []\n")
        self.rejected("one payload mapping", "one payload mapping")

    def test_reference_must_be_active_unique_and_for_own_group(self):
        original = self.read(ROUTES)
        for replacement in ("", "  # RULE-SET,MangoTV,🥭 芒果TV\n", "  - RULE-SET,MangoTV,DIRECT\n",
                            MARKER + MARKER):
            with self.subTest(replacement=replacement):
                self.write(ROUTES, original.replace(MARKER, replacement, 1))
                self.rejected("exactly one dedicated policy reference", "exactly one dedicated policy reference")

    def test_required_predecessors_and_successors(self):
        original = self.read(ROUTES)
        for anchor, before, reason in (
            ("RULE-SET,Privacy,REJECT", True, "must follow security"),
            ("RULE-SET,ChinaGaming,DIRECT", True, "must follow security"),
            ("RULE-SET,WeChat,💬 微信", True, "must follow security"),
            ("RULE-SET,Weibo,🟠 微博", True, "must follow security"),
            ("RULE-SET,SiriAI,🤖 AI 服务", False, "must precede broader"),
            ("RULE-SET,GlobalMedia,🛰️ International-Global", False, "must precede broader"),
            ("GEOIP,CN,DIRECT,no-resolve", False, "must precede broader"),
            ("RULE-SET,ChinaMax,🇨🇳 China-Global", False, "must precede broader"),
        ):
            with self.subTest(anchor=anchor):
                literal = "  - " + anchor + "\n"
                moved = MARKER + literal if before else literal + MARKER
                self.write(ROUTES, original.replace(MARKER, "").replace(literal, moved, 1))
                self.rejected(reason, reason if anchor.startswith(("RULE-SET,Weibo", "RULE-SET,SiriAI")) else None)

    def test_valid_equivalent_group_structure_passes(self):
        original = self.read(GROUPS)
        equivalent = GROUP.replace('"🥭 芒果TV"', "'🥭 芒果TV'")
        equivalent = equivalent.replace("type: select", "'type': 'select' # literal select")
        equivalent = equivalent.replace("- DIRECT", "- 'DIRECT' # builtin")
        self.assertEqual(yaml.safe_load(original), yaml.safe_load(original.replace(GROUP, equivalent)))
        self.write(GROUPS, original.replace(GROUP, equivalent))
        validate.validate_mango_tv(self.root)
        self.check_tree()

    def test_wrong_type_default_final_or_group_missing_fails(self):
        original = self.read(GROUPS)
        for replacement in (GROUP.replace("type: select", "type: fallback"),
                            GROUP.replace("      - DIRECT\n", ""),
                            GROUP.replace('      - "🧭 Final"\n', ""),
                            GROUP.replace('      - "🚀 节点选择"\n', ""),
                            GROUP + "    lazy: true\n", ""):
            with self.subTest(replacement=replacement):
                self.write(GROUPS, original.replace(GROUP, replacement))
                self.rejected("DIRECT-first select group",
                              "DIRECT-first select group" if replacement else "undefined policy groups")

    def test_invalid_public_root_or_policy_group_syntax(self):
        original_rules = self.read(ROUTES)
        self.write(ROUTES, original_rules + "\nrules: []\n")
        self.rejected(r"Public config/rules\.yaml", r"Public config/rules\.yaml")
        self.write(ROUTES, original_rules)
        original_groups = self.read(GROUPS)
        for broken in ("    type: !!str select\n", "    type: select\n    'type': fallback\n"):
            with self.subTest(broken=broken):
                self.write(GROUPS, original_groups.replace(GROUP, GROUP.replace("    type: select\n", broken)))
                self.rejected(r"Public config/proxy-groups\.yaml", r"Public config/proxy-groups\.yaml")

    def test_missing_and_unknown_provider_fail(self):
        original = self.read("local-rulesets.json")
        local = json.loads(original)
        del local["MangoTV"]
        self.write("local-rulesets.json", json.dumps(local))
        self.rejected("reviewed classical local provider", "ruleset file mismatch")
        self.write("local-rulesets.json", original)
        original_rules = self.read(ROUTES)
        self.write(ROUTES, original_rules.replace(MARKER, "  - RULE-SET,MissingMangoTV,DIRECT\n" + MARKER))
        self.rejected("references missing providers: MissingMangoTV", "references undefined providers")

    def test_invalid_top_level_shapes_cannot_bypass_gate(self):
        original_rules = self.read(ROUTES)
        for rule, reason, tree_reason in (
            ("DST-PORT,443,DIRECT", "Unsupported top-level rule", "Unsupported top-level rule"),
            ("DOMAIN,www.mgtv.com", "requires complete supported rules", "BaiduMap encountered an unsupported domain rule"),
            ("MATCH,DIRECT,extra", "requires complete supported rules", "BaiduMap encountered an unsupported MATCH rule"),
            ("RULE-SET", "requires complete supported rules", None),
            ("GEOIP,US,DIRECT,invalid", "requires complete supported rules", "requires complete supported rules"),
            ("DOMAIN,www.mgtv.com ,DIRECT", "leading or trailing ASCII spaces", "leading or trailing ASCII spaces"),
        ):
            with self.subTest(rule=rule):
                self.write(ROUTES, original_rules + "  - " + rule + "\n")
                self.rejected(reason, tree_reason)

    def test_ip_condition_preceding_app_fails_closed(self):
        original = self.read(ROUTES)
        for rule in ("GEOIP,US,DIRECT", "IP-CIDR,192.0.2.0/24,DIRECT,no-resolve",
                     "IP-CIDR6,2001:db8::/32,DIRECT,no-resolve"):
            with self.subTest(rule=rule):
                self.write(ROUTES, original.replace(MARKER, "  - " + rule + "\n" + MARKER))
                self.rejected("cannot validate preceding IP conditions", "cannot validate preceding IP conditions")

    def test_existing_provider_or_early_match_can_shadow_target(self):
        original = self.read(ROUTES)
        self.write(ROUTES, original.replace(MARKER, FINAL + MARKER).removesuffix(FINAL))
        self.rejected("MangoTV is shadowed", "MangoTV is shadowed")
        self.write(ROUTES, original)
        path = "ruleset/Weibo.yaml"
        self.write(path, self.read(path) + "  - DOMAIN,WWW.MGTV.COM\n")
        self.rejected("MangoTV is shadowed.*Weibo")

    def test_ascii_case_of_top_level_domain_operands_cannot_hide_shadowing(self):
        original = self.read(ROUTES)
        for rule in ("DOMAIN,www.mgtv.com,DIRECT", "DOMAIN,WWW.MGTV.COM,DIRECT",
                     "DOMAIN-SUFFIX,MGTV.COM,DIRECT", "DOMAIN-KEYWORD,MGTV,DIRECT"):
            with self.subTest(rule=rule):
                self.write(ROUTES, original.replace(MARKER, "  - " + rule + "\n" + MARKER))
                self.rejected("MangoTV is shadowed", "MangoTV is shadowed")

    def test_valid_security_precedence_still_passes_full_tree(self):
        lock_original = self.read("sources.lock.json")
        for provider in ("Privacy", "Hijacking"):
            with self.subTest(provider=provider), contextlib.redirect_stdout(io.StringIO()):
                path = json.loads(self.read("sources.json"))[provider]["path"]
                original = self.read(path)
                self.write(path, original + "  - DOMAIN,WWW.MGTV.COM\n")
                data = (self.root / path).read_bytes()
                sha = hashlib.sha256(data).hexdigest()
                lock = json.loads(lock_original)
                lock["rulesets"][provider].update(bytes=len(data), sha256=sha, upstream_sha256=sha)
                self.write("sources.lock.json", json.dumps(lock))
                generate(self.root, write=True)
                validate.validate_mango_tv(self.root)
                self.check_tree()
                self.write(path, original)
                self.write("sources.lock.json", lock_original)
                generate(self.root, write=True)


if __name__ == "__main__":
    unittest.main()
