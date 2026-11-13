"""Exact scope and effective domain routing for public NetEase Music endpoints."""
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries

EXPECTED = {'music.163.com', 'st.music.163.com', 'y.music.163.com',
            's1.music.126.net', 's2.music.126.net', 'p1.music.126.net',
            'p3.music.126.net', 'p6.music.126.net'}
TARGET = '🎵 网易云音乐'


class NetEaseMusicRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            cls.manifests.update(json.loads((ROOT / name).read_text()))
        cls.providers = {name: DomainRules(entries(ROOT / record['path']))
                         for name, record in cls.manifests.items()}
        cls.ordered = yaml.safe_load((ROOT / 'config/rules.yaml').read_text())['rules']

    def route(self, domain, skip=False, providers=None):
        providers = self.providers if providers is None else providers
        for rule in self.ordered:
            fields = rule.split(',')
            if fields[0] == 'RULE-SET':
                if skip and fields[1] == 'NetEaseMusic':
                    continue
                if providers[fields[1]].matches(domain):
                    return fields[1], fields[2]
            elif fields[0] == 'MATCH':
                return 'MATCH', fields[1]
            elif fields[0] in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                if DomainRules([rule]).matches(domain):
                    return ','.join(fields[:2]), fields[2]
            elif fields[0] not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                raise ValueError('Unsupported domain-model rule: ' + fields[0])
        self.fail('Missing MATCH')

    def test_reviewed_exact_scope(self):
        payload = yaml.safe_load((ROOT / 'ruleset/NetEaseMusic.yaml').read_text())['payload']
        self.assertEqual(len(payload), len(EXPECTED))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in EXPECTED})

    def check_effective_first_match(self, providers=None):
        for host in EXPECTED:
            with self.subTest(host=host):
                self.assertIn(self.route(host, providers=providers),
                              {('NetEaseMusic', TARGET), ('Privacy', 'REJECT'),
                               ('Hijacking', '🚫 Hijacking')})

    def test_effective_first_match(self):
        self.check_effective_first_match()

    def test_non_target_hosts_keep_their_routes(self):
        controls = {'163.com', '126.net', 'reg.163.com', 'mail.163.com',
                    'example.org', 'guzzoni.apple.com', 'hoyoverse.com',
                    'fastcdn.hoyoverse.com', 'clientlog.music.163.com',
                    'sentry.music.163.com'}
        controls |= {host for domain in EXPECTED for host in
                     ('child.' + domain, 'not' + domain, domain + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(self.providers['NetEaseMusic'].matches(host))
                self.assertEqual(self.route(host), self.route(host, skip=True))

    def test_security_rule_updates_keep_precedence(self):
        for name, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            for host in EXPECTED:
                with self.subTest(provider=name, host=host):
                    providers = dict(self.providers)
                    providers[name] = DomainRules(entries(ROOT / self.manifests[name]['path'])
                                                  + ['DOMAIN,' + host])
                    self.assertEqual(self.route(host, providers=providers), (name, target))
                    self.check_effective_first_match(providers)

    def test_non_security_shadowing_fails_the_same_contract(self):
        providers = dict(self.providers)
        providers['ChinaGaming'] = DomainRules(['DOMAIN,music.163.com'])
        # Run the same contract without subTest so assertRaises observes its failure.
        self.assertNotIn(self.route('music.163.com', providers=providers),
                         {('NetEaseMusic', TARGET), ('Privacy', 'REJECT'),
                          ('Hijacking', '🚫 Hijacking')})

    def test_direct_first_with_manual_proxy_choice(self):
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text())['proxy-groups']
        matches = [group for group in groups if group['name'] == TARGET]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['type'], 'select')
        self.assertEqual(matches[0]['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', matches[0]['proxies'])

    def test_order_and_single_reference(self):
        marker = 'RULE-SET,NetEaseMusic,' + TARGET
        self.assertEqual(self.ordered.count(marker), 1)
        pos = self.ordered.index(marker)
        for before in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking',
                       'RULE-SET,InternationalGaming,🎮 国际游戏', 'RULE-SET,ChinaGaming,DIRECT'):
            self.assertLess(self.ordered.index(before), pos)
        for after in ('RULE-SET,Apple,🍎 Apple', 'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            self.assertLess(pos, self.ordered.index(after))


if __name__ == '__main__':
    unittest.main()
