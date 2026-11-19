"""BOSS Zhipin rule scope, first-match behavior and complete public-tree gates."""
import hashlib
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
from generate_catalog import generate
from siri_ai import DomainRules

TARGET = '💼 BOSS直聘'
HOSTS = ('www.zhipin.com', 'app.zhipin.com')
CONTROLS = {'zhipin.com', 'bosszhipin.com', 'kanzhun.com', 'about.zhipin.com',
            'ir.zhipin.com', 'static.zhipin.com', 'img.bosszhipin.com',
            'youle.zhipin.com', 'hi.zhipin.com', 'gongyi.zhipin.com',
            'www.dianzhangzhipin.com', 'www.offertoday.com', 'www.quark.cn',
            'pan.quark.cn', 'www.feishu.cn', 'www.dingtalk.com', 'www.wps.cn',
            'weixin.qq.com', 'weibo.com', 'www.sf-express.com',
            'guzzoni.apple.com', 'fastcdn.hoyoverse.com', 'hmma.baidu.com', 'example.org'}
CONTROLS |= {near for host in HOSTS for near in
             ('child.' + host, 'not' + host, host + '.example.org')}
PRIOR = ('Privacy', 'Hijacking', 'InternationalGaming', 'ChinaGaming',
         'QQMusic', 'Douyin', 'Amap', 'Zhihu', 'Xiaohongshu', 'NetEaseMusic',
         'Douban', 'JD', 'Meituan', 'BaiduPan', 'Ctrip', 'Pinduoduo', 'Taobao',
         'BaiduMap', 'Kuaishou', 'TencentVideo', 'AliPan', 'IQIYI', 'Xianyu',
         'Railway12306', 'Youku', 'WPSOffice', 'Feishu', 'DingTalk', 'Quark')
LATER = ('SiriAI', 'Apple', 'YouTube', 'Bilibili', 'TikTok', 'Disney', 'Netflix',
         'Gemini', 'Google', 'Microsoft', 'GlobalMedia', 'ChinaMax')


