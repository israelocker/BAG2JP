"""Block-level (100 ms) map game->CD: absolute CD time per block + gain; fine local search."""
import numpy as np, os, json, sys
SR=8000; B=800; L=48
cd_dir=os.path.expanduser('~/work/hq_b1/cd')
seg=json.load(open(os.path.expanduser('~/work/hq_b1/segmap.json')))
def local(g,y,center):
    lo=center-L; hi=center+L+B
    if lo<0 or hi>len(y): return -2,None,0
    h=y[lo:hi]; c=np.correlate(h,g,'valid')
    cs=np.concatenate([[0],np.cumsum(h**2)]); e=np.sqrt(cs[B:]-cs[:-B])+1e-9
    n=c/(e*np.linalg.norm(g)+1e-9); i=int(np.argmax(n)); pos=lo+i
    hh=y[pos:pos+B]; gain=float(np.dot(g,hh)/(np.dot(hh,hh)+1e-9))
    return float(n[i]),pos,gain
def blockmap(name):
    m=seg[name]; x=np.fromfile(os.path.expanduser(f'~/work/hq_b1/xa/{name}.f32'),dtype=np.float32)
    y=np.fromfile(f"{cd_dir}/{m['track']}.f32",dtype=np.float32)
    deltas=sorted({s[2] for s in m['segments'] if s[2] is not None})
    nb=len(x)//B; out=[]; prev=None   # prev = CD sample index mapped to previous block start
    for b in range(nb):
        g=x[b*B:(b+1)*B]
        if float(np.dot(g,g))/B<1e-7:
            out.append([None if prev is None else (prev+B)/SR,0.0]); prev=None if prev is None else prev+B; continue
        cands=[]
        if prev is not None: cands.append(('prev',prev+B))
        cands+= [(d,int(round(b*B+d*SR))) for d in deltas]
        best=(-2,None,0,None)
        for tag,center in cands:
            s,pos,gain=local(g,y,center)
            if pos is None: continue
            if tag=='prev': s+=0.05
            if s>best[0]: best=(s,pos,gain,tag)
        if best[0]<0.45: out.append([None,0.0]); prev=None; continue
        out.append([best[1]/SR,round(max(0.0,min(4.0,best[2])),3)]); prev=best[1]
    return m['track'],len(x)/SR,out
if __name__=='__main__':
    res={}
    names=sys.argv[1:] or list(seg)
    p=os.path.expanduser('~/work/hq_b1/blockmap.json'); res=json.load(open(p)) if os.path.exists(p) and sys.argv[1:] else {}
    for n in names:
        trk,dur,out=blockmap(n)
        mapped=sum(1 for t,_ in out if t is not None)
        res[n]=dict(track=trk,duration=dur,block=0.1,blocks=out)
        print(f"{n} track {trk} mapped {mapped}/{len(out)} ({100*mapped/len(out):.1f}%)",flush=True)
    json.dump(res,open(p,'w'))
