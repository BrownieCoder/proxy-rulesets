"""Ctrip production-validator mutations with public fixtures only."""
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
import validate
from siri_ai import DomainRules

HOSTS = {'www.ctrip.com', 'm.ctrip.com', 'app.ctrip.com', 'hotels.ctrip.com',
         'flights.ctrip.com', 'trains.ctrip.com', 'vacations.ctrip.com'}


class CtripValidator(unittest.TestCase):
    MARKER = '  - RULE-SET,Ctrip,🧳 携程\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, name, old, new):
        path = self.root / name
        original = path.read_text(encoding='utf-8')
        self.assertIn(old, original)
        path.write_text(original.replace(old, new), encoding='utf-8')

    def test_current_contract(self):
        validate.validate_ctrip(self.root)

    def test_tree_calls_contract_with_complete_public_fixture(self):
        with patch.object(validate, 'validate_ctrip', side_effect=RuntimeError('Ctrip gate')) as gate:
            with self.assertRaisesRegex(RuntimeError, 'Ctrip gate'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_exact_scope_and_non_target_boundaries(self):
        payload = yaml.safe_load((self.root / 'ruleset/Ctrip.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        controls = validate.CTRIP_CONTROLS | {value for host in HOSTS for value in
                                            ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_broadening_and_duplicate_scope_are_rejected(self):
        path = self.root / 'ruleset/Ctrip.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.ctrip.com', 'DOMAIN-SUFFIX,ctrip.com'),
                        original + '  - DOMAIN,www.ctrip.com\n',
                        original + '  - DOMAIN,static.tripcdn.com\n',
                        original.replace('  - DOMAIN,app.ctrip.com\n', '')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'seven reviewed exact hosts'):
                    validate.validate_ctrip(self.root)

    def test_missing_comment_duplicate_and_wrong_reference_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(self.MARKER, ''),
                        original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                        original + self.MARKER,
                        original.replace(self.MARKER, '  - RULE-SET,Ctrip,DIRECT\n')):
            with self.subTest(reference=changed[-80:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_ctrip(self.root)

    def test_late_placement_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_ctrip(self.root)

    def test_security_bypass_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede Ctrip'):
            validate.validate_ctrip(self.root)

    def test_commented_order_marker_cannot_pass(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,ChinaMax,', '  # RULE-SET,ChinaMax,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_ctrip(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_ctrip(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🧳 携程"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for changed in (block.replace('      - DIRECT\n', ''),
                        block.replace('    type: select', '    type: fallback'),
                        block.replace('    type: select', '    type: select\n    type: select'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('      - DIRECT\n', '      - "🚀 节点选择"\n')):
            with self.subTest(group=changed):
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError,
                        (r'Public config/proxy-groups\.yaml.*duplicate group field: type'
                         if changed.count('type: select') > 1 else 'DIRECT-first select')):
                    validate.validate_ctrip(self.root)

    def test_duplicate_type_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🧳 携程"\n    type: select\n'
        for override in ('type: fallback # duplicate override', 'type:', 'type : fallback',
                         '"type": fallback', "'type': fallback"):
            with self.subTest(override=override):
                path.write_text(original.replace(marker, marker + '    ' + override + '\n'),
                                encoding='utf-8')
                parsed = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                effective = next(group for group in parsed if group['name'] == '🧳 携程')
                self.assertNotEqual(effective['type'], 'select')
                with self.assertRaisesRegex(ValueError, r'Public config/proxy-groups\.yaml.*duplicate group field: type'):
                    validate.validate_ctrip(self.root)
                with self.assertRaisesRegex(ValueError, r'Public config/proxy-groups\.yaml.*duplicate group field: type'):
                    validate.validate_tree(self.root)

    def test_complex_keys_and_proxy_overrides_fail_helper_and_complete_tree(self):
        def structural_error(declaration):
            value = declaration.strip()
            if value.startswith(('type:', 'type :', '"type":', "'type':")):
                reason = 'duplicate group field: type'
            elif value.startswith(('proxies:', '"proxies":', "'proxies':")):
                reason = 'duplicate group field: proxies'
            elif value.startswith('unsupported:'):
                reason = 'unsupported group field: unsupported'
            elif value.startswith('- '):
                reason = ('expected an unescaped whole quoted literal'
                          if chr(92) in value else 'unsupported scalar syntax')
            else:
                reason = 'expected a literal mapping key with a separated value'
            return r'Public config/proxy-groups\.yaml.*' + reason

        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🧳 携程"')
        end = original.index('  - name:', start + 1)
        for declaration in ('"t\\u0079pe": fallback', '!!str type: fallback',
                            '&policy_type type: fallback', '? type\n    : fallback',
                            'proxies: []', '"pro\\u0078ies": []',
                            '!!str proxies: []', '? proxies\n    : []',
                            '<<: {type: fallback}', 'unsupported: value'):
            with self.subTest(declaration=declaration):
                changed = original[:end] + '    ' + declaration + '\n' + original[end:]
                path.write_text(changed, encoding='utf-8')
                groups = yaml.safe_load(changed)['proxy-groups']
                effective = next(group for group in groups if group['name'] == '🧳 携程')
                if 'fallback' in declaration and not declaration.startswith('<<:'):
                    self.assertEqual(effective['type'], 'fallback')
                if '[]' in declaration:
                    self.assertEqual(effective['proxies'], [])
                with self.assertRaisesRegex(ValueError, structural_error(declaration)):
                    validate.validate_ctrip(self.root)
                with self.assertRaisesRegex(ValueError, structural_error(declaration)):
                    validate.validate_tree(self.root)

    def test_duplicate_policy_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        path.write_text(path.read_text(encoding='utf-8') +
                        '\n  - name: "🧳 携程"\n    type: select\n    proxies:\n      - DIRECT\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            validate.validate_ctrip(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text(encoding='utf-8')
                    path.write_text(original + f'  - {kind},www.ctrip.com\n', encoding='utf-8')
                    try:
                        validate.validate_ctrip(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.ctrip.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_ctrip(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,ctrip,DIRECT',
                     'AND,((DOMAIN,www.ctrip.com)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', 'rules:\n  - ' + rule + '\n'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_ctrip(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownCtrip,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownCtrip'):
            validate.validate_ctrip(self.root)

    def test_missing_own_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        del manifest['Ctrip']
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: Ctrip'):
            validate.validate_ctrip(self.root)

    def test_manifest_provider_collision_is_rejected(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Ctrip manifests contain duplicate providers: Apple'):
            validate.validate_ctrip(self.root)
        with self.assertRaisesRegex(ValueError, 'Ctrip manifests contain duplicate providers: Apple'):
            validate.validate_tree(self.root)

    def test_contract_text_reads_are_explicit_utf8(self):
        original = Path.read_text
        seen = []
        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', checked):
            validate.validate_ctrip(self.root)
        self.assertTrue(seen)


if __name__ == '__main__':
    unittest.main()