class BossZhipinContract(unittest.TestCase):
    MARKER = '  - RULE-SET,BossZhipin,' + TARGET + '\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, path):
        return (self.root / path).read_text(encoding='utf-8')

    def write(self, path, text):
        (self.root / path).write_text(text, encoding='utf-8')

    def reject(self, reason, tree_reason=None):
        with self.assertRaisesRegex(ValueError, reason):
            validate.validate_boss_zhipin(self.root)
        with self.assertRaisesRegex(ValueError, tree_reason or reason):
            validate.validate_tree(self.root)

    def test_complete_fixture_runs_real_gate_once(self):
        gate = validate.validate_boss_zhipin
        with patch.object(validate, 'validate_boss_zhipin', wraps=gate) as called:
            self.assertEqual(validate.validate_tree(self.root), 0)
            called.assert_called_once_with(self.root)

    def test_exact_payload_group_and_actual_first_matches(self):
        payload = yaml.safe_load(self.read('ruleset/BossZhipin.yaml'))['payload']
        self.assertEqual(payload, ['DOMAIN,' + h for h in HOSTS])
        self.assertLessEqual(set(HOSTS), DomainRules(payload).exact)
        groups = yaml.safe_load(self.read('config/proxy-groups.yaml'))['proxy-groups']
        self.assertEqual([g for g in groups if g['name'] == TARGET], [
            dict(name=TARGET, type='select', proxies=['DIRECT', '🚀 节点选择', '🧭 Final'])
        ])
        manifests = {}
        for file in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads(self.read(file)))
        providers = {name: DomainRules(yaml.safe_load(self.read(item['path']))['payload'])
                     for name, item in manifests.items()}
        active = yaml.safe_load(self.read('config/rules.yaml'))['rules']

        def route(host, without_app=False):
            for line in active:
                fields = line.split(',')
                kind = fields[0]
                if kind == 'RULE-SET':
                    name, dest = fields[1:3]
                    if (not without_app or name != 'BossZhipin') and providers[name].matches(host):
                        return name, dest
                elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([line]).matches(host):
                        return ','.join(fields[:2]), fields[2]
                elif kind == 'MATCH':
                    return kind, fields[1]
                else:
                    self.assertIn(kind, {'IP-CIDR', 'IP-CIDR6', 'GEOIP'})
            self.fail('missing MATCH')

        for host in HOSTS:
            with self.subTest(host=host):
                self.assertIn(route(host), {('BossZhipin', TARGET), ('Privacy', 'REJECT'),
                                            ('Hijacking', '🚫 Hijacking')})
                if route(host)[0] != 'BossZhipin':
                    self.assertEqual(route(host), route(host, without_app=True))
        for host in CONTROLS:
            with self.subTest(control=host):
                self.assertFalse(providers['BossZhipin'].matches(host))
                self.assertEqual(route(host), route(host, without_app=True))

    def test_broad_domain_duplicate_and_missing_scope_fail(self):
        path = 'ruleset/BossZhipin.yaml'
        text = self.read(path)
        for content in (
            text.replace('DOMAIN,www.zhipin.com', 'DOMAIN-SUFFIX,zhipin.com'),
            text + '  - DOMAIN,www.zhipin.com\n',
            *(text.replace('  - DOMAIN,' + h + '\n', '') for h in HOSTS),
            text.replace('DOMAIN,app.zhipin.com', 'DOMAIN,static.zhipin.com'),
        ):
            with self.subTest(content=content):
                self.write(path, content)
                self.reject('two reviewed exact hosts', 'two reviewed exact hosts|duplicate entries')

    def test_unique_dedicated_reference(self):
        path = 'config/rules.yaml'
        text = self.read(path)
        for changed in (text.replace(self.MARKER, ''), text + self.MARKER,
                        text.replace(self.MARKER, self.MARKER.replace(TARGET, 'DIRECT'))):
            self.write(path, changed)
            self.reject('one dedicated policy reference')

    def test_each_existing_app_security_and_gaming_anchor_precedes(self):
        path = 'config/rules.yaml'
        text = self.read(path)
        clean = text.replace(self.MARKER, '')
        for name in PRIOR:
            anchor = next(line for line in clean.splitlines() if line.startswith('  - RULE-SET,' + name + ','))
            with self.subTest(predecessor=name), self.assertRaisesRegex(ValueError, 'existing app rules must precede'):
                self.write(path, clean.replace(anchor, self.MARKER + anchor))
                validate.validate_boss_zhipin(self.root)
        quark = next(line for line in clean.splitlines() if line.startswith('  - RULE-SET,Quark,'))
        self.write(path, clean.replace(quark, self.MARKER + quark))
        self.reject('existing app rules must precede')

    def test_each_broader_anchor_follows(self):
        path = 'config/rules.yaml'
        text = self.read(path)
        anchors = [next(line for line in text.splitlines() if line.startswith('  - RULE-SET,' + name + ','))
                   for name in LATER]
        anchors.append('  - GEOIP,CN,DIRECT,no-resolve')
        for anchor in anchors:
            with self.subTest(successor=anchor), self.assertRaisesRegex(ValueError, 'must precede broader providers'):
                changed = text.replace(anchor + '\n', '').replace(self.MARKER, anchor + '\n' + self.MARKER)
                self.write(path, changed)
                validate.validate_boss_zhipin(self.root)

    def test_ordered_literal_group_members_are_required(self):
        path = 'config/proxy-groups.yaml'
        text = self.read(path)
        marker = '  - name: "' + TARGET + '"\n'
        start = text.index(marker)
        end = text.index('  - name:', start + len(marker))
        group = text[start:end]
        options = '      - DIRECT\n      - "🚀 节点选择"\n      - "🧭 Final"\n'
        for value in ('      - DIRECT\n      - "🚀 节点选择"\n',
                      '      - "🚀 节点选择"\n      - DIRECT\n      - "🧭 Final"\n',
                      options + '      - REJECT\n'):
            self.assertIn(options, group)
            self.write(path, text[:start] + group.replace(options, value) + text[end:])
            self.reject('BossZhipin.*DIRECT-first select')
        self.write(path, text[:start] + group.replace('type: select', 'type: fallback') + text[end:])
        self.reject('BossZhipin.*DIRECT-first select')

    def test_ambiguous_group_fields_reject_without_weakening_app_gate(self):
        path = 'config/proxy-groups.yaml'
        text = self.read(path)
        start = text.index('  - name: "' + TARGET + '"')
        end = text.index('  - name:', start + 1)
        for extra, reason in (
            ('    "type": fallback\n', 'duplicate group field: type'),
            ('    "proxies": []\n', 'duplicate group field: proxies'),
            ('      - {name: DIRECT}\n', 'unsupported scalar syntax'),
        ):
            with self.subTest(extra=extra):
                self.write(path, text[:end] + extra + text[end:])
                self.reject('BossZhipin.*DIRECT-first select', r'Public config/proxy-groups\.yaml.*' + reason)

    def test_supported_literal_select_format_passes(self):
        path = 'config/proxy-groups.yaml'
        text = self.read(path)
        marker = '  - name: "' + TARGET + '"\n    type: select'
        self.write(path, text.replace(marker, marker.replace('type: select', '"type": \'select\' # literal')))
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_policy_and_routing_root_rejections_reach_both_gates(self):
        for path, key in (('config/proxy-groups.yaml', 'proxy-groups'), ('config/rules.yaml', 'rules')):
            text = self.read(path)
            for changed in (text + '\n' + key + ': []\n', text.replace(key + ':', 'unrelated:', 1)):
                with self.subTest(path=path, mutation=changed[-30:]):
                    self.write(path, changed)
                    self.reject('Public ' + path)
            self.write(path, text)

    def test_known_security_matches_may_preempt_new_route(self):
        for filename in ('Privacy_No_Resolve.yaml', 'Hijacking_No_Resolve.yaml'):
            path = 'ruleset/' + filename
            original = self.read(path)
            self.write(path, original + '  - DOMAIN,' + HOSTS[0] + '\n')
            lockpath = 'sources.lock.json'
            original_lock = self.read(lockpath)
            lock = json.loads(original_lock)
            source = next(x for x in lock['rulesets'].values() if x['path'] == path)
            data = (self.root / path).read_bytes()
            source['bytes'] = len(data)
            source['sha256'] = hashlib.sha256(data).hexdigest()
            self.write(lockpath, json.dumps(lock))
            generate(self.root, write=True)
            self.assertEqual(validate.validate_tree(self.root), 0)
            self.write(path, original)
            self.write(lockpath, original_lock)

    def test_non_security_preemption_does_not_pass(self):
        path = 'config/rules.yaml'
        text = self.read(path)
        self.write(path, text.replace(self.MARKER, '  - DOMAIN,' + HOSTS[0] + ',DIRECT\n' + self.MARKER))
        self.reject('shadowed by an earlier rule')

    def test_bad_rule_fields_unknown_provider_and_preceding_ip_hold(self):
        path = 'config/rules.yaml'
        text = self.read(path)
        for line, reason, tree_reason in (
            ('  - PROCESS-NAME,unknown,DIRECT\n', 'Unsupported top-level.*BossZhipin', 'Unsupported top-level'),
            ('  - DOMAIN, ,DIRECT\n', 'complete supported rules', 'complete supported rules'),
            ('  - RULE-SET,MissingPublicProvider,DIRECT\n', 'routing references missing providers', 'undefined providers'),
            ('  - IP-CIDR,192.0.2.0/24,DIRECT,no-resolve\n', 'cannot validate preceding IP conditions', None),
        ):
            with self.subTest(line=line):
                self.write(path, text.replace(self.MARKER, line + self.MARKER))
                self.reject(reason, tree_reason)


if __name__ == '__main__':
    unittest.main()
