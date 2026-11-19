"""Feishu production-validator mutations with public fixtures only."""
import json
import hashlib
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
from siri_ai import DomainRules
from generate_catalog import generate

HOSTS = {'www.feishu.cn'}
CONTROLS = {
    "feishu.cn", "www.larksuite.com", "larksuite.com", "apps.apple.com",
    "y.qq.com", "www.douyin.com", "restapi.amap.com", "www.zhihu.com",
    "www.xiaohongshu.com", "music.163.com", "www.douban.com", "www.jd.com",
    "www.meituan.com", "pan.baidu.com", "www.ctrip.com", "www.pinduoduo.com",
    "www.taobao.com", "map.baidu.com", "www.kuaishou.com", "v.qq.com", "m.v.qq.com",
    "www.alipan.com", "www.aliyundrive.com", "www.iqiyi.com", "goofish.com",
    "www.goofish.com", "terms.goofish.com", "www.12306.cn", "kyfw.12306.cn",
    "dynamic.12306.cn", "www.youku.com", "guzzoni.apple.com", "msg.qy.net",
    "hmma.baidu.com", "fastcdn.hoyoverse.com", "hoyoverse.com", "game.qq.com",
    "www.bilibili.com", "www.youtube.com", "www.tiktok.com", "www.netflix.com",
    "www.disneyplus.com", "www.google.com", "www.microsoft.com", "www.datadoghq.com",
    "example.org",
}


