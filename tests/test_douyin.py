"""Real Douyin validator mutations; no account traffic or private input."""
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
from siri_ai import DomainRules, entries

HOSTS = {'www.douyin.com', 'lf-douyin-pc-web.douyinstatic.com',
         'sf1-cdn-tos.douyinstatic.com'}


class DouyinContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, filename, old, new):
        path = self.root / filename
        path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')

    def test_current_contract(self):
        validate.validate_douyin(self.root)

    def test_tree_calls_douyin_gate(self):
        for directory in ('catalog', 'docs', 'research', 'rules', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('README.md', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)
        with patch.object(validate, 'validate_douyin', side_effect=ValueError('Douyin gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'Douyin gate reached'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_helper_reads_explicit_utf8(self):
        read_text = Path.read_text
        seen = []

        def utf8_read(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_text', utf8_read):
            validate.validate_douyin(self.root)
        self.assertTrue(seen)

    def test_broadening_or_duplicate_scope_is_rejected(self):
        path = self.root / 'ruleset/Douyin.yaml'
        original = path.read_text(encoding='utf-8')
        for text in (original.replace('DOMAIN,www.douyin.com', 'DOMAIN-SUFFIX,douyin.com'),
                     original + '  - DOMAIN,www.douyin.com\n'):
            with self.subTest(scope=text):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'three reviewed exact hosts'):
                    validate.validate_douyin(self.root)

    def test_prefetch_candidate_is_not_accepted_without_review(self):
        path = self.root / 'ruleset/Douyin.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,v3-web.douyinvod.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'three reviewed exact hosts'):
            validate.validate_douyin(self.root)

    def test_missing_duplicate_or_wrong_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,Douyin,🎶 抖音\n'
        for text in (original.replace(marker, '  # RULE-SET,Douyin,🎶 抖音\n'),
                     original + marker, original.replace(marker, '  - RULE-SET,Douyin,DIRECT\n')):
            with self.subTest(rule=text[-80:]):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_douyin(self.root)

    def test_security_bypass_and_late_placement_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        marker = '  - RULE-SET,Douyin,🎶 抖音\n'
        without = path.read_text(encoding='utf-8').replace(marker, '')
        for text, expected in ((without.replace('rules:\n', 'rules:\n' + marker), 'Security and gaming'),
                               (without.replace('  - MATCH,', marker + '  - MATCH,'), 'broader providers')):
            with self.subTest(expected=expected):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, expected):
                    validate.validate_douyin(self.root)

    def test_comments_cannot_replace_active_order_markers(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,TikTok,', '  # RULE-SET,TikTok,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_douyin(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎶 抖音"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for replacement in (block.replace('      - DIRECT\n', ''),
                            block.replace('    type: select', '    type: fallback'),
                            block.replace('    type: select', '    type: select\n    type: select'),
                            block.replace('      - "🚀 节点选择"\n', '')):
            with self.subTest(group=replacement):
                path.write_text(original[:start] + replacement + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_douyin(self.root)

    def test_future_security_matches_remain_valid(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},www.douyin.com\n', encoding='utf-8')
                    try:
                        validate.validate_douyin(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.douyin.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_douyin(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_douyin(self.root)

    def test_unknown_top_level_types_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,douyin,DIRECT',
                     'AND,((DOMAIN,www.douyin.com)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', f'rules:\n  - {rule}\n'), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_douyin(self.root)

    def test_exact_rules_and_non_target_boundaries(self):
        payload = yaml.safe_load((ROOT / 'ruleset/Douyin.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        controls = validate.DOUYIN_CONTROLS | {value for host in HOSTS for value in
                                             ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_tiktok_control_routes_are_unchanged(self):
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((ROOT / name).read_text(encoding='utf-8')))
        providers = {name: DomainRules(entries(ROOT / record['path']))
                     for name, record in manifests.items()}
        rules = yaml.safe_load((ROOT / 'config/rules.yaml').read_text(encoding='utf-8'))['rules']

        def route(host, include_douyin):
            for rule in rules:
                fields = rule.split(',')
                kind = fields[0]
                if kind == 'RULE-SET':
                    if not include_douyin and fields[1] == 'Douyin':
                        continue
                    if providers[fields[1]].matches(host):
                        return fields[1], fields[2]
                elif kind == 'MATCH':
                    return kind, fields[1]
                elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return ','.join(fields[:2]), fields[2]
                elif kind not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                    raise ValueError('Unsupported domain model kind: ' + kind)
            self.fail('Missing MATCH')

        for host in ('www.tiktok.com', 'p16-sign-va.tiktokcdn.com', 'p16-va.tiktokcdn.com',
                     'p16-sg.tiktokcdn.com', 'p1.ibyteimg.com'):
            with self.subTest(host=host):
                self.assertEqual(route(host, True), route(host, False))

    def test_missing_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifests = json.loads(path.read_text(encoding='utf-8'))
        del manifests['Douyin']
        path.write_text(json.dumps(manifests, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: Douyin'):
            validate.validate_douyin(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownDouyin,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownDouyin'):
            validate.validate_douyin(self.root)


if __name__ == '__main__':
    unittest.main()
