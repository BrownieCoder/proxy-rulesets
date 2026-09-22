"""Independent syntax/semantic checks and fail-closed regressions for installation."""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import generate_install_assets as gen


class InstallAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = gen.build(ROOT)
        cls.catalog = json.loads(cls.output['install/catalog.json'])

    def test_all_yaml_parses_and_provider_metadata_matches(self):
        manifests = {**gen.load(ROOT, 'sources.json'), **gen.load(ROOT, 'local-rulesets.json')}
        # Use PyYAML's independent parser, not the generator's line parser.
        loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
        for name, record in manifests.items():
            with self.subTest(name=name):
                text = (ROOT / record['path']).read_text()
                parsed = yaml.load(text, Loader=loader)
                self.assertEqual(set(parsed), {'payload'})
                self.assertEqual(parsed['payload'], gen.read_rules(text))
        for path in ('config/rule-providers.local.yaml', 'config/rule-providers.remote.yaml'):
            providers = yaml.load(self.output[path], Loader=loader)['rule-providers']
            self.assertEqual(set(providers), set(manifests))
            for name, record in providers.items():
                self.assertEqual(record['behavior'], 'classical')
                expected_type = 'http' if 'remote' in path else 'file'
                self.assertEqual(record['type'], expected_type)
                if expected_type == 'http':
                    self.assertEqual(record['url'].split('/main/')[1], manifests[name]['path'])

    def test_module_has_only_rules_and_exact_ordered_semantics(self):
        module = self.output['modules/privacy.module']
        active = [l for l in module.splitlines() if l and not l.startswith('#')]
        self.assertEqual([l for l in active if l.startswith('[')], ['[Rule]'])
        source = yaml.safe_load((ROOT / 'ruleset/Privacy_No_Resolve.yaml').read_text())['payload']
        decoded = []
        for line in active[1:]:
            fields = line.split(',')
            self.assertEqual(fields[2], 'REJECT')
            decoded.append(','.join(fields[:2] + fields[3:]))
        self.assertEqual(decoded, source)
        self.assertEqual(len(decoded), len(set(decoded)))
        self.assertGreater(len(decoded), 0)
        for forbidden in ('[MITM]', '[Rewrite]', '[Script]', '[Proxy]', '[General]', 'FINAL,', 'MATCH,'):
            self.assertNotIn(forbidden, module)
        self.assertIn('# AUTHOR: blackmatrix7', module)

    def test_catalog_paths_and_url_encoding(self):
        seen = set()
        for service in self.catalog['services']:
            self.assertNotIn(service['id'], seen)
            seen.add(service['id'])
            self.assertIn('services/' + service['id'] + '.md', self.output)
            self.assertTrue((ROOT / service['path']).is_file())
            self.assertEqual(service['rawUrl'].split('/main/')[1], service['path'])
            if service['module']:
                m = service['module']
                self.assertIn(m['path'], self.output)
                parsed = urlparse(m['schemeUrl'])
                self.assertEqual((parsed.scheme, parsed.netloc), ('shadowrocket', 'install'))
                self.assertEqual(parse_qs(parsed.query), {'module': [m['rawUrl']]})
            else:
                self.assertTrue(service['moduleReason'])
        self.assertEqual(len(seen), 28)
        special = 'https://example.org/a b.module?name=中文&version=1'
        self.assertEqual(parse_qs(urlparse(gen.shadowrocket_url(special)).query), {'module': [special]})

    def test_unverified_policies_not_flattened(self):
        modules = [s['provider'] for s in self.catalog['services'] if s['module']]
        self.assertEqual(modules, ['Privacy'])
        for provider in ('ChinaGaming', 'InternationalGaming', 'SiriAI', 'Apple', 'OpenAI', 'Claude', 'Gemini', 'Lan'):
            self.assertIsNone(next(s for s in self.catalog['services'] if s['provider'] == provider)['module'])
        claude = next(s for s in self.catalog['services'] if s['provider'] == 'Claude')
        self.assertIn('10 条补充', claude['warning'])

    def test_invalid_syntax_domains_duplicates_fail_closed(self):
        for rule in ('DOMAIN,a..com', 'DOMAIN,*.example.com', 'DOMAIN,-bad.com', 'DOMAIN,ok.com,PROXY',
                     'IP-CIDR,broken', 'IP-CIDR6,192.0.2.1/32', 'IP-ASN,not-a-number', 'NEW-RULE,x'):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                gen.read_rules('payload:\n  - ' + rule + '\n')
        with self.assertRaises(ValueError):
            gen.read_rules('payload:\n  - DOMAIN,example.com\n  - DOMAIN,example.com\n')
        with self.assertRaises(ValueError):
            gen.module_reason('Privacy', 'PROXY', ['DOMAIN,example.com'])
        with self.assertRaises(ValueError):
            gen.module_reason('Privacy', 'REJECT', ['PROCESS-NAME,example'])

    def test_missing_provider_and_duplicate_metadata_rejected(self):
        original = gen.load
        for mutate in (lambda x: x[0].update(provider='Missing'), lambda x: x.append(x[0])):
            modified = copy.deepcopy(original(ROOT, 'catalog/services.json'))
            mutate(modified)
            with patch.object(gen, 'load', side_effect=lambda r, p: modified if p == 'catalog/services.json' else original(r, p)):
                with self.assertRaises(ValueError):
                    gen.build(ROOT)

    def test_changed_or_missing_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(gen, 'build', return_value={'modules/a.module': '[Rule]\nDOMAIN,example.com,REJECT\n'}):
                with self.assertRaises(ValueError):
                    gen.generate(root)
                (root / 'modules').mkdir()
                (root / 'modules/a.module').write_text('[Rule]\nDOMAIN,example.com,DIRECT\n')
                with self.assertRaises(ValueError):
                    gen.generate(root)

    def test_generated_markdown_relative_links_resolve(self):
        files = {**self.output}
        files.update({str(p.relative_to(ROOT)): p.read_text() for p in (ROOT / 'docs').rglob('*.md')})
        files['README.en.md'] = (ROOT / 'README.en.md').read_text()
        for path, text in files.items():
            if not path.endswith('.md'):
                continue
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                target = target.split('#')[0]
                resolved = (ROOT / path).parent / target
                with self.subTest(path=path, target=target):
                    self.assertTrue(resolved.is_file() or str(resolved.resolve().relative_to(ROOT)) in self.output)


if __name__ == '__main__':
    unittest.main()
