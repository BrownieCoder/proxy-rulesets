"""Independent YAML-parser oracles for the restricted public select-group grammar."""
import sys
import unittest
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from app_policy import validate_select_group

BASE = '    type: select\n    proxies:\n      - DIRECT\n      - "🚀 节点选择"\n'


class SelectGroupSyntax(unittest.TestCase):
    def test_supported_literal_select_forms(self):
        for value in ('select', '"select"', "'select'", 'select # manual',
                      '"select" # manual', "'select' # manual"):
            with self.subTest(value=value):
                block = BASE.replace('type: select', 'type: ' + value)
                parsed = yaml.safe_load('groups:\n  - name: public\n' + block)['groups'][0]
                self.assertEqual(parsed['type'], 'select')
                validate_select_group(block, 'public group')
                validate_select_group(block.replace('\n', '\r\n'), 'public group')

    def test_complex_type_keys_cannot_override_select(self):
        for declaration in ('"t\\u0079pe": fallback', '!!str type: fallback',
                            '&policy_type type: fallback', '? type\n    : fallback',
                            '<<: {type: fallback}', 'type: fallback # duplicate',
                            'type:', 'type : fallback', '"type": fallback', "'type': fallback"):
            with self.subTest(declaration=declaration):
                block = BASE + '    ' + declaration + '\n'
                parsed = yaml.safe_load('groups:\n  - name: public\n' + block)['groups'][0]
                # YAML merge keys do not override an explicit key, but are still
                # intentionally outside this project-owned template grammar.
                if not declaration.startswith('<<:'):
                    self.assertNotEqual(parsed['type'], 'select')
                with self.assertRaises(ValueError):
                    validate_select_group(block, 'public group')

    def test_duplicate_and_complex_proxies_are_rejected(self):
        for declaration in ('proxies: []', '"proxies": []', '"pro\\u0078ies": []',
                            '!!str proxies: []', '&list_key proxies: []', '? proxies\n    : []'):
            with self.subTest(declaration=declaration):
                block = BASE + '    ' + declaration + '\n'
                parsed = yaml.safe_load('groups:\n  - name: public\n' + block)['groups'][0]
                self.assertEqual(parsed['proxies'], [])
                with self.assertRaises(ValueError):
                    validate_select_group(block, 'public group')

    def test_unknown_fields_and_non_block_lists_are_rejected(self):
        for block in (BASE + '    unsupported: value\n',
                      BASE.replace('    proxies:\n      - DIRECT\n      - "🚀 节点选择"',
                                   '    proxies: [DIRECT, "🚀 节点选择"]'),
                      BASE.replace('type: select', 'type: &kind select'),
                      BASE.replace('type: select', 'type: !!str select')):
            with self.subTest(block=block), self.assertRaises(ValueError):
                validate_select_group(block, 'public group')

    def test_missing_fields_and_misplaced_members_are_rejected(self):
        for block in ('', BASE.replace('    type: select\n', ''),
                      BASE.replace('    proxies:\n', ''),
                      '    type: select\n    proxies:\n', '      - DIRECT\n' + BASE):
            with self.subTest(block=block), self.assertRaises(ValueError):
                validate_select_group(block, 'public group')

    def test_proxy_members_must_be_supported_literal_scalars(self):
        for member in ('type: fallback', '*alias', '&member DIRECT', '!!str DIRECT',
                       '[DIRECT]', '{type: fallback}', '|', 'null', 'true', '123',
                       '"DI\\u0052ECT"', '"unterminated', '""', "'DIRECT'",
                       'DIRECT # comment', '"unknown" # comment'):
            with self.subTest(member=member), self.assertRaises(ValueError):
                validate_select_group(BASE + '      - ' + member + '\n', 'public group')
        for block in (BASE + '\t# noncanonical indentation\n',
                      BASE + '\u00a0# not an ASCII-indented comment\n',
                      BASE.replace('    type: select', '    type: "select # not a comment"'),
                      BASE.replace('    type: select', '    type: select#not-a-comment')):
            with self.subTest(block=block), self.assertRaises(ValueError):
                validate_select_group(block, 'public group')

    def test_control_characters_and_noncanonical_line_breaks_are_rejected(self):
        for char in ('\0', '\v', '\f', '\t', '\r', '\x7f', '\x85', '\u2028', '\u2029'):
            with self.subTest(char=repr(char)), self.assertRaises(ValueError):
                validate_select_group(BASE + '    # comment' + char + 'hidden\n', 'public group')
        for value in ('select\t# comment', '"select"\t# comment'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_select_group(BASE.replace('select', value), 'public group')


if __name__ == '__main__':
    unittest.main()
