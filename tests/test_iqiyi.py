"""IQIYI exact entries and actual live/staged validator contract mutations."""
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

HOSTS = {'www.iqiyi.com'}
TARGET = '🎬 爱奇艺'
CONTROLS = {
    'iqiyi.com', 'qiyi.com', 'iqiyipic.com', 'qy.net', 'static.iqiyi.com',
    'mesh.if.iqiyi.com', 'pic0.iqiyipic.com', 'pic1.iqiyipic.com', 'pic2.iqiyipic.com',
    'pic3.iqiyipic.com', 'dl-static.iqiyi.com', 'static-d.iqiyi.com', 'mbdapp.iqiyi.com',
    'app.iqiyi.com', 'privacy.iqiyi.com', 'creator.iqiyi.com', 'g.iqiyi.com',
    'game.iqiyi.com', 'iq.com', 'www.iq.com', 'msg.qy.net', 'apps.apple.com',
    'itunes.apple.com', 'appgallery.huawei.com', 'beian.miit.gov.cn',
    'v.qq.com', 'm.v.qq.com', 'film.qq.com', 'film.video.qq.com',
    'y.qq.com', 'c.y.qq.com', 'dldir.y.qq.com', 'www.bilibili.com',
    'www.youtube.com', 'www.tiktok.com', 'www.disneyplus.com', 'www.netflix.com',
    'www.alipan.com', 'www.aliyundrive.com', 'guzzoni.apple.com',
    'fastcdn.hoyoverse.com', 'example.org',
}


class IQIYIRouting(unittest.TestCase):
    def test_independent_yaml_scope_and_default(self):
        payload = yaml.safe_load((ROOT / 'ruleset/IQIYI.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        groups = yaml.safe_load((ROOT / 'config/proxy-groups.yaml').read_text(encoding='utf-8'))['proxy-groups']
        matches = [group for group in groups if group['name'] == TARGET]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['type'], 'select')
        self.assertEqual(matches[0]['proxies'][0], 'DIRECT')
        self.assertIn('🚀 节点选择', matches[0]['proxies'])
        self.assertIn('🧭 Final', matches[0]['proxies'])

    def test_effective_routing_contract(self):
        validate.validate_iqiyi(ROOT)

    def test_unreviewed_hosts_do_not_match(self):
        self.assertEqual(validate.IQIYI_CONTROLS, frozenset(CONTROLS))
        model = DomainRules(entries(ROOT / 'ruleset/IQIYI.yaml'))
        controls = CONTROLS | {value for host in HOSTS for value in
                               ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))


