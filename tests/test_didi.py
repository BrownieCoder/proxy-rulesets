"""Exact public DiDi entries and first-match validation on disposable fixtures."""
from __future__ import annotations

import contextlib
import hashlib
import io
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
from generate_catalog import generate
from siri_ai import DomainRules

HOSTS = {"www.didichuxing.com", "www.didiglobal.com"}
TARGET = "🚕 滴滴出行"
MARKER = f"  - RULE-SET,Didi,{TARGET}\n"
CONTROL_ROUTES = {
    ("ChinaMax", "🇨🇳 China-Global"): {
        "didichuxing.com", "didiglobal.com", "hk.didiglobal.com", "mexico.didiglobal.com",
        "ir.didiglobal.com", "page.udache.com", "s.didi.cn", "img0.didiglobal.com",
        "www6.didiglobal.com", "child.www.didiglobal.com", "notwww.didichuxing.com",
    },
    ("MATCH", "🧭 Final"): {
        "example.org", "www.didichuxing.com.example.org", "www.didiglobal.com.example.org",
    },
    ("Weibo", "🟠 微博"): {"www.weibo.com"},
    ("SiriAI", "🤖 AI 服务"): {"guzzoni.apple.com"},
    ("Privacy", "REJECT"): {"hmma.baidu.com"},
    ("InternationalGaming", "🎮 国际游戏"): {"hoyoverse.com"},
    ("DOMAIN,fastcdn.hoyoverse.com", "DIRECT"): {"fastcdn.hoyoverse.com"},
}


