"""Independent YAML oracle and real consumers for public policy-group structure."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import public_policy_groups as policy
import validate

SIMPLE = 'proxy-groups:\n  - name: "first"\n    type: select\n    proxies:\n      - DIRECT\n'
APPS = ('qq_music', 'douyin', 'amap', 'zhihu', 'xiaohongshu', 'netease_music',
        'douban', 'jd', 'meituan', 'baidu_pan', 'ctrip', 'pinduoduo', 'taobao',
        'baidu_map', 'kuaishou', 'tencent_video', 'alipan', 'iqiyi', 'xianyu',
        'railway_12306', 'youku', 'wps_office', 'feishu', 'dingtalk', 'quark', 'boss_zhipin',
        'wechat', 'sf_express', 'weibo', 'tencent_qq',
        'mango_tv',
        'didi')


class PolicyGroupGrammar(unittest.TestCase):
    def assert_oracle(self, text):
        expected = yaml.safe_load(text)['proxy-groups']
        actual = policy.parse_policy_group_model(text)
        self.assertEqual(actual, expected)
        self.assertIs(type(actual), list)
        for group, oracle in zip(actual, expected):
            self.assertIs(type(group), dict)
            for key, value in group.items():
                self.assertIs(type(value), type(oracle[key]), key)
                if isinstance(value, list):
                    self.assertTrue(all(type(member) is str for member in value), key)
                    self.assertTrue(all(type(member) is str for member in oracle[key]), key)
        return actual

    def test_actual_mappings_names_and_ordered_members_match_yaml(self):
        text = (ROOT / 'config/proxy-groups.yaml').read_text(encoding='utf-8')
        groups = self.assert_oracle(text)
        self.assertTrue(groups)
        self.assertEqual(sum(g['type'] == 'url-test' for g in groups), 2)
        names, members = validate.parse_policy_groups(ROOT)
        self.assertEqual(names, {g['name'] for g in groups})
        self.assertEqual(members, {g['name']: g.get('proxies', []) for g in groups})

    def test_quoted_and_plain_keys_types_comments_and_crlf(self):
        for root_quote in ('', "'", '"'):
            for type_key in ('type', "'type'", '"type"'):
                for type_value in ('select', "'select'", '"select"'):
                    for newline in ('\n', '\r\n'):
                        text = SIMPLE.replace('proxy-groups:', root_quote + 'proxy-groups' + root_quote + ': # root')
                        text = text.replace('type: select', type_key + ': ' + type_value + ' # literal')
                        with self.subTest(root=root_quote, key=type_key, value=type_value, newline=newline):
                            self.assert_oracle(text.replace('\n', newline))

    def test_quoted_internal_spaces_and_hash_are_not_trimmed(self):
        text = ('proxy-groups:\n  - name: " first # [] " # outside\n'
                '    type: select\n    proxies:\n      - " second: # [x] " # outside\n'
                '  - name: " second: # [x] "\n    type: url-test\n')
        groups = self.assert_oracle(text)
        self.assertEqual(groups[0]['name'], ' first # [] ')
        self.assertEqual(groups[0]['proxies'], [' second: # [x] '])
        self.assert_oracle(SIMPLE.replace('type: select', 'type: select#literal'))

    def test_typed_scalar_fields_url_and_filter_match_yaml(self):
        for boolean in ('true', 'false'):
            for integer in ('0', '300', '-1'):
                text = ('proxy-groups:\n  - name: auto\n    type: url-test\n'
                        f'    include-all: {boolean}\n    lazy: {boolean}\n'
                        f'    interval: {integer}\n    timeout: 5000\n    tolerance: 50\n'
                        '    expected-status: 204\n    empty-fallback: REJECT\n'
                        '    exclude-type: direct\n    url: https://example.org/check#fragment\n'
                        '    filter: "(?i)([A-Z]|美国|(^|[^A-Za-z])US([^A-Za-z]|$))"\n')
                with self.subTest(boolean=boolean, integer=integer):
                    self.assert_oracle(text)

    def test_url_test_missing_proxies_is_not_explicit_null_or_flow(self):
        text = 'proxy-groups:\n  - name: auto\n    type: url-test\n    include-all: true\n'
        self.assertNotIn('proxies', self.assert_oracle(text)[0])
        for suffix in ('    proxies:\n', '    proxies: null\n', '    proxies: []\n',
                       '    proxies: DIRECT\n', '    proxies: {}\n'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                policy.parse_policy_group_model(text + suffix)

    def test_wrong_duplicate_nested_and_extra_roots_fail(self):
        cases = (SIMPLE.replace('proxy-groups:', 'unrelated:', 1),
                 SIMPLE + '\nproxy-groups: []\n', SIMPLE + '\n"proxy-groups": []\n',
                 SIMPLE + "\n'proxy-groups':\n  - name: second\n",
                 SIMPLE + '\nunrelated: value\n',
                 'wrapper:\n' + ''.join('  ' + line + '\n' for line in SIMPLE.splitlines()),
                 SIMPLE.replace('proxy-groups:\n', ''), 'proxy-groups: []\n',
                 'proxy-groups:\n', 'proxy-groups: null\n', 'proxy-groups: {name: first}\n')
        for text in cases:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'Public config/proxy-groups.yaml'):
                policy.parse_policy_group_model(text)

    def test_mapping_and_member_nesting_cannot_be_scanned_as_groups(self):
        for text in ('proxy-groups:\n  - true\n', 'proxy-groups:\n  - DIRECT\n',
                     'proxy-groups:\n  - {name: first}\n',
                     SIMPLE.replace('      - DIRECT', '        - DIRECT'),
                     SIMPLE.replace('      - DIRECT', '      - [DIRECT]'),
                     SIMPLE.replace('      - DIRECT', '      - name: nested'),
                     SIMPLE.replace('      - DIRECT', '    - DIRECT'),
                     SIMPLE.replace('      - DIRECT', '      - true'),
                     SIMPLE.replace('      - DIRECT', '      - 123'),
                     SIMPLE.replace('    type: select', '    type: select\n      - DIRECT')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                policy.parse_policy_group_model(text)

    def test_duplicate_name_type_and_proxies_keys_fail_including_equivalents(self):
        for key, extra in (('name', 'other'), ('type', 'fallback'), ('proxies', '[]')):
            for quote in ('', "'", '"'):
                with self.subTest(key=key, quote=quote), self.assertRaisesRegex(ValueError, 'duplicate group field'):
                    policy.parse_policy_group_model(SIMPLE + '    ' + quote + key + quote + ': ' + extra + '\n')
        with self.assertRaisesRegex(ValueError, 'duplicate group'):
            policy.parse_policy_group_model(SIMPLE + SIMPLE.partition('proxy-groups:\n')[2])

    def test_complex_yaml_and_implicit_scalar_types_fail_closed(self):
        variants = ('"na\\u006de": first', '!!str name: first', '&key name: first',
                    '? name\n    : first', '<<: {name: first}', 'unknown: value')
        for field in variants:
            text = SIMPLE + '    ' + field + '\n'
            with self.subTest(field=field), self.assertRaises(ValueError):
                policy.parse_policy_group_model(text)
        for value in ('!!str first', '&anchor first', '*anchor', 'true', 'null',
                      '123', '2026-11-18', '"fi\\u0072st"', "'it''s'", '|', '>'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                policy.parse_policy_group_model(SIMPLE.replace('"first"', value))

    def test_wrong_typed_field_values_fail_without_coercion(self):
        for field in ('include-all: "true"', 'include-all: 1', 'lazy: null',
                      'interval: true', 'timeout: "5000"', 'tolerance: 1.5',
                      'expected-status: 0204', 'filter: [US]', 'url: null', 'type: 1'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                text = (SIMPLE.replace('type: select', field) if field.startswith('type:')
                        else SIMPLE + '    ' + field + '\n')
                policy.parse_policy_group_model(text)

    def test_plain_url_trailing_colon_cannot_diverge_from_yaml(self):
        text = SIMPLE + '    url: https://example.org:\n'
        with self.assertRaises(yaml.YAMLError):
            yaml.safe_load(text)
        with self.assertRaisesRegex(ValueError, 'scalar syntax'):
            policy.parse_policy_group_model(text)
        self.assert_oracle(SIMPLE + '    url: "https://example.org:"\n')

    def test_raw_controls_and_document_markers_fail_closed(self):
        for char in ('\t', '\r', '\x00', '\x85', '\u200b', '\u2028', '\u2029', '\ufeff'):
            with self.subTest(char=repr(char)), self.assertRaisesRegex(ValueError, 'control characters'):
                policy.parse_policy_group_model(SIMPLE + '# comment' + char + 'marker\n')
        with self.assertRaises(ValueError):
            policy.parse_policy_group_model(SIMPLE + '---\nproxy-groups: []\n')

    def test_runtime_reader_is_stdlib_only(self):
        code = ('import sys; from pathlib import Path; sys.path.insert(0,"scripts"); '
                'import public_policy_groups,validate; '
                'assert validate.parse_policy_groups(Path(".")); assert "yaml" not in sys.modules')
        result = subprocess.run([sys.executable, '-S', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


class PolicyGroupConsumers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / folder, self.root / folder)
        for filename in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / filename, self.root / filename)
        self.path = self.root / 'config/proxy-groups.yaml'
        self.original = self.path.read_text(encoding='utf-8')
        self.providers = set(json.loads((self.root / 'sources.json').read_text(encoding='utf-8')))
        self.providers.update(json.loads((self.root / 'local-rulesets.json').read_text(encoding='utf-8')))

    def test_complete_public_fixture_and_all_app_direct_entries_pass(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate.validate_tree(self.root), 0)
            validate.validate_config_references(self.providers, self.root)
            for name in APPS:
                with self.subTest(app=name):
                    getattr(validate, 'validate_' + name)(self.root)

    def test_two_core_reproductions_fail_every_actual_consumer(self):
        self.assertEqual(len(APPS), len(set(APPS)))
        for text in (self.original + '\nproxy-groups: []\n',
                     self.original.replace('proxy-groups:', 'unrelated:', 1)):
            actual = yaml.safe_load(text).get('proxy-groups')
            self.assertTrue(actual is None or actual == [])
            self.path.write_text(text, encoding='utf-8')
            consumers = (lambda: validate.parse_policy_groups(self.root),
                         lambda: validate.validate_config_references(self.providers, self.root),
                         lambda: validate.validate_tree(self.root))
            for consumer in consumers:
                with self.assertRaisesRegex(ValueError, 'Public config/proxy-groups.yaml'):
                    consumer()
            for name in APPS:
                with self.subTest(app=name), self.assertRaisesRegex(ValueError, 'Public config/proxy-groups.yaml'):
                    getattr(validate, 'validate_' + name)(self.root)

    def test_missing_references_and_cycles_still_use_actual_model(self):
        for text, reason in ((SIMPLE.replace('DIRECT', 'Missing'), 'undefined groups'),
                             (SIMPLE.replace('DIRECT', 'first'), 'group cycle')):
            self.path.write_text(text, encoding='utf-8')
            with self.subTest(reason=reason), self.assertRaisesRegex(ValueError, reason):
                validate.parse_policy_groups(self.root)

    def test_public_url_tests_without_proxy_lists_remain_empty_members(self):
        names, members = validate.parse_policy_groups(self.root)
        self.assertIn('⚡ 自动选择', names)
        self.assertEqual(members['⚡ 自动选择'], [])
        self.assertEqual(members['🇺🇸 美国节点'], [])

    def test_internal_spaces_are_not_normalized_into_a_reference(self):
        self.path.write_text(SIMPLE.replace('DIRECT', '" first "'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'undefined groups'):
            validate.parse_policy_groups(self.root)


if __name__ == '__main__':
    unittest.main()