class FeishuValidator(unittest.TestCase):
    MARKER = '  - RULE-SET,Feishu,💼 飞书\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, name, old, new):
        path = self.root / name
        original = path.read_text(encoding='utf-8')
        self.assertIn(old, original)
        path.write_text(original.replace(old, new), encoding='utf-8')

    def test_current_contract(self):
        validate.validate_feishu(self.root)

    def test_complete_public_fixture_passes_the_real_tree(self):
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_final_option_is_required_by_helper_and_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        self.assertIn('      - "🧭 Final"\n', block)
        changed = original[:start] + block.replace('      - "🧭 Final"\n', '') + original[end:]
        path.write_text(changed, encoding='utf-8')
        group = next(group for group in yaml.safe_load(changed)['proxy-groups']
                     if group['name'] == '💼 飞书')
        self.assertEqual(group['proxies'], ['DIRECT', '🚀 节点选择'])
        for gate in (validate.validate_feishu, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Feishu.*Final options'):
                    gate(self.root)

    def test_existing_apps_must_precede_feishu_in_helper_and_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        predecessors = ('QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图',
                        'Zhihu,💡 知乎', 'Xiaohongshu,📕 小红书 / REDnote',
                        'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣', 'JD,🛒 京东',
                        'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
                        'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝',
                        'BaiduMap,🗺️ 百度地图', 'Kuaishou,📹 快手',
                        'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘',
                        'IQIYI,🎬 爱奇艺', 'Xianyu,🐟 闲鱼',
                        'Railway12306,🚄 铁路12306', 'Youku,🎞️ 优酷')
        self.assertEqual(len(predecessors), 21)
        self.assertEqual(validate.validate_tree(self.root), 0)
        for predecessor in predecessors:
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_feishu, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede Feishu'):
                        gate(self.root)

    def test_bilibili_must_follow_feishu_even_when_siri_stays_later(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        anchor = '  - RULE-SET,Bilibili,📺 Bilibili\n'
        self.assertEqual(original.count(anchor), 1)
        changed = original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER)
        self.assertLess(changed.index('RULE-SET,Taobao,'), changed.index(anchor))
        self.assertLess(changed.index(self.MARKER), changed.index('RULE-SET,SiriAI,'))
        path.write_text(changed, encoding='utf-8')
        for gate in (validate.validate_feishu, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Feishu must precede broader providers'):
                    gate(self.root)

    def test_tree_calls_contract_with_complete_public_fixture(self):
        with patch.object(validate, 'validate_feishu', side_effect=RuntimeError('Feishu gate')) as gate:
            with self.assertRaisesRegex(RuntimeError, 'Feishu gate'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_exact_scope_and_non_target_boundaries(self):
        payload = yaml.safe_load((self.root / 'ruleset/Feishu.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        controls = CONTROLS | {value for host in HOSTS for value in
                                            ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_broadening_and_duplicate_scope_are_rejected(self):
        path = self.root / 'ruleset/Feishu.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.feishu.cn', 'DOMAIN-SUFFIX,feishu.cn'),
                        original + '  - DOMAIN,www.feishu.cn\n',
                        original + '  - DOMAIN,www.larksuite.com\n',
                        original.replace('  - DOMAIN,www.feishu.cn\n', '')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'one reviewed exact host'):
                    validate.validate_feishu(self.root)

    def test_missing_comment_duplicate_and_wrong_reference_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(self.MARKER, ''),
                        original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                        original + self.MARKER,
                        original.replace(self.MARKER, '  - RULE-SET,Feishu,DIRECT\n')):
            with self.subTest(reference=changed[-80:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_feishu(self.root)

    def test_late_placement_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_feishu(self.root)

    def test_security_bypass_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede Feishu'):
            validate.validate_feishu(self.root)

    def test_commented_order_marker_cannot_pass(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,ChinaMax,', '  # RULE-SET,ChinaMax,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_feishu(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_feishu(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for changed in (block.replace('      - DIRECT\n', ''),
                        block.replace('    type: select', '    type: fallback'),
                        block.replace('    type: select', '    type: select\n    type: select'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('      - DIRECT\n', '      - "🚀 节点选择"\n')):
            with self.subTest(group=changed):
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_feishu(self.root)

    def test_duplicate_type_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "💼 飞书"\n    type: select\n'
        for override in ('type: fallback # duplicate override', 'type:', 'type : fallback',
                         '"type": fallback', "'type': fallback"):
            with self.subTest(override=override):
                path.write_text(original.replace(marker, marker + '    ' + override + '\n'),
                                encoding='utf-8')
                parsed = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                effective = next(group for group in parsed if group['name'] == '💼 飞书')
                self.assertNotEqual(effective['type'], 'select')
                with self.assertRaisesRegex(ValueError, 'Feishu must be a DIRECT-first select'):
                    validate.validate_feishu(self.root)
                with self.assertRaisesRegex(ValueError,
                        r'Public config/proxy-groups\.yaml.*duplicate group field: type'):
                    validate.validate_tree(self.root)

    def test_complex_keys_and_proxy_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        for declaration in ('"t\\u0079pe": fallback', '!!str type: fallback',
                            '&policy_type type: fallback', '? type\n    : fallback',
                            'proxies: []', '"pro\\u0078ies": []',
                            '!!str proxies: []', '? proxies\n    : []',
                            '<<: {type: fallback}', 'unsupported: value'):
            with self.subTest(declaration=declaration):
                changed = original[:end] + '    ' + declaration + '\n' + original[end:]
                path.write_text(changed, encoding='utf-8')
                groups = yaml.safe_load(changed)['proxy-groups']
                effective = next(group for group in groups if group['name'] == '💼 飞书')
                if 'fallback' in declaration and not declaration.startswith('<<:'):
                    self.assertEqual(effective['type'], 'fallback')
                if '[]' in declaration:
                    self.assertEqual(effective['proxies'], [])
                with self.assertRaisesRegex(ValueError, 'Feishu must be a DIRECT-first select'):
                    validate.validate_feishu(self.root)
                # The full tree now rejects invalid structure before the App body gate.
                reason = ('duplicate group field: proxies' if declaration == 'proxies: []'
                          else 'unsupported group field: unsupported' if declaration == 'unsupported: value'
                          else 'expected a literal mapping key with a separated value')
                with self.assertRaisesRegex(ValueError, r'Public config/proxy-groups\.yaml.*' + reason):
                    validate.validate_tree(self.root)

    def test_duplicate_policy_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        path.write_text(path.read_text(encoding='utf-8') +
                        '\n  - name: "💼 飞书"\n    type: select\n    proxies:\n      - DIRECT\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Feishu must be a DIRECT-first select'):
            validate.validate_feishu(self.root)
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            validate.validate_tree(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text(encoding='utf-8')
                    path.write_text(original + f'  - {kind},www.feishu.cn\n', encoding='utf-8')
                    try:
                        validate.validate_feishu(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.feishu.cn\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_feishu(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,feishu,DIRECT',
                     'AND,((DOMAIN,www.feishu.cn)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', 'rules:\n  - ' + rule + '\n'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_feishu(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownFeishu,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownFeishu'):
            validate.validate_feishu(self.root)

    def test_missing_own_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        del manifest['Feishu']
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: Feishu'):
            validate.validate_feishu(self.root)

    def test_manifest_provider_collision_is_rejected(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Feishu manifests contain duplicate providers: Apple'):
            validate.validate_feishu(self.root)
        # An earlier existing App may detect the shared manifest collision
        # before Feishu's own gate. The dedicated gate is tested above.
        with self.assertRaisesRegex(ValueError, 'manifests contain duplicate providers: Apple'):
            validate.validate_tree(self.root)

    def test_contract_text_reads_are_explicit_utf8(self):
        original = Path.read_text
        seen = []
        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', checked):
            validate.validate_feishu(self.root)
        self.assertTrue(seen)


    def test_preceding_ip_conditions_fail_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER),
                                encoding='utf-8')
                for gate in (validate.validate_feishu, validate.validate_tree):
                    with self.subTest(gate=gate.__name__):
                        with self.assertRaisesRegex(ValueError, 'Feishu domain-only model cannot validate preceding IP'):
                            gate(self.root)

    def test_missing_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        path.write_text(original[:start] + original[end:], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Feishu must be a DIRECT-first select'):
            validate.validate_feishu(self.root)
        with self.assertRaisesRegex(ValueError, 'undefined policy groups'):
            validate.validate_tree(self.root)

    def test_incomplete_supported_rules_have_clear_errors_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('RULE-SET', 'RULE-SET,IncompleteFeishu', 'DOMAIN,www.feishu.cn', 'MATCH'):
            with self.subTest(rule=rule):
                path.write_text(original + '  - ' + rule + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Feishu domain-only model requires complete supported rules'):
                    validate.validate_feishu(self.root)


    def test_merged_apps_remain_before_feishu_in_both_gates(self):
        self.assertEqual(validate.validate_tree(self.root), 0)
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for predecessor in ('IQIYI,🎬 爱奇艺', 'Xianyu,🐟 闲鱼',
                            'Railway12306,🚄 铁路12306', 'Youku,🎞️ 优酷'):
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor)
            self.assertLess(changed.index('RULE-SET,Taobao,'), changed.index(self.MARKER))
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_feishu, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede Feishu'):
                        gate(self.root)


    def test_whitespace_fields_fail_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('RULE-SET, ,DIRECT', 'DOMAIN, ,DIRECT', 'GEOIP, ,DIRECT'):
            changed = original + '  - ' + rule + '\n'
            path.write_text(changed, encoding='utf-8')
            self.assertEqual(yaml.safe_load(changed)['rules'][-1], rule)
            for gate in (validate.validate_feishu, validate.validate_tree):
                with self.subTest(rule=rule, gate=gate.__name__):
                    # The shared reader rejects ASCII-only fields before App semantics.
                    error = r'^Public config/rules\.yaml line \d+: routing fields must not have leading or trailing ASCII spaces$'
                    with self.assertRaisesRegex(ValueError, error):
                        gate(self.root)

    def test_fixed_exact_host_and_all_excluded_controls(self):
        self.assertEqual(HOSTS, {'www.feishu.cn'})
        self.assertEqual(validate.FEISHU_CONTROLS, frozenset(CONTROLS))
        self.assertFalse(HOSTS & CONTROLS)

    def test_scope_mutations_also_fail_the_complete_tree(self):
        path = self.root / 'ruleset/Feishu.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.feishu.cn', 'DOMAIN-SUFFIX,feishu.cn'),
                        original + '  - DOMAIN,www.feishu.cn\n',
                        original + '  - DOMAIN,www.larksuite.com\n',
                        original.replace('  - DOMAIN,www.feishu.cn\n', '')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'one reviewed exact host'):
                    validate.validate_feishu(self.root)
                with self.assertRaises(ValueError):
                    validate.validate_tree(self.root)

    def test_future_valid_security_update_passes_complete_tree(self):
        lock_path = self.root / 'sources.lock.json'
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            original_lock = lock_path.read_text(encoding='utf-8')
            with self.subTest(provider=provider):
                # Simulate a complete public upstream snapshot update, only in this temp fixture.
                path.write_text(original + '  - DOMAIN,www.feishu.cn\n', encoding='utf-8')
                lock = json.loads(original_lock)
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                lock['rulesets'][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                lock_path.write_text(json.dumps(lock, ensure_ascii=False), encoding='utf-8')
                generate(self.root, write=True)
                validate.validate_feishu(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)
                path.write_text(original, encoding='utf-8')
                lock_path.write_text(original_lock, encoding='utf-8')
                generate(self.root, write=True)

    def test_each_later_anchor_stays_after_feishu_in_both_gates(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for later in ('RULE-SET,SiriAI,🤖 AI 服务', 'RULE-SET,Apple,🍎 Apple',
                      'RULE-SET,YouTube,📼 YouTube', 'RULE-SET,Bilibili,📺 Bilibili',
                      'RULE-SET,TikTok,🎵 Tiktok', 'RULE-SET,Disney,🏰 Disney',
                      'RULE-SET,Netflix,🎞️ Netflix',
                      'RULE-SET,GlobalMedia,🛰️ International-Global',
                      'GEOIP,CN,DIRECT,no-resolve', 'RULE-SET,ChinaMax,🇨🇳 China-Global'):
            with self.subTest(later=later):
                anchor = '  - ' + later + '\n'
                changed = original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER)
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Feishu must precede broader providers'):
                    validate.validate_feishu(self.root)
                with self.assertRaises(ValueError):
                    validate.validate_tree(self.root)

    def test_legal_select_formats_pass_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for declaration in ('type: select', 'type : select # public template',
                            '"type": "select"', "'type': 'select' # literal",
                            'type: "select" # literal', '"type" : select'):
            with self.subTest(declaration=declaration):
                changed = original[:start] + block.replace('type: select', declaration) + original[end:]
                path.write_text(changed, encoding='utf-8')
                group = next(g for g in yaml.safe_load(changed)['proxy-groups'] if g['name'] == '💼 飞书')
                self.assertEqual(group['type'], 'select')
                validate.validate_feishu(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_complex_proxy_members_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "💼 飞书"')
        end = original.index('  - name:', start + 1)
        for member in ('{name: DIRECT}', '&proxy DIRECT', '!!str DIRECT',
                       '*missing_proxy', '[DIRECT]', 'true', 'null', '123',
                       "'DIRECT'", '"D\\\\u0049RECT"', 'DIRECT # trailing comment'):
            with self.subTest(member=member):
                changed = original[:end] + '      - ' + member + '\n' + original[end:]
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Feishu must be a DIRECT-first select'):
                    validate.validate_feishu(self.root)
                # The full tree can reject an undefined proxy member before the App gate.
                with self.assertRaises(ValueError):
                    validate.validate_tree(self.root)

    def test_unknown_and_incomplete_rules_reach_both_gates(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        # Place after MATCH so this tests exhaustive preflight, not a simulated hit.
        for rule in ('PROCESS-NAME,feishu,DIRECT', 'DST-PORT,443,DIRECT',
                     'DOMAIN,www.feishu.cn', 'MATCH',
                     'IP-CIDR,192.0.2.0/24,DIRECT,unknown-option'):
            with self.subTest(rule=rule):
                path.write_text(original + '  - ' + rule + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Feishu domain-only model|in Feishu domain-only model'):
                    validate.validate_feishu(self.root)
                with self.assertRaises(ValueError):
                    validate.validate_tree(self.root)


    def test_shared_policy_guard_is_used(self):
        with patch('app_policy.validate_select_group', side_effect=ValueError('Feishu shared gate')) as gate:
            with self.assertRaisesRegex(ValueError, 'Feishu shared gate'):
                validate.validate_feishu(self.root)
        self.assertEqual(gate.call_count, 1)

    def test_public_structure_rejections_reach_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original + '\nrules: []\n',
                        original.replace('rules:\n', 'unrelated:\n', 1)):
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_feishu, validate.validate_tree):
                with self.subTest(gate=gate.__name__, changed=changed[-30:]):
                    with self.assertRaisesRegex(ValueError, 'Public config/rules.yaml'):
                        gate(self.root)

    def test_actual_first_matches_and_non_target_routes(self):
        manifests = {}
        for filename in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((self.root / filename).read_text(encoding='utf-8')))
        models = {name: DomainRules(yaml.safe_load((self.root / item['path']).read_text(encoding='utf-8'))['payload'])
                  for name, item in manifests.items()}
        ordered = yaml.safe_load((self.root / 'config/rules.yaml').read_text(encoding='utf-8'))['rules']

        def route(host, include_feishu=True):
            for rule in ordered:
                fields = rule.split(',')
                kind = fields[0]
                if kind == 'RULE-SET':
                    if not include_feishu and fields[1] == 'Feishu':
                        continue
                    if models[fields[1]].matches(host):
                        return fields[1], fields[2]
                elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return ','.join(fields[:2]), fields[2]
                elif kind == 'MATCH':
                    return kind, fields[1]
                else:
                    self.assertIn(kind, {'GEOIP', 'IP-CIDR', 'IP-CIDR6'})
            self.fail('Missing MATCH')
        security = {('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')}
        for host in HOSTS:
            current, previous = route(host), route(host, False)
            self.assertIn(current, security | {('Feishu', '💼 飞书')})
            if current in security:
                self.assertEqual(current, previous)
        controls = CONTROLS | {value for host in HOSTS for value in
                               ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertEqual(route(host), route(host, False))


if __name__ == '__main__':
    unittest.main()
