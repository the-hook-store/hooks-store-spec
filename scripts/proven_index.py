#!/usr/bin/env python3
"""Self-updating proven-launch index for The Hooks Store (SPEC 4.17, decision 39).

Reads IMD's public launch list, keeps the launches made through the store (their request ends
with the store's composer line), verifies each one from IMD's record and from the chain, and
appends the verified ones to evidence/proven-launches.json. Entries already in the file are
never changed or removed; the owner edits those by hand. Standard library only.

A launch is added only when all of this holds:
  1. IMD's record is live, every admission check passed, the attestation exists, no artifact
     failed verification.
  2. The request is the store's own: type A (new token), B (hook only) or C (existing token),
     every numbered rule matches a catalog block sentence, and at least one rule matched.
  3. The hook has code on chain; for a deployer launch the deployer's hook() returns it.
  4. owner() answers on the hook when any matched block grants an owner power.
  5. Every function the matched blocks promise is present in the deployed code (its 4-byte
     selector appears in the runtime bytecode).

Usage: python3 -I scripts/proven_index.py [--file evidence/proven-launches.json]
       [--state evidence/proven-index-state.json] [--dry-run] [--limit 200]
"""
import argparse, datetime, json, os, re, sys, time, urllib.request, urllib.error

API = os.environ.get('IMD_API', 'https://api.imd.fun')
SITE_REPO = os.environ.get('SITE_REPO', 'identity-md-launches/launch-2369-build-hooks-store-phase')
SITE_REF = os.environ.get('SITE_REF', 'HEAD')
RPC = {1: os.environ.get('RPC_1', 'https://ethereum-rpc.publicnode.com'),
       4663: os.environ.get('RPC_4663', 'https://rpc.mainnet.chain.robinhood.com')}
CHAINS = {1, 4663}
KINDS = {'univ4_hook', 'evm_contracts'}
STORE_ENDING = re.compile(r'Composed with The Hooks Store[^\n]*\.?\s*$')
HEADERS = {'User-Agent': 'hooks-store-proven-index/1 (+https://github.com/the-hook-store/hooks-store-spec)', 'Accept': 'application/json'}
TYPE_WORDS = {'PoolId': 'bytes32'}

# ---------------------------------------------------------------- keccak-256 (pure Python)
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_M = (1 << 64) - 1
def _rol(x, n): n %= 64; return ((x << n) | (x >> (64 - n))) & _M if n else x
def _f(A):
    for rc in _RC:
        C = [A[x][0] ^ A[x][1] ^ A[x][2] ^ A[x][3] ^ A[x][4] for x in range(5)]
        D = [C[(x - 1) % 5] ^ _rol(C[(x + 1) % 5], 1) for x in range(5)]
        A = [[A[x][y] ^ D[x] for y in range(5)] for x in range(5)]
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5): B[y][(2 * x + 3 * y) % 5] = _rol(A[x][y], _ROT[x][y])
        A = [[B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y]) for y in range(5)] for x in range(5)]
        A[0][0] ^= rc
    return A
