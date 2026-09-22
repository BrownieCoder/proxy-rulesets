#!/usr/bin/env python3
"""Explicit online GET verification of public install URLs; never syncs rules."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(item: tuple[str, str, str | None]) -> dict:
    url, kind, expected_hash = item
    record = {'url': url, 'kind': kind}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'proxy-rulesets-install-link-check/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            record.update(status=response.status, sha256=hashlib.sha256(data).hexdigest())
            if expected_hash:
                record['matchesLocal'] = record['sha256'] == expected_hash
    except urllib.error.HTTPError as error:
        record['status'] = error.code
    except (urllib.error.URLError, TimeoutError) as error:
        record.update(status=0, error=type(error).__name__)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='save public URL/status/hash evidence locally')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'install/catalog.json').read_text())
    items = []
    for service in catalog['services']:
        data = (ROOT / service['path']).read_bytes()
        items.append((service['rawUrl'], 'existing-provider', hashlib.sha256(data).hexdigest()))
        module = service['module']
        if module:
            data = (ROOT / module['path']).read_bytes()
            items.append((module['rawUrl'], 'module', hashlib.sha256(data).hexdigest()))
    items.append(('https://browniecoder.github.io/proxy-rulesets/install/', 'site', None))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, items))
    report = {'checkedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'method': 'GET', 'results': results}
    if args.record:
        (ROOT / 'catalog/online-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for r in results:
        print(f'{r["status"]} {r["kind"]} {r["url"]}' + (' [local bytes differ]' if r.get('matchesLocal') is False else ''))
    existing_ok = all(r['status'] == 200 and r.get('matchesLocal') for r in results if r['kind'] == 'existing-provider')
    pending = any(r['status'] != 200 or r.get('matchesLocal') is False for r in results)
    print('Existing providers: ' + ('PASS' if existing_ok else 'FAILED'))
    print('All public install endpoints: ' + ('NOT READY (unpublished or mismatched endpoints)' if pending else 'PASS'))
    return 1 if pending else 0


if __name__ == '__main__':
    raise SystemExit(main())
