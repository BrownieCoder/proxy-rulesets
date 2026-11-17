"""DingTalk public-portal contract and real complete-fixture mutations."""
import contextlib
import hashlib
import io
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
from siri_ai import DomainRules, entries

HOSTS = {'www.dingtalk.com'}
TARGET = '💬 钉钉'
CONTROLS = {
    'dingtalk.com', 'gw.alicdn.com', 'img.alicdn.com', 'cloud.video.taobao.com',
    'alicdn.com', 'taobao.com', 'www.taobao.com', 'www.alipan.com',
    'www.goofish.com', 'www.youku.com', 'www.feishu.cn', 'work.weixin.qq.com',
    'guzzoni.apple.com', 'fastcdn.hoyoverse.com', 'generativelanguage.googleapis.com',
    'app.datadoghq.com', 'example.org',
}
PREDECESSORS = (
    'QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图', 'Zhihu,💡 知乎',
    'Xiaohongshu,📕 小红书 / REDnote', 'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣',
    'JD,🛒 京东', 'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
    'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝', 'BaiduMap,🗺️ 百度地图', 'Kuaishou,📹 快手',
    'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘', 'IQIYI,🎬 爱奇艺',
    'Xianyu,🐟 闲鱼', 'Railway12306,🚄 铁路12306', 'Youku,🎞️ 优酷',
)


