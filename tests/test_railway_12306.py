"""Railway12306 production-validator mutations with public fixtures only."""
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
from siri_ai import DomainRules

HOSTS = {'www.12306.cn', 'kyfw.12306.cn', 'dynamic.12306.cn'}


class Railway12306Validator(unittest.TestCase):
    MARKER = '  - RULE-SET,Railway12306,🚄 铁路12306\n'

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
        validate.validate_railway_12306(self.root)

    def test_complete_public_fixture_passes_the_real_tree(self):
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_final_option_is_required_by_helper_and_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🚄 铁路12306"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        self.assertIn('      - "🧭 Final"\n', block)
        changed = original[:start] + block.replace('      - "🧭 Final"\n', '') + original[end:]
        path.write_text(changed, encoding='utf-8')
        group = next(group for group in yaml.safe_load(changed)['proxy-groups']
                     if group['name'] == '🚄 铁路12306')
        self.assertEqual(group['proxies'], ['DIRECT', '🚀 节点选择'])
        for gate in (validate.validate_railway_12306, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Railway12306.*Final options'):
                    gate(self.root)

    def test_existing_apps_must_precede_railway_12306_in_helper_and_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        predecessors = ('QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图',
                        'Zhihu,💡 知乎', 'Xiaohongshu,📕 小红书 / REDnote',
                        'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣', 'JD,🛒 京东',
                        'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
                        'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝')
        for predecessor in predecessors:
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_railway_12306, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede Railway12306'):
                        gate(self.root)

    def test_bilibili_must_follow_railway_12306_even_when_siri_stays_later(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        anchor = '  - RULE-SET,Bilibili,📺 Bilibili\n'
        self.assertEqual(original.count(anchor), 1)
        changed = original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER)
        self.assertLess(changed.index('RULE-SET,Taobao,'), changed.index(anchor))
        self.assertLess(changed.index(self.MARKER), changed.index('RULE-SET,SiriAI,'))
        path.write_text(changed, encoding='utf-8')
        for gate in (validate.validate_railway_12306, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Railway12306 must precede broader providers'):
                    gate(self.root)

    def test_tree_calls_contract_with_complete_public_fixture(self):
        with patch.object(validate, 'validate_railway_12306', side_effect=RuntimeError('Railway12306 gate')) as gate:
            with self.assertRaisesRegex(RuntimeError, 'Railway12306 gate'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_exact_scope_and_non_target_boundaries(self):
        required = {
            '12306.cn', 'mobile.12306.cn', '95306.cn', 'www.95306.cn',
            'g.alicdn.com', 'www.taobao.com', 'www.alipay.com', 'www.alipan.com',
            'www.jd.com', 'www.meituan.com', 'www.pinduoduo.com', 'www.ctrip.com',
            'pan.baidu.com', 'map.baidu.com', 'restapi.amap.com', 'www.zhihu.com', 'www.douban.com',
            'www.xiaohongshu.com', 'www.kuaishou.com', 'v.qq.com', 'y.qq.com', 'music.163.com',
            'www.douyin.com', 'www.bilibili.com', 'guzzoni.apple.com', 'fastcdn.hoyoverse.com',
            'wlog.kuaishou.com', 'msg.qy.net', 'example.org',
        }
        self.assertLessEqual(required, validate.RAILWAY_12306_CONTROLS)
        payload = yaml.safe_load((self.root / 'ruleset/Railway12306.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        controls = validate.RAILWAY_12306_CONTROLS | {value for host in HOSTS for value in
                                            ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_broadening_and_duplicate_scope_are_rejected(self):
        path = self.root / 'ruleset/Railway12306.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.12306.cn', 'DOMAIN-SUFFIX,12306.cn'),
                        original + '  - DOMAIN,www.12306.cn\n',
                        original + '  - DOMAIN,mobile.12306.cn\n',
                        original.replace('  - DOMAIN,kyfw.12306.cn\n', '')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'three reviewed exact hosts'):
                    validate.validate_railway_12306(self.root)

    def test_missing_comment_duplicate_and_wrong_reference_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(self.MARKER, ''),
                        original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                        original + self.MARKER,
                        original.replace(self.MARKER, '  - RULE-SET,Railway12306,DIRECT\n')):
            with self.subTest(reference=changed[-80:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_railway_12306(self.root)

    def test_late_placement_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_railway_12306(self.root)

    def test_security_bypass_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede Railway12306'):
            validate.validate_railway_12306(self.root)

    def test_commented_order_marker_cannot_pass(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,ChinaMax,', '  # RULE-SET,ChinaMax,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_railway_12306(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_railway_12306(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🚄 铁路12306"')
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
                    validate.validate_railway_12306(self.root)

    def test_duplicate_type_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🚄 铁路12306"\n    type: select\n'
        for override in ('type: fallback # duplicate override', 'type:', 'type : fallback',
                         '"type": fallback', "'type': fallback"):
            with self.subTest(override=override):
                path.write_text(original.replace(marker, marker + '    ' + override + '\n'),
                                encoding='utf-8')
                parsed = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                effective = next(group for group in parsed if group['name'] == '🚄 铁路12306')
                self.assertNotEqual(effective['type'], 'select')
                with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
                    validate.validate_railway_12306(self.root)
                with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
                    validate.validate_tree(self.root)

    def test_complex_keys_and_proxy_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🚄 铁路12306"')
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
                effective = next(group for group in groups if group['name'] == '🚄 铁路12306')
                if 'fallback' in declaration and not declaration.startswith('<<:'):
                    self.assertEqual(effective['type'], 'fallback')
                if '[]' in declaration:
                    self.assertEqual(effective['proxies'], [])
                with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
                    validate.validate_railway_12306(self.root)
                with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
                    validate.validate_tree(self.root)

    def test_duplicate_policy_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        path.write_text(path.read_text(encoding='utf-8') +
                        '\n  - name: "🚄 铁路12306"\n    type: select\n    proxies:\n      - DIRECT\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
            validate.validate_railway_12306(self.root)
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            validate.validate_tree(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text(encoding='utf-8')
                    path.write_text(original + f'  - {kind},www.12306.cn\n', encoding='utf-8')
                    try:
                        validate.validate_railway_12306(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.12306.cn\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_railway_12306(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,railway_12306,DIRECT',
                     'AND,((DOMAIN,www.12306.cn)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', 'rules:\n  - ' + rule + '\n'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_railway_12306(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownRailway12306,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownRailway12306'):
            validate.validate_railway_12306(self.root)

    def test_missing_own_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        del manifest['Railway12306']
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: Railway12306'):
            validate.validate_railway_12306(self.root)

    def test_manifest_provider_collision_is_rejected(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Railway12306 manifests contain duplicate providers: Apple'):
            validate.validate_railway_12306(self.root)
        # An earlier existing App may detect the shared manifest collision
        # before Railway12306's own gate. The dedicated gate is tested above.
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
            validate.validate_railway_12306(self.root)
        self.assertTrue(seen)


    def test_preceding_ip_conditions_fail_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER),
                                encoding='utf-8')
                for gate in (validate.validate_railway_12306, validate.validate_tree):
                    with self.subTest(gate=gate.__name__):
                        with self.assertRaisesRegex(ValueError, 'Railway12306 domain-only model cannot validate preceding IP'):
                            gate(self.root)

    def test_missing_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🚄 铁路12306"')
        end = original.index('  - name:', start + 1)
        path.write_text(original[:start] + original[end:], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Railway12306 must be a DIRECT-first select'):
            validate.validate_railway_12306(self.root)
        with self.assertRaisesRegex(ValueError, 'undefined policy groups'):
            validate.validate_tree(self.root)

    def test_incomplete_supported_rules_have_clear_errors_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('RULE-SET', 'RULE-SET,IncompleteRailway12306', 'DOMAIN,www.12306.cn', 'MATCH',
                     'RULE-SET, ,DIRECT', 'DOMAIN, ,DIRECT', 'GEOIP, ,DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original + '  - ' + rule + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Railway12306 domain-only model requires complete supported rules'):
                    validate.validate_railway_12306(self.root)


    def test_merged_apps_remain_before_railway_12306_in_both_gates(self):
        self.assertEqual(validate.validate_tree(self.root), 0)
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for predecessor in ('BaiduMap,🗺️ 百度地图', 'Kuaishou,📹 快手',
                            'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘'):
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor)
            self.assertLess(changed.index('RULE-SET,Taobao,'), changed.index(self.MARKER))
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_railway_12306, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede Railway12306'):
                        gate(self.root)


    def test_supported_literal_select_forms_pass_both_real_gates(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🚄 铁路12306"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for declaration in ('type: select # manual', 'type: "select"', "type: 'select'",
                            "'type': select", '"type": select', 'type : select'):
            with self.subTest(declaration=declaration):
                changed = block.replace('type: select', declaration)
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                validate.validate_railway_12306(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_all_media_anchors_follow_railway_even_with_apple_later(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for media in ('YouTube,📼 YouTube', 'Bilibili,📺 Bilibili', 'TikTok,🎵 Tiktok',
                      'Disney,🏰 Disney', 'Netflix,🎞️ Netflix'):
            anchor = '  - RULE-SET,' + media + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(anchor, '').replace(self.MARKER, anchor + self.MARKER)
            self.assertLess(changed.index('RULE-SET,AliPan,'), changed.index(anchor))
            self.assertLess(changed.index(self.MARKER), changed.index('RULE-SET,SiriAI,'))
            self.assertLess(changed.index(self.MARKER), changed.index('RULE-SET,Apple,'))
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_railway_12306, validate.validate_tree):
                with self.subTest(media=media, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'Railway12306 must precede broader providers'):
                        gate(self.root)

    def test_download_entry_is_required_without_broadening_to_other_hosts(self):
        path = self.root / 'ruleset/Railway12306.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('  - DOMAIN,dynamic.12306.cn\n', ''),
                        original.replace('DOMAIN,dynamic.12306.cn', 'DOMAIN,12306.cn'),
                        original.replace('DOMAIN,dynamic.12306.cn', 'DOMAIN,mobile.12306.cn')):
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_railway_12306, validate.validate_tree):
                with self.subTest(gate=gate.__name__, scope=changed):
                    with self.assertRaisesRegex(ValueError, 'three reviewed exact hosts'):
                        gate(self.root)


if __name__ == '__main__':
    unittest.main()
