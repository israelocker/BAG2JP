import os, hashlib, json, sys
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
J=C.text('inputs.bag2jp_assets') + '/archive'
U=C.text('inputs.bag2us_assets') + '/archive'
def entries(root):
    # top-level archive entries = dirs/files with _container.json at depth matching catalog
    out={}
    import csv
    cat=os.path.join(os.path.dirname(root),'catalog.csv')
    for r in csv.DictReader(open(cat)):
        p=os.path.join(os.path.dirname(root), r['path'])
        files={}
        if os.path.isdir(p):
            for dp,dn,fn in os.walk(p):
                for f in fn:
                    if f.startswith('_') or f.endswith('.png'): continue
                    fp=os.path.join(dp,f)
                    files[os.path.relpath(fp,p)]=hashlib.sha1(open(fp,'rb').read()).hexdigest()
        else:
            for ext in ('','.bin','.dbi','.bpe','.tim','.sedt'):
                if os.path.isfile(p+ext) or os.path.isfile(p):
                    fp=p if os.path.isfile(p) else p+ext
                    files['.']=hashlib.sha1(open(fp,'rb').read()).hexdigest(); break
        out[int(r['index'])]=dict(path=r['path'],sha1=r['sha1'],size=int(r['size']),files=files)
    return out
je=entries(J); ue=entries(U)
res=[]
for ji,j in je.items():
    js=set(j['files'].values())
    best=None
    for ui,u in ue.items():
        if u['sha1']==j['sha1']: best=(ui,1.0,'identical'); break
        us=set(u['files'].values())
        if not js or not us: continue
        sc=len(js&us)/len(js|us)
        if best is None or sc>best[1]: best=(ui,sc,'partial')
    res.append(dict(jp=ji,jp_path=j['path'],us=best[0] if best else None,score=round(best[1],3) if best else 0,kind=best[2] if best else 'none'))
json.dump(dict(map=res,us_paths={i:u['path'] for i,u in ue.items()}),open(C.text('paths.regional_work') + '/entry_map.json','w'),indent=1)
from collections import Counter
print(Counter(r['kind'] for r in res))
for r in res:
    if r['kind']!='identical': print(r['jp'],r['jp_path'],'->',r['us'],ue[r['us']]['path'] if r['us'] is not None else '',r['score'])
