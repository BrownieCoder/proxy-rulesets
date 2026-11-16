"""Real TencentVideo validator mutations; no account traffic or private input."""
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
from siri_ai import DomainRules, entries

HOSTS = {'v.qq.com', 'm.v.qq.com', 'film.qq.com', 'film.video.qq.com'}


class TencentVideoContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, filename, old, new):
        path = self.root / filename
        path.write_text(path.read_text(encoding='utf-8').replace(old, new), encoding='utf-8')

    def test_current_contract(self):
        validate.validate_tencent_video(self.root)

    def complete_public_fixture(self):
        for directory in ('catalog', 'docs', 'research', 'rules', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('README.md', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def test_tree_calls_tencent_video_gate(self):
        self.complete_public_fixture()
        with patch.object(validate, 'validate_tencent_video', side_effect=ValueError('TencentVideo gate reached')) as gate:
            with self.assertRaisesRegex(ValueError, 'TencentVideo gate reached'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_helper_reads_explicit_utf8(self):
        read_text = Path.read_text
        seen = []

        def utf8_read(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8', str(path))
            seen.append(path)
            return read_text(path, *args, **kwargs)

        with patch.object(Path, 'read_text', utf8_read):
            validate.validate_tencent_video(self.root)
        self.assertTrue(seen)

    def test_broadening_or_duplicate_scope_is_rejected(self):
        path = self.root / 'ruleset/TencentVideo.yaml'
        original = path.read_text(encoding='utf-8')
        for text in (original.replace('DOMAIN,v.qq.com', 'DOMAIN-SUFFIX,qq.com'),
                     original + '  - DOMAIN,v.qq.com\n'):
            with self.subTest(scope=text):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'four reviewed exact hosts'):
                    validate.validate_tencent_video(self.root)

    def test_shared_cdn_is_not_accepted_without_review(self):
        path = self.root / 'ruleset/TencentVideo.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,imgcache.qq.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'four reviewed exact hosts'):
            validate.validate_tencent_video(self.root)

    def test_missing_duplicate_or_wrong_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,TencentVideo,📺 腾讯视频\n'
        for text in (original.replace(marker, '  # RULE-SET,TencentVideo,📺 腾讯视频\n'),
                     original + marker, original.replace(marker, '  - RULE-SET,TencentVideo,DIRECT\n')):
            with self.subTest(rule=text[-80:]):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
                    validate.validate_tencent_video(self.root)

    def test_security_bypass_and_late_placement_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        marker = '  - RULE-SET,TencentVideo,📺 腾讯视频\n'
        without = path.read_text(encoding='utf-8').replace(marker, '')
        for text, expected in ((without.replace('rules:\n', 'rules:\n' + marker), 'Security and gaming'),
                               (without.replace('  - RULE-SET,GlobalMedia,',
                                                marker + '  - RULE-SET,GlobalMedia,'), 'broader providers')):
            with self.subTest(expected=expected):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, expected):
                    validate.validate_tencent_video(self.root)

    def test_preceding_ip_conditions_rejected_by_helper_and_real_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,TencentVideo,📺 腾讯视频\n'
        for rule in ('GEOIP,US,DIRECT', 'IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
                     'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve'):
            with self.subTest(rule=rule):
                path.write_text(original.replace(marker, '  - ' + rule + '\n' + marker), encoding='utf-8')
                for validator in (validate.validate_tencent_video, validate.validate_tree):
                    with self.subTest(entry=validator.__name__):
                        with self.assertRaisesRegex(ValueError, 'TencentVideo domain-only model cannot validate preceding IP'):
                            validator(self.root)

    def test_comments_cannot_replace_active_order_markers(self):
        self.mutate('config/rules.yaml', '  - RULE-SET,Apple,', '  # RULE-SET,Apple,')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_tencent_video(self.root)

    def test_direct_first_select_and_manual_proxy_are_required(self):
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📺 腾讯视频"')
        end = original.index('  - name:', start + 1)
        block = original[start:end]
        for replacement in (block.replace('      - DIRECT\n', ''),
                            block.replace('      - DIRECT\n      - "🚀 节点选择"',
                                          '      - "🚀 节点选择"\n      - DIRECT'),
                            block.replace('    type: select', '    type: fallback'),
                            block.replace('    type: select', '    type: select\n    type: select'),
                            block.replace('      - "🚀 节点选择"\n', ''),
                            block.replace('      - "🧭 Final"\n', '')):
            with self.subTest(group=replacement):
                path.write_text(original[:start] + replacement + original[end:], encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
                    validate.validate_tencent_video(self.root)

    def test_equivalent_duplicate_type_keys_rejected_by_helper_and_real_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "📺 腾讯视频"\n    type: select\n'
        self.assertIn(marker, original)
        self.assertEqual(validate.validate_tree(self.root), 0)
        for declaration, expected_type in (('type: fallback # duplicate type', 'fallback'),
                                           ('type:', None),
                                           ('type : fallback', 'fallback'),
                                           ('"type": fallback', 'fallback'),
                                           ("'type': fallback", 'fallback')):
            with self.subTest(declaration=declaration):
                changed = original.replace(marker, marker + '    ' + declaration + '\n')
                parsed = yaml.safe_load(changed)
                groups = [g for g in parsed['proxy-groups'] if g['name'] == '📺 腾讯视频']
                self.assertEqual(len(groups), 1)
                self.assertEqual(groups[0]['type'], expected_type)
                self.assertNotEqual(groups[0]['type'], 'select')
                path.write_text(changed, encoding='utf-8')
                for validator in (validate.validate_tencent_video, validate.validate_tree):
                    with self.subTest(entry=validator.__name__):
                        with self.assertRaisesRegex(ValueError, 'TencentVideo must be a DIRECT-first select'):
                            validator(self.root)

    def test_complex_group_yaml_rejected_by_helper_and_real_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📺 腾讯视频"\n')
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
                groups = [group for group in parsed if group['name'] == '📺 腾讯视频']
                self.assertEqual(len(groups), 1)
                effective = groups[0]
                actual = effective['proxies'][-1] if field == 'last_proxy' else effective[field]
                self.assertEqual(actual, expected)
                path.write_text(changed, encoding='utf-8')
                for validator in (validate.validate_tencent_video, validate.validate_tree):
                    with self.subTest(entry=validator.__name__):
                        # The tree's existing global reference gate rejects
                        # complex members before the new App helper runs.
                        error = ('proxy-groups.yaml references undefined groups'
                                 if validator is validate.validate_tree and field == 'last_proxy'
                                 else 'TencentVideo must be a DIRECT-first select')
                        with self.assertRaisesRegex(ValueError, error):
                            validator(self.root)

    def test_supported_literal_select_forms_pass_helper_and_real_tree(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - name: "📺 腾讯视频"\n    type: select\n'
        for declaration in ('type: "select"', "type: 'select'", 'type: select # manual selection',
                            'type: "select" # manual selection', '"type": select', "'type': 'select'"):
            with self.subTest(declaration=declaration):
                changed = original.replace(marker, '  - name: "📺 腾讯视频"\n    ' + declaration + '\n')
                groups = yaml.safe_load(changed)['proxy-groups']
                self.assertEqual(next(group for group in groups if group['name'] == '📺 腾讯视频')['type'],
                                 'select')
                path.write_text(changed, encoding='utf-8')
                validate.validate_tencent_video(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_future_security_matches_remain_valid(self):
        for provider in ('Privacy', 'Hijacking'):
            path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
            original = path.read_text(encoding='utf-8')
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path.write_text(original + f'  - {kind},v.qq.com\n', encoding='utf-8')
                    try:
                        validate.validate_tencent_video(self.root)
                    finally:
                        path.write_text(original, encoding='utf-8')

    def test_non_security_shadowing_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text(encoding='utf-8') + '  - DOMAIN,v.qq.com\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_tencent_video(self.root)

    def test_non_security_direct_shadow_even_same_policy_is_rejected(self):
        self.complete_public_fixture()
        marker = '  - RULE-SET,TencentVideo,📺 腾讯视频\n'
        self.mutate('config/rules.yaml', marker, '  - DOMAIN,v.qq.com,📺 腾讯视频\n' + marker)
        for validator in (validate.validate_tencent_video, validate.validate_tree):
            with self.subTest(entry=validator.__name__):
                with self.assertRaisesRegex(ValueError, 'TencentVideo is shadowed'):
                    validator(self.root)

    def test_wrong_security_targets_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for marker in ('RULE-SET,Privacy,REJECT', 'RULE-SET,Hijacking,🚫 Hijacking'):
            with self.subTest(marker=marker):
                path.write_text(original.replace(marker, marker.rsplit(',', 1)[0] + ',DIRECT'), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'requires one active rule'):
                    validate.validate_tencent_video(self.root)

    def test_unknown_top_level_types_are_rejected(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        for rule in ('DST-PORT,443,DIRECT', 'PROCESS-NAME,tencent_video,DIRECT',
                     'AND,((DOMAIN,v.qq.com)),DIRECT'):
            for late in (False, True):
                with self.subTest(rule=rule, late=late):
                    text = (original + f'  - {rule}\n' if late else
                            original.replace('rules:\n', f'rules:\n  - {rule}\n'))
                    path.write_text(text, encoding='utf-8')
                    with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
                        validate.validate_tencent_video(self.root)

    def test_exact_rules_and_non_target_boundaries(self):
        payload = yaml.safe_load((self.root / 'ruleset/TencentVideo.yaml').read_text(encoding='utf-8'))['payload']
        self.assertEqual(len(payload), len(HOSTS))
        self.assertEqual(set(payload), {'DOMAIN,' + host for host in HOSTS})
        model = DomainRules(payload)
        self.assertLessEqual({'y.qq.com', 'c.y.qq.com', 'dldir.y.qq.com', 'game.qq.com',
                              'wegame.gtimg.com', 'iwan.video.qq.com', 'www.iqiyi.com', 'www.youku.com'},
                             validate.TENCENT_VIDEO_CONTROLS)
        controls = validate.TENCENT_VIDEO_CONTROLS | {value for host in HOSTS for value in
                                             ('child.' + host, 'not' + host, host + '.example.org')}
        for host in controls:
            with self.subTest(host=host):
                self.assertFalse(model.matches(host))

    def test_unrelated_tencent_and_streaming_control_routes_are_unchanged(self):
        manifests = {}
        for name in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((ROOT / name).read_text(encoding='utf-8')))
        providers = {name: DomainRules(entries(ROOT / record['path']))
                     for name, record in manifests.items()}
        rules = yaml.safe_load((ROOT / 'config/rules.yaml').read_text(encoding='utf-8'))['rules']

        def route(host, include_tencent_video):
            for rule in rules:
                fields = rule.split(',')
                kind = fields[0]
                if kind == 'RULE-SET':
                    if not include_tencent_video and fields[1] == 'TencentVideo':
                        continue
                    if providers[fields[1]].matches(host):
                        return fields[1], fields[2]
                elif kind == 'MATCH':
                    return kind, fields[1]
                elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return ','.join(fields[:2]), fields[2]
                elif kind not in {'GEOIP', 'IP-CIDR', 'IP-CIDR6'}:
                    raise ValueError('Unsupported domain model kind: ' + kind)
            self.fail('Missing MATCH')

        for host in validate.TENCENT_VIDEO_CONTROLS:
            with self.subTest(host=host):
                self.assertEqual(route(host, True), route(host, False))

    def test_existing_apps_and_siri_order_is_enforced(self):
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        marker = '  - RULE-SET,TencentVideo,📺 腾讯视频\n'
        without = original.replace(marker, '')
        for text, expected in ((without.replace('  - RULE-SET,Taobao,', marker + '  - RULE-SET,Taobao,'),
                                'existing App rules must precede'),
                               (without.replace('  - RULE-SET,Apple,', marker + '  - RULE-SET,Apple,'),
                                'must precede broader')):
            with self.subTest(expected=expected):
                path.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, expected):
                    validate.validate_tencent_video(self.root)

    def test_each_media_anchor_moved_ahead_is_rejected_by_both_gates(self):
        self.complete_public_fixture()
        self.assertEqual(validate.validate_tree(self.root), 0)
        path = self.root / 'config/rules.yaml'
        original = path.read_text(encoding='utf-8')
        app = 'RULE-SET,TencentVideo,📺 腾讯视频'
        for media in ('RULE-SET,YouTube,📼 YouTube', 'RULE-SET,Bilibili,📺 Bilibili',
                      'RULE-SET,TikTok,🎵 Tiktok', 'RULE-SET,Disney,🏰 Disney',
                      'RULE-SET,Netflix,🎞️ Netflix'):
            with self.subTest(media=media):
                marker = '  - ' + media + '\n'
                self.assertEqual(original.count(marker), 1)
                changed = original.replace(marker, '').replace('  - ' + app + '\n',
                                                               marker + '  - ' + app + '\n')
                path.write_text(changed, encoding='utf-8')
                ordered = entries(path)
                self.assertLess(ordered.index('RULE-SET,Taobao,🛍️ 淘宝'), ordered.index(media))
                self.assertLess(ordered.index(media), ordered.index(app))
                self.assertLess(ordered.index(app), ordered.index('RULE-SET,SiriAI,🤖 AI 服务'))
                self.assertLess(ordered.index(app), ordered.index('RULE-SET,Apple,🍎 Apple'))
                for validator in (validate.validate_tencent_video, validate.validate_tree):
                    with self.subTest(entry=validator.__name__):
                        with self.assertRaisesRegex(ValueError, 'TencentVideo must precede broader providers'):
                            validator(self.root)

    def test_cross_manifest_provider_collision_rejected_by_both_gates(self):
        self.complete_public_fixture()
        path = self.root / 'local-rulesets.json'
        records = json.loads(path.read_text(encoding='utf-8'))
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        records['Apple'] = sources['Apple']
        path.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')
        for validator in (validate.validate_tencent_video, validate.validate_tree):
            with self.subTest(entry=validator.__name__):
                # An existing earlier App may reject the same collision first.
                with self.assertRaisesRegex(ValueError, 'manifests contain duplicate providers: Apple'):
                    validator(self.root)

    def test_incomplete_provider_reference_has_clear_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,Privacy\n')
        with self.assertRaisesRegex(ValueError, 'TencentVideo encountered an incomplete RULE-SET reference'):
            validate.validate_tencent_video(self.root)

    def test_missing_or_duplicate_policy_groups_rejected(self):
        self.complete_public_fixture()
        path = self.root / 'config/proxy-groups.yaml'
        original = path.read_text(encoding='utf-8')
        start = original.index('  - name: "📺 腾讯视频"\n')
        end = original.index('  - name:', start + 1)
        for changed in (original[:start] + original[end:], original + original[start:end]):
            with self.subTest(count=changed.count('name: "📺 腾讯视频"')):
                path.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'TencentVideo must be a DIRECT-first select'):
                    validate.validate_tencent_video(self.root)
                with self.assertRaises(ValueError):
                    validate.validate_tree(self.root)

    def test_missing_provider_has_actionable_error(self):
        path = self.root / 'local-rulesets.json'
        manifests = json.loads(path.read_text(encoding='utf-8'))
        del manifests['TencentVideo']
        path.write_text(json.dumps(manifests, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'missing providers: TencentVideo'):
            validate.validate_tencent_video(self.root)

    def test_unknown_provider_has_actionable_error(self):
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n  - RULE-SET,UnknownTencentVideo,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'missing providers: UnknownTencentVideo'):
            validate.validate_tencent_video(self.root)


if __name__ == '__main__':
    unittest.main()
