"""Exact Zhihu scope, policy and first-match domain regression checks."""
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

    def route(self, domain, skip=False, providers=None, ordered=None):
        providers = self.providers if providers is None else providers
        ordered = self.ordered if ordered is None else ordered
        for rule in ordered:
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

    def assert_reviewed_hosts_route(self, providers=None, ordered=None):
        allowed = {('Zhihu', TARGET), ('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')}
        for host in HOSTS:
            self.assertIn(self.route(host, providers=providers, ordered=ordered), allowed, host)

    def test_hosts_reach_dedicated_or_security_policy(self):
        self.assert_reviewed_hosts_route()

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
            self.assert_reviewed_hosts_route(providers=providers)
            for host in HOSTS:
                with self.subTest(provider=provider, host=host):
                    self.assertEqual(self.route(host, providers=providers), (provider, target))

    def test_non_security_shadowing_still_fails_acceptance(self):
        providers = dict(self.providers)
        providers['ChinaGaming'] = DomainRules(['DOMAIN,' + host for host in HOSTS])
        with self.assertRaises(AssertionError):
            self.assert_reviewed_hosts_route(providers=providers)

    def test_wrong_security_target_still_fails_acceptance(self):
        for provider, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            with self.subTest(provider=provider):
                providers = dict(self.providers)
                providers[provider] = DomainRules(['DOMAIN,' + host for host in HOSTS])
                ordered = [rule.replace(f'RULE-SET,{provider},{target}', f'RULE-SET,{provider},DIRECT')
                           for rule in self.ordered]
                with self.assertRaises(AssertionError):
                    self.assert_reviewed_hosts_route(providers=providers, ordered=ordered)

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


class ZhihuValidator(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, name, old, new):
        path = self.root / name
        path.write_text(path.read_text().replace(old, new))

    def test_current_contract(self):
        validate.validate_zhihu(self.root)

    def test_tree_calls_zhihu_contract(self):
        with patch.object(validate, 'validate_zhihu', side_effect=ValueError('Zhihu contract reached')):
            with self.assertRaisesRegex(ValueError, 'Zhihu contract reached'):
                validate.validate_tree(ROOT)

    def test_broadening_scope_is_rejected(self):
        self.mutate('ruleset/Zhihu.yaml', 'DOMAIN,www.zhihu.com', 'DOMAIN-SUFFIX,www.zhihu.com')
        with self.assertRaisesRegex(ValueError, 'eight reviewed exact hosts'):
            validate.validate_zhihu(self.root)

    def test_duplicates_are_rejected(self):
        path = self.root / 'ruleset/Zhihu.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,www.zhihu.com\n')
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            validate.validate_zhihu(self.root)

    def test_late_placement_is_rejected(self):
        line = '  - RULE-SET,Zhihu,💡 知乎\n'
        self.mutate('config/rules.yaml', line, '')
        self.mutate('config/rules.yaml', '  - MATCH,', line + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'must precede broader'):
            validate.validate_zhihu(self.root)

    def test_default_proxy_is_rejected(self):
        self.mutate('config/proxy-groups.yaml',
                    'name: "💡 知乎"\n    type: select\n    proxies:\n      - DIRECT',
                    'name: "💡 知乎"\n    type: select\n    proxies:\n      - "🚀 节点选择"')
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_zhihu(self.root)

    def test_security_bypass_is_rejected(self):
        line = '  - RULE-SET,Zhihu,💡 知乎\n'
        self.mutate('config/rules.yaml', line, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + line)
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_zhihu(self.root)

    def test_unknown_top_level_kind_is_rejected(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - DST-PORT,443,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_zhihu(self.root)

    def test_legal_security_additions_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            with self.subTest(provider=provider):
                path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                original = path.read_text()
                path.write_text(original + '  - DOMAIN,www.zhihu.com\n')
                try:
                    validate.validate_zhihu(self.root)
                finally:
                    path.write_text(original)

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,www.zhihu.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_zhihu(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_zhihu(self.root)

    def test_duplicate_provider_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + '  - RULE-SET,Zhihu,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_zhihu(self.root)


if __name__ == '__main__':
    unittest.main()
