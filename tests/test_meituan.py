"""Public Meituan exact-host contract through the real live/staged validator."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules
import validate


class MeituanRouting(unittest.TestCase):
    HOSTS = {'www.meituan.com', 'i.meituan.com', 'waimai.meituan.com',
             'img.meituan.net', 'p0.meituan.net', 'p1.meituan.net', 's3plus.meituan.net'}
    MARKER = '  - RULE-SET,Meituan,🍜 美团\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, name, old, new):
        path = self.root / name
        self.assertIn(old, path.read_text())
        path.write_text(path.read_text().replace(old, new))

    def test_live_and_staged_contracts(self):
        validate.validate_meituan(ROOT)
        validate.validate_meituan(self.root)

    def test_exact_scope_and_child_boundaries(self):
        payload = yaml.safe_load((ROOT / 'ruleset/Meituan.yaml').read_text())['payload']
        self.assertEqual(len(payload), len(self.HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in self.HOSTS})
        model = DomainRules(payload)
        for host in self.HOSTS:
            self.assertTrue(model.matches(host))
            for control in ('child.' + host, 'not' + host, host + '.example.org'):
                self.assertFalse(model.matches(control))

    def test_missing_or_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/Meituan.yaml'
        original = path.read_text()
        for mutated in (original.replace('  - DOMAIN,www.meituan.com\n', ''),
                        original + '  - DOMAIN,www.meituan.com\n'):
            path.write_text(mutated)
            with self.assertRaisesRegex(ValueError, 'seven reviewed exact hosts'):
                validate.validate_meituan(self.root)

    def test_scope_broadening_is_rejected_by_tree_gate(self):
        self.mutate('ruleset/Meituan.yaml', 'DOMAIN,www.meituan.com', 'DOMAIN-SUFFIX,meituan.com')
        with self.assertRaisesRegex(ValueError, 'seven reviewed exact hosts'):
            validate.validate_tree(self.root)

    def test_late_rule_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_meituan(self.root)

    def test_bypassing_security_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_meituan(self.root)

    def test_unknown_rule_type_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '  - DST-PORT,443,DIRECT\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_meituan(self.root)

    def test_comment_cannot_replace_active_reference(self):
        self.mutate('config/rules.yaml', self.MARKER, self.MARKER.replace('  - ', '  # '))
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_meituan(self.root)

    def test_duplicate_or_wrong_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text()
        for mutated in (original + self.MARKER, original.replace(self.MARKER, '  - RULE-SET,Meituan,DIRECT\n')):
            path.write_text(mutated)
            with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                validate.validate_meituan(self.root)

    def test_commented_marker_does_not_duplicate_active_rule(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + self.MARKER.replace('  - ', '  # '))
        validate.validate_meituan(self.root)

    def test_direct_first_select_with_manual_proxy(self):
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text())['proxy-groups']
        group = next(group for group in groups if group['name'] == '🍜 美团')
        self.assertEqual(group['type'], 'select')
        self.assertEqual(group['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', group['proxies'])

    def test_wrong_group_type_or_default_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        prefix, group = path.read_text().split('  - name: "🍜 美团"\n', 1)
        for wrong in (group.replace('type: select', 'type: fallback', 1),
                      group.replace('      - DIRECT\n', '', 1)):
            path.write_text(prefix + '  - name: "🍜 美团"\n' + wrong)
            with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                validate.validate_meituan(self.root)

    def test_missing_proxy_option_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        prefix, group = path.read_text().split('  - name: "🍜 美团"\n', 1)
        path.write_text(prefix + '  - name: "🍜 美团"\n' + group.replace('      - "🚀 节点选择"\n', '', 1))
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_meituan(self.root)

    def test_legal_security_updates_remain_valid(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text()
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},www.meituan.com\n')
                    try:
                        validate.validate_meituan(self.root)
                    finally:
                        path.write_text(original)

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,www.meituan.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_meituan(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_meituan(self.root)


if __name__ == '__main__':
    unittest.main()
