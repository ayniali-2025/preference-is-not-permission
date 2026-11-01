# Extracted without modification from original Colab cell 26 (zero-based).
# IMPORTANT: Requires state initialized in preceding notebook cells; not standalone.

"""
PINP publication assets - Colab-safe final generator.

Creates vector PDF figures, 600-dpi PNG previews, same-basename CSV data,
analysis tables, a ZIP archive, and (when run in Google Colab) triggers a
browser download of the ZIP.

Preferred data source: frozen v1.3 Qwen/Ministral JSONL files in /content or
latest /content/drive/MyDrive/PINP_FINAL_BACKUP_*/ folder.
Fallback: pinp_cross_model_transcript.txt beside this script or in /content.
"""
from pathlib import Path
import hashlib, json, math, re, shutil, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
from matplotlib.patches import FancyBboxPatch, Rectangle
from scipy.stats import binomtest

ROOT = Path('/content/PINP_IEEE_DETAILED_FINAL') if Path('/content').exists() else Path(__file__).resolve().parent
FIG = ROOT / 'figures'; TAB = ROOT / 'tables'
FIG.mkdir(parents=True, exist_ok=True); TAB.mkdir(parents=True, exist_ok=True)

MODELS = ['Qwen3-8B','Ministral-8B-Instruct-2410']
CONDS = ['C0','P','G']
SCENS = [f'CAL0{i}' for i in range(1,7)]
DOMAINS = {'CAL01':'Email','CAL02':'Calendar','CAL03':'Files','CAL04':'Document sharing','CAL05':'Backup','CAL06':'Sandbox finance'}
SOURCES = {
 'Qwen3-8B': {'CAL':'PINP_V13_Qwen3-8B_CAL.jsonl','P':'PINP_V13_Qwen3-8B_P.jsonl'},
 'Ministral-8B-Instruct-2410': {'CAL':'PINP_V13_Ministral-8B-Instruct-2410_CAL.jsonl','P':'PINP_V13_Ministral-8B-Instruct-2410_P.jsonl'}
}

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def find_file(name):
    candidates=[Path('/content')/name, ROOT/name, Path.cwd()/name]
    if '__file__' in globals(): candidates.append(Path(__file__).resolve().parent/name)
    for p in candidates:
        if p.exists(): return p
    drive=Path('/content/drive/MyDrive')
    if drive.exists():
        hits=sorted(drive.glob(f'PINP_FINAL_BACKUP_*/{name}'), key=lambda x:x.stat().st_mtime, reverse=True)
        if hits: return hits[0]
    return None

def wilson(k,n,z=1.959963984540054):
    p=k/n; den=1+z*z/n
    ctr=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return ctr-half, ctr+half

def savefig(fig,stem):
    fig.savefig(FIG/f'{stem}.pdf',bbox_inches='tight')
    fig.savefig(FIG/f'{stem}.png',dpi=600,bbox_inches='tight')
    plt.close(fig)

# ---------------- Load frozen runs ----------------
rows=[]; provenance=[]
for model in MODELS:
    for phase,name in SOURCES[model].items():
        p=find_file(name)
        if p:
            provenance.append({'artifact':name,'model':model,'phase':phase,'path':str(p),'sha256':sha256_file(p)})
            with open(p,encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    r=json.loads(line)
                    rows.append({'model':model,'run_id':r['run_id'],'scenario':r.get('scenario_id') or re.search(r'CAL\d+',r['run_id']).group(0),
                                 'condition':r['condition'],'repetition':int(r['repetition']),'seed':r.get('seed'),
                                 'outcome':r['outcome'],'execute':int(r['execute']),'parse_ok':bool(r.get('parse_ok',True)),
                                 'schema_ok':bool(r.get('schema_ok',True))})

if len(rows)!=180:
    rows=[]
    tr=find_file('pinp_cross_model_transcript.txt')
    if tr is None: raise FileNotFoundError('Frozen JSONLs not found and transcript fallback is unavailable.')
    txt=Path(tr).read_text(encoding='utf-8')
    provenance=[{'artifact':Path(tr).name,'model':'cross-model','phase':'transcript-fallback','path':str(tr),'sha256':sha256_file(tr)}]
    sections={}
    starts={'Qwen3-8B':'LOADING: Qwen3-8B','Ministral-8B-Instruct-2410':'LOADING: Ministral-8B-Instruct-2410'}
    qstart=txt.index(starts['Qwen3-8B']); mstart=txt.index(starts['Ministral-8B-Instruct-2410']); fend=txt.index('FINAL CROSS-MODEL SUMMARY')
    sections['Qwen3-8B']=txt[qstart:mstart]; sections['Ministral-8B-Instruct-2410']=txt[mstart:fend]
    pat=re.compile(r'\[(\d+)/(\d+)\]\s+(V13_CAL(\d+)_(C0|G|P)_R(\d+))\s+([A-Z_]+)\s+X=(\d)')
    for model,sec in sections.items():
        for m in pat.finditer(sec):
            rows.append({'model':model,'run_id':m.group(3),'scenario':f'CAL{m.group(4)}','condition':m.group(5),
                         'repetition':int(m.group(6)),'seed':None,'outcome':m.group(7),'execute':int(m.group(8)),
                         'parse_ok':m.group(7)!='PARSE_FAILURE','schema_ok':m.group(7)!='SCHEMA_FAILURE'})

df=pd.DataFrame(rows)
