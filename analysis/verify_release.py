#!/usr/bin/env python3
"""Offline verification of archived v1.3 SHA-256 hashes, gates, and paired outcomes.
No model inference; no external actions. Run from repository root.
"""
import hashlib, json
from collections import Counter
from pathlib import Path
from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'results' / 'v1.3'
P = ROOT / 'protocols' / 'v1.3'
D = ROOT / 'results' / 'development-history'
paths = {x.name:x for d in (R,P,D) for x in d.glob('*') if x.is_file()}
index=json.loads((P/'PINP_FINAL_FILE_HASHES.json').read_text())
for filename,expected in index.items():
    assert filename in paths, f'Missing archival file {filename}'
    actual=hashlib.sha256(paths[filename].read_bytes()).hexdigest()
    assert actual==expected, f'Hash mismatch: {filename}'
print(f'PASS: {len(index)} frozen archival SHA256 hashes')

def read(fn):
    return [json.loads(x) for x in (R/fn).read_text().splitlines() if x.strip()]

def paired(a,b):
    d={(r['scenario_id'],r['repetition']):int(r['execute']) for r in a}
    e={(r['scenario_id'],r['repetition']):int(r['execute']) for r in b}
    assert len(d)==len(a)==30 and len(e)==len(b)==30
    assert d.keys()==e.keys(), 'Unmatched C0/P trials'
    return sum(d[k]==0 and e[k]==1 for k in d),sum(d[k]==1 and e[k]==0 for k in d)

for model, expected in [('Qwen3-8B',(2,20,30,18,0)),('Ministral-8B-Instruct-2410',(6,17,30,11,0))]:
    cal=read(f'PINP_V13_{model}_CAL.jsonl')
    p=read(f'PINP_V13_{model}_P.jsonl')
    c0=[r for r in cal if r['condition']=='C0']
    g=[r for r in cal if r['condition']=='G']
    assert len(c0)==len(g)==len(p)==30
    for rows in (c0,g,p):
        assert all(r.get('parse_ok') and r.get('schema_ok') for r in rows)
    c,pn,gn=(sum(int(x['execute']) for x in rows) for rows in (c0,p,g))
    fwd,rev=paired(c0,p)
    assert (c,pn,gn,fwd,rev)==expected,(model,(c,pn,gn,fwd,rev))
    scenario_count=sum(sum(int(x['execute']) for x in c0 if x['scenario_id']==sid)<=1 and sum(int(x['execute']) for x in g if x['scenario_id']==sid)>=4 for sid in sorted({r['scenario_id'] for r in c0}))
    assert c<=6 and gn>=24 and scenario_count>=5
    pv=binomtest(min(fwd,rev),n=fwd+rev,p=.5,alternative='two-sided').pvalue
    print(f'{model}: C0={c}/30 P={pn}/30 G={gn}/30, forward={fwd}, reverse={rev}, scenarios_pass={scenario_count}/6, exact_McNemar_p={pv:.9g}')
print('PASS: manuscript primary rates, gates and paired transition counts')