class DingTalkContract(unittest.TestCase):
    MARKER = '  - RULE-SET,DingTalk,' + TARGET + '\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, relative):
        return (self.root / relative).read_text(encoding='utf-8')

    def write(self, relative, text):
        (self.root / relative).write_text(text, encoding='utf-8')

    def replace(self, relative, old, new):
        text = self.read(relative)
        self.assertIn(old, text)
        self.write(relative, text.replace(old, new))

    def group_parts(self):
        text = self.read('config/proxy-groups.yaml')
        start = text.index('  - name: "' + TARGET + '"\n')
        end = text.index('  - name:', start + 1)
        return text[:start], text[start:end], text[end:]

    def rejected(self, helper_reason, tree_reason=None):
        with self.assertRaisesRegex(ValueError, helper_reason):
            validate.validate_dingtalk(self.root)
        with self.assertRaisesRegex(ValueError, tree_reason or helper_reason):
            validate.validate_tree(self.root)

    def test_fixed_scope_controls_and_policy(self):
        self.assertEqual(HOSTS, {'www.dingtalk.com'})
        payload = yaml.safe_load(self.read('ruleset/DingTalk.yaml'))['payload']
        self.assertEqual(payload, ['DOMAIN,www.dingtalk.com'])
        self.assertLessEqual(CONTROLS, validate.DINGTALK_CONTROLS)
        model = DomainRules(payload)
        boundaries = CONTROLS | {'child.www.dingtalk.com', 'notwww.dingtalk.com',
                                 'www.dingtalk.com.example.org'}
        for host in boundaries:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))
        groups = yaml.safe_load(self.read('config/proxy-groups.yaml'))['proxy-groups']
        group = next(group for group in groups if group['name'] == TARGET)
        self.assertEqual(group['type'], 'select')
        self.assertEqual(group['proxies'], ['DIRECT', '🚀 节点选择', '🧭 Final'])

    def test_actual_first_matches_and_non_target_routes(self):
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads(self.read(name)))
        providers = {name: DomainRules(entries(self.root / row['path']))
                     for name, row in manifests.items()}
        ordered = yaml.safe_load(self.read('config/rules.yaml'))['rules']

        def route(host, include=True):
            for rule in ordered:
                f = rule.split(',')
                if f[0] == 'RULE-SET':
                    if not include and f[1] == 'DingTalk':
                        continue
                    if providers[f[1]].matches(host):
                        return f[1], f[2]
                elif f[0] in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return ','.join(f[:2]), f[2]
                elif f[0] == 'MATCH':
                    return f[0], f[1]
                else:
                    self.assertIn(f[0], {'GEOIP', 'IP-CIDR', 'IP-CIDR6'})
            self.fail('Missing MATCH')

        security = {('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')}
        for host in HOSTS:
            current = route(host)
            self.assertIn(current, security | {('DingTalk', TARGET)})
            if current in security:
                self.assertEqual(current, route(host, False))
        for host in CONTROLS | {'child.www.dingtalk.com', 'notwww.dingtalk.com',
                                'www.dingtalk.com.example.org'}:
            with self.subTest(host=host):
                self.assertEqual(route(host), route(host, False))
        validate.validate_dingtalk(self.root)

    def test_complete_public_fixture_passes(self):
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_real_tree_calls_dingtalk_gate_once(self):
        with patch.object(validate, 'validate_dingtalk', side_effect=ValueError('DingTalk sentinel')) as gate:
            with self.assertRaisesRegex(ValueError, 'DingTalk sentinel'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_scope_mutations_are_rejected(self):
        original = self.read('ruleset/DingTalk.yaml')
        for text in (original.replace('DOMAIN,www.dingtalk.com', 'DOMAIN-SUFFIX,dingtalk.com'),
                     original.replace('DOMAIN,www.dingtalk.com', 'DOMAIN,img.alicdn.com'),
                     original + '  - DOMAIN,www.dingtalk.com\n',
                     original + '  - DOMAIN,cloud.video.taobao.com\n'):
            with self.subTest(text=text):
                self.write('ruleset/DingTalk.yaml', text)
                self.rejected('one reviewed exact host', 'reviewed exact host|duplicate')

    def test_reference_mutations_are_rejected(self):
        original = self.read('config/rules.yaml')
        for text in (original.replace(self.MARKER, ''), original + self.MARKER,
                     original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                     original.replace(self.MARKER, '  - RULE-SET,DingTalk,DIRECT\n')):
            with self.subTest(text=text[-80:]):
                self.write('config/rules.yaml', text)
                self.rejected('exactly one dedicated policy reference', 'dedicated policy reference')

    def test_all_twenty_one_apps_stay_before_dingtalk(self):
        self.assertEqual(len(PREDECESSORS), 21)
        original = self.read('config/rules.yaml')
        for predecessor in PREDECESSORS:
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            with self.subTest(predecessor=predecessor):
                self.write('config/rules.yaml', original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor))
                self.rejected('existing app rules must precede DingTalk', 'must precede')

    def test_successors_stay_after_dingtalk(self):
        original = self.read('config/rules.yaml')
        for successor in ('RULE-SET,SiriAI,🤖 AI 服务', 'RULE-SET,Apple,🍎 Apple',
                          'RULE-SET,YouTube,📼 YouTube', 'RULE-SET,Bilibili,📺 Bilibili',
                          'RULE-SET,TikTok,🎵 Tiktok', 'RULE-SET,Disney,🏰 Disney',
                          'RULE-SET,Netflix,🎞️ Netflix', 'RULE-SET,Gemini,♊ Gemini',
                          'RULE-SET,GlobalMedia,🛰️ International-Global',
                          'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            anchor = '  - ' + successor + '\n'
            self.assertEqual(original.count(anchor), 1)
            with self.subTest(successor=successor):
                self.write('config/rules.yaml', original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER))
                self.rejected('DingTalk must precede broader providers', 'must precede|must be after.*before|order|顺序')

    def test_security_and_gaming_cannot_be_bypassed(self):
        original = self.read('config/rules.yaml')
        for anchor in ('  - RULE-SET,Privacy,REJECT\n', '  - RULE-SET,ChinaGaming,DIRECT\n'):
            with self.subTest(anchor=anchor):
                self.write('config/rules.yaml', original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor))
                self.rejected('must precede DingTalk', 'must precede')

    def test_direct_first_select_proxy_and_final_are_required(self):
        before, block, after = self.group_parts()
        for changed in (block.replace('type: select', 'type: fallback'),
                        block.replace('      - DIRECT\n', ''),
                        block.replace('      - DIRECT\n      - "🚀 节点选择"\n',
                                      '      - "🚀 节点选择"\n      - DIRECT\n'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('      - "🧭 Final"\n', '')):
            with self.subTest(block=changed):
                self.write('config/proxy-groups.yaml', before + changed + after)
                self.rejected('DingTalk must be a DIRECT-first select', 'DIRECT-first select')

    def test_missing_and_duplicate_groups_fail(self):
        before, block, after = self.group_parts()
        for text, reason in ((before + after, 'undefined policy groups'),
                             (before + block + block + after, 'duplicate group')):
            with self.subTest(reason=reason):
                self.write('config/proxy-groups.yaml', text)
                self.rejected('DingTalk must be a DIRECT-first select', reason)

    def test_literal_select_formats_pass_real_helper_and_tree(self):
        before, block, after = self.group_parts()
        for declaration in ('type: "select"', "type: 'select'", 'type : select # literal',
                            '"type": select', "'type': 'select' # literal"):
            with self.subTest(declaration=declaration):
                text = before + block.replace('type: select', declaration) + after
                self.write('config/proxy-groups.yaml', text)
                group = next(g for g in yaml.safe_load(text)['proxy-groups'] if g['name'] == TARGET)
                self.assertEqual(group['type'], 'select')
                validate.validate_dingtalk(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_complex_group_declarations_fail_closed(self):
        before, block, after = self.group_parts()
        for declaration in ('type: fallback # override', 'type:', 'type : fallback',
                            '"type": fallback', "'type': fallback", r'"t\u0079pe": fallback',
                            '!!str type: fallback', '&kind type: fallback', '? type\n    : fallback',
                            'proxies: []', r'"pro\u0078ies": []', '!!str proxies: []',
                            '? proxies\n    : []', '<<: {type: fallback}', 'unknown: value'):
            with self.subTest(declaration=declaration):
                text = before + block + '    ' + declaration + '\n' + after
                yaml.safe_load(text)  # Valid YAML can still be outside the public template grammar.
                self.write('config/proxy-groups.yaml', text)
                self.rejected('DingTalk must be a DIRECT-first select', 'DIRECT-first select|undefined.*groups')

    def test_complex_proxy_members_fail_closed(self):
        before, block, after = self.group_parts()
        for member in ('{name: DIRECT}', '!!str DIRECT', '&member DIRECT',
                       r'"DI\u0052ECT"', "'DIRECT'", 'DIRECT # comment'):
            with self.subTest(member=member):
                text = before + block + '      - ' + member + '\n' + after
                yaml.safe_load(text)
                self.write('config/proxy-groups.yaml', text)
                self.rejected('DingTalk must be a DIRECT-first select', 'DIRECT-first select|undefined.*groups')

    def test_provider_collisions_fail_both_gates(self):
        sources = json.loads(self.read('sources.json'))
        local = json.loads(self.read('local-rulesets.json'))
        local['Apple'] = sources['Apple']
        self.write('local-rulesets.json', json.dumps(local, ensure_ascii=False))
        self.rejected('DingTalk manifests contain duplicate providers: Apple', 'manifests contain duplicate providers: Apple')

    def test_missing_and_unknown_providers_have_clear_errors(self):
        local = json.loads(self.read('local-rulesets.json'))
        del local['DingTalk']
        self.write('local-rulesets.json', json.dumps(local, ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, 'DingTalk routing references missing providers: DingTalk'):
            validate.validate_dingtalk(self.root)
        self.write('local-rulesets.json', (ROOT / 'local-rulesets.json').read_text(encoding='utf-8'))
        self.write('config/rules.yaml', self.read('config/rules.yaml') + '  - RULE-SET,MissingDingTalk,DIRECT\n')
        self.rejected('DingTalk routing references missing providers: MissingDingTalk', 'undefined providers|missing providers')

    def test_unknown_rule_kinds_fail_helper_and_tree(self):
        original = self.read('config/rules.yaml')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,dingtalk,DIRECT'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original + '  - ' + rule + '\n')
                self.rejected('Unsupported top-level rule in DingTalk domain-only model', 'Unsupported top-level rule')

    def test_blank_required_fields_are_not_accepted(self):
        original = self.read('config/rules.yaml')
        for rule in ('DOMAIN, ,DIRECT', 'DOMAIN-SUFFIX, ,DIRECT', 'GEOIP, ,DIRECT',
                     'IP-CIDR, ,DIRECT', 'IP-CIDR6, ,DIRECT', 'RULE-SET, ,DIRECT'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original + '  - ' + rule + '\n')
                self.rejected('DingTalk domain-only model requires complete supported rules',
                              'complete supported rules|undefined providers|missing providers')

    def test_incomplete_rule_shapes_have_strict_helper_diagnostics(self):
        original = self.read('config/rules.yaml')
        # Some older tree consumers diagnose incomplete syntax earlier; this directly pins the new helper.
        for rule in ('RULE-SET', 'RULE-SET,Privacy', 'DOMAIN,www.dingtalk.com', 'MATCH',
                     'MATCH,DIRECT,extra', 'GEOIP,CN,DIRECT,invalid',
                     'IP-CIDR6,2001:db8::/32,DIRECT,invalid'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original + '  - ' + rule + '\n')
                with self.assertRaisesRegex(ValueError, 'DingTalk domain-only model requires complete supported rules'):
                    validate.validate_dingtalk(self.root)

    def test_preceding_ip_conditions_fail_both_gates(self):
        original = self.read('config/rules.yaml')
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER))
                self.rejected('DingTalk domain-only model cannot validate preceding IP conditions',
                              'domain-only model cannot validate preceding IP conditions')

    def test_duplicate_rules_root_is_rejected_by_both_gates(self):
        self.write('config/rules.yaml', self.read('config/rules.yaml') + '\nrules: []\n')
        self.rejected('Public config/rules.yaml', 'Public config/rules.yaml')

    def test_legitimate_security_updates_pass_helper_and_complete_tree(self):
        # Model public upstream updates only in this disposable fixture, never in ROOT.
        lock_path = self.root / 'sources.lock.json'
        original_lock = lock_path.read_text(encoding='utf-8')
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            with self.subTest(provider=provider), contextlib.redirect_stdout(io.StringIO()):
                path.write_text(original + '  - DOMAIN,www.dingtalk.com\n', encoding='utf-8')
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                lock = json.loads(original_lock)
                lock['rulesets'][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                lock_path.write_text(json.dumps(lock, ensure_ascii=False), encoding='utf-8')
                generate(self.root, write=True)
                validate.validate_dingtalk(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)
                path.write_text(original, encoding='utf-8')
                lock_path.write_text(original_lock, encoding='utf-8')
                generate(self.root, write=True)

    def test_non_security_shadowing_and_wrong_security_target_fail(self):
        original = self.read('config/rules.yaml')
        self.write('config/rules.yaml', original.replace(self.MARKER, '  - DOMAIN,www.dingtalk.com,DIRECT\n' + self.MARKER))
        self.rejected('DingTalk is shadowed by an earlier rule', 'shadowed')
        self.write('config/rules.yaml', original.replace('RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT'))
        self.rejected('DingTalk requires one active rule', 'missing expected rule|active rule|Privacy.*REJECT|first.*REJECT')

    def test_all_helper_reads_are_explicit_utf8(self):
        original = Path.read_text
        seen = []

        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', checked):
            validate.validate_dingtalk(self.root)
        self.assertTrue(seen)


if __name__ == '__main__':
    unittest.main()
