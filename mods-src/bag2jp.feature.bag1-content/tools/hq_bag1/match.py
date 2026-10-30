import numpy as np, os, glob, json
SR=8000; HOP=80   # 100 Hz envelope
xa_dir=os.path.expanduser('~/work/hq_b1/xa'); cd_dir=os.path.expanduser('~/work/hq_b1/cd')
def env(x):
    n=len(x)//HOP; f=x[:n*HOP].reshape(n,HOP)
    # high-passed energy (difference) -> onset-like envelope
    d=np.diff(np.concatenate([[0],x[:n*HOP]])).reshape(n,HOP)
    e=np.log1p(1e3*np.sqrt((d**2).mean(1)))
    e=e-np.convolve(e,np.ones(50)/50,'same'); return e.astype(np.float64)
cd={os.path.basename(p)[:2]: np.fromfile(p,dtype=np.float32) for p in sorted(glob.glob(cd_dir+'/*.f32'))}
cde={k:env(v) for k,v in cd.items()}
def ncc(seg,sig):
    m=len(seg)
    if len(sig)<m: return -1,0
    N=1<<(len(sig)+m).bit_length()
    c=np.fft.irfft(np.fft.rfft(sig,N)*np.conj(np.fft.rfft(seg,N)),N)[:len(sig)-m+1]
    cs=np.concatenate([[0],np.cumsum(sig**2)]); e=np.sqrt(cs[m:]-cs[:-m])+1e-9
    c=c/(e*np.linalg.norm(seg)+1e-9); i=int(np.argmax(c)); return float(c[i]),i
def refine(xseg,trk,coarse):
    lo=max(0,coarse-400); hi=min(len(trk),coarse+len(xseg)+400)
    s,i=ncc(xseg,trk[lo:hi]); return s,(lo+i)
if __name__=='__main__':
    skip={'BUST2_02_ch4','BUST2_02_ch5','BUST2_02_ch6','BUST2_04_ch6'}
    res={}
    for p in sorted(glob.glob(xa_dir+'/*.f32')):
        name=os.path.basename(p)[:-4]
        if name in skip: continue
        x=np.fromfile(p,dtype=np.float32); xe=env(x); dur=len(x)/SR
        rows=[]
        for t in range(0,len(xe)-600,500):          # 6 s windows every 5 s
            seg=xe[t:t+600]
            if np.std(seg)<1e-3: continue
            best=max(((*ncc(seg,e),k) for k,e in cde.items()),key=lambda r:r[0])
            sc,off,k=best
            fs,fo=refine(x[t*HOP:(t+600)*HOP],cd[k],off*HOP)
            rows.append((t/100,k,round(sc,2),round(fs,2),round(fo/SR,4)))
        res[name]=dict(duration=round(dur,2),windows=rows)
        good=[r for r in rows if r[3]>0.6]
        tr=sorted({r[1] for r in good}); dl=sorted({round(r[4]-r[0],2) for r in good})
        print(f"{name} {dur:6.1f}s tracks {tr} fine-min {min([r[3] for r in good],default=0):.2f} delta {dl[:5]}{'...' if len(dl)>5 else ''} ({len(good)}/{len(rows)})",flush=True)
    json.dump(res,open(os.path.expanduser('~/work/hq_b1/match.json'),'w'))
