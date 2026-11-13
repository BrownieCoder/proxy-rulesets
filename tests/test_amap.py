"""AMap exact-host, first-match and configurable DIRECT-first contract."""
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


class AmapRouting(unittest.TestCase):
    HOSTS = {'ditu.amap.com', 'm.amap.com', 'maps.amap.com',
             'mobile.amap.com', 'restapi.amap.com', 'webapi.amap.com'}
    POLICY = '🗺️ 高德地图'

    @classmethod
    def setUpClass(cls):
        cls.rules = entries(ROOT / 'config/rules.yaml')
        cls.manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            cls.manifests.update(json.loads((ROOT / name).read_text()))
        cls.providers = {name: DomainRules(entries(ROOT / record['path']))
                         for name, record in cls.manifests.items()}

    def route(self, domain, include_amap=True, providers=None):
        providers = self.providers if providers is None else providers
        for rule in self.rules:
            fields = rule.split(',')
            kind = fields[0]
            if kind == 'RULE-SET':
                if fields[1] == 'Amap' and not include_amap:
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == 'MATCH':
                return 'MATCH', fields[1]
            elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                if DomainRules([rule]).matches(domain):
                    return ','.join(fields[:2]), fields[2]
            elif kind not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                raise ValueError(f'Unsupported top-level rule: {kind}')
        raise ValueError('Missing MATCH')

    def assert_accepted_host_route(self, host, providers=None):
        self.assertIn(self.route(host, providers=providers),
                      {('Amap', self.POLICY), ('Privacy', 'REJECT'),
                       ('Hijacking', '🚫 Hijacking')})

    def test_exact_reviewed_hosts_only(self):
        payload = yaml.safe_load((ROOT / 'ruleset/Amap.yaml').read_text())['payload']
        self.assertEqual(set(payload), {f'DOMAIN,{host}' for host in self.HOSTS})
        self.assertEqual(len(payload), len(self.HOSTS))
        rules = self.providers['Amap']
        for host in self.HOSTS:
            self.assertTrue(rules.matches(host))
            self.assertFalse(rules.matches('child.' + host))
            self.assertFalse(rules.matches(host + '.example.org'))

    def test_first_match_order_and_direct_first_options(self):
        marker = 'RULE-SET,Amap,' + self.POLICY
        self.assertEqual(self.rules.count(marker), 1)
        pos = self.rules.index(marker)
        for name in ('Privacy', 'Hijacking', 'InternationalGaming', 'ChinaGaming'):
            earlier = next(r for r in self.rules if r.startswith('RULE-SET,' + name + ','))
            self.assertLess(self.rules.index(earlier), pos)
        for name in ('Apple', 'GlobalMedia', 'ChinaMax'):
            later = next(r for r in self.rules if r.startswith('RULE-SET,' + name + ','))
            self.assertLess(pos, self.rules.index(later))
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text())['proxy-groups']
        group = next(g for g in groups if g['name'] == self.POLICY)
        self.assertEqual(group['type'], 'select')
        self.assertEqual(group['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', group['proxies'])
        for host in self.HOSTS:
            self.assert_accepted_host_route(host)

    def test_security_rules_still_win(self):
        for name, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            providers = dict(self.providers)
            providers[name] = DomainRules(['DOMAIN,maps.amap.com'])
            self.assert_accepted_host_route('maps.amap.com', providers=providers)
            self.assertEqual(self.route('maps.amap.com', providers=providers), (name, target))

    def test_wrong_security_target_is_rejected(self):
        providers = dict(self.providers)
        providers['Privacy'] = DomainRules(['DOMAIN,maps.amap.com'])
        self.rules = [rule.replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
                      for rule in self.rules]
        with self.assertRaises(AssertionError):
            self.assert_accepted_host_route('maps.amap.com', providers=providers)

    def test_non_security_shadowing_is_rejected(self):
        providers = dict(self.providers)
        providers['ChinaGaming'] = DomainRules(['DOMAIN,maps.amap.com'])
        with self.assertRaises(AssertionError):
            self.assert_accepted_host_route('maps.amap.com', providers=providers)

    def test_non_target_routes_unchanged(self):
        controls = {'amap.com', 'autonavi.com', 'www.autonavi.com',
                    'aliyun.com', 'alibaba.com', 'example.org',
                    'hoyoverse.com', 'fastcdn.hoyoverse.com',
                    'guzzoni.apple.com', 'www.xiaohongshu.com', 'hmma.baidu.com'}
        controls |= {d for h in self.HOSTS for d in ('child.' + h, h + '.example.org', 'not' + h)}
        for domain in controls:
            with self.subTest(domain=domain):
                self.assertEqual(self.route(domain), self.route(domain, include_amap=False))


class AmapValidatorContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('config', 'ruleset'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('sources.json', 'sources.lock.json', 'local-rulesets.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def test_current_public_fixture(self):
        validate.validate_amap(self.root)

    def test_validate_tree_runs_amap_gate(self):
        with patch.object(validate, 'validate_amap', side_effect=ValueError('Amap gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'Amap gate reached'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_broadening_and_duplicate_hosts_are_rejected(self):
        path = self.root / 'ruleset/Amap.yaml'
        original = path.read_text()
        for suffix in ('  - DOMAIN-SUFFIX,amap.com\n', '  - DOMAIN,maps.amap.com\n'):
            with self.subTest(rule=suffix):
                path.write_text(original + suffix)
                with self.assertRaisesRegex(ValueError, 'six reviewed exact hosts'):
                    validate.validate_amap(self.root)

    def test_late_rule_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        rule = '  - RULE-SET,Amap,🗺️ 高德地图\n'
        text = path.read_text().replace(rule, '')
        path.write_text(text.replace('  - MATCH,', rule + '  - MATCH,'))
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_amap(self.root)

    def test_security_bypass_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        rule = '  - RULE-SET,Amap,🗺️ 高德地图\n'
        path.write_text(path.read_text().replace(rule, '').replace('rules:\n', 'rules:\n' + rule))
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_amap(self.root)

    def test_only_one_exact_active_reference_is_allowed(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text()
        for text in (original.replace('  - RULE-SET,Amap,🗺️ 高德地图', '  # RULE-SET,Amap,🗺️ 高德地图'),
                     original + '  - RULE-SET,Amap,🗺️ 高德地图\n',
                     original + '  - RULE-SET,Amap,DIRECT\n'):
            with self.subTest(text=text[-60:]):
                path.write_text(text)
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated policy reference'):
                    validate.validate_amap(self.root)

    def test_comment_cannot_replace_required_marker(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('  - RULE-SET,GlobalMedia,', '  # RULE-SET,GlobalMedia,'))
        with self.assertRaisesRegex(ValueError, 'exactly one active rule'):
            validate.validate_amap(self.root)

    def test_direct_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text()
        start = original.index('  - name: "🗺️ 高德地图"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for modified in (block.replace('      - DIRECT\n', ''),
                         block.replace('    type: select', '    type: fallback'),
                         block.replace('      - "🚀 节点选择"\n', '')):
            with self.subTest(block=modified):
                path.write_text(original[:start] + modified + original[end:])
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_amap(self.root)

    def test_legal_security_updates_remain_valid(self):
        for name in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{name}_No_Resolve.yaml'
            original = path.read_text()
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=name, kind=kind):
                    path.write_text(original + f'  - {kind},maps.amap.com\n')
                    try:
                        validate.validate_amap(self.root)
                    finally:
                        path.write_text(original)

    def test_wrong_security_policy_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT'))
        path = self.root / 'ruleset/Privacy_No_Resolve.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,maps.amap.com\n')
        with self.assertRaises(ValueError):
            validate.validate_amap(self.root)

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,maps.amap.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_amap(self.root)

    def test_unknown_top_level_rule_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('rules:\n', 'rules:\n  - DST-PORT,443,DIRECT\n'))
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_amap(self.root)


if __name__ == '__main__':
    unittest.main()
