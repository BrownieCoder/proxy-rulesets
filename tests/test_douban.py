"""Exact Douban host scope, configurable egress and security-first routing."""
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries


class DoubanRouting(unittest.TestCase):
    HOSTS = {
        'accounts.douban.com', 'asset.doubanio.com', 'book.douban.com',
        'img3.doubanio.com', 'img9.doubanio.com', 'm.douban.com',
        'movie.douban.com', 'www.douban.com',
    }
    POLICY = '📚 豆瓣'

    @classmethod
    def setUpClass(cls):
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((ROOT / name).read_text()))
        cls.providers = {name: DomainRules(entries(ROOT / source['path']))
                         for name, source in manifests.items()}
        cls.ordered = entries(ROOT / 'config/rules.yaml')

    def route(self, domain, include_douban=True, providers=None):
        providers = self.providers if providers is None else providers
        for rule in self.ordered:
            fields = rule.split(',')
            kind = fields[0]
            if kind == 'RULE-SET':
                if fields[1] == 'Douban' and not include_douban:
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif kind == 'MATCH':
                return 'MATCH', fields[1]
            elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                if DomainRules([rule]).matches(domain):
                    return fields[0] + ',' + fields[1], fields[2]
            elif kind not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                raise ValueError(f'Unsupported top-level rule in domain-only model: {kind}')
        raise ValueError('Missing MATCH rule')

    def test_only_reviewed_exact_hosts(self):
        rules = entries(ROOT / 'ruleset/Douban.yaml')
        self.assertEqual(len(rules), len(self.HOSTS))
        self.assertEqual(set(rules), {'DOMAIN,' + host for host in self.HOSTS})

    def test_hosts_reach_dedicated_policy(self):
        for host in self.HOSTS:
            with self.subTest(host=host):
                self.assertEqual(self.route(host), ('Douban', self.POLICY))

    def test_security_and_game_precedence(self):
        marker = 'RULE-SET,Douban,' + self.POLICY
        self.assertEqual(self.ordered.count(marker), 1)
        position = self.ordered.index(marker)
        for earlier in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking',
                        'RULE-SET,InternationalGaming,🎮 国际游戏', 'RULE-SET,ChinaGaming,DIRECT'):
            self.assertLess(self.ordered.index(earlier), position)
        for later in ('RULE-SET,Apple,🍎 Apple', 'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            self.assertLess(position, self.ordered.index(later))
        for provider, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            models = dict(self.providers)
            models[provider] = DomainRules(['DOMAIN,www.douban.com'])
            with self.subTest(provider=provider):
                self.assertEqual(self.route('www.douban.com', providers=models), (provider, target))

    def test_default_direct_with_manual_proxy_choice(self):
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text())['proxy-groups']
        group = next(group for group in groups if group['name'] == self.POLICY)
        self.assertEqual(group['type'], 'select')
        self.assertEqual(group['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', group['proxies'])

    def test_non_target_domain_routes_are_unchanged(self):
        controls = {'douban.com', 'doubanio.com', 'api.douban.com', 'music.douban.com',
                    'douban.fm', 'notdouban.com', 'cloudflare.com', 'reddit.com',
                    'hmma.baidu.com', 'hoyoverse.com', 'guzzoni.apple.com'}
        controls |= {variant for host in self.HOSTS
                     for variant in ('child.' + host, host + '.example.org', 'not' + host)}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(self.providers['Douban'].matches(host))
                self.assertEqual(self.route(host), self.route(host, include_douban=False))


if __name__ == '__main__':
    unittest.main()
