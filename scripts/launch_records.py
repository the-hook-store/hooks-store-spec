#!/usr/bin/env python3
"""Snapshot of IMD's records for every launch made through The Hooks Store (SPEC 7.3, decision 48 item r).

Reads IMD's public launch list, keeps the launches whose request ends with the store's composer
line, and writes evidence/launch-records.json: per launch, IMD's status, its job's state, the
artifacts with their addresses, the seeded pool and a SHA-256 of the request's objective, which
the site matches against the objective it decodes from the Intake's Requested log. The site
fetches this file at load and falls back to it whenever IMD's record plane fails, so Live and
the public rule of 3.1 do not depend on the relay. Standard library only.

Usage: python3 -I scripts/launch_records.py [--file evidence/launch-records.json]
       [--state evidence/launch-records-state.json] [--dry-run] [--limit 200] [--max-reads 60]
"""
import argparse, datetime, hashlib, json, os, re, sys, time, urllib.request, urllib.error

API = os.environ.get('IMD_API', 'https://api.imd.fun')
CHAINS = {1, 4663}
KINDS = {'univ4_hook', 'evm_contracts'}
STORE_ENDING = re.compile(r'Composed with The Hooks Store[^\n]*\.?\s*$')
HEADERS = {'User-Agent': 'hooks-store-launch-records/1 (+https://github.com/the-hook-store/hooks-store-spec)', 'Accept': 'application/json'}

def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')[:200]
            if e.code in (429, 502, 503) or 'busy' in body: time.sleep(5 * (i + 1)); continue
            raise RuntimeError(f'{url}: http {e.code} {body}')
        except Exception:
            if i == tries - 1: raise
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'{url}: still busy after {tries} tries')

def unwrap(d, key):
    return d.get(key) if isinstance(d, dict) and isinstance(d.get(key), dict) else d

def entry_for(rec, job):
    arts = [{'role': a.get('role'), 'name': a.get('name'), 'address': (a.get('address') or '').lower() or None,
             'txHash': a.get('txHash'), 'blockNumber': a.get('blockNumber')} for a in (rec.get('artifacts') or []) if isinstance(a, dict)]
    pools = ((rec.get('seeded') or {}).get('pools') or []) if isinstance(rec.get('seeded'), dict) else []
    objective = job.get('objective') or ''
    return {
        'launchId': rec['id'], 'launchNumber': rec.get('launchNumber'), 'chainId': rec.get('chainId'), 'kind': rec.get('kind'),
        'status': rec.get('status'), 'parkedReason': rec.get('parkedReason'), 'createdAt': rec.get('createdAt'), 'updatedAt': rec.get('updatedAt'),
        'jobId': job.get('id'), 'jobState': job.get('state'), 'blockedReason': job.get('blockedReason'),
        'paidBy': (job.get('paidBy') or rec.get('requester') or '').lower() or None,
        'objectiveSha256': hashlib.sha256(objective.encode('utf-8')).hexdigest(),
        'sourceRepoUrl': rec.get('sourceRepoUrl'), 'sourceCommit': rec.get('sourceCommit'),
        'attested': bool(rec.get('attestation')) and not rec.get('attestationFailure'),
        'artifacts': arts, 'pool': pools[0] if pools else None,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default='evidence/launch-records.json'); ap.add_argument('--state', default='evidence/launch-records-state.json')
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--limit', type=int, default=200); ap.add_argument('--max-reads', type=int, default=60)
    a = ap.parse_args()
    snapshot = json.load(open(a.file)) if os.path.exists(a.file) else {'version': 1, 'generatedAt': None, 'launches': []}
    state = json.load(open(a.state)) if os.path.exists(a.state) else {'checked': {}}
    by_id = {e['launchId']: e for e in snapshot['launches']}
    listing = get_json(f'{API}/launches?limit={a.limit}').get('launches') or []
    reads, changed = 0, []
    for row in listing:
        lid = row.get('id')
        if not lid or row.get('chainId') not in CHAINS or row.get('kind') not in KINDS: continue
        prev = state['checked'].get(lid)
        if prev and prev.get('updatedAt') == row.get('updatedAt') and (prev.get('store') is False or lid in by_id): continue
        if reads >= a.max_reads: break
        reads += 1; time.sleep(0.7)
        try:
            rec = unwrap(get_json(f'{API}/launches/{lid}'), 'launch')
            jobs = rec.get('jobs') or []
            jid = jobs[0].get('id') if jobs and isinstance(jobs[0], dict) else None
            job = unwrap(get_json(f'{API}/jobs/{jid}'), 'job') if jid else {}
            objective = job.get('objective') or (jobs[0].get('objective') if jobs else '') or ''
            store = bool(STORE_ENDING.search(objective))
            state['checked'][lid] = {'updatedAt': row.get('updatedAt'), 'store': store, 'launchNumber': row.get('launchNumber')}
            if store:
                e = entry_for(rec, job); by_id[lid] = e; changed.append(e)
        except Exception as ex:
            print(f"  launch {row.get('launchNumber')}: error {str(ex)[:120]}", file=sys.stderr)
    snapshot['launches'] = sorted(by_id.values(), key=lambda e: e.get('launchNumber') or 0)
    print(f'listed {len(listing)}, read {reads}, store launches {len(snapshot["launches"])}, changed {len(changed)}: ' + ', '.join(f"{e['launchNumber']} {e['status']}/{e['jobState']}" for e in changed))
    if a.dry_run: print('dry run: nothing written'); return
    if changed or snapshot.get('generatedAt') is None:
        snapshot['generatedAt'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        with open(a.file, 'w') as f: json.dump(snapshot, f, indent=2); f.write('\n')
    with open(a.state, 'w') as f: json.dump(state, f, indent=2, sort_keys=True); f.write('\n')

if __name__ == '__main__':
    main()
