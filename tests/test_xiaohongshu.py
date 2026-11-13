"""RedNote scope, policy choice and first-match routing regressions."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate


class RedNoteRouting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('config', 'ruleset'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('sources.json', 'local-rulesets.json'):
            shutil.copyfile(ROOT / name, self.root / name)
        self.providers = set(json.loads((ROOT / 'sources.json').read_text()))
        self.providers |= set(json.loads((ROOT / 'local-rulesets.json').read_text()))

    def test_current_routing_and_default(self):
        validate.validate_config_references(self.providers, self.root)
        validate.validate_xiaohongshu(self.root)

    def test_broadening_scope_is_rejected(self):
        path = self.root / 'ruleset/Xiaohongshu.yaml'
        path.write_text(path.read_text() + '  - DOMAIN-SUFFIX,cloudflare.com\n')
        with self.assertRaisesRegex(ValueError, 'four reviewed'):
            validate.validate_xiaohongshu(self.root)

    def test_security_shadowing_is_detected(self):
        path = self.root / 'ruleset/Privacy_No_Resolve.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,creator.rednote.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_xiaohongshu(self.root)

    def test_late_rule_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        rule = '  - RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n'
        text = path.read_text().replace(rule, '')
        path.write_text(text.replace('  - MATCH,', rule + '  - MATCH,'))
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_config_references(self.providers, self.root)

    def test_bypassing_security_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        rule = '  - RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n'
        path.write_text(path.read_text().replace(rule, '').replace('rules:\n', 'rules:\n' + rule))
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_config_references(self.providers, self.root)

    def test_proxy_default_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        text = path.read_text()
        start = text.index('  - name: "📕 小红书 / REDnote"')
        prefix, suffix = text[:start], text[start:]
        path.write_text(prefix + suffix.replace('      - DIRECT\n', '', 1))
        with self.assertRaisesRegex(ValueError, 'default to DIRECT'):
            validate.validate_config_references(self.providers, self.root)


if __name__ == '__main__':
    unittest.main()
