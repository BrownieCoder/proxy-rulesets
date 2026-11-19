"""Raw YAML character checks, public readers and real offline write boundaries."""
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
import generate_catalog
import siri_ai
import sync
import validate
from yaml_characters import validate_yaml_characters

PAYLOAD = 'payload:\n  - DOMAIN,example.org\n'
RULES = ['DOMAIN,example.org']
FORBIDDEN = tuple(c for c in range(0xA0) if c not in (9, 10, 13, 0x85)
                  and not 0x20 <= c <= 0x7E) + (0xD800, 0xDFFF, 0xFFFE, 0xFFFF)
LEGAL = (9, 10, 13, 0x20, 0x7E, 0x85, 0xA0, 0xD7FF, 0xE000, 0xFFFD,
         0x10000, 0x10FFFF, 0x2028, 0x2029, 0x200D, 0xFEFF, 0x1F4E6)


class PayloadCharacters(unittest.TestCase):
    def test_forbidden_ranges_fail_before_filtering(self):
        for code in FORBIDDEN:
            for text in (chr(code) + PAYLOAD, PAYLOAD + '# public note ' + chr(code) + '\n'):
                with self.subTest(code=f'U+{code:04X}', prefix=text.startswith(chr(code))):
                    with self.assertRaisesRegex(ValueError, f'forbidden raw character U\\+{code:04X}'):
                        validate_yaml_characters(text)

    def test_legal_ranges_and_unicode_oracle(self):
        for code in LEGAL:
            text = PAYLOAD + '# 中文公开注释 ' + chr(code) + '\n'
            with self.subTest(code=f'U+{code:04X}'):
                self.assertIsNone(validate_yaml_characters(text))
                self.assertEqual(yaml.safe_load(text)['payload'], RULES)
                self.assertEqual(generate_catalog.read_rules(text), RULES)
                with patch.object(Path, 'read_text', return_value=text) as read:
                    self.assertEqual(siri_ai.entries(Path('ruleset/Public.yaml')), RULES)
                read.assert_called_once_with(encoding='utf-8')
                sync.validate('Public', text.encode('utf-8'))

    def test_three_public_readers_reject_comment_hidden_characters(self):
        for code in FORBIDDEN:
            text = PAYLOAD + '# public note ' + chr(code) + '\n'
            pattern = f'forbidden raw character U\\+{code:04X}'
            with self.subTest(code=f'U+{code:04X}', reader='catalog'):
                with self.assertRaisesRegex(ValueError, pattern):
                    generate_catalog.read_rules(text)
            with self.subTest(code=f'U+{code:04X}', reader='domain'):
                with patch.object(Path, 'read_text', return_value=text):
                    with self.assertRaisesRegex(ValueError, pattern):
                        siri_ai.entries(Path('ruleset/Public.yaml'))
            if not 0xD800 <= code <= 0xDFFF:
                with self.subTest(code=f'U+{code:04X}', reader='sync'):
                    with self.assertRaisesRegex(ValueError, pattern):
                        sync.validate('Public', text.encode('utf-8'))

    def test_pyyaml_independently_rejects_splitlines_hidden_characters(self):
        for code in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E):
            text = PAYLOAD + '# public note ' + chr(code) + '\n'
            with self.subTest(code=f'U+{code:04X}'):
                self.assertNotIn(chr(code), ''.join(text.splitlines()))
                with self.assertRaises(yaml.YAMLError):
                    yaml.safe_load(text)

    def test_diagnostic_contains_only_codepoint_and_position(self):
        prefix = PAYLOAD + '# public diagnostic canary '
        with self.assertRaises(ValueError) as result:
            validate_yaml_characters(prefix + chr(0x0B))
        self.assertEqual(str(result.exception),
                         f'YAML payload contains a forbidden raw character U+000B at character {len(prefix) + 1}')
        self.assertNotIn('canary', str(result.exception))

    def test_escaped_text_is_not_a_raw_control_character(self):
        text = PAYLOAD + r'# literal \x0b and \u000b' + '\n'
        self.assertIsNone(validate_yaml_characters(text))
        self.assertEqual(generate_catalog.read_rules(text), RULES)

    def test_utf8_decoding_stays_strict(self):
        for data in (PAYLOAD.encode() + b'#\xff\n', PAYLOAD.encode() + b'#\xed\xa0\x80\n'):
            with self.subTest(data=data[-5:]):
                with self.assertRaises(UnicodeDecodeError):
                    sync.validate('Public', data)

    def test_config_rules_keep_the_existing_reader(self):
        path = Path('config/rules.yaml')
        with patch.object(siri_ai, 'read_routing_rules', return_value=['existing']) as read, \
                patch.object(siri_ai, 'validate_yaml_characters', side_effect=AssertionError('payload-only gate')):
            self.assertEqual(siri_ai.entries(path), ['existing'])
        read.assert_called_once_with(path)

    def test_surge_normalization_does_not_use_the_yaml_gate(self):
        with patch.object(sync, 'validate_yaml_characters', side_effect=AssertionError('not YAML yet')):
            self.assertEqual(sync.normalize({'source_format': 'surge'}, b'DOMAIN,example.org\n'),
                             b'# Normalized from an upstream Surge ruleset by scripts/sync.py.\npayload:\n  - DOMAIN,example.org\n')


class PayloadCharacterIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('ruleset', 'catalog', 'docs', 'rules', 'research', 'config', 'services'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('README.md', 'sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def snapshot(self):
        return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob('*') if p.is_file()}

    def test_real_generate_rejects_before_any_asset_write(self):
        path = self.root / 'ruleset/Quark.yaml'
        original = path.read_bytes()
        for code in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E):
            with self.subTest(code=f'U+{code:04X}'):
                path.write_bytes(original + b'# public note ' + bytes([code]) + b'\n')
                before = self.snapshot()
                with patch.object(Path, 'write_text', side_effect=AssertionError('must reject before writing')):
                    with self.assertRaisesRegex(ValueError, f'forbidden raw character U\\+{code:04X}'):
                        generate_catalog.generate(self.root, write=True)
                self.assertEqual(before, self.snapshot())

    def test_complete_tree_rejects_hidden_raw_characters(self):
        path = self.root / 'ruleset/Quark.yaml'
        original = path.read_bytes()
        for code in (0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x7F, 0x80, 0x9F, 0xFFFE, 0xFFFF):
            with self.subTest(code=f'U+{code:04X}'):
                path.write_bytes(original + ('# public note ' + chr(code) + '\n').encode('utf-8'))
                with self.assertRaisesRegex(ValueError, f'forbidden raw character U\\+{code:04X}'):
                    validate.validate_tree(self.root)

    def test_valid_unicode_lf_crlf_generate_and_complete_tree(self):
        path = self.root / 'ruleset/Quark.yaml'
        original = path.read_text(encoding='utf-8')
        for newline in ('\n', '\r\n'):
            text = original + '# 公开中文、emoji 📦、NEL ' + chr(0x85) + '\n'
            with self.subTest(newline=repr(newline)), contextlib.redirect_stdout(io.StringIO()):
                path.write_bytes(text.replace('\n', newline).encode('utf-8'))
                self.assertEqual(yaml.safe_load(path.read_bytes())['payload'],
                                 generate_catalog.read_rules(text))
                generate_catalog.generate(self.root, write=True)
                generate_catalog.generate(self.root)
                self.assertEqual(validate.validate_tree(self.root), 0)

    def test_mock_sync_rejects_before_replacing_live_assets(self):
        sources = json.loads((self.root / 'sources.json').read_text(encoding='utf-8'))
        bodies = {s['url']: (self.root / s['path']).read_bytes() for s in sources.values()}
        bodies[sources['Privacy']['url']] += b'# public note ' + bytes([0x0B]) + b'\n'
        before = self.snapshot()

        class Response(io.BytesIO):
            def __init__(self, body, url):
                super().__init__(body)
                self.url = url

            def geturl(self):
                return self.url

        def download(request, timeout):
            return Response(bodies[request.full_url], request.full_url)

        errors = io.StringIO()
        with patch.object(sync, 'ROOT', self.root), \
                patch.object(sync, 'SOURCES_FILE', self.root / 'sources.json'), \
                patch.object(sync, 'LOCAL_RULESETS_FILE', self.root / 'local-rulesets.json'), \
                patch.object(sync, 'LOCK_FILE', self.root / 'sources.lock.json'), \
                patch.object(sys, 'argv', ['sync.py']), \
                patch.object(sync.urllib.request, 'urlopen', side_effect=download) as mocked, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            self.assertEqual(sync.main(), 1)
        self.assertTrue(mocked.called)
        self.assertIn('forbidden raw character U+000B', errors.getvalue())
        self.assertEqual(before, self.snapshot())
        self.assertFalse(list(self.root.glob('proxy-rulesets-*')), 'staging must be cleaned up')


if __name__ == '__main__':
    unittest.main()
