"""Piecewise map game-time -> CD-time for each in-game song (8 kHz mono analysis)."""
import numpy as np, os, json, sys
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[4]))
from tools.workflow import configured as C  # noqa: E402
sys.path.insert(0, C.text('paths.hq_work'))
SR=8000; HOP=80
from match import env, ncc, cd, cde      # reuse (match.py guarded below)
SONGS={'BUST2_01_ch0':'02','BUST2_01_ch1':'03','BUST2_01_ch2':'07','BUST2_01_ch3':'06','BUST2_01_ch4':'09',
       'BUST2_01_ch5':'04','BUST2_01_ch6':'13','BUST2_01_ch7':'10','BUST2_02_ch0':'05','BUST2_02_ch1':'08',
       'BUST2_02_ch2':'11','BUST2_02_ch3':'12','BUST2_04_ch7':'14'}
def peaks(c,k,sep):
    out=[]; c=c.copy()
    for _ in range(k):
        i=int(np.argmax(c)); out.append(i); c[max(0,i-sep):i+sep]=-9
    return out
def corr_all(seg,sig):
    m=len(seg); N=1<<(len(sig)+m).bit_length()
    c=np.fft.irfft(np.fft.rfft(sig,N)*np.conj(np.fft.rfft(seg,N)),N)[:len(sig)-m+1]
    cs=np.concatenate([[0],np.cumsum(sig**2)]); e=np.sqrt(cs[m:]-cs[:-m])+1e-9
    return c/(e*np.linalg.norm(seg)+1e-9)
def song_map(name,trk):
    x=np.fromfile(C.text('paths.hq_work') + f'/xa/{name}.f32',dtype=np.float32); y=cd[trk]; ye=cde[trk]; xe=env(x)
    WIN,STEP=300,100      # 3 s windows, 1 s step (envelope units)
    cols=[]
    for t in range(0,len(xe)-WIN+1,STEP):
        seg=xe[t:t+WIN]
        if np.std(seg)<1e-3: cols.append((t,[])); continue
        c=corr_all(seg,ye); cand=[]
        for p in peaks(c,6,50):
            lo=max(0,p*HOP-400); s,i=ncc(x[t*HOP:(t+WIN)*HOP],y[lo:lo+WIN*HOP+800])
            if s>0.55: cand.append((s,(lo+i)/SR-t/100))
        cols.append((t,cand))
    # Viterbi over deltas
    INF=1e9; prev=None
    for t,cand in cols:
        if not cand: cand=[(0.0,None)]
        cur=[]
        for s,d in cand:
            if prev is None: cur.append((-s,[d])); continue
            best=min(((ps + (0 if (pd[-1] is None or d is None or abs(pd[-1]-d)<0.01) else 0.8) - s, pd) for ps,pd in prev),key=lambda r:r[0])
            cur.append((best[0],best[1]+[d]))
        prev=cur
    path=min(prev,key=lambda r:r[0])[1]
    # segments
    segs=[]; 
    for (t,cand),d in zip(cols,path):
        ts=t/100
        if segs and d is not None and segs[-1][2] is not None and abs(segs[-1][2]-d)<0.01: segs[-1][1]=ts+1
        else: segs.append([ts,ts+1,d])
    segs[-1][1]=len(x)/SR
    # refine boundaries between consecutive known deltas
    for a,b in zip(segs,segs[1:]):
        if a[2] is None or b[2] is None: continue
        lo=int(max(a[0],b[0]-1.5)*SR); hi=int(min(b[1],b[0]+1.5)*SR)
        blk=160; best=(None,-1)
        errs_a=[];errs_b=[]
        for s0 in range(lo,hi,blk):
            g=x[s0:s0+blk]
            ia=int(s0+a[2]*SR); ib=int(s0+b[2]*SR)
            ea=np.sum((g-y[ia:ia+blk])**2) if 0<=ia and ia+blk<=len(y) else 1e9
            eb=np.sum((g-y[ib:ib+blk])**2) if 0<=ib and ib+blk<=len(y) else 1e9
            errs_a.append(ea); errs_b.append(eb)
        ca=np.cumsum([0]+errs_a); cb=np.cumsum([0]+errs_b)[::-1]
        tot=ca+np.concatenate([np.cumsum(errs_b[::-1])[::-1],[0]])
        k=int(np.argmin(tot)); split=(lo+k*blk)/SR
        a[1]=split; b[0]=split
    cover=sum(e-s for s,e,d in segs if d is not None)/(len(x)/SR)
    return dict(track=trk,duration=len(x)/SR,coverage=round(cover,3),segments=[[round(s,4),round(e,4),None if d is None else round(d,4)] for s,e,d in segs])
if __name__=='__main__':
    out={}
    for n in sys.argv[1:] or SONGS:
        m=song_map(n,SONGS[n]); out[n]=m
        print(n,'track',m['track'],'coverage',m['coverage'],'segments',len(m['segments']),flush=True)
    p=C.text('paths.hq_work') + '/segmap.json'; old=json.load(open(p)) if os.path.exists(p) else {}
    old.update(out); json.dump(old,open(p,'w'),indent=1)
