"""Exercise the real synchronization path with public bytes and mocked networking."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync


class Response(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url
    def geturl(self):
        return self.url


class SyncCatalog(unittest.TestCase):
    def run_sync(self, invalid=False, payload=None, rename_service=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for directory in ('ruleset', 'catalog', 'docs', 'rules', 'research', 'config', 'services'):
                shutil.copytree(ROOT / directory, root / directory)
            for name in ('README.md', 'sources.json', 'local-rulesets.json', 'sources.lock.json'):
                shutil.copyfile(ROOT / name, root / name)
            sources = json.loads((root / 'sources.json').read_text())
            if rename_service:
                metadata = root / 'catalog/services.json'
                catalog = json.loads(metadata.read_text())
                catalog[0]['id'] += '-renamed'
                metadata.write_text(json.dumps(catalog))
            before = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            bodies = {s['url']: (root / s['path']).read_bytes() for s in sources.values()}
            privacy_url = sources['Privacy']['url']
            if payload is not None:
                bodies[privacy_url] = payload
            elif invalid:
                bodies[privacy_url] += b'  - UNREVIEWED-RULE,example.org\n'
            else:
                bodies[privacy_url] = b'# mocked public upstream metadata change\n' + bodies[privacy_url]
            with patch.object(sync, 'ROOT', root), patch.object(sync, 'SOURCES_FILE', root / 'sources.json'), patch.object(sync, 'LOCAL_RULESETS_FILE', root / 'local-rulesets.json'), patch.object(sync, 'LOCK_FILE', root / 'sources.lock.json'), patch.object(sys, 'argv', ['sync.py']), patch.object(sync.urllib.request, 'urlopen', side_effect=lambda request, timeout: Response(bodies[request.full_url], request.full_url)):
                errors = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
                    result = sync.main()
            after = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            if invalid or payload is not None or rename_service:
                self.assertEqual(result, 1)
                self.assertEqual(before, after, 'failed candidate must not modify any live asset')
            else:
                self.assertEqual(result, 0, errors.getvalue())
                self.assertNotEqual(before['catalog/assets.lock.json'], after['catalog/assets.lock.json'])
                self.assertNotEqual(before['sources.lock.json'], after['sources.lock.json'])
                from generate_catalog import generate
                with contextlib.redirect_stdout(io.StringIO()):
                    generate(root)

    def test_invalid_download_preserves_all_existing_assets(self):
        self.run_sync(invalid=True)

    def test_yaml_semantic_changes_preserve_all_existing_assets(self):
        for payload in (
            b'payload:\n  - "DOMAIN-KEYWORD,foo\\nbar"\n',
            b"payload:\n  - 'DOMAIN-KEYWORD,foo''bar'\n",
            b'payload:\n  - PROCESS-NAME,foo: bar\n',
            b'payload:\n  - DOMAIN,example.org\n    - DOMAIN,example.net\n',
        ):
            with self.subTest(payload=payload):
                self.run_sync(payload=payload)

    def test_renamed_service_preserves_all_existing_assets(self):
        self.run_sync(rename_service=True)

    def test_valid_download_updates_derived_assets_together(self):
        self.run_sync(invalid=False)


if __name__ == '__main__':
    unittest.main()
