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

    def test_security_matches_remain_valid(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text()
                    path.write_text(original + f'  - {kind},rednote.com\n'
                                    + f'  - {kind},creator.rednote.com\n')
                    try:
                        validate.validate_xiaohongshu(self.root)
                    finally:
                        path.write_text(original)

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,creator.rednote.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_xiaohongshu(self.root)

    def test_security_match_with_wrong_policy_is_rejected(self):
        path = self.root / 'ruleset/Privacy_No_Resolve.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,creator.rednote.com\n')
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT'))
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_xiaohongshu(self.root)

    def test_unknown_top_level_rule_is_not_silently_ignored(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text()
        for rule in ('PROCESS-NAME,rednote,DIRECT', 'DST-PORT,443,DIRECT',
                     'AND,((DOMAIN,rednote.com)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', f'rules:\n  - {rule}\n'))
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_xiaohongshu(self.root)

    def test_commented_marker_cannot_replace_active_rule(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('  - RULE-SET,Bilibili,📺 Bilibili',
                                                '  # RULE-SET,Bilibili,📺 Bilibili'))
        with self.assertRaisesRegex(ValueError, 'missing expected rule: RULE-SET,Bilibili'):
            validate.validate_config_references(self.providers, self.root)

    def test_duplicate_marker_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + '  - RULE-SET,Bilibili,📺 Bilibili\n')
        with self.assertRaisesRegex(ValueError, 'duplicate expected rule: RULE-SET,Bilibili'):
            validate.validate_config_references(self.providers, self.root)

    def test_comment_does_not_duplicate_active_marker(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + '  # RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n')
        validate.validate_config_references(self.providers, self.root)

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
