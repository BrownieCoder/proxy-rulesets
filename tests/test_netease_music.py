"""Exact scope and effective domain routing for public NetEase Music endpoints."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries
import validate

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

    def test_effective_first_match(self):
        validate.validate_netease_music(ROOT)

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


class NetEaseMusicValidatorMutations(unittest.TestCase):
    MARKER = '  - RULE-SET,NetEaseMusic,' + TARGET + '\n'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('config', 'ruleset'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def test_security_updates_pass_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text()
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},music.163.com\n')
                    try:
                        validate.validate_netease_music(self.root)
                    finally:
                        path.write_text(original)

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,music.163.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_netease_music(self.root)

    def test_wrong_security_target_is_rejected(self):
        path = self.root / 'ruleset/Privacy_No_Resolve.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,music.163.com\n')
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT'))
        with self.assertRaisesRegex(ValueError, 'active expected rule'):
            validate.validate_netease_music(self.root)

    def test_scope_broadening_is_rejected_by_tree_validation(self):
        path = self.root / 'ruleset/NetEaseMusic.yaml'
        path.write_text(path.read_text().replace('DOMAIN,music.163.com', 'DOMAIN-SUFFIX,163.com'))
        with self.assertRaisesRegex(ValueError, 'eight reviewed exact'):
            validate.validate_tree(self.root)

    def test_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/NetEaseMusic.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,music.163.com\n')
        with self.assertRaisesRegex(ValueError, 'eight reviewed exact'):
            validate.validate_netease_music(self.root)

    def test_late_rule_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        text = path.read_text().replace(self.MARKER, '')
        path.write_text(text.replace('  - MATCH,', self.MARKER + '  - MATCH,'))
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_netease_music(self.root)

    def test_bypassing_security_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        text = path.read_text().replace(self.MARKER, '')
        path.write_text(text.replace('rules:\n', 'rules:\n' + self.MARKER))
        with self.assertRaisesRegex(ValueError, 'Security and gaming'):
            validate.validate_netease_music(self.root)

    def test_unknown_top_level_rule_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace(self.MARKER, '  - DST-PORT,443,DIRECT\n' + self.MARKER))
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_netease_music(self.root)

    def test_proxy_default_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        prefix, group = path.read_text().split('  - name: "🎵 网易云音乐"\n', 1)
        path.write_text(prefix + '  - name: "🎵 网易云音乐"\n' + group.replace('      - DIRECT\n', '', 1))
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_netease_music(self.root)

    def test_non_select_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        prefix, group = path.read_text().split('  - name: "🎵 网易云音乐"\n', 1)
        path.write_text(prefix + '  - name: "🎵 网易云音乐"\n' + group.replace('type: select', 'type: fallback', 1))
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_netease_music(self.root)

    def test_comment_cannot_replace_active_reference(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace(self.MARKER, self.MARKER.replace('  - ', '  # ')))
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_netease_music(self.root)

    def test_duplicate_provider_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_netease_music(self.root)


if __name__ == '__main__':
    unittest.main()
