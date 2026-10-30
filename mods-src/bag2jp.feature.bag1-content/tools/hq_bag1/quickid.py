import numpy as np, glob, os, sys
sys.path.insert(0,'.')
from match import env, ncc, cd, cde, refine, HOP, SR
for p in sorted(glob.glob('xa/XA*.f32')):
    x=np.fromfile(p,dtype=np.float32); xe=env(x); best=[]
    for t in (3000, 6000, 9000):
        if t+600>len(xe): continue
        seg=xe[t:t+600]
        if np.std(seg)<1e-3: continue
        sc,off,k=max(((*ncc(seg,e),k) for k,e in cde.items()),key=lambda r:r[0])
        fs,fo=refine(x[t*HOP:(t+600)*HOP],cd[k],off*HOP)
        best.append((k,round(sc,2),round(fs,2)))
    print(os.path.basename(p)[:-4], round(len(x)/SR,1), best, flush=True)
