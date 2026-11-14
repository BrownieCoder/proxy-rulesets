"""JD exact-host, policy and live/staged validator mutation regressions."""
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

HOSTS = {'app.jd.com', 'h5.m.jd.com', 'img12.360buyimg.com', 'img14.360buyimg.com',
         'img20.360buyimg.com', 'm.360buyimg.com', 'm.jd.com', 'storage.360buyimg.com'}
TARGET = '🛒 京东'


class JDRouting(unittest.TestCase):
    def test_independent_yaml_scope_and_default(self):
        payload = yaml.safe_load((ROOT / 'ruleset/JD.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text(encoding='utf-8'))['proxy-groups']
        matches = [g for g in groups if g['name'] == TARGET]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['type'], 'select')
        self.assertEqual(matches[0]['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', matches[0]['proxies'])

    def test_effective_routing_contract(self):
        validate.validate_jd(ROOT)

    def test_unreviewed_hosts_do_not_match(self):
        model = DomainRules(entries(ROOT / 'ruleset/JD.yaml'))
        controls = {'jd.com', '360buyimg.com', 'passport.jd.com', 'api.m.jd.com',
                    'www.jd.com', 'm.jr.jd.com', 'jdpay.com'}
        controls |= {value for host in HOSTS for value in
                     ('child.' + host, 'not' + host, host + '.example.org')}
        for domain in controls:
            with self.subTest(domain=domain):
                self.assertFalse(model.matches(domain))


class JDValidatorMutations(unittest.TestCase):
    MARKER = '  - RULE-SET,JD,' + TARGET + '\n'

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
        self.assertIn(old, path.read_text(encoding='utf-8'))
        path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')

    def test_valid_public_fixture(self):
        validate.validate_jd(self.root)

    def test_scope_broadening_is_rejected(self):
        self.mutate('ruleset/JD.yaml', 'DOMAIN,m.jd.com', 'DOMAIN-SUFFIX,jd.com')
        with self.assertRaisesRegex(ValueError, 'eight reviewed exact hosts'):
            validate.validate_jd(self.root)

    def test_complete_public_tree_calls_jd_gate(self):
        with patch.object(validate, 'validate_jd', side_effect=ValueError('JD gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'JD gate reached'):
                validate.validate_tree(ROOT)
        gate.assert_called_once_with(ROOT)

    def test_missing_provider_reports_clear_validation_error(self):
        path = self.root / 'local-rulesets.json'
        records = json.loads(path.read_text(encoding='utf-8'))
        del records['JD']
        path.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'JD routing references missing provider: JD'):
            validate.validate_jd(self.root)

    def test_all_jd_validator_text_reads_request_utf8(self):
        original = Path.read_text

        def read_utf8(path, *args, **kwargs):
            encoding = kwargs.get('encoding', args[0] if args else None)
            self.assertEqual(encoding, 'utf-8', str(path))
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', autospec=True, side_effect=read_utf8):
            validate.validate_jd(self.root)

    def test_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/JD.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,m.jd.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            validate.validate_jd(self.root)

    def test_no_reference_or_duplicate_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for text in (original.replace(self.MARKER, ''), original + self.MARKER,
                     original + '  - RULE-SET,JD,DIRECT\n'):
            with self.subTest(tail=text[-40:]):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_jd(self.root)

    def test_late_reference_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_jd(self.root)

    def test_security_bypass_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_jd(self.root)

    def test_comments_cannot_replace_reference_or_order_marker(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in (self.MARKER, '  - RULE-SET,GlobalMedia,🛰️ International-Global\n'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.replace('  - ', '  # ')), encoding='utf-8')
                with self.assertRaises(ValueError):
                    validate.validate_jd(self.root)

    def test_default_type_and_proxy_choice_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🛒 京东"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for changed in (block.replace('      - DIRECT\n', ''),
                        block.replace('type: select', 'type: fallback'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('    type: select\n', '    type: select\n    type: select\n')):
            with self.subTest(block=changed):
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_jd(self.root)

    def test_legal_security_updates_use_same_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},m.jd.com\n', encoding='utf-8')
                    try:
                        validate.validate_jd(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,m.jd.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_jd(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'one active rule'):
            validate.validate_jd(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,jd,DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(self.MARKER, f'  - {rule}\n' + self.MARKER), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_jd(self.root)


if __name__ == '__main__':
    unittest.main()
