"""Pinduoduo production-validator mutations using public, temporary fixtures."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries
import validate


class PinduoduoRouting(unittest.TestCase):
    HOSTS = {'www.yangkeduo.com', 'mobile.yangkeduo.com', 'commimg.pddpic.com',
             'img.pddpic.com', 't13img.yangkeduo.com'}
    MARKER = '  - RULE-SET,Pinduoduo,🛍️ 拼多多\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, filename, old, new):
        path = self.root / filename
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding='utf-8')

    def complete_public_fixture(self):
        for directory in ('catalog', 'docs', 'research', 'rules', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        shutil.copyfile(ROOT / 'README.md', self.root / 'README.md')

    def test_live_and_staged_contract(self):
        validate.validate_pinduoduo(ROOT)
        validate.validate_pinduoduo(self.root)

    def test_complete_tree_runs_and_calls_contract_once(self):
        self.complete_public_fixture()
        self.assertEqual(validate.validate_tree(self.root), 0)
        with patch.object(validate, 'validate_pinduoduo',
                          side_effect=ValueError('Pinduoduo tree gate')) as gate:
            with self.assertRaisesRegex(ValueError, 'Pinduoduo tree gate'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_complete_tree_rejects_real_scope_mutation(self):
        self.complete_public_fixture()
        self.mutate('ruleset/Pinduoduo.yaml', 'DOMAIN,www.yangkeduo.com',
                    'DOMAIN-SUFFIX,yangkeduo.com')
        with self.assertRaisesRegex(ValueError, 'five reviewed exact hosts'):
            validate.validate_tree(self.root)

    def test_helper_reads_explicit_utf8(self):
        original = Path.read_text
        seen = []

        def utf8_read(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', utf8_read):
            validate.validate_pinduoduo(self.root)
        for filename in ('ruleset/Pinduoduo.yaml', 'config/rules.yaml',
                         'config/proxy-groups.yaml', 'sources.json', 'local-rulesets.json'):
            self.assertIn(self.root / filename, seen)

    def test_exact_scope_and_negative_controls(self):
        rules = entries(ROOT / 'ruleset/Pinduoduo.yaml')
        self.assertEqual(len(rules), len(self.HOSTS))
        self.assertEqual(set(rules), {'DOMAIN,' + host for host in self.HOSTS})
        required_controls = {'pinduoduo.com', 'yangkeduo.com', 'pddpic.com',
                             'www.pinduoduo.com', 'cdn.pinduoduo.com',
                             'images.pinduoduo.com', 'promotion.pddpic.com',
                             'www.temu.com', 'pftk.temu.com', 'thtk.temu.com',
                             'm.jd.com', 'guzzoni.apple.com'}
        self.assertLessEqual(required_controls, validate.PINDUODUO_CONTROLS)
        model = DomainRules(rules)
        controls = validate.PINDUODUO_CONTROLS | {value for host in self.HOSTS for value in
                                               ('child.' + host, 'not' + host, host + '.example.org')}
        for host in self.HOSTS:
            with self.subTest(target=host):
                self.assertTrue(model.matches(host))
        for host in controls:
            with self.subTest(control=host):
                self.assertFalse(model.matches(host))

    def test_broad_suffix_is_rejected(self):
        self.mutate('ruleset/Pinduoduo.yaml', 'DOMAIN,img.pddpic.com', 'DOMAIN-SUFFIX,pddpic.com')
        with self.assertRaisesRegex(ValueError, 'five reviewed exact hosts'):
            validate.validate_pinduoduo(self.root)

    def test_missing_duplicate_and_unreviewed_hosts_are_rejected(self):
        path = self.root / 'ruleset/Pinduoduo.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('  - DOMAIN,www.yangkeduo.com\n', ''),
                        original + '  - DOMAIN,www.yangkeduo.com\n',
                        original.replace('DOMAIN,www.yangkeduo.com', 'DOMAIN,www.pinduoduo.com')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'five reviewed exact hosts'):
                    validate.validate_pinduoduo(self.root)

    def test_missing_duplicate_and_wrong_reference_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(self.MARKER, ''), original + self.MARKER,
                        original.replace(self.MARKER, '  - RULE-SET,Pinduoduo,DIRECT\n')):
            with self.subTest(reference=changed[-100:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_pinduoduo(self.root)

    def test_commented_reference_is_not_active(self):
        self.mutate('config/rules.yaml', self.MARKER, self.MARKER.replace('  - ', '  # '))
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_pinduoduo(self.root)

    def test_commented_duplicate_does_not_change_active_reference(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text(encoding='utf-8') + self.MARKER.replace('  - ', '  # '),
                        encoding='utf-8')
        validate.validate_pinduoduo(self.root)

    def test_security_bypass_and_existing_app_preemption_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        without = path.read_text(encoding='utf-8').replace(self.MARKER, '')
        for before in ('rules:\n', '  - RULE-SET,BaiduPan,☁️ 百度网盘\n',
                       '  - RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n'):
            with self.subTest(before=before):
                changed = (without.replace(before, before + self.MARKER) if before == 'rules:\n'
                           else without.replace(before, self.MARKER + before))
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'must precede Pinduoduo'):
                    validate.validate_pinduoduo(self.root)

    def test_after_siri_or_broader_placement_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        without = path.read_text(encoding='utf-8').replace(self.MARKER, '')
        for before in ('  - RULE-SET,Apple,🍎 Apple\n', '  - MATCH,'):
            with self.subTest(before=before):
                path.write_text(without.replace(before, self.MARKER + before), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'precede SiriAI and broader'):
                    validate.validate_pinduoduo(self.root)

    def test_active_order_markers_must_be_unique(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,SiriAI,🤖 AI 服务\n'
        for changed in (original.replace(marker, marker.replace('  - ', '  # ')), original + marker):
            with self.subTest(marker_count=changed.count(marker)):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_pinduoduo(self.root)

    def test_group_type_default_and_proxy_option_are_enforced(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🛍️ 拼多多"\n')
        end = original.index('  - name:', start + 1)
        group = original[start:end]
        for changed in (group.replace('type: select', 'type: fallback'),
                        group.replace('type: select', 'type: select\n    type: select'),
                        group.replace('      - DIRECT\n', ''),
                        group.replace('      - DIRECT\n      - "🚀 节点选择"\n',
                                      '      - "🚀 节点选择"\n      - DIRECT\n'),
                        group.replace('      - "🚀 节点选择"\n', '')):
            with self.subTest(group=changed):
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_pinduoduo(self.root)

    def test_missing_or_duplicate_policy_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🛍️ 拼多多"\n')
        end = original.index('  - name:', start + 1)
        for changed in (original[:start] + original[end:], original + original[start:end]):
            with self.subTest(group_count=changed.count('name: "🛍️ 拼多多"')):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select|duplicate group'):
                    validate.validate_pinduoduo(self.root)

    def test_duplicate_type_keys_cannot_override_select(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🛍️ 拼多多"\n    type: select\n'
        self.assertIn(marker, original)
        variants = (('type: fallback # overriding comment', 'fallback'),
                    ('type:', None), ('type : fallback', 'fallback'),
                    ('"type": fallback', 'fallback'), ("'type': fallback", 'fallback'))
        for declaration, effective_type in variants:
            changed = original.replace(marker, marker + '    ' + declaration + '\n')
            parsed = yaml.safe_load(changed)['proxy-groups']
            group = next(group for group in parsed if group['name'] == '🛍️ 拼多多')
            with self.subTest(declaration=declaration, check='effective YAML type'):
                self.assertEqual(group['type'], effective_type)
                self.assertNotEqual(group['type'], 'select')
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_pinduoduo, validate.validate_tree):
                with self.subTest(declaration=declaration, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                        gate(self.root)

    def test_complex_type_and_proxies_keys_fail_closed_at_both_gates(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🛍️ 拼多多"\n')
        end = original.index('  - name:', start + 1)
        variants = ((r'"t\u0079pe": fallback', 'type', 'fallback'),
                    ('!!str type: fallback', 'type', 'fallback'),
                    ('&policy_type type: fallback', 'type', 'fallback'),
                    ('? type\n    : fallback', 'type', 'fallback'),
                    ('<<: {type: fallback}', 'type', 'select'),
                    ('proxies: []', 'proxies', []),
                    ('"proxies": []', 'proxies', []),
                    (r'"pro\u0078ies": []', 'proxies', []),
                    ('!!str proxies: []', 'proxies', []),
                    ('&proxy_list proxies: []', 'proxies', []),
                    ('? proxies\n    : []', 'proxies', []))
        for declaration, key, expected in variants:
            changed = original[:end] + '    ' + declaration + '\n' + original[end:]
            group = next(group for group in yaml.safe_load(changed)['proxy-groups']
                         if group['name'] == '🛍️ 拼多多')
            self.assertEqual(group[key], expected, declaration)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_pinduoduo, validate.validate_tree):
                with self.subTest(declaration=declaration, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'Pinduoduo must be a DIRECT-first select'):
                        gate(self.root)

    def test_literal_select_formats_pass_helper_and_complete_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🛍️ 拼多多"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # manual',
                            'type: "select" # manual', '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                changed = original.replace(marker, '  - name: "🛍️ 拼多多"\n    ' + declaration + '\n')
                group = next(group for group in yaml.safe_load(changed)['proxy-groups']
                             if group['name'] == '🛍️ 拼多多')
                self.assertEqual(group['type'], 'select')
                path.write_text(changed, encoding='utf-8')
                validate.validate_pinduoduo(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_noncanonical_group_shapes_fail_helper_and_complete_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🛍️ 拼多多"\n')
        end = original.index('  - name:', start + 1)
        group = original[start:end]
        for changed in (group.replace('    proxies:\n      - DIRECT\n      - "🚀 节点选择"\n      - "🧭 Final"\n',
                                      '    proxies: [DIRECT, "🚀 节点选择", "🧭 Final"]\n'),
                        group.replace('    type: select\n', '    type: &kind select\n'),
                        group.replace('    proxies:\n', '      - DIRECT\n    proxies:\n'),
                        group + '    unsupported: value\n',
                        group + '      - type: fallback\n'):
            self.assertNotEqual(changed, group)
            for gate in (validate.validate_pinduoduo, validate.validate_tree):
                with self.subTest(group=changed, gate=gate.__name__):
                    path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                    with self.assertRaises(ValueError):
                        gate(self.root)

    def test_legal_future_security_updates_remain_valid(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    added = ''.join(f'  - {kind},{host}\n' for host in sorted(self.HOSTS))
                    path.write_text(original + added, encoding='utf-8')
                    try:
                        validate.validate_pinduoduo(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_pinduoduo(self.root)

    def test_nonsecurity_provider_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.yangkeduo.com\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_pinduoduo(self.root)

    def test_nonsecurity_direct_rule_even_same_target_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER,
                    '  - DOMAIN,www.yangkeduo.com,🛍️ 拼多多\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_pinduoduo(self.root)

    def test_unknown_top_level_types_are_rejected_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,pinduoduo,DIRECT',
                     'AND,((DOMAIN,www.yangkeduo.com)),DIRECT'):
            for changed in (original.replace('rules:\n', f'rules:\n  - {rule}\n'),
                            original + f'  - {rule}\n'):
                with self.subTest(rule=rule, tail=changed.endswith(rule + '\n')):
                    path.write_text(changed, encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'Unsupported top-level.*domain-only model'):
                        validate.validate_pinduoduo(self.root)

    def test_early_ip_rules_are_rejected_by_helper_and_complete_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        rules = ('GEOIP,US,DIRECT,no-resolve',
                 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                 'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve')
        for rule in rules:
            path.write_text(original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER),
                            encoding='utf-8')
            for gate in (validate.validate_pinduoduo, validate.validate_tree):
                with self.subTest(rule=rule, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'domain-only model limitation: IP/GeoIP rules'):
                        gate(self.root)

    def test_unknown_provider_has_clear_validation_error(self):
        self.mutate('config/rules.yaml', self.MARKER,
                    '  - RULE-SET,UnreviewedProvider,DIRECT\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Pinduoduo references undefined provider: UnreviewedProvider'):
            validate.validate_pinduoduo(self.root)

    def test_missing_provider_has_clear_validation_error(self):
        path = self.root / 'local-rulesets.json'
        manifests = json.loads(path.read_text(encoding='utf-8'))
        del manifests['Pinduoduo']
        path.write_text(json.dumps(manifests, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Pinduoduo references undefined provider: Pinduoduo'):
            validate.validate_pinduoduo(self.root)

    def test_incomplete_reference_has_clear_validation_error(self):
        self.mutate('config/rules.yaml', self.MARKER, '  - RULE-SET,Privacy\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Pinduoduo encountered an incomplete RULE-SET reference'):
            validate.validate_pinduoduo(self.root)


if __name__ == '__main__':
    unittest.main()
