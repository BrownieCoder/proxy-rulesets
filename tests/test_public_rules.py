"""Independent YAML oracle and real public-template consumer regressions."""
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import generate_catalog as catalog
import public_rules
import siri_ai
import validate


class PublicRuleGrammar(unittest.TestCase):
    def test_current_sequence_equals_independent_yaml(self):
        text = (ROOT / 'config/rules.yaml').read_text(encoding='utf-8')
        parsed = yaml.safe_load(text)
        self.assertEqual(set(parsed), {'rules'})
        self.assertTrue(all(isinstance(rule, str) for rule in parsed['rules']))
        self.assertEqual(public_rules.parse_routing_rules(text), parsed['rules'])

    def test_accepted_forms_have_identical_yaml_values(self):
        values = ('RULE-SET,Privacy,REJECT', 'DOMAIN,example.org,🧭 Final',
                  'IP-CIDR6,2001:db8::/32,DIRECT,no-resolve', 'MATCH', 'RULE-SET')
        for indent in ('', '  ', '    '):
            for quote in ('', "'", '"'):
                for newline in ('\n', '\r\n'):
                    text = '# Public template\nrules:  \n\n' + ''.join(
                        indent + '- ' + quote + value + quote + '  \n' for value in values)
                    text = text.replace('\n', newline)
                    with self.subTest(indent=indent, quote=quote, newline=newline):
                        self.assertEqual(public_rules.parse_routing_rules(text), list(values))
                        self.assertEqual(public_rules.parse_routing_rules(text), yaml.safe_load(text)['rules'])

    def test_quoted_literals_preserve_yaml_special_characters_as_strings(self):
        for value in ('true', '123', 'NULL', 'DOMAIN,x,DIRECT # literal',
                      'DOMAIN,x,policy: literal', 'DOMAIN,x,🧭 Final'):
            for quote in ("'", '"'):
                text = 'rules:\n  - ' + quote + value + quote + '\n'
                with self.subTest(value=value, quote=quote):
                    self.assertEqual(public_rules.parse_routing_rules(text), yaml.safe_load(text)['rules'])
                    self.assertEqual(public_rules.parse_routing_rules(text), [value])

    def test_yaml_types_and_ambiguous_plain_scalars_are_rejected(self):
        for value in ('true', 'FALSE', 'yes', 'ON', 'null', 'NULL', '~', '123', '1.5',
                      '.nan', '2026-11-17', '{kind: DOMAIN}', '[DOMAIN,x,DIRECT]',
                      'DOMAIN,x,policy: different', 'DOMAIN,x,DIRECT # comment'):
            text = 'rules:\n  - ' + value + '\n'
            yaml.safe_load(text)  # Valid YAML need not belong to our literal template subset.
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Public config/rules.yaml'):
                public_rules.parse_routing_rules(text)

    def test_complex_yaml_is_fail_closed(self):
        cases = ('"rules": []\n', "'rules': []\n", '!!str rules: []\n',
                 '"r\\u0075les": []\n', '&key rules: []\n', '? rules\n: []\n',
                 'rules: &rules\n  - MATCH,DIRECT\n', 'rules: *rules\n',
                 'rules:\n  - !!str MATCH,DIRECT\n', 'rules:\n  - &rule MATCH,DIRECT\n',
                 'rules:\n  - |\n    MATCH,DIRECT\n', 'rules:\n  - >\n    MATCH,DIRECT\n',
                 'rules:\n  - "MATCH,\\u0044IRECT"\n', "rules:\n  - 'MATCH,it''s'\n",
                 'rules:\n  - ""\n', 'rules:\n  - "MATCH,DIRECT\n',
                 'rules:\n  - MATCH,DIRECT\n---\nrules: []\n',
                 'rules:\n  - MATCH,DIRECT\n    - MATCH,DIRECT\n')
        for text in cases:
            with self.subTest(text=text), self.assertRaises(ValueError):
                public_rules.parse_routing_rules(text)

    def test_unicode_controls_and_tabs_cannot_hide_structure(self):
        for char in ('\t', '\r', '\x00', '\x85', '\u200b', '\u2028', '\u2029', '\ufeff'):
            for text in ('rules:\n  - MATCH,' + char + 'DIRECT\n',
                         'rules:\n  - MATCH,DIRECT\n# comment' + char + 'marker\n'):
                with self.subTest(char=repr(char), text=text), self.assertRaisesRegex(ValueError, 'control characters'):
                    public_rules.parse_routing_rules(text)

    def test_dispatch_is_limited_to_config_rules_and_keeps_payload_scanning(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for directory in ('config', 'ruleset', 'other'):
                (root / directory).mkdir()
            for relative in ('config/rules.yaml', 'ruleset/rules.yaml', 'other/rules.yaml', 'config/other.yaml'):
                path = root / relative
                path.write_text('unrelated:\n  - DOMAIN,example.org\n', encoding='utf-8')
                with self.subTest(relative=relative):
                    if relative == 'config/rules.yaml':
                        with self.assertRaises(ValueError):
                            siri_ai.entries(path)
                    else:
                        self.assertEqual(siri_ai.entries(path), ['DOMAIN,example.org'])

    def test_reader_always_requests_utf8(self):
        original = Path.read_text
        def checked(path, *args, **kwargs):
            self.assertEqual(kwargs.get('encoding'), 'utf-8')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', autospec=True, side_effect=checked):
            self.assertEqual(public_rules.read_routing_rules(ROOT / 'config/rules.yaml'),
                             siri_ai.entries(ROOT / 'config/rules.yaml'))

    def test_runtime_entrypoints_do_not_require_site_packages(self):
        code = ('import sys; from pathlib import Path; '
                'sys.path.insert(0, "scripts"); '
                'import public_rules, validate, generate_catalog, siri_ai; '
                'assert public_rules.read_routing_rules(Path("config/rules.yaml")); '
                'assert "yaml" not in sys.modules')
        result = subprocess.run([sys.executable, '-S', '-c', code], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


class PublicRuleConsumers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for filename in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / filename, self.root / filename)
        self.path = self.root / 'config/rules.yaml'
        self.original = self.path.read_text(encoding='utf-8')
        self.providers = set(json.loads((self.root / 'sources.json').read_text(encoding='utf-8')))
        self.providers.update(json.loads((self.root / 'local-rulesets.json').read_text(encoding='utf-8')))
        self.domains, _ = siri_ai.canonical(self.root)

    def consumers(self):
        return {
            'entries': lambda: siri_ai.entries(self.path),
            'targets': lambda: validate.parse_rule_targets(self.path.read_text(encoding='utf-8')),
            'references': lambda: validate.validate_config_references(self.providers, self.root),
            'catalog routing': lambda: catalog.routing(self.root),
            'catalog build': lambda: catalog.build(self.root),
            'Siri first-match': lambda: siri_ai.routing_check(self.domains, self.root),
            'App direct': lambda: validate.validate_alipan(self.root),
            'complete tree': lambda: validate.validate_tree(self.root),
        }

    def test_unmodified_complete_fixture_and_all_direct_consumers_pass(self):
        expected = yaml.safe_load(self.original)['rules']
        self.assertEqual(siri_ai.entries(self.path), expected)
        self.assertEqual(catalog.routing(self.root)[0], expected)
        for name, consumer in self.consumers().items():
            with self.subTest(consumer=name), contextlib.redirect_stdout(io.StringIO()):
                consumer()

    def test_structure_mutations_are_rejected_by_every_direct_consumer(self):
        first = '  - RULE-SET,Privacy,REJECT\n'
        variants = {
            'duplicate empty override': self.original + '\nrules: []\n',
            'duplicate block': self.original + '\nrules:\n  - MATCH,DIRECT\n',
            'duplicate quoted key': self.original + '\n"rules": []\n',
            'wrong key': self.original.replace('rules:\n', 'unrelated:\n', 1),
            'missing key': self.original.replace('rules:\n', '', 1),
            'nested key': 'wrapper:\n' + ''.join('  ' + line + '\n' for line in self.original.splitlines()),
            'extra list': self.original + '\nunrelated:\n  - MATCH,DIRECT\n',
            'mapping value': 'rules: {entry: MATCH,DIRECT}\n',
            'null value': 'rules:\n',
            'scalar value': 'rules: MATCH,DIRECT\n',
            'flow sequence': 'rules: ' + json.dumps(yaml.safe_load(self.original)['rules']) + '\n',
            'non-string item': self.original.replace(first, '  - true\n'),
            'nested sequence item': self.original.replace(first, '  - [RULE-SET, Privacy, REJECT]\n'),
            'mapping item': self.original.replace(first, '  - key: value\n'),
            'tagged item': self.original.replace(first, '  - !!str RULE-SET,Privacy,REJECT\n'),
            'inline comment': self.original.replace(first, '  - RULE-SET,Privacy,REJECT # comment\n'),
            'inline mapping': self.original.replace(first, '  - RULE-SET,Privacy,policy: value\n'),
            'unicode line break': self.original + '# comment\u2028rules: []\n',
        }
        for label, text in variants.items():
            self.path.write_text(text, encoding='utf-8')
            for name, consumer in self.consumers().items():
                with self.subTest(mutation=label, consumer=name), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(ValueError, 'Public config/rules.yaml'):
                        consumer()

    def test_duplicate_and_wrong_key_reproduce_the_independent_yaml_difference(self):
        expected = yaml.safe_load(self.original)['rules']
        self.assertTrue(expected)
        for text in (self.original + '\nrules: []\n', self.original.replace('rules:\n', 'unrelated:\n', 1)):
            parsed = yaml.safe_load(text)
            self.assertNotEqual(parsed.get('rules'), expected)
            self.path.write_text(text, encoding='utf-8')
            with self.assertRaises(ValueError):
                validate.validate_tree(self.root)

    def test_plain_and_quoted_sequences_have_one_semantics_and_no_generated_changes(self):
        expected = yaml.safe_load(self.original)['rules']
        original_output = catalog.build(self.root)
        expected_transitions = siri_ai.routing_check(self.domains, self.root)
        for quote in ('', "'", '"'):
            text = '# Same rules, alternate literal scalar form\nrules:\n' + ''.join(
                '  - ' + quote + rule + quote + '\n' for rule in expected)
            self.path.write_text(text, encoding='utf-8')
            with self.subTest(quote=quote), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(yaml.safe_load(text)['rules'], expected)
                self.assertEqual(siri_ai.entries(self.path), expected)
                self.assertEqual(catalog.routing(self.root)[0], expected)
                self.assertEqual(catalog.build(self.root), original_output)
                self.assertEqual(siri_ai.routing_check(self.domains, self.root), expected_transitions)
                self.assertEqual(validate.parse_rule_targets(text), validate.parse_rule_targets(self.original))
                validate.validate_config_references(self.providers, self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_quoted_unknown_provider_is_not_hidden_from_reference_validation(self):
        self.path.write_text(self.original + '  - "RULE-SET,MissingPublicProvider,DIRECT"\n', encoding='utf-8')
        self.assertIn('RULE-SET,MissingPublicProvider,DIRECT', siri_ai.entries(self.path))
        for consumer in (lambda: validate.validate_config_references(self.providers, self.root),
                         lambda: validate.validate_tree(self.root)):
            with self.assertRaisesRegex(ValueError, 'undefined providers.*MissingPublicProvider'):
                consumer()

    def test_quoted_unknown_target_is_not_hidden_from_target_validation(self):
        self.path.write_text(self.original + "  - 'DOMAIN,example.org,MissingPublicPolicy'\n", encoding='utf-8')
        self.assertIn('MissingPublicPolicy', validate.parse_rule_targets(self.path.read_text(encoding='utf-8')))
        with self.assertRaisesRegex(ValueError, 'undefined policy groups.*MissingPublicPolicy'):
            validate.validate_config_references(self.providers, self.root)

    def test_every_existing_app_direct_gate_uses_structural_semantics(self):
        self.path.write_text(self.original + '\nrules: []\n', encoding='utf-8')
        names = ('xiaohongshu', 'douban', 'baidu_pan', 'zhihu', 'amap', 'netease_music',
                 'douyin', 'qq_music', 'jd', 'meituan', 'ctrip', 'pinduoduo', 'taobao',
                 'baidu_map', 'kuaishou', 'tencent_video', 'alipan')
        self.assertEqual(len(names), 17)
        for name in names:
            with self.subTest(app=name), self.assertRaisesRegex(ValueError, 'Public config/rules.yaml'):
                getattr(validate, 'validate_' + name)(self.root)

    def test_incomplete_literal_rules_still_reach_existing_semantic_gate(self):
        for rule in ('RULE-SET', 'DOMAIN,www.alipan.com', 'MATCH'):
            self.path.write_text(self.original + '  - ' + rule + '\n', encoding='utf-8')
            with self.subTest(rule=rule):
                self.assertEqual(siri_ai.entries(self.path)[-1], rule)
                with self.assertRaisesRegex(ValueError, 'AliPan domain-only model requires complete supported rules'):
                    validate.validate_alipan(self.root)


if __name__ == '__main__':
    unittest.main()
