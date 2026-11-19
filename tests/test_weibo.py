"""Weibo exact-entry routing and actual public-fixture validation contracts."""
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
from siri_ai import DomainRules

HOSTS = {'weibo.com', 'www.weibo.com'}
TARGET = '🟠 微博'
CONTROLS = {
    'm.weibo.cn', 'weibo.cn', 'm.weibo.com', 'visitor.passport.weibo.cn',
    'passport.weibo.com', 'api.weibo.com', 'd.weibo.com', 's.weibo.com',
    'vip.weibo.com', 'photo.weibo.com', 'game.weibo.com', 'data.weibo.com',
    'kefu.weibo.com', 'new.vip.weibo.cn', 'ir.weibo.com',
    'sina.com.cn', 'www.sina.com.cn', 'sinaimg.cn', 'wx1.sinaimg.cn',
    'tva1.sinaimg.cn', 'h5.sinaimg.cn', 'sinajs.cn', 'js.t.sinajs.cn', 'weibocdn.com',
    'www.wps.cn', 'www.feishu.cn', 'www.dingtalk.com', 'www.quark.cn', 'pan.quark.cn',
    'www.youku.com', 'www.xiaohongshu.com', 'www.bilibili.com', 'www.google.com',
    'guzzoni.apple.com', 'hmma.baidu.com', 'fastcdn.hoyoverse.com',
    'app.datadoghq.com', 'example.org',
}
PREDECESSORS = (
    'QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图', 'Zhihu,💡 知乎',
    'Xiaohongshu,📕 小红书 / REDnote', 'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣',
    'JD,🛒 京东', 'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
    'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝', 'BaiduMap,🗺️ 百度地图', 'Kuaishou,📹 快手',
    'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘', 'IQIYI,🎬 爱奇艺',
    'Xianyu,🐟 闲鱼', 'Railway12306,🚄 铁路12306', 'Youku,🎞️ 优酷',
    'WPSOffice,📝 WPS Office', 'Feishu,💼 飞书', 'DingTalk,💬 钉钉', 'Quark,🔍 夸克',
)