class IQIYIValidatorMutations(unittest.TestCase):
    MARKER = '  - RULE-SET,IQIYI,' + TARGET + '\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Complete public fixture also exercises validate_tree without touching ROOT.
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / filename, self.root / filename)

    def mutate(self, filename, old, new):
        path = self.root / filename
        text = path.read_text(encoding='utf-8')
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding='utf-8')

    def test_valid_public_fixture(self):
        validate.validate_iqiyi(self.root)

    def test_scope_broadening_is_rejected(self):
        self.mutate('ruleset/IQIYI.yaml', 'DOMAIN,www.iqiyi.com', 'DOMAIN-SUFFIX,iqiyi.com')
        with self.assertRaisesRegex(ValueError, 'one reviewed exact host'):
            validate.validate_iqiyi(self.root)

    def test_unreviewed_exact_host_is_rejected(self):
        self.mutate('ruleset/IQIYI.yaml', 'DOMAIN,www.iqiyi.com', 'DOMAIN,static.iqiyi.com')
        with self.assertRaisesRegex(ValueError, 'one reviewed exact host'):
            validate.validate_iqiyi(self.root)

    def test_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/IQIYI.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.iqiyi.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            validate.validate_iqiyi(self.root)

    def test_complete_public_tree_calls_iqiyi_gate(self):
        with patch.object(validate, 'validate_iqiyi', side_effect=ValueError('IQIYI gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'IQIYI gate reached'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_missing_provider_reports_clear_validation_error(self):
        path = self.root / 'local-rulesets.json'
        records = json.loads(path.read_text(encoding='utf-8'))
        del records['IQIYI']
        path.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'IQIYI routing references missing provider: IQIYI'):
            validate.validate_iqiyi(self.root)

    def test_unknown_provider_is_rejected_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - RULE-SET,Unknown,DIRECT\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'IQIYI routing references missing provider: Unknown'):
            validate.validate_iqiyi(self.root)

    def test_all_validator_text_reads_request_utf8(self):
        original = Path.read_text

        def read_utf8(path, *args, **kwargs):
            encoding = kwargs.get('encoding', args[0] if args else None)
            self.assertEqual(encoding, 'utf-8', str(path))
            return original(path, *args, **kwargs)

        with patch.object(Path, 'read_text', autospec=True, side_effect=read_utf8):
            validate.validate_iqiyi(self.root)

    def test_existing_shared_syntax_guard_is_used(self):
        with patch('app_policy.validate_select_group', side_effect=ValueError('IQIYI shared gate')) as gate:
            with self.assertRaisesRegex(ValueError, 'IQIYI shared gate'):
                validate.validate_iqiyi(self.root)
        self.assertEqual(gate.call_count, 1)

    def test_cross_manifest_provider_collision_is_rejected_by_both_gates(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'IQIYI manifests contain duplicate providers: Apple'):
            validate.validate_iqiyi(self.root)
        # The already-present Ctrip gate can reject this global collision earlier.
        with self.assertRaisesRegex(ValueError, 'manifests contain duplicate providers: Apple'):
            validate.validate_tree(self.root)

    def test_early_ip_conditions_fail_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('GEOIP,US,DIRECT,no-resolve', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER),
                                encoding='utf-8')
                for gate in (validate.validate_iqiyi, validate.validate_tree):
                    with self.assertRaisesRegex(ValueError, 'IQIYI domain-only model cannot validate preceding IP'):
                        gate(self.root)

    def test_malformed_domain_model_rules_fail_clearly(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('RULE-SET,Privacy', 'RULE-SET,,DIRECT', 'RULE-SET,Privacy,REJECT,extra',
                     'DOMAIN,www.iqiyi.com', 'DOMAIN,,DIRECT', 'DOMAIN,www.iqiyi.com,DIRECT,extra',
                     'DOMAIN-SUFFIX,iqiyi.com', 'DOMAIN-SUFFIX, ,DIRECT',
                     'DOMAIN-KEYWORD,iqiyi', 'DOMAIN-KEYWORD,iqiyi,DIRECT,extra',
                     'MATCH', 'MATCH,', 'MATCH,DIRECT,extra',
                     'GEOIP,CN', 'GEOIP,,DIRECT', 'GEOIP,CN,DIRECT,invalid',
                     'IP-CIDR,192.0.2.0/24', 'IP-CIDR,,DIRECT',
                     'IP-CIDR,192.0.2.0/24,DIRECT,invalid',
                     'IP-CIDR6,2001:db8::/32', 'IP-CIDR6,2001:db8::/32,',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve,extra'):
            with self.subTest(rule=rule):
                path.write_text(original + '  - ' + rule + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'IQIYI domain-only model requires complete supported rules'):
                    validate.validate_iqiyi(self.root)

    def test_complete_tree_accepts_supported_post_app_ip_shapes(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        rules = ('GEOIP,US,DIRECT', 'GEOIP,US,DIRECT,no-resolve',
                 'IP-CIDR,192.0.2.0/24,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                 'IP-CIDR6,2001:db8::/32,DIRECT', 'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve')
        path.write_text(original + ''.join('  - ' + rule + '\n' for rule in rules), encoding='utf-8')
        validate.validate_iqiyi(self.root)
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_all_seventeen_existing_apps_precede_iqiyi_in_complete_tree(self):
        self.assertEqual(validate.validate_tree(self.root), 0)
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        predecessors = ('QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图',
                        'Zhihu,💡 知乎', 'Xiaohongshu,📕 小红书 / REDnote',
                        'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣', 'JD,🛒 京东',
                        'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
                        'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝', 'BaiduMap,🗺️ 百度地图',
                        'Kuaishou,📹 快手', 'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘')
        self.assertEqual(len(predecessors), 17)
        for predecessor in predecessors:
            marker = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(marker), 1)
            changed = original.replace(self.MARKER, '').replace(marker, self.MARKER + marker)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_iqiyi, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede IQIYI'):
                        gate(self.root)

    def test_each_media_successor_is_independently_enforced_in_complete_tree(self):
        self.assertEqual(validate.validate_tree(self.root), 0)
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for successor in ('YouTube,📼 YouTube', 'Bilibili,📺 Bilibili', 'TikTok,🎵 Tiktok',
                          'Disney,🏰 Disney', 'Netflix,🎞️ Netflix'):
            marker = '  - RULE-SET,' + successor + '\n'
            self.assertEqual(original.count(marker), 1)
            # Move only this media rule, leaving AliPan < IQIYI < SiriAI intact.
            changed = original.replace(marker, '').replace(self.MARKER, marker + self.MARKER)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_iqiyi, validate.validate_tree):
                with self.subTest(successor=successor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'IQIYI must precede broader providers'):
                        gate(self.root)

    def test_duplicate_policy_groups_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎬 爱奇艺"')
        end = original.index('  - name:', start + 1)
        path.write_text(original + original[start:end], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'IQIYI must be a DIRECT-first select'):
            validate.validate_iqiyi(self.root)
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            validate.validate_tree(self.root)

    def test_no_duplicate_or_wrong_target_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for text in (original.replace(self.MARKER, ''), original + self.MARKER,
                     original.replace(self.MARKER, '  - RULE-SET,IQIYI,DIRECT\n'),
                     original + '  - RULE-SET,IQIYI,DIRECT\n'):
            with self.subTest(tail=text[-40:]):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_iqiyi(self.root)

    def test_late_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8').replace(self.MARKER, '')
        for marker in ('  - RULE-SET,SiriAI,🤖 AI 服务\n', '  - RULE-SET,Apple,🍎 Apple\n',
                       '  - RULE-SET,ChinaMax,🇨🇳 China-Global\n'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker + self.MARKER), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'broader providers'):
                    validate.validate_iqiyi(self.root)

    def test_security_or_existing_app_bypass_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8').replace(self.MARKER, '')
        for marker in ('  - RULE-SET,Privacy,REJECT\n', '  - RULE-SET,ChinaGaming,DIRECT\n',
                       '  - RULE-SET,BaiduPan,☁️ 百度网盘\n'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, self.MARKER + marker), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'must precede IQIYI'):
                    validate.validate_iqiyi(self.root)

    def test_active_markers_are_unique_and_not_comments(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in (self.MARKER, '  - RULE-SET,Privacy,REJECT\n',
                       '  - RULE-SET,GlobalMedia,🛰️ International-Global\n'):
            for text in (original.replace(marker, marker.replace('  - ', '  # ')), original + marker):
                with self.subTest(marker=marker, tail=text[-40:]):
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaises(ValueError):
                        validate.validate_iqiyi(self.root)

    def test_default_type_and_choices_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎬 爱奇艺"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for changed in (block.replace('      - DIRECT\n', ''),
                        block.replace('      - DIRECT\n      - "🚀 节点选择"\n',
                                      '      - "🚀 节点选择"\n      - DIRECT\n'),
                        block.replace('type: select', 'type: fallback'),
                        block.replace('      - "🚀 节点选择"\n', ''),
                        block.replace('      - "🧭 Final"\n', ''),
                        block.replace('    type: select\n', '    type: select\n    type: select\n')):
            with self.subTest(block=changed):
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_iqiyi(self.root)

    def test_equivalent_duplicate_type_keys_are_rejected_by_both_gates(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎬 爱奇艺"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        variants = (
            ('    type: fallback # duplicate override\n', 'fallback'),
            ('    type:\n', None),
            ('    type : fallback\n', 'fallback'),
            ("    'type': fallback\n", 'fallback'),
            ('    "type": fallback\n', 'fallback'),
        )
        for extra, effective in variants:
            with self.subTest(extra=extra):
                changed = block.replace('    type: select\n', '    type: select\n' + extra)
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                groups = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                group = next(group for group in groups if group['name'] == TARGET)
                self.assertEqual(group['type'], effective)
                self.assertNotEqual(group['type'], 'select')
                for gate in (validate.validate_iqiyi, validate.validate_tree):
                    with self.subTest(gate=gate.__name__):
                        with self.assertRaisesRegex(ValueError, (r'Public config/proxy-groups\.yaml.*duplicate group field: type' if gate is validate.validate_tree else 'IQIYI must be a DIRECT-first select')):
                            gate(self.root)

    def test_known_select_formats_pass_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🎬 爱奇艺"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # same policy',
                            'type: "select" # same policy', '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                path.write_text(original.replace(marker, '  - name: "🎬 爱奇艺"\n    ' + declaration + '\n'),
                                encoding='utf-8')
                groups = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                group = next(group for group in groups if group['name'] == TARGET)
                self.assertEqual(group['type'], 'select')
                validate.validate_iqiyi(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_duplicate_select_formats_still_fail_both_gates(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🎬 爱奇艺"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # still duplicated',
                            '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                path.write_text(original.replace(marker, marker + '    ' + declaration + '\n'),
                                encoding='utf-8')
                groups = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                group = next(group for group in groups if group['name'] == TARGET)
                self.assertEqual(group['type'], 'select')
                for gate in (validate.validate_iqiyi, validate.validate_tree):
                    with self.assertRaisesRegex(ValueError, (r'Public config/proxy-groups\.yaml.*duplicate group field: type' if gate is validate.validate_tree else 'IQIYI must be a DIRECT-first select')):
                        gate(self.root)

    def test_unseparated_or_nonselect_type_formats_fail_both_gates(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🎬 爱奇艺"\n    type: select\n'
        for declaration in ('type:select', 'type: "fallback"', "type: 'fallback'", 'type: select#not-comment'):
            with self.subTest(declaration=declaration):
                path.write_text(original.replace(marker, '  - name: "🎬 爱奇艺"\n    ' + declaration + '\n'),
                                encoding='utf-8')
                for gate in (validate.validate_iqiyi, validate.validate_tree):
                    with self.assertRaisesRegex(ValueError,
                            (r'Public config/proxy-groups\.yaml.*expected a literal mapping key'
                             if declaration == 'type:select' and gate is validate.validate_tree else 'IQIYI must be a DIRECT-first select')):
                        gate(self.root)

    def test_missing_policy_group_fails_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎬 爱奇艺"')
        end = original.index('  - name:', start + 1)
        path.write_text(original[:start] + original[end:], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'IQIYI must be a DIRECT-first select'):
            validate.validate_iqiyi(self.root)
        with self.assertRaises(ValueError):
            validate.validate_tree(self.root)

    def test_complex_type_and_proxy_overrides_fail_helper_and_complete_tree(self):
        def structural_error(declaration):
            value = declaration.strip()
            if value.startswith(('type:', 'type :', '"type":', "'type':")):
                reason = 'duplicate group field: type'
            elif value.startswith(('proxies:', '"proxies":', "'proxies':")):
                reason = 'duplicate group field: proxies'
            elif value.startswith('unsupported:'):
                reason = 'unsupported group field: unsupported'
            elif value.startswith('- '):
                reason = ('expected an unescaped whole quoted literal'
                          if chr(92) in value else 'unsupported scalar syntax')
            else:
                reason = 'expected a literal mapping key with a separated value'
            return r'Public config/proxy-groups\.yaml.*' + reason

        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🎬 爱奇艺"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        cases = (
            (r'"t\u0079pe": fallback', 'type', 'fallback'),
            ('!!str type: fallback', 'type', 'fallback'),
            ('&policy_type type: fallback', 'type', 'fallback'),
            ('? type\n    : fallback', 'type', 'fallback'),
            ('<<: {type: fallback}', 'type', 'select'),
            ('proxies: []', 'proxies', []),
            ('"proxies": []', 'proxies', []),
            (r'"pro\u0078ies": []', 'proxies', []),
            ('!!str proxies: []', 'proxies', []),
            ('&list_key proxies: []', 'proxies', []),
            ('? proxies\n    : []', 'proxies', []),
            ('unsupported: value', 'unsupported', 'value'),
        )
        for declaration, key, effective in cases:
            with self.subTest(declaration=declaration):
                changed = block + '    ' + declaration + '\n'
                path.write_text(original[:start] + changed + original[end:], encoding='utf-8')
                groups = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                group = next(group for group in groups if group['name'] == TARGET)
                self.assertEqual(group[key], effective)
                for gate in (validate.validate_iqiyi, validate.validate_tree):
                    with self.subTest(gate=gate.__name__):
                        with self.assertRaisesRegex(ValueError, (structural_error(declaration) if gate is validate.validate_tree else 'IQIYI must be a DIRECT-first select')):
                            gate(self.root)

    def test_legal_security_updates_use_same_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},www.iqiyi.com\n', encoding='utf-8')
                    try:
                        validate.validate_iqiyi(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.iqiyi.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_iqiyi(self.root)

    def test_inline_non_security_preemption_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '  - DOMAIN,www.iqiyi.com,DIRECT\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_iqiyi(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'one active rule'):
            validate.validate_iqiyi(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,iqiyi,DIRECT'):
            for text in (original.replace(self.MARKER, f'  - {rule}\n' + self.MARKER),
                         original + f'  - {rule}\n'):
                with self.subTest(rule=rule, tail=text[-40:]):
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                        validate.validate_iqiyi(self.root)


if __name__ == '__main__':
    unittest.main()
