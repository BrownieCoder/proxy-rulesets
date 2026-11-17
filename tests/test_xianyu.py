"""Xianyu production-validator mutations with public fixtures only."""
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

HOSTS = {'goofish.com', 'www.goofish.com', 'terms.goofish.com'}
NEGATIVE_HOSTS = {
    'goofish.cn', 'h5.m.goofish.com', 'm.goofish.com', 'api.goofish.com',
    'alicdn.com', 'g.alicdn.com', 'gw.alicdn.com', 'img.alicdn.com', 'o.alicdn.com',
    'terms.alicdn.com', 'gm.mmstat.com', 'log.mmstat.com', 'taobao.com', 'www.taobao.com',
    'login.taobao.com', 'h5api.m.taobao.com', 'alipay.com', 'www.alipay.com',
    'www.alipan.com', 'pan.baidu.com', 'map.baidu.com', 'www.kuaishou.com',
    'v.qq.com', 'www.jd.com', 'guzzoni.apple.com', 'fastcdn.hoyoverse.com', 'example.org',
}


class XianyuValidator(unittest.TestCase):
    MARKER = '  - RULE-SET,Xianyu,🐟 闲鱼\n'

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
        validate.validate_xianyu(self.root)

    def test_complete_public_fixture_passes_the_real_tree(self):
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_final_option_is_required_by_helper_and_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🐟 闲鱼"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        self.assertIn('      - "🧭 Final"\n', block)
        changed = original[:start] + block.replace('      - "🧭 Final"\n', '') + original[end:]
        path.write_text(changed, encoding='utf-8')
        group = next(group for group in yaml.safe_load(changed)['proxy-groups']
                     if group['name'] == '🐟 闲鱼')
        self.assertEqual(group['proxies'], ['DIRECT', '🚀 节点选择'])
        for gate in (validate.validate_xianyu, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Xianyu.*Final options'):
                    gate(self.root)

    def test_existing_apps_must_precede_xianyu_in_helper_and_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        predecessors = ('QQMusic,🎧 QQ 音乐', 'Douyin,🎶 抖音', 'Amap,🗺️ 高德地图',
                        'Zhihu,💡 知乎', 'Xiaohongshu,📕 小红书 / REDnote',
                        'NetEaseMusic,🎵 网易云音乐', 'Douban,📚 豆瓣', 'JD,🛒 京东',
                        'Meituan,🍜 美团', 'BaiduPan,☁️ 百度网盘', 'Ctrip,🧳 携程',
                        'Pinduoduo,🛍️ 拼多多', 'Taobao,🛍️ 淘宝',
                        'BaiduMap,🗺️ 百度地图', 'Kuaishou,📹 快手',
                        'TencentVideo,📺 腾讯视频', 'AliPan,📁 阿里云盘')
        for predecessor in predecessors:
            anchor = '  - RULE-SET,' + predecessor + '\n'
            self.assertEqual(original.count(anchor), 1)
            changed = original.replace(self.MARKER, '').replace(anchor, self.MARKER + anchor)
            path.write_text(changed, encoding='utf-8')
            for gate in (validate.validate_xianyu, validate.validate_tree):
                with self.subTest(predecessor=predecessor, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'existing app rules must precede Xianyu'):
                        gate(self.root)

    def test_each_media_must_follow_xianyu_even_when_siri_stays_later(self):
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
            for gate in (validate.validate_xianyu, validate.validate_tree):
                with self.subTest(media=media, gate=gate.__name__):
                    with self.assertRaisesRegex(ValueError, 'Xianyu must precede broader providers'):
                        gate(self.root)

    def test_tree_calls_contract_with_complete_public_fixture(self):
        with patch.object(validate, 'validate_xianyu', side_effect=RuntimeError('Xianyu gate')) as gate:
            with self.assertRaisesRegex(RuntimeError, 'Xianyu gate'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_exact_scope_and_non_target_boundaries(self):
        payload = yaml.safe_load((self.root / 'ruleset/Xianyu.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        self.assertLessEqual(NEGATIVE_HOSTS, validate.XIANYU_CONTROLS)
        controls = validate.XIANYU_CONTROLS | {value for host in HOSTS for value in
                                            ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_broadening_and_duplicate_scope_are_rejected(self):
        path = self.root / 'ruleset/Xianyu.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace('DOMAIN,www.goofish.com', 'DOMAIN-SUFFIX,goofish.com'),
                        original + '  - DOMAIN,www.goofish.com\n',
                        original + '  - DOMAIN,g.alicdn.com\n',
                        original.replace('  - DOMAIN,terms.goofish.com\n', '')):
            with self.subTest(scope=changed):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'three reviewed exact hosts'):
                    validate.validate_xianyu(self.root)

    def test_missing_comment_duplicate_and_wrong_reference_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for changed in (original.replace(self.MARKER, ''),
                        original.replace(self.MARKER, self.MARKER.replace('  - ', '  # ')),
                        original + self.MARKER,
                        original.replace(self.MARKER, '  - RULE-SET,Xianyu,DIRECT\n')):
            with self.subTest(reference=changed[-80:]):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_xianyu(self.root)

    def test_late_placement_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_xianyu(self.root)

    def test_security_bypass_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede Xianyu'):
            validate.validate_xianyu(self.root)

    def test_commented_order_marker_cannot_pass(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,ChinaMax,', '  # RULE-SET,ChinaMax,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_xianyu(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_xianyu(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🐟 闲鱼"')
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
                    validate.validate_xianyu(self.root)

    def test_duplicate_type_overrides_fail_helper_and_complete_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🐟 闲鱼"\n    type: select\n'
        for override in ('type: fallback # duplicate override', 'type:', 'type : fallback',
                         '"type": fallback', "'type': fallback"):
            with self.subTest(override=override):
                path.write_text(original.replace(marker, marker + '    ' + override + '\n'),
                                encoding='utf-8')
                parsed = yaml.safe_load(path.read_text(encoding='utf-8'))['proxy-groups']
                effective = next(group for group in parsed if group['name'] == '🐟 闲鱼')
                self.assertNotEqual(effective['type'], 'select')
                with self.assertRaisesRegex(ValueError, 'Xianyu must be a DIRECT-first select'):
                    validate.validate_xianyu(self.root)
                with self.assertRaisesRegex(ValueError, 'Xianyu must be a DIRECT-first select'):
                    validate.validate_tree(self.root)

    def test_complex_group_yaml_rejected_by_helper_and_real_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🐟 闲鱼"\n')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        cases = (
            ('    "t\\u0079pe": fallback\n', 'type', 'fallback'),
            ('    !!str type: fallback\n', 'type', 'fallback'),
            ('    &policy_type type: fallback\n', 'type', 'fallback'),
            ('    ? type\n    : fallback\n', 'type', 'fallback'),
            ('    <<: {type: fallback}\n', 'type', 'select'),
            ('    proxies: []\n', 'proxies', []),
            ('    "proxies": []\n', 'proxies', []),
            ('    "pro\\u0078ies": []\n', 'proxies', []),
            ('    !!str proxies: []\n', 'proxies', []),
            ('    &list_key proxies: []\n', 'proxies', []),
            ('    ? proxies\n    : []\n', 'proxies', []),
            ('    unsupported: value\n', 'unsupported', 'value'),
            ('      - {type: fallback}\n', 'last_proxy', {'type': 'fallback'}),
            ('      - "DI\\u0052ECT"\n', 'last_proxy', 'DIRECT'),
        )
        for extra, field, expected in cases:
            with self.subTest(extra=extra):
                changed = original[:start] + block + extra + original[end:]
                parsed = yaml.safe_load(changed)['proxy-groups']
                groups = [group for group in parsed if group['name'] == '🐟 闲鱼']
                self.assertEqual(len(groups), 1)
                effective = groups[0]
                actual = effective['proxies'][-1] if field == 'last_proxy' else effective[field]
                self.assertEqual(actual, expected)
                path.write_text(changed, encoding='utf-8')
                for validator in (validate.validate_xianyu, validate.validate_tree):
                    with self.subTest(entry=validator.__name__):
                        # The tree's existing global reference gate rejects
                        # complex members before the new App helper runs.
                        error = ('proxy-groups.yaml references undefined groups'
                                 if validator is validate.validate_tree and field == 'last_proxy'
                                 else 'Xianyu must be a DIRECT-first select')
                        with self.assertRaisesRegex(ValueError, error):
                            validator(self.root)

    def test_supported_literal_select_forms_pass_helper_and_real_tree(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "🐟 闲鱼"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # manual selection',
                            'type: "select" # manual selection', '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                changed = original.replace(marker, '  - name: "🐟 闲鱼"\n    ' + declaration + '\n')
                groups = yaml.safe_load(changed)['proxy-groups']
                self.assertEqual(next(group for group in groups if group['name'] == '🐟 闲鱼')['type'],
                                 'select')
                path.write_text(changed, encoding='utf-8')
                validate.validate_xianyu(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_duplicate_policy_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        path.write_text(path.read_text(encoding='utf-8') +
                        '\n  - name: "🐟 闲鱼"\n    type: select\n    proxies:\n      - DIRECT\n',
                        encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Xianyu must be a DIRECT-first select'):
            validate.validate_xianyu(self.root)
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            validate.validate_tree(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text(encoding='utf-8')
                    path.write_text(original + f'  - {kind},www.goofish.com\n', encoding='utf-8')
                    try:
                        validate.validate_xianyu(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,www.goofish.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_xianyu(self.root)

    def test_direct_shadow_with_same_target_fails_helper_and_tree(self):
        self.mutate('config/rules.yaml', self.MARKER,
                    '  - DOMAIN,www.goofish.com,🐟 闲鱼\n' + self.MARKER)
        for gate in (validate.validate_xianyu, validate.validate_tree):
            with self.subTest(gate=gate.__name__):
                with self.assertRaisesRegex(ValueError, 'Xianyu is shadowed'):
                    gate(self.root)

    def test_unknown_top_level_rules_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,xianyu,DIRECT',
                     'AND,((DOMAIN,www.goofish.com)),DIRECT'):
            with self.subTest(rule=rule):
                path.write_text(original.replace('rules:\n', 'rules:\n  - ' + rule + '\n'),
                                encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                    validate.validate_xianyu(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownXianyu,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownXianyu'):
            validate.validate_xianyu(self.root)

    def test_missing_own_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        del manifest['Xianyu']
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: Xianyu'):
            validate.validate_xianyu(self.root)

    def test_manifest_provider_collision_is_rejected(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        path = self.root / 'local-rulesets.json'
        local = json.loads(path.read_text(encoding='utf-8'))
        local['Apple'] = sources['Apple']
        path.write_text(json.dumps(local, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Xianyu manifests contain duplicate providers: Apple'):
            validate.validate_xianyu(self.root)
        # An earlier existing App may detect the shared manifest collision
        # before Xianyu's own gate. The dedicated gate is tested above.
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
            validate.validate_xianyu(self.root)
        self.assertTrue(seen)


    def test_preceding_ip_conditions_fail_helper_and_complete_tree(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(self.MARKER, '  - ' + rule + '\n' + self.MARKER),
                                encoding='utf-8')
                for gate in (validate.validate_xianyu, validate.validate_tree):
                    with self.subTest(gate=gate.__name__):
                        with self.assertRaisesRegex(ValueError, 'Xianyu domain-only model cannot validate preceding IP'):
                            gate(self.root)

    def test_missing_group_is_rejected(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "🐟 闲鱼"')
        end = original.index('  - name:', start + 1)
        path.write_text(original[:start] + original[end:], encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Xianyu must be a DIRECT-first select'):
            validate.validate_xianyu(self.root)
        with self.assertRaisesRegex(ValueError, 'undefined policy groups'):
            validate.validate_tree(self.root)

    def test_incomplete_supported_rules_have_clear_errors_even_after_match(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('RULE-SET', 'RULE-SET,IncompleteXianyu', 'RULE-SET,Privacy,REJECT,extra',
                     'DOMAIN,www.goofish.com', 'DOMAIN,,DIRECT', 'DOMAIN-SUFFIX,goofish.com',
                     'DOMAIN-KEYWORD,goofish', 'MATCH', 'MATCH,DIRECT,extra',
                     'GEOIP,CN', 'GEOIP,CN,DIRECT,invalid', 'IP-CIDR,192.0.2.0/24',
                     'IP-CIDR6,2001:db8::/32,DIRECT,extra'):
            with self.subTest(rule=rule):
                path.write_text(original + '  - ' + rule + '\n', encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'Xianyu domain-only model requires complete supported rules'):
                    validate.validate_xianyu(self.root)


    def test_actual_first_matches_and_non_target_routes(self):
        manifests = {}
        for filename in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((self.root / filename).read_text(encoding='utf-8')))
        providers = {name: DomainRules(yaml.safe_load((self.root / item['path']).read_text(encoding='utf-8'))['payload'])
                     for name, item in manifests.items()}
        rules = yaml.safe_load((self.root / 'config/rules.yaml').read_text(encoding='utf-8'))['rules']

        def route(host, include_xianyu=True):
            for rule in rules:
                fields = rule.split(',')
                kind = fields[0]
                if kind == 'RULE-SET':
                    if not include_xianyu and fields[1] == 'Xianyu':
                        continue
                    if providers[fields[1]].matches(host):
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
            with self.subTest(host=host):
                current, previous = route(host), route(host, False)
                self.assertIn(current, security | {('Xianyu', '🐟 闲鱼')})
                if current in security:
                    self.assertEqual(current, previous)
        controls = NEGATIVE_HOSTS | {value for host in HOSTS for value in
                                    ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(control=host):
                self.assertEqual(route(host), route(host, False))


if __name__ == '__main__':
    unittest.main()