class WeiboContract(unittest.TestCase):
    MARKER = '  - RULE-SET,Weibo,' + TARGET + '\n'

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, name):
        return (self.root / name).read_text(encoding='utf-8')

    def write(self, name, text):
        (self.root / name).write_text(text, encoding='utf-8')

    def group_parts(self):
        text = self.read('config/proxy-groups.yaml')
        start = text.index('  - name: "' + TARGET + '"\n')
        end = text.index('  - name:', start + 1)
        return text[:start], text[start:end], text[end:]

    def rejected(self, helper_error, tree_error=None):
        with self.assertRaisesRegex(ValueError, helper_error):
            validate.validate_weibo(self.root)
        with self.assertRaisesRegex(ValueError, tree_error or helper_error):
            validate.validate_tree(self.root)

    def test_fixed_hosts_controls_and_options(self):
        self.assertEqual(HOSTS, {'weibo.com', 'www.weibo.com'})
        self.assertLessEqual(CONTROLS, validate.WEIBO_CONTROLS)
        self.assertFalse(HOSTS & CONTROLS)
        payload = yaml.safe_load(self.read('ruleset/Weibo.yaml'))['payload']
        self.assertEqual(set(payload), {'DOMAIN,weibo.com', 'DOMAIN,www.weibo.com'})
        self.assertEqual(len(payload), 2)
        model = DomainRules(payload)
        for host in CONTROLS | {value for h in HOSTS for value in
                               ('child.' + h, 'not' + h, h + '.example.org')}:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))
        group = next(g for g in yaml.safe_load(self.read('config/proxy-groups.yaml'))['proxy-groups']
                     if g['name'] == TARGET)
        self.assertEqual(group, {'name': TARGET, 'type': 'select',
                                'proxies': ['DIRECT', '🚀 节点选择', '🧭 Final']})

    def test_real_first_matches_and_non_target_routes(self):
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads(self.read(name)))
        models = {name: DomainRules(yaml.safe_load(self.read(row['path']))['payload'])
                  for name, row in manifests.items()}
        ordered = yaml.safe_load(self.read('config/rules.yaml'))['rules']

        def route(host, include=True):
            for rule in ordered:
                fields = rule.split(',')
                if fields[0] == 'RULE-SET':
                    if not include and fields[1] == 'Weibo':
                        continue
                    if models[fields[1]].matches(host):
                        return fields[1], fields[2]
                elif fields[0] in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return ','.join(fields[:2]), fields[2]
                elif fields[0] == 'MATCH':
                    return fields[0], fields[1]
                else:
                    self.assertIn(fields[0], {'GEOIP', 'IP-CIDR', 'IP-CIDR6'})
            self.fail('Missing MATCH')

        security = {('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')}
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertIn(route(host), security | {('Weibo', TARGET)})
                if route(host) in security:
                    self.assertEqual(route(host), route(host, False))
        for host in CONTROLS | {value for h in HOSTS for value in
                               ('child.' + h, 'not' + h, h + '.example.org')}:
            with self.subTest(control=host):
                self.assertEqual(route(host), route(host, False))
        validate.validate_weibo(self.root)

    def test_complete_public_fixture_passes(self):
        validate.validate_weibo(self.root)
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_real_tree_calls_weibo_once(self):
        with patch.object(validate, 'validate_weibo', side_effect=ValueError('Weibo gate')) as gate:
            with self.assertRaisesRegex(ValueError, '^Weibo gate$'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_each_host_and_exact_scope_are_required(self):
        original = self.read('ruleset/Weibo.yaml')
        variants = [(original.replace('  - DOMAIN,' + h + '\n', ''), 'two reviewed exact hosts')
                    for h in HOSTS]
        variants += [(original.replace('DOMAIN,weibo.com', 'DOMAIN-SUFFIX,weibo.com'), 'two reviewed exact hosts'),
                     (original.replace('DOMAIN,www.weibo.com', 'DOMAIN,wx1.sinaimg.cn'), 'two reviewed exact hosts'),
                     (original + '  - DOMAIN,weibo.com\n', 'Weibo: local ruleset contains duplicate entries')]
        for text, tree_error in variants:
            with self.subTest(text=text):
                self.write('ruleset/Weibo.yaml', text)
                self.rejected('two reviewed exact hosts', tree_error)

    def test_active_reference_is_unique_and_correct(self):
        original = self.read('config/rules.yaml')
        for changed in (original.replace(self.MARKER, ''), original + self.MARKER,
                        original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                        original.replace(self.MARKER, '  - RULE-SET,Weibo,DIRECT\n')):
            with self.subTest(rule=changed[-80:]):
                self.write('config/rules.yaml', changed)
                self.rejected('exactly one dedicated policy reference')

    def test_all_twenty_five_apps_stay_before_weibo(self):
        self.assertEqual(len(PREDECESSORS), 25)
        original = self.read('config/rules.yaml')
        for previous in PREDECESSORS:
            anchor = '  - RULE-SET,' + previous + '\n'
            self.assertEqual(original.count(anchor), 1)
            with self.subTest(previous=previous):
                self.write('config/rules.yaml', original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor))
                self.rejected('existing app rules must precede Weibo')

    def test_security_and_gaming_stay_before_weibo(self):
        original = self.read('config/rules.yaml')
        for previous in ('Privacy,REJECT', 'Hijacking,🚫 Hijacking',
                         'InternationalGaming,🎮 国际游戏', 'ChinaGaming,DIRECT'):
            with self.subTest(previous=previous):
                anchor = '  - RULE-SET,' + previous + '\n'
                self.write('config/rules.yaml', original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor))
                self.rejected('must precede Weibo')

    def test_broader_rules_stay_after_weibo(self):
        original = self.read('config/rules.yaml')
        for later in ('RULE-SET,SiriAI,🤖 AI 服务', 'RULE-SET,Apple,🍎 Apple',
                      'RULE-SET,YouTube,📼 YouTube', 'RULE-SET,Bilibili,📺 Bilibili',
                      'RULE-SET,TikTok,🎵 Tiktok', 'RULE-SET,Disney,🏰 Disney',
                      'RULE-SET,Netflix,🎞️ Netflix', 'RULE-SET,Gemini,♊ Gemini',
                      'RULE-SET,Google,🔎 Google', 'RULE-SET,Microsoft,🪟 Microsoft',
                      'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            anchor = '  - ' + later + '\n'
            self.assertEqual(original.count(anchor), 1)
            tree_error = 'Weibo must precede broader providers'
            if later.startswith(('RULE-SET,GlobalMedia,', 'RULE-SET,ChinaMax,')):
                tree_error = 'rules.yaml game/provider priority order is unsafe'
            elif later.startswith('GEOIP,'):
                tree_error = 'GEOIP CN fallback must be after GlobalMedia and before ChinaMax'
            elif later.startswith('RULE-SET,Google,'):
                tree_error = 'Gemini must be matched before the broader Google provider'
            with self.subTest(later=later):
                self.write('config/rules.yaml', original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER))
                self.rejected('Weibo must precede broader providers', tree_error)

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
                self.rejected('Weibo must be a DIRECT-first select')

    def test_missing_and_duplicate_groups_fail(self):
        before, block, after = self.group_parts()
        for changed, reason in ((before + after, 'undefined policy groups'),
                                (before + block + block + after, 'duplicate group')):
            with self.subTest(reason=reason):
                self.write('config/proxy-groups.yaml', changed)
                self.rejected('Weibo must be a DIRECT-first select', reason)

    def test_literal_select_formats_pass_helper_and_tree(self):
        before, block, after = self.group_parts()
        for declaration in ('type: "select"', "type: 'select'", 'type : select # literal',
                            '"type": select', "'type': 'select' # literal"):
            with self.subTest(declaration=declaration):
                text = before + block.replace('type: select', declaration) + after
                self.write('config/proxy-groups.yaml', text)
                group = next(g for g in yaml.safe_load(text)['proxy-groups'] if g['name'] == TARGET)
                self.assertEqual(group['type'], 'select')
                validate.validate_weibo(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_complex_and_duplicate_group_declarations_fail(self):
        before, block, after = self.group_parts()
        for declaration in ('type: fallback # override', 'type:', 'type : fallback',
                            '"type": fallback', "'type': fallback", r'"t\u0079pe": fallback',
                            '!!str type: fallback', '&kind type: fallback', '? type\n    : fallback',
                            'proxies: []', r'"pro\u0078ies": []', '!!str proxies: []',
                            '? proxies\n    : []', '<<: {type: fallback}', 'unknown: value'):
            with self.subTest(declaration=declaration):
                text = before + block + '    ' + declaration + '\n' + after
                yaml.safe_load(text)
                self.write('config/proxy-groups.yaml', text)
                if declaration.startswith(('type:', 'type :', '"type":', "'type':")):
                    reason = 'duplicate group field: type'
                elif declaration == 'proxies: []':
                    reason = 'duplicate group field: proxies'
                elif declaration == 'unknown: value':
                    reason = 'unsupported group field: unknown'
                else:
                    reason = 'expected a literal mapping key with a separated value'
                self.rejected('Weibo must be a DIRECT-first select',
                              r'Public config/proxy-groups\.yaml.*' + reason)

    def test_complex_proxy_members_fail_without_weakening_valid_structure(self):
        before, block, after = self.group_parts()
        for member in ('{name: DIRECT}', '!!str DIRECT', '&member DIRECT',
                       r'"DI\u0052ECT"', "'DIRECT'", 'DIRECT # comment'):
            with self.subTest(member=member):
                text = before + block + '      - ' + member + '\n' + after
                yaml.safe_load(text)
                self.write('config/proxy-groups.yaml', text)
                if member in ("'DIRECT'", 'DIRECT # comment'):
                    reason = 'Weibo must be a DIRECT-first select'
                elif member.startswith('"'):
                    reason = r'Public config/proxy-groups\.yaml.*expected an unescaped whole quoted literal'
                else:
                    reason = r'Public config/proxy-groups\.yaml.*unsupported scalar syntax'
                self.rejected('Weibo must be a DIRECT-first select', reason)

    def test_manifest_collision_is_rejected(self):
        local = json.loads(self.read('local-rulesets.json'))
        local['Apple'] = json.loads(self.read('sources.json'))['Apple']
        self.write('local-rulesets.json', json.dumps(local, ensure_ascii=False))
        self.rejected('Weibo manifests contain duplicate providers: Apple',
                      'manifests contain duplicate providers: Apple')

    def test_missing_own_and_unknown_providers_have_clear_errors(self):
        original = self.read('local-rulesets.json')
        local = json.loads(original)
        del local['Weibo']
        self.write('local-rulesets.json', json.dumps(local, ensure_ascii=False))
        with self.assertRaisesRegex(ValueError, 'Weibo routing references missing providers: Weibo'):
            validate.validate_weibo(self.root)
        self.write('local-rulesets.json', original)
        self.write('config/rules.yaml', self.read('config/rules.yaml') + '  - RULE-SET,MissingWeibo,DIRECT\n')
        self.rejected('Weibo routing references missing providers: MissingWeibo', 'references undefined providers')

    def test_unknown_kinds_and_whitespace_fields_fail_after_match(self):
        original = self.read('config/rules.yaml')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,weibo,DIRECT',
                     'DOMAIN, ,DIRECT', 'GEOIP, ,DIRECT', 'RULE-SET, ,DIRECT'):
            kind = rule.split(',')[0]
            if kind in {'DST-PORT', 'PROCESS-NAME'}:
                helper = 'Unsupported top-level rule in Weibo domain-only model: ' + kind
                tree = 'Unsupported top-level rule.*' + kind
            else:
                helper = 'Weibo domain-only model requires complete supported rules: ' + kind
                tree = ('references undefined providers' if kind == 'RULE-SET'
                        else 'domain-only model requires complete supported rules: ' + kind)
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original + '  - ' + rule + '\n')
                self.rejected(helper, tree)

    def test_incomplete_rule_shapes_have_strict_helper_diagnostics(self):
        # Existing tree consumers may diagnose bare RULE-SET earlier; pin this helper directly.
        original = self.read('config/rules.yaml')
        for rule in ('RULE-SET', 'RULE-SET,Privacy', 'DOMAIN,weibo.com', 'MATCH',
                     'MATCH,DIRECT,extra', 'GEOIP,CN,DIRECT,invalid',
                     'IP-CIDR6,2001:db8::/32,DIRECT,invalid'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original + '  - ' + rule + '\n')
                with self.assertRaisesRegex(ValueError, 'Weibo domain-only model requires complete supported rules'):
                    validate.validate_weibo(self.root)

    def test_preceding_ip_conditions_fail_helper_and_tree(self):
        original = self.read('config/rules.yaml')
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER))
                self.rejected('Weibo domain-only model cannot validate preceding IP conditions')

    def test_wrong_and_duplicate_public_roots_fail_both_gates(self):
        for path, key in (('config/rules.yaml', 'rules'), ('config/proxy-groups.yaml', 'proxy-groups')):
            original = self.read(path)
            for changed in (original + '\n' + key + ': []\n', original.replace(key + ':', 'unrelated:', 1)):
                with self.subTest(path=path, changed=changed[-30:]):
                    self.write(path, changed)
                    self.rejected('Public ' + path.replace('.', r'\.'))
            self.write(path, original)

    def test_future_security_updates_pass_helper_and_complete_tree(self):
        original_lock = self.read('sources.lock.json')
        for provider in ('Privacy', 'Hijacking'):
            path = f'ruleset/{provider}_No_Resolve.yaml'
            original = self.read(path)
            with self.subTest(provider=provider), contextlib.redirect_stdout(io.StringIO()):
                self.write(path, original + ''.join('  - DOMAIN,' + h + '\n' for h in sorted(HOSTS)))
                data = (self.root / path).read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                lock = json.loads(original_lock)
                lock['rulesets'][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                self.write('sources.lock.json', json.dumps(lock, ensure_ascii=False))
                generate(self.root, write=True)
                validate.validate_weibo(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)
                self.write(path, original)
                self.write('sources.lock.json', original_lock)
                generate(self.root, write=True)

    def test_non_security_preemption_and_wrong_security_targets_fail(self):
        original = self.read('config/rules.yaml')
        self.write('config/rules.yaml', original.replace(self.MARKER, '  - DOMAIN,weibo.com,DIRECT\n' + self.MARKER))
        self.rejected('Weibo is shadowed by an earlier rule', 'shadowed')
        for rule in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(rule=rule):
                self.write('config/rules.yaml', original.replace(rule, rule.rsplit(',', 1)[0] + ',DIRECT'))
                self.rejected('Weibo requires one active rule', 'missing expected rule: ' + rule)

    def test_all_helper_reads_are_explicit_utf8(self):
        original = Path.read_text
        seen = []

        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', checked):
            validate.validate_weibo(self.root)
        self.assertTrue(seen)


if __name__ == '__main__':
    unittest.main()
