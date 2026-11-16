"""Public Kuaishou scope and real validator mutations; no private configuration."""
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

HOSTS = {'www.kuaishou.com', 'm.kuaishou.com'}
TARGET = '📹 快手'
MARKER = '  - RULE-SET,Kuaishou,' + TARGET + '\n'


class KuaishouContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ('sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / filename, self.root / filename)

    def complete_fixture(self):
        for directory in ('catalog', 'docs', 'research', 'rules', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        shutil.copyfile(ROOT / 'README.md', self.root / 'README.md')

    def mutate(self, filename, old, new):
        path = self.root / filename
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding='utf-8')

    def test_live_and_staged_contract(self):
        validate.validate_kuaishou(ROOT)
        validate.validate_kuaishou(self.root)

    def test_fixed_exact_hosts_and_excluded_controls(self):
        rules = entries(ROOT / 'ruleset/Kuaishou.yaml')
        self.assertEqual(len(rules), len(HOSTS))
        self.assertEqual(set(rules), {'DOMAIN,' + host for host in HOSTS})
        required = {'kuaishou.com', 'yximgs.com', 'yximg.com', 'kwimgs.com', 'wskwai.com',
                    'kwai.com', 'static.yximgs.com', 's2-11673.kwimgs.com',
                    'p1-plat.wskwai.com', 'p2-plat.wskwai.com', 'live.kuaishou.com',
                    'liveopen.kuaishou.com', 'cp.kuaishou.com', 'jigou.kuaishou.com',
                    'e.kuaishou.com', 'tuiguang.kuaishou.com', 'pay.ssl.kuaishou.com',
                    'game.kuaishou.com', 'klingai.kuaishou.com', 'music.kuaishou.com',
                    'www.acfun.cn', 'www.kwaixiaodian.com', 'www.kwai.com',
                    'wlog.kuaishou.com', 'www.douyin.com', 'y.qq.com',
                    'guzzoni.apple.com', 'example.org'}
        self.assertLessEqual(required, validate.KUAISHOU_CONTROLS)
        model = DomainRules(rules)
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertTrue(model.matches(host))
        controls = validate.KUAISHOU_CONTROLS | {value for host in HOSTS for value in
                                               ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(control=host):
                self.assertFalse(model.matches(host))

    def test_scope_broadening_missing_duplicate_or_extra_hosts_fail(self):
        path = self.root / 'ruleset/Kuaishou.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.kuaishou.com', 'DOMAIN-SUFFIX,kuaishou.com'),
                        original.replace('  - DOMAIN,m.kuaishou.com\n', ''),
                        original + '  - DOMAIN,m.kuaishou.com\n',
                        original.replace('DOMAIN,m.kuaishou.com', 'DOMAIN,static.yximgs.com')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'two reviewed exact hosts'):
                    validate.validate_kuaishou(self.root)

    def test_complete_public_tree_and_unique_hook(self):
        self.complete_fixture()
        self.assertEqual(validate.validate_tree(self.root), 0)
        with patch.object(validate, 'validate_kuaishou', side_effect=ValueError('Kuaishou gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'Kuaishou gate reached'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_scope_mutation_fails_the_complete_tree(self):
        self.complete_fixture()
        self.mutate('ruleset/Kuaishou.yaml', 'DOMAIN,www.kuaishou.com', 'DOMAIN-SUFFIX,kuaishou.com')
        with self.assertRaisesRegex(ValueError, 'two reviewed exact hosts'):
            validate.validate_tree(self.root)

    def test_contract_reads_are_explicit_utf8(self):
        original = Path.read_text
        seen = []

        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', checked):
            validate.validate_kuaishou(self.root)
        for filename in ('ruleset/Kuaishou.yaml', 'config/rules.yaml', 'config/proxy-groups.yaml',
                         'sources.json', 'local-rulesets.json'):
            self.assertIn(self.root / filename, seen)

    def test_missing_duplicate_wrong_or_commented_reference_fails(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(MARKER, ''), original + MARKER,
                        original.replace(MARKER, '  - RULE-SET,Kuaishou,DIRECT\n'),
                        original.replace(MARKER, MARKER.replace('  - ', '  # '))):
            with self.subTest(tail=changed[-80:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_kuaishou(self.root)

    def test_commented_duplicate_is_not_an_active_reference(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text(encoding='utf-8') + MARKER.replace('  - ', '  # '),
                        encoding='utf-8')
        validate.validate_kuaishou(self.root)

    def test_security_gaming_and_existing_apps_remain_before_kuaishou(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8').replace(MARKER, '')
        for before in ('  - RULE-SET,Privacy,REJECT\n', '  - RULE-SET,ChinaGaming,DIRECT\n',
                       '  - RULE-SET,Taobao,🛍️ 淘宝\n'):
            with self.subTest(before=before):
                path.write_text(original.replace(before, MARKER + before), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'must precede Kuaishou'):
                    validate.validate_kuaishou(self.root)

    def test_after_siri_or_broader_placement_fails(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8').replace(MARKER, '')
        for before in ('  - RULE-SET,Apple,🍎 Apple\n', '  - MATCH,'):
            with self.subTest(before=before):
                path.write_text(original.replace(before, MARKER + before), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'precede SiriAI and broader'):
                    validate.validate_kuaishou(self.root)

    def test_order_markers_must_be_unique_and_active(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,SiriAI,🤖 AI 服务\n'
        for changed in (original.replace(marker, marker.replace('  - ', '  # ')), original + marker):
            with self.subTest(marker_count=changed.count(marker)):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_kuaishou(self.root)

    def test_direct_first_type_and_proxy_final_options(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📹 快手"\n')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for changed in (block.replace('type: select', 'type: fallback'),
                        block.replace('type: select', 'type: select\n    type: select'),
                        block.replace('      - DIRECT\n', ''),
                        block.replace('      - DIRECT\n      - "🚀 节点选择"\n',
                                      '      - "🚀 节点选择"\n      - DIRECT\n'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('      - "🧭 Final"\n', '')):
            with self.subTest(block=changed):
                self.assertNotEqual(block, changed)
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_kuaishou(self.root)

    def test_missing_or_duplicate_group_fails(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📹 快手"\n')
        end = original.index('  - name:', start + 1)
        for changed in (original[:start] + original[end:], original + original[start:end]):
            with self.subTest(count=changed.count('name: "📹 快手"')):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select|duplicate group'):
                    validate.validate_kuaishou(self.root)

    def test_duplicate_and_complex_keys_fail_helper_and_complete_tree(self):
        self.complete_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📹 快手"\n')
        end = original.index('  - name:', start + 1)
        cases = (('type: fallback # override', 'type', 'fallback'), ('type:', 'type', None),
                 ('type : fallback', 'type', 'fallback'), ('"type": fallback', 'type', 'fallback'),
                 ("'type': fallback", 'type', 'fallback'),
                 (r'"t\u0079pe": fallback', 'type', 'fallback'),
                 ('!!str type: fallback', 'type', 'fallback'),
                 ('&policy_type type: fallback', 'type', 'fallback'),
                 ('? type\n    : fallback', 'type', 'fallback'),
                 ('<<: {type: fallback}', 'type', 'select'),
                 ('proxies: []', 'proxies', []), ('"proxies": []', 'proxies', []),
                 (r'"pro\u0078ies": []', 'proxies', []),
                 ('!!str proxies: []', 'proxies', []), ('&members proxies: []', 'proxies', []),
                 ('? proxies\n    : []', 'proxies', []))
        for declaration, field, effective in cases:
            changed = original[:end] + '    ' + declaration + '\n' + original[end:]
            group = next(group for group in yaml.safe_load(changed)['proxy-groups'] if group['name'] == TARGET)
            self.assertEqual(group[field], effective, declaration)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_kuaishou, validate.validate_tree):
                with self.subTest(declaration=declaration, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'Kuaishou must be a DIRECT-first select'):
                        gate(self.root)

    def test_safe_select_formats_pass_helper_and_complete_tree(self):
        self.complete_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "📹 快手"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # manual',
                            'type: "select" # manual', '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                changed = original.replace(marker, '  - name: "📹 快手"\n    ' + declaration + '\n')
                group = next(group for group in yaml.safe_load(changed)['proxy-groups'] if group['name'] == TARGET)
                self.assertEqual(group['type'], 'select')
                path.write_text(changed, encoding='utf-8')
                validate.validate_kuaishou(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_unknown_kinds_fail_closed_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,kuaishou,DIRECT',
                     'AND,((DOMAIN,www.kuaishou.com)),DIRECT'):
            for changed in (original.replace(MARKER, '  - ' + rule + '\n' + MARKER),
                            original + '  - ' + rule + '\n'):
                with self.subTest(rule=rule, tail=changed.endswith(rule + '\n')):
                    path.write_text(changed, encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'domain-only model limitation: unsupported'):
                        validate.validate_kuaishou(self.root)

    def test_preceding_ip_conditions_fail_helper_and_complete_tree(self):
        self.complete_fixture()
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('GEOIP,US,DIRECT,no-resolve', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            path.write_text(original.replace(MARKER, '  - ' + rule + '\n' + MARKER), encoding='utf-8')
            for gate in (validate.validate_kuaishou, validate.validate_tree):
                with self.subTest(rule=rule, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'Kuaishou domain-only model cannot validate preceding IP'):
                        gate(self.root)

    def test_legal_security_updates_use_the_same_contract(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + ''.join(f'  - {kind},{host}\n' for host in sorted(HOSTS)),
                                    encoding='utf-8')
                    try:
                        validate.validate_kuaishou(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_wrong_security_targets_fail(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_kuaishou(self.root)

    def test_nonsecurity_provider_shadowing_fails(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.kuaishou.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_kuaishou(self.root)

    def test_inline_same_target_shadowing_still_fails(self):
        self.mutate('config/rules.yaml', MARKER, '  - DOMAIN,www.kuaishou.com,' + TARGET + '\n' + MARKER)
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_kuaishou(self.root)

    def test_unknown_provider_has_clear_diagnostic(self):
        self.mutate('config/rules.yaml', MARKER, '  - RULE-SET,MissingKuaishou,DIRECT\n' + MARKER)
        with self.assertRaisesRegex(ValueError, 'Kuaishou routing references missing provider: MissingKuaishou'):
            validate.validate_kuaishou(self.root)

    def test_missing_own_provider_has_clear_diagnostic(self):
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        del local['Kuaishou']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Kuaishou routing references missing provider: Kuaishou'):
            validate.validate_kuaishou(self.root)

    def test_provider_collision_fails_helper_and_complete_tree(self):
        self.complete_fixture()
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Kuaishou manifests contain duplicate providers: Apple'):
            validate.validate_kuaishou(self.root)
        # The existing Ctrip gate may reject the same manifest collision first.
        with self.assertRaisesRegex(ValueError, 'manifests contain duplicate providers: Apple'):
            validate.validate_tree(self.root)

    def test_incomplete_reference_has_clear_diagnostic(self):
        self.mutate('config/rules.yaml', MARKER, '  - RULE-SET,Privacy\n' + MARKER)
        with self.assertRaisesRegex(ValueError, 'Kuaishou encountered an incomplete RULE-SET reference'):
            validate.validate_kuaishou(self.root)


if __name__ == '__main__':
    unittest.main()