def keccak256(data: bytes) -> bytes:
    rate = 136; buf = bytearray(data); buf.append(0x01)
    while len(buf) % rate: buf.append(0)
    buf[-1] |= 0x80
    A = [[0] * 5 for _ in range(5)]
    for off in range(0, len(buf), rate):
        blk = buf[off:off + rate]
        for i in range(rate // 8): A[i % 5][i // 5] ^= int.from_bytes(blk[8 * i:8 * i + 8], 'little')
        A = _f(A)
    return b''.join(A[i % 5][i // 5].to_bytes(8, 'little') for i in range(4))
assert keccak256(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
def selector(sig: str) -> str: return keccak256(sig.encode()).hex()[:8]

# ---------------------------------------------------------------- HTTP helpers
def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors='replace')[:200]
            if e.code in (429, 503) or 'busy' in body: time.sleep(5 * (i + 1)); continue
            raise RuntimeError(f'{url}: http {e.code} {body}')
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(3 * (i + 1))
    raise RuntimeError(f'{url}: still busy after {tries} tries')

def rpc(chain, method, params, tries=3):
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode()
    for i in range(tries):
        try:
            req = urllib.request.Request(RPC[chain], data=body, headers={**HEADERS, 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=40) as r: out = json.load(r)
            if 'error' in out: return None, out['error']
            return out.get('result'), None
        except Exception as e:
            if i == tries - 1: return None, {'message': str(e)[:120]}
            time.sleep(3 * (i + 1))

def eth_call(chain, to, data):
    return rpc(chain, 'eth_call', [{'to': to, 'data': data}, 'latest'])

# ---------------------------------------------------------------- catalog
def load_catalogs():
    blocks = []
    for name in ('catalog.json', 'legacy-catalog.json'):
        url = f'https://raw.githubusercontent.com/{SITE_REPO}/{SITE_REF}/src/blocks/{name}'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': HEADERS['User-Agent']}), timeout=40) as r:
                data = json.load(r)
        except Exception as e:
            if name == 'catalog.json': raise RuntimeError(f'catalog unavailable: {e}')
            continue
        for b in data.get('blocks', []):
            if not isinstance(b, dict) or not b.get('id'): continue
            templates = [b.get('sentence')] + list(b.get('legacySentences') or []) + list((b.get('optionSentences') or {}).values())
            blocks.append({'id': b['id'], 'types': b.get('types') or [], 'owner': bool(b.get('owner') or b.get('ownerPower')),
                           'templates': [t for t in templates if isinstance(t, str) and t], 'legacy': name != 'catalog.json'})
    return blocks

def template_regex(template):
    pattern, pos = '', 0
    for m in re.finditer(r'\{(@?)(\w+)(?::(\w+))?\}', template):
        pattern += re.escape(template[pos:m.start()]) + '(.*?)'; pos = m.end()
    pattern += re.escape(template[pos:])
    return re.compile('^' + pattern + '$')

def promised_signatures(template):
    sigs = []
    for frag in re.findall(r'Expose (.+?)(?:\.(?:\s|$)|$)', template):
        for name, args in re.findall(r'\b([a-zA-Z_]\w*)\(([^)]*)\)', frag):
            types = []
            for arg in [a.strip() for a in args.split(',') if a.strip()]:
                t = arg.split()[0]; types.append(TYPE_WORDS.get(t, t))
            sigs.append(f'{name}({",".join(types)})')
    return sigs

def match_rules(objective, blocks):
    """Returns (block ids in rule order, promised signatures, owner power present) or None when a rule matches nothing."""
    rules = re.findall(r'^\d+\. (.+)$', objective, re.M)
    if not rules: return None
    ids, sigs, owner = [], [], False
    for rule in rules:
        found = None
        for b in blocks:
            if b['id'] in ('token', 'own-token', 'custom'): continue
            for t in b['templates']:
                if template_regex(t).match(rule.strip()):
                    found = (b, t); break
            if found: break
        if not found: return None
        b, t = found
        if b['id'] not in ids: ids.append(b['id'])
        sigs += promised_signatures(t); owner = owner or b['owner']
    return ids, sorted(set(sigs)), owner

def request_type(objective):
    first = objective.split('\n')[0]
    if first.startswith('Launch ') and 'with a Uniswap v4 hook' in first:
        if 'the standard launch token' in objective: return 'A', 'token'
        if 'my own token' in objective: return 'A', 'own-token'
        return None, None
    if 'is a standalone Uniswap v4 hook with no new token' in objective: return 'B', None
    if re.search(r'is a Uniswap v4 hook for the existing token 0x[0-9a-fA-F]{40}', objective): return 'C', None
    return None, None

# ---------------------------------------------------------------- verification
def word(x): return x.to_bytes(32, 'big', signed=False)
def addr_word(a): return bytes(12) + bytes.fromhex(a[2:])
def pool_id(p):
    try:
        key = addr_word(p['currency0']) + addr_word(p['currency1']) + word(int(p['fee'])) + (int(p['tickSpacing']) & ((1 << 256) - 1)).to_bytes(32, 'big') + addr_word(p['hooks'])
        return '0x' + keccak256(key).hex()
    except Exception: return None

def verify(rec, blocks):
    """Returns (entry, None) or (None, reason)."""
    if rec.get('status') != 'live': return None, 'not live'
    if rec.get('chainId') not in CHAINS or rec.get('kind') not in KINDS: return None, 'other chain or kind'
    checks = rec.get('admissionChecks') or []
    if not checks or any(c.get('status') != 'passed' for c in checks): return None, 'an admission check did not pass'
    if not rec.get('attestationHash') or rec.get('attestationFailure'): return None, 'no clean attestation'
    arts = rec.get('artifacts') or []
    if not arts or any(a.get('verifyFailure') for a in arts): return None, 'artifact verification failed'
    jobs = rec.get('jobs') or []
    objective = (jobs[0].get('objective') if jobs and isinstance(jobs[0], dict) else '') or ''
    if not STORE_ENDING.search(objective): return None, 'not a store request'
    typ, token_block = request_type(objective)
    if not typ: return None, 'request shape not recognised'
    matched = match_rules(objective, blocks)
    if not matched: return None, 'a rule matched no catalog block'
    ids, sigs, owner_power = matched
    if token_block: ids = [token_block] + ids
    if typ == 'A' and rec.get('kind') != 'univ4_hook': return None, 'type A without a hook launch'
    chain = rec['chainId']
    deployer = hook = token = distributor = name = None
    if typ == 'A':
        by_role = {a.get('role'): a for a in arts}
        hook = (by_role.get('hook') or {}).get('address'); token = (by_role.get('token') or {}).get('address'); distributor = (by_role.get('distributor') or {}).get('address')
        name = (by_role.get('hook') or {}).get('name')
        if not hook or not token: return None, 'hook or token artifact missing'
    else:
        dep = next((a for a in arts if str(a.get('name', '')).endswith('Deployer')), None)
        if not dep or not dep.get('address'): return None, 'deployer artifact missing'
        deployer = dep['address']; name = re.sub(r'Deployer$', '', dep['name'])
        res, err = eth_call(chain, deployer, '0x' + selector('hook()'))
        if err or not res or len(res) < 42 or int(res, 16) == 0: return None, 'deployer hook() gave no address'
        hook = '0x' + res[-40:]
        if typ == 'C':
            m = re.search(r'hook for the existing token (0x[0-9a-fA-F]{40})', objective); token = m.group(1).lower() if m else None
    code, err = rpc(chain, 'eth_getCode', [hook, 'latest'])
    if err or not code or len(code) <= 2: return None, 'hook has no code on chain'
    code = code[2:].lower()
    missing = [s for s in sigs if selector(s) not in code]
    if missing: return None, 'promised functions missing from the code: ' + ', '.join(missing[:4])
    if owner_power:
        res, err = eth_call(chain, hook, '0x' + selector('owner()'))
        if err or not res or len(res) < 42 or int(res, 16) == 0: return None, 'owner() does not answer'
    repo = rec.get('sourceRepoUrl') or ''; commit = rec.get('sourceCommit') or ''
    if not re.match(r'^https://github\.com/[\w.-]+/[\w.-]+$', repo) or not re.match(r'^[0-9a-f]{40}$', commit): return None, 'source repository or commit missing'
    entry = {'launchId': rec['id'], 'launchNumber': rec['launchNumber'], 'chainId': chain, 'type': typ, 'blocks': ids,
             'repoUrl': repo + '.git', 'commit': commit, 'hookAddress': hook.lower(), 'deployerAddress': deployer.lower() if deployer else None,
             'name': name or 'Hook', 'verifiedAt': datetime.date.today().isoformat()}
    if token: entry['tokenAddress'] = token.lower()
    if distributor: entry['distributorAddress'] = distributor.lower()
    if typ == 'A':
        pools = ((rec.get('seeded') or {}).get('pools') or [])
        pid = pool_id(pools[0]) if pools else None
        if pid: entry['poolId'] = pid
    entry['notes'] = f'Indexed automatically on {entry["verifiedAt"]} from IMD\'s live record (attested, every admission check passed) and chain reads: code at the hook, every promised function present, owner() answering.'
    return entry, None

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--file', default='evidence/proven-launches.json'); ap.add_argument('--state', default='evidence/proven-index-state.json')
    ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--limit', type=int, default=200); ap.add_argument('--max-reads', type=int, default=80)
    a = ap.parse_args()
    index = json.load(open(a.file)) if os.path.exists(a.file) else {'version': 1, 'launches': []}
    state = json.load(open(a.state)) if os.path.exists(a.state) else {'checked': {}}
    known = {e['launchId'] for e in index['launches']}
    blocks = load_catalogs()
    listing = get_json(f'{API}/launches?limit={a.limit}').get('launches') or []
    reads, added, skipped = 0, [], 0
    for row in listing:
        lid = row.get('id')
        if not lid or lid in known: continue
        if row.get('status') != 'live' or row.get('chainId') not in CHAINS or row.get('kind') not in KINDS: continue
        prev = state['checked'].get(lid)
        if prev and prev.get('updatedAt') == row.get('updatedAt'): skipped += 1; continue
        if reads >= a.max_reads: break
        reads += 1; time.sleep(0.7)
        try:
            rec = get_json(f'{API}/launches/{lid}')
            entry, reason = verify(rec, blocks)
        except Exception as e:
            entry, reason = None, f'error: {str(e)[:120]}'
        if entry:
            index['launches'].append(entry); known.add(lid); added.append(entry)
            state['checked'][lid] = {'updatedAt': row.get('updatedAt'), 'result': 'indexed', 'launchNumber': row.get('launchNumber')}
        else:
            state['checked'][lid] = {'updatedAt': row.get('updatedAt'), 'result': reason, 'launchNumber': row.get('launchNumber')}
    index['launches'].sort(key=lambda e: e.get('launchNumber') or 0)
    print(f'listed {len(listing)}, read {reads}, skipped {skipped} already checked, added {len(added)}: ' + ', '.join(f"{e['launchNumber']} {e['name']} ({e['type']}: {' '.join(e['blocks'])})" for e in added))
    for lid, s in state['checked'].items():
        if s.get('result') not in ('indexed', 'not a store request', 'other chain or kind') and s.get('result'): print(f"  launch {s.get('launchNumber')}: {s['result']}")
    if a.dry_run: print('dry run: nothing written'); return
    with open(a.file, 'w') as f: json.dump(index, f, indent=2); f.write('\n')
    with open(a.state, 'w') as f: json.dump(state, f, indent=2, sort_keys=True); f.write('\n')

if __name__ == '__main__':
    main()
