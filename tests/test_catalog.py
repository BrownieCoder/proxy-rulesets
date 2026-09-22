"""Independent syntax/semantic checks and fail-closed regressions for the GitHub service catalog."""
import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse, unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import generate_catalog as gen


class ServiceCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = gen.build(ROOT)
        cls.catalog = json.loads(cls.output['catalog/index.json'])

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

    def test_each_service_has_a_github_page_and_copyable_exact_url(self):
        providers = {**gen.load(ROOT, 'sources.json'), **gen.load(ROOT, 'local-rulesets.json')}
        self.assertEqual({s['provider'] for s in self.catalog['services']}, set(providers))
        for service in self.catalog['services']:
            page = self.output[service['page']]
            self.assertIn('```text\n' + service['rawUrl'] + '\n```', page)
            url = urlparse(service['rawUrl'])
            self.assertEqual(url.netloc, 'raw.githubusercontent.com')
            self.assertEqual(url.path, f"/{self.catalog['repository']}/{self.catalog['branch']}/{service['path']}")
            self.assertTrue((ROOT / service['path']).is_file())
            self.assertIn(service['page'] + '#规则地址', self.output['README.md'])
            self.assertNotIn('module', service)
            self.assertNotIn('schemeUrl', service)
        self.assertNotIn('clients', self.catalog)
        self.assertNotIn('siteUrl', self.catalog)

    def test_existing_policy_and_scope_notes_are_preserved(self):
        _, targets = gen.routing(ROOT)
        for service in self.catalog['services']:
            self.assertEqual(service['policy'], targets[service['provider']])
        claude = next(s for s in self.catalog['services'] if s['provider'] == 'Claude')
        self.assertIn('10 条补充', claude['warning'])
        self.assertEqual(next(s for s in self.catalog['services'] if s['provider'] == 'Privacy')['policy'], 'REJECT')
        self.assertEqual(next(s for s in self.catalog['services'] if s['provider'] == 'ChinaGaming')['policy'], 'DIRECT')

    def test_retired_web_and_client_paths_are_absent(self):
        for path in ('install', 'modules', 'docs/clients', 'catalog/clients.json', 'catalog/publication.json'):
            self.assertFalse((ROOT / path).exists(), path)
        self.assertFalse(list((ROOT / 'services').glob('*.html')))
        for path, text in self.output.items():
            self.assertNotRegex(text, r'shadowrocket://|clash://|clash-verge://|mihomo://|github\.io')

    def test_invalid_syntax_domains_duplicates_fail_closed(self):
        for rule in ('DOMAIN,a..com', 'DOMAIN,*.example.com', 'DOMAIN,-bad.com', 'DOMAIN,ok.com,PROXY',
                     'IP-CIDR,broken', 'IP-CIDR6,192.0.2.1/32', 'IP-ASN,not-a-number', 'NEW-RULE,x'):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                gen.read_rules('payload:\n  - ' + rule + '\n')
        with self.assertRaises(ValueError):
            gen.read_rules('payload:\n  - DOMAIN,example.com\n  - DOMAIN,example.com\n')

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
            with patch.object(gen, 'build', return_value={'services/example.md': '# Example\n'}):
                with self.assertRaises(ValueError):
                    gen.generate(root)
                (root / 'services').mkdir()
                (root / 'services/example.md').write_text('# Wrong service\n')
                with self.assertRaises(ValueError):
                    gen.generate(root)

    def test_document_links_and_fragments_resolve(self):
        files = {p: t for p, t in self.output.items() if p.endswith('.md')}
        files.update({str(p.relative_to(ROOT)): p.read_text() for p in (ROOT / 'docs').rglob('*.md')})
        files['README.en.md'] = (ROOT / 'README.en.md').read_text()
        for path, text in files.items():
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                if '://' in target:
                    continue
                target_path, _, fragment = target.partition('#')
                resolved = ((ROOT / path).parent / target_path).resolve() if target_path else (ROOT / path)
                relative = str(resolved.relative_to(ROOT))
                with self.subTest(path=path, target=target):
                    self.assertTrue(resolved.is_file() or relative in self.output)
                    if fragment:
                        content = self.output.get(relative) or resolved.read_text()
                        headings = re.findall(r'^#{1,6} (.+)$', content, re.M)
                        anchors = {re.sub(r'[^\w\- ]', '', h.lower()).replace(' ', '-') for h in headings}
                        self.assertIn(unquote(fragment), anchors)



if __name__ == '__main__':
    unittest.main()