class DidiContract(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name)
        for name in ("config", "ruleset", "catalog", "rules", "research", "services"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ("sources.json", "local-rulesets.json", "sources.lock.json", "README.md"):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def complete_tree(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate.validate_tree(self.root), 0)

    def test_exact_payload_select_group_and_successful_full_fixture(self):
        payload = yaml.safe_load(self.read("ruleset/Didi.yaml"))["payload"]
        self.assertCountEqual(payload, ["DOMAIN," + host for host in HOSTS])
        group = next(g for g in yaml.safe_load(self.read("config/proxy-groups.yaml"))["proxy-groups"]
                     if g["name"] == TARGET)
        self.assertEqual(group, {"name": TARGET, "type": "select",
                                 "proxies": ["DIRECT", "🚀 节点选择", "🧭 Final"]})
        self.assertEqual(self.read("config/rules.yaml").count(MARKER), 1)
        validate.validate_didi(self.root)
        self.complete_tree()

    def test_actual_first_match_and_unchanged_non_target_routes(self):
        manifests = {}
        for name in ("sources.json", "local-rulesets.json"):
            manifests.update(json.loads(self.read(name)))
        models = {name: DomainRules(yaml.safe_load(self.read(row["path"]))["payload"])
                  for name, row in manifests.items()}
        ordered = yaml.safe_load(self.read("config/rules.yaml"))["rules"]

        def first(host, include=True):
            for rule in ordered:
                kind, operand, *target = rule.split(",")
                if kind == "RULE-SET" and (include or operand != "Didi") and models[operand].matches(host):
                    return operand, target[0]
                if kind in {"DOMAIN", "DOMAIN-SUFFIX", "DOMAIN-KEYWORD"} and DomainRules([rule]).matches(host):
                    return f"{kind},{operand}", target[0]
                if kind == "MATCH":
                    return kind, operand
            self.fail("Missing MATCH")

        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(first(host), ("Didi", TARGET))
                self.assertEqual(first(host, False), ("ChinaMax", "🇨🇳 China-Global"))
        for route, hosts in CONTROL_ROUTES.items():
            for host in hosts:
                with self.subTest(control=host):
                    self.assertEqual(first(host), route)
                    self.assertEqual(first(host, False), route)

    def test_committed_tree_calls_didi_once(self):
        with patch.object(validate, "validate_didi", side_effect=ValueError("Didi gate")) as gate:
            with self.assertRaisesRegex(ValueError, "^Didi gate$"):
                validate.validate_tree(self.root)
            gate.assert_called_once_with(self.root)

    def test_payload_and_policy_reference_are_both_exact(self):
        path = "ruleset/Didi.yaml"
        original = self.read(path)
        for bad in (original.replace("  - DOMAIN,www.didichuxing.com\n", ""),
                    original.replace("DOMAIN,www.didiglobal.com", "DOMAIN-SUFFIX,didiglobal.com"),
                    original + "  - DOMAIN,www.didiglobal.com\n"):
            with self.subTest(payload=bad):
                self.write(path, bad)
                with self.assertRaisesRegex(ValueError, "two reviewed exact hosts"):
                    validate.validate_didi(self.root)
        self.write(path, original)
        path = "config/rules.yaml"
        original = self.read(path)
        for bad in ("", MARKER * 2, "  - RULE-SET,Didi,DIRECT\n"):
            with self.subTest(reference=bad):
                self.write(path, original.replace(MARKER, bad))
                with self.assertRaisesRegex(ValueError, "exactly one valid Didi policy reference"):
                    validate.validate_didi(self.root)

    def test_security_apps_and_broad_provider_order(self):
        path = "config/rules.yaml"
        original = self.read(path)
        for anchor, after, reason in (
            ("RULE-SET,Privacy,REJECT", False, "Security, gaming and existing app"),
            ("RULE-SET,ChinaGaming,DIRECT", False, "Security, gaming and existing app"),
            ("RULE-SET,Weibo,🟠 微博", False, "existing app rules"),
            ("RULE-SET,SFExpress,📦 顺丰速运", False, "existing app rules"),
            ("RULE-SET,SiriAI,🤖 AI 服务", True, "precede broader providers"),
            ("RULE-SET,ChinaMax,🇨🇳 China-Global", True, "precede broader providers"),
        ):
            with self.subTest(anchor=anchor):
                rule = "  - " + anchor + "\n"
                self.assertEqual(original.count(rule), 1)
                self.write(path, original.replace(MARKER, "").replace(
                    rule, rule + MARKER if after else MARKER + rule))
                with self.assertRaisesRegex(ValueError, reason):
                    validate.validate_didi(self.root)

    def test_plain_and_quoted_nonsecurity_preemption_fail_helper_and_tree(self):
        path = "config/rules.yaml"
        original = self.read(path)
        for kind, operand in (("DOMAIN", "WWW.DIDICHUXING.COM"),
                              ("DOMAIN", "WWW.D\u0130D\u0130GLOBAL.COM"),
                              ("DOMAIN-SUFFIX", "DIDIGLOBAL.COM"),
                              ("DOMAIN-KEYWORD", "DIDIGLOBAL")):
            scalar = f"{kind},{operand},DIRECT"
            rule = f"  - {scalar}\n" if kind == "DOMAIN" else f'  - "{scalar}"\n'
            with self.subTest(rule=rule):
                self.write(path, original.replace(MARKER, rule + MARKER))
                with self.assertRaisesRegex(ValueError, "Didi is shadowed by an earlier rule"):
                    validate.validate_didi(self.root)
                with self.assertRaisesRegex(ValueError, "Didi is shadowed by an earlier rule"):
                    validate.validate_tree(self.root)

    def test_prior_provider_operands_are_case_insensitive(self):
        path = "ruleset/Weibo.yaml"
        original = self.read(path)
        for operand in ("WWW.DIDIGLOBAL.COM", "WWW.D\u0130D\u0130GLOBAL.COM"):
            with self.subTest(operand=operand):
                self.write(path, original + f"  - DOMAIN,{operand}\n")
                with self.assertRaisesRegex(ValueError, "Didi is shadowed.*www.didiglobal.com.*Weibo"):
                    validate.validate_didi(self.root)

    def test_later_case_variants_do_not_shadow_didi(self):
        path = "config/rules.yaml"
        original = self.read(path)
        self.write(path, original.replace(
            MARKER, MARKER + "  - DOMAIN,WWW.DIDICHUXING.COM,DIRECT\n"
            "  - DOMAIN,WWW.D\u0130D\u0130GLOBAL.COM,DIRECT\n"))
        validate.validate_didi(self.root)
        self.complete_tree()

    def test_model_rejects_uninterpretable_conditions_and_missing_provider(self):
        path = "config/rules.yaml"
        original = self.read(path)
        for rule, error in (
            ("IP-CIDR,192.0.2.0/24,DIRECT,no-resolve", "preceding IP conditions"),
            ("GEOIP,US,DIRECT", "preceding IP conditions"),
            ("MATCH,DIRECT", "preceding IP conditions or MATCH"),
            ("DOMAIN,www.didiglobal.com", "complete supported rules: DOMAIN"),
            ("DST-PORT,443,DIRECT", "Unsupported top-level rule.*DST-PORT"),
            ("RULE-SET,MissingDidi,DIRECT", "references missing providers: MissingDidi"),
            ("DOMAIN, www.didiglobal.com,DIRECT", "must not have leading or trailing ASCII spaces"),
        ):
            with self.subTest(rule=rule):
                self.write(path, original.replace(MARKER, "  - " + rule + "\n" + MARKER))
                with self.assertRaisesRegex(ValueError, error):
                    validate.validate_didi(self.root)

    def test_final_cycle_and_missing_group_fail_both_validation_entries(self):
        path = "config/proxy-groups.yaml"
        original = self.read(path)
        final = '  - name: "🧭 Final"\n    type: select\n    proxies:\n'
        self.assertEqual(original.count(final), 1)
        for member, reason in ((TARGET, "contains a group cycle"),
                               ("MissingPublicGroup", "references undefined groups")):
            with self.subTest(member=member):
                self.write(path, original.replace(final, final + f'      - "{member}"\n', 1))
                for gate in (validate.validate_didi, validate.validate_tree):
                    with self.subTest(gate=gate.__name__), self.assertRaisesRegex(ValueError, reason):
                        gate(self.root)

    def test_group_structure_and_literal_values_are_enforced(self):
        path = "config/proxy-groups.yaml"
        original = self.read(path)
        block = (f'  - name: "{TARGET}"\n    type: select\n    proxies:\n'
                 '      - DIRECT\n      - "🚀 节点选择"\n      - "🧭 Final"\n')
        self.assertIn(block, original)
        for changed, error in (
            (block.replace("type: select", "type: fallback"), "Didi must be a DIRECT-first select"),
            (block.replace('      - "🧭 Final"\n', ""), "Didi must be a DIRECT-first select"),
            (block.replace('      - DIRECT\n      - "🚀 节点选择"\n',
                           '      - "🚀 节点选择"\n      - DIRECT\n'), "Didi must be a DIRECT-first select"),
            (block.replace("  - name", '  - &hidden name'), "Public config/proxy-groups"),
            (block + '    "type": select\n', "duplicate group field: type"),
        ):
            with self.subTest(group=changed):
                self.write(path, original.replace(block, changed))
                with self.assertRaisesRegex(ValueError, error):
                    validate.validate_didi(self.root)
                with self.assertRaisesRegex(ValueError, error):
                    validate.validate_tree(self.root)
        quoted = block.replace("type: select", "'type': \"select\"")
        self.write(path, original.replace(block, quoted))
        validate.validate_didi(self.root)
        self.complete_tree()

    def test_legal_security_preemption_remains_allowed(self):
        lock_path = "sources.lock.json"
        original_lock = self.read(lock_path)
        for provider in ("Privacy", "Hijacking"):
            with self.subTest(provider=provider):
                path = f"ruleset/{provider}_No_Resolve.yaml"
                original = self.read(path)
                added = "".join("  - DOMAIN," + host.upper() + "\n" for host in sorted(HOSTS))
                self.write(path, original + added)
                data = (self.root / path).read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                lock = json.loads(original_lock)
                lock["rulesets"][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                self.write(lock_path, json.dumps(lock, ensure_ascii=False))
                with contextlib.redirect_stdout(io.StringIO()):
                    generate(self.root, write=True)
                    validate.validate_didi(self.root)
                self.complete_tree()
                self.write(path, original)
                self.write(lock_path, original_lock)


if __name__ == "__main__":
    unittest.main()
