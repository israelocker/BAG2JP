import os,json,hashlib,csv,struct
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
J=C.text('inputs.bag2jp_assets')
U=C.text('inputs.bag2us_assets')
d=json.load(open('entry_map.json'))
upaths={int(k):v for k,v in d['us_paths'].items()}
def members(base,rel):
    p=os.path.join(base,rel); out={}
    if not os.path.isdir(p): return out
    for dp,dn,fn in os.walk(p):
        for f in fn:
            if f.startswith('_') or f.endswith('.png'): continue
            fp=os.path.join(dp,f); out[os.path.relpath(fp,p)]=fp
    return out
def timinfo(fp):
    b=open(fp,'rb').read()
    try:
        fl=struct.unpack_from('<I',b,4)[0]; o=8; c=''
        if fl&8:
            L,x,y,w,h=struct.unpack_from('<IHHHH',b,o); c=f'clut({x},{y},{w}x{h})'; o+=L
        L,x,y,w,h=struct.unpack_from('<IHHHH',b,o)
        return f'{c} img({x},{y},{w}x{h}) bpp{fl&7}'
    except Exception: return '?'
sha=lambda f: hashlib.sha1(open(f,'rb').read()).hexdigest()
rows=[]
for r in d['map']:
    if r['kind']!='partial' or r['us'] is None or r['score']<0.2: continue
    jm=members(J,r['jp_path']); um=members(U,upaths[r['us']])
    for name,jf in jm.items():
        uf=um.get(name)
        if uf is None: rows.append((r['jp'],r['jp_path'],r['us'],name,'missing in US','')); continue
        if sha(jf)!=sha(uf):
            info=timinfo(jf) if name.endswith('.tim') else ''
            same = (timinfo(uf)==info) if name.endswith('.tim') else ''
            rows.append((r['jp'],r['jp_path'],r['us'],name,f'{os.path.getsize(jf)}/{os.path.getsize(uf)}',f'{info} sameVRAM={same}'))
json.dump(rows,open('member_diff.json','w'),indent=0)
for x in rows: print(*x)
