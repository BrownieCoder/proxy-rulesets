"""AMap exact-host, first-match and configurable DIRECT-first contract."""
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries


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
            self.assertEqual(self.route(host), ('Amap', self.POLICY))

    def test_security_rules_still_win(self):
        for name, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            providers = dict(self.providers)
            providers[name] = DomainRules(['DOMAIN,maps.amap.com'])
            self.assertEqual(self.route('maps.amap.com', providers=providers), (name, target))

    def test_non_target_routes_unchanged(self):
        controls = {'amap.com', 'autonavi.com', 'www.autonavi.com',
                    'aliyun.com', 'alibaba.com', 'example.org',
                    'hoyoverse.com', 'fastcdn.hoyoverse.com',
                    'guzzoni.apple.com', 'www.xiaohongshu.com', 'hmma.baidu.com'}
        controls |= {d for h in self.HOSTS for d in ('child.' + h, h + '.example.org', 'not' + h)}
        for domain in controls:
            with self.subTest(domain=domain):
                self.assertEqual(self.route(domain), self.route(domain, include_amap=False))


if __name__ == '__main__':
    unittest.main()
