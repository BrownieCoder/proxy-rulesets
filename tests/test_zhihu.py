"""Exact Zhihu scope, policy and first-match domain regression checks."""
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries

HOSTS = {
    'www.zhihu.com', 'api.zhihu.com', 'zhuanlan.zhihu.com', 'static.zhihu.com',
    'static.zhimg.com', 'pic1.zhimg.com', 'pica.zhimg.com', 'picx.zhimg.com',
}
TARGET = '💡 知乎'


class ZhihuRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ordered = entries(ROOT / 'config/rules.yaml')
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((ROOT / name).read_text()))
        cls.providers = {name: DomainRules(entries(ROOT / item['path']))
                         for name, item in manifests.items()}

    def route(self, domain, skip=False, providers=None):
        providers = self.providers if providers is None else providers
        for rule in self.ordered:
            fields = rule.split(',')
            kind = fields[0]
            if kind == 'RULE-SET':
                name, target = fields[1:3]
                if skip and name == 'Zhihu':
                    continue
                if providers[name].matches(domain):
                    return name, target
            elif kind == 'MATCH':
                return kind, fields[1]
            elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                if DomainRules([rule]).matches(domain):
                    return kind + ',' + fields[1], fields[2]
            elif kind not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                raise ValueError('Unsupported top-level domain simulation rule: ' + kind)
        raise ValueError('Missing MATCH rule')

    def test_reviewed_exact_scope(self):
        rules = entries(ROOT / 'ruleset/Zhihu.yaml')
        self.assertEqual(len(rules), len(HOSTS))
        self.assertEqual(set(rules), {'DOMAIN,' + host for host in HOSTS})

    def test_hosts_reach_dedicated_policy(self):
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), ('Zhihu', TARGET))
                self.assertEqual(self.route(host, skip=True), ('ChinaMax', '🇨🇳 China-Global'))

    def test_non_target_routing_is_unchanged(self):
        controls = {'zhihu.com', 'zhimg.com', 'zhihuishu.com', 'cloudflare.com',
                    'example.org', 'static.example.org', 'p1.music.126.net',
                    'www.xiaohongshu.com', 'guzzoni.apple.com', 'hoyoverse.com'}
        controls |= {'probe.' + host for host in HOSTS}
        controls |= {host + '.example.org' for host in HOSTS}
        controls |= {'not' + host for host in HOSTS}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(self.providers['Zhihu'].matches(host))
                self.assertEqual(self.route(host), self.route(host, skip=True))

    def test_security_remains_first(self):
        for provider, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            providers = dict(self.providers)
            providers[provider] = DomainRules(['DOMAIN,' + host for host in HOSTS])
            for host in HOSTS:
                with self.subTest(provider=provider, host=host):
                    self.assertEqual(self.route(host, providers=providers), (provider, target))

    def test_policy_default_and_override(self):
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text())['proxy-groups']
        group = next(g for g in groups if g['name'] == TARGET)
        self.assertEqual(group['type'], 'select')
        self.assertEqual(group['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', group['proxies'])

    def test_position_preserves_security_gaming_and_specificity(self):
        marker = 'RULE-SET,Zhihu,' + TARGET
        self.assertEqual(self.ordered.count(marker), 1)
        position = self.ordered.index(marker)
        for earlier in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking',
                        'RULE-SET,InternationalGaming,🎮 国际游戏', 'RULE-SET,ChinaGaming,DIRECT'):
            self.assertLess(self.ordered.index(earlier), position)
        for later in ('RULE-SET,Apple,🍎 Apple', 'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            self.assertLess(position, self.ordered.index(later))


if __name__ == '__main__':
    unittest.main()
