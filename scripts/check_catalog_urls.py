#!/usr/bin/env python3
"""Explicit online GET verification of public rule URLs; never syncs rules."""
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
        request = urllib.request.Request(url, headers={'User-Agent': 'proxy-rulesets-catalog-link-check/1.0'})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            record.update(status=response.status, sha256=hashlib.sha256(data).hexdigest())
            if expected_hash:
                record['snapshotSha256AtCheck'] = expected_hash
                record['matchesSnapshotAtCheck'] = record['sha256'] == expected_hash
    except urllib.error.HTTPError as error:
        record['status'] = error.code
    except (urllib.error.URLError, TimeoutError) as error:
        record.update(status=0, error=type(error).__name__)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='save public URL/status/hash evidence locally')
    args = parser.parse_args()
    catalog = json.loads((ROOT / 'catalog/index.json').read_text())
    items = []
    for service in catalog['services']:
        data = (ROOT / service['path']).read_bytes()
        items.append((service['rawUrl'], 'existing-provider', hashlib.sha256(data).hexdigest()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(check, items))
    report = {'checkedAt': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'method': 'GET', 'scope': 'Response hashes compared with the local snapshot at checkedAt only; not a claim about later snapshots.', 'results': results}
    if args.record:
        (ROOT / 'catalog/online-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for r in results:
        print(f'{r["status"]} {r["kind"]} {r["url"]}' + (' [local bytes differ]' if r.get('matchesSnapshotAtCheck') is False else ''))
    ok = bool(results) and all(r['status'] == 200 and r.get('matchesSnapshotAtCheck') for r in results)
    print('Public rule URLs: ' + ('PASS' if ok else 'FAILED'))
    return 0 if ok else 1



if __name__ == '__main__':
    raise SystemExit(main())
