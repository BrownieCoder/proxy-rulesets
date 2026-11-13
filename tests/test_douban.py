"""Exact Douban host scope, configurable egress and security-first routing."""
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

    def assert_reviewed_host_routes(self, providers=None):
        allowed = {('Douban', self.POLICY), ('Privacy', 'REJECT'),
                   ('Hijacking', '🚫 Hijacking')}
        actual = {host: self.route(host, providers=providers) for host in self.HOSTS}
        unexpected = {host: result for host, result in actual.items() if result not in allowed}
        self.assertEqual(unexpected, {}, f'Unexpected host routing: {unexpected}')

    def test_hosts_reach_dedicated_or_security_policy(self):
        self.assert_reviewed_host_routes()

    def test_security_and_game_precedence(self):
        marker = 'RULE-SET,Douban,' + self.POLICY
        self.assertEqual(self.ordered.count(marker), 1)
        position = self.ordered.index(marker)
        for earlier in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking',
                        'RULE-SET,InternationalGaming,🎮 国际游戏', 'RULE-SET,ChinaGaming,DIRECT',
                        'RULE-SET,Xiaohongshu,📕 小红书 / REDnote'):
            self.assertLess(self.ordered.index(earlier), position)
        for later in ('RULE-SET,Apple,🍎 Apple', 'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            self.assertLess(position, self.ordered.index(later))
        for provider, target in (('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')):
            models = dict(self.providers)
            models[provider] = DomainRules(['DOMAIN,www.douban.com'])
            with self.subTest(provider=provider):
                self.assertEqual(self.route('www.douban.com', providers=models), (provider, target))
                self.assert_reviewed_host_routes(providers=models)

    def test_non_security_preemption_fails_host_contract(self):
        models = dict(self.providers)
        models['ChinaGaming'] = DomainRules(['DOMAIN,www.douban.com'])
        with self.assertRaises(AssertionError):
            self.assert_reviewed_host_routes(providers=models)

    def test_wrong_security_target_fails_host_contract(self):
        models = dict(self.providers)
        models['Privacy'] = DomainRules(['DOMAIN,www.douban.com'])
        rules = [rule.replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
                 for rule in self.ordered]
        with patch.object(self, 'ordered', rules), self.assertRaises(AssertionError):
            self.assert_reviewed_host_routes(providers=models)

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


class DoubanValidator(unittest.TestCase):
    MARKER = '  - RULE-SET,Douban,📚 豆瓣\n'

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
        path.write_text(path.read_text().replace(old, new))

    def test_current_contract(self):
        validate.validate_douban(self.root)

    def test_scope_broadening_is_rejected_by_tree_validation(self):
        self.mutate('ruleset/Douban.yaml', 'DOMAIN,www.douban.com', 'DOMAIN-SUFFIX,douban.com')
        with self.assertRaisesRegex(ValueError, 'eight reviewed exact hosts'):
            validate.validate_tree(self.root)

    def test_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/Douban.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,www.douban.com\n')
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            validate.validate_douban(self.root)

    def test_late_rule_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_douban(self.root)

    def test_bypassing_security_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede Douban'):
            validate.validate_douban(self.root)

    def test_preempting_xiaohongshu_order_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        before = '  - RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n'
        self.mutate('config/rules.yaml', before, self.MARKER + before)
        with self.assertRaisesRegex(ValueError, 'must precede Douban'):
            validate.validate_douban(self.root)

    def test_unknown_top_level_rule_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '  - DST-PORT,443,DIRECT\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_douban(self.root)

    def test_proxy_default_is_rejected(self):
        self.mutate('config/proxy-groups.yaml',
                    'name: "📚 豆瓣"\n    type: select\n    proxies:\n      - DIRECT',
                    'name: "📚 豆瓣"\n    type: select\n    proxies:\n      - "🚀 节点选择"')
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_douban(self.root)

    def test_group_type_is_checked(self):
        self.mutate('config/proxy-groups.yaml', 'name: "📚 豆瓣"\n    type: select',
                    'name: "📚 豆瓣"\n    type: fallback')
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_douban(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text()
                    path.write_text(original + f'  - {kind},www.douban.com\n')
                    try:
                        validate.validate_douban(self.root)
                    finally:
                        path.write_text(original)

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,www.douban.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_douban(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_douban(self.root)

    def test_comment_cannot_replace_active_reference(self):
        self.mutate('config/rules.yaml', self.MARKER, self.MARKER.replace('  - ', '  # '))
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_douban(self.root)

    def test_duplicate_provider_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + '  - RULE-SET,Douban,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_douban(self.root)


if __name__ == '__main__':
    unittest.main()
