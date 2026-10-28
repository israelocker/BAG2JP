"""Offline render following blockmap.json, same model as the runtime plugin:
- anchors every 100 ms (CD time per game block); between consecutive anchors whose spacing is
  ~100 ms (+-5 ms) the CD position is interpolated linearly (absorbs the drift, no clicks);
- other transitions (splices, unmapped<->mapped) switch source with a 5 ms crossfade;
- unmapped blocks play the game's own audio."""
import numpy as np, os, json, subprocess, sys
OUT=44100
bm=json.load(open(os.path.expanduser('~/work/hq/blockmap.json')))
CDDIR=os.path.expanduser('~/mnt/Dev/Recomp/BAG2JP/assets/music_cd/Bust a Move 2')
flacs=sorted(f for f in os.listdir(CDDIR) if f.endswith('.flac'))
def load(cmd): return np.frombuffer(subprocess.run(cmd,capture_output=True).stdout,dtype=np.float32).reshape(-1,2)
def plan(m):
    """per-block (cd_start_sec, cd_end_sec) or None, and level."""
    blocks=m['blocks']; gs=np.array([g for t,g in blocks if t is not None and g>0]); med=float(np.median(gs))
    P=[]
    for b,(t,g) in enumerate(blocks):
        if t is None: P.append(None); continue
        nxt=blocks[b+1][0] if b+1<len(blocks) else None
        end=nxt if (nxt is not None and abs(nxt-t-0.1)<0.005) else t+0.1
        lvl=med*min(1.0,(g/med) if g>0 else 1.0)
        P.append((t,end,lvl))
    return P,med
def render(name, xa_override=None):
    m=bm[name]; trk=flacs[int(m['track'])-1]
    y=load(['ffmpeg','-v','error','-i',os.path.join(CDDIR,trk),'-f','f32le','-ac','2','-ar',str(OUT),'-'])
    xa=xa_override if xa_override is not None else load(['ffmpeg','-v','error','-f','f32le','-ar','8000','-ac','1','-i',os.path.expanduser(f'~/work/hq/xa/{name}.f32'),'-f','f32le','-ac','2','-ar',str(OUT),'-'])
    P,med=plan(m); bs=int(0.1*OUT); n=min(len(xa),len(P)*bs); out=np.zeros((n,2),np.float32)
    X=5*OUT//1000
    for b,p in enumerate(P):
        s=b*bs; e=min(n,s+bs)
        if s>=n: break
        if p is None: seg=xa[s:e]
        else:
            t0,t1,lvl=p; pos=np.linspace(t0*OUT,t1*OUT,e-s,endpoint=False)
            i=np.floor(pos).astype(int); f=(pos-i)[:,None]
            ok=i+1<len(y); i=np.clip(i,0,len(y)-2)
            seg=(y[i]*(1-f)+y[i+1]*f)*lvl; seg[~ok]=0
        out[s:e]=seg
        # crossfade into this block if the previous block was a different source / a jump
        if b>0:
            q=P[b-1]
            jump= (p is None)!=(q is None) or (p is not None and q is not None and abs(q[1]-p[0])>0.0005)
            if jump and s>=X:
                prev_tail=out[s-X:s].copy(); w=np.linspace(0,1,X)[:,None]
                # extend previous source into this block for X samples and fade
                if q is None: ext=xa[s:s+X]
                else:
                    pos=q[1]*OUT+np.arange(X); i=np.clip(pos.astype(int),0,len(y)-1); ext=y[i]*q[2]
                out[s:s+X]=ext*(1-w)+out[s:s+X]*w
    return out
def check(name,out):
    x=np.fromfile(os.path.expanduser(f'~/work/hq/xa/{name}.f32'),dtype=np.float32)
    r=subprocess.run(['ffmpeg','-v','error','-f','f32le','-ar','44100','-ac','2','-i','-','-ac','1','-ar','8000','-f','f32le','-'],input=out.tobytes(),capture_output=True).stdout
    z=np.frombuffer(r,dtype=np.float32); n=min(len(x),len(z)); sc=[]
    for k in range(0,n-8000,8000):
        a=x[k:k+8000]; b=z[k:k+8000]; d=np.linalg.norm(a)*np.linalg.norm(b)
        if d>1e-3: sc.append(float(np.dot(a,b)/d))
    sc=np.array(sc); return float(np.median(sc)), float(np.percentile(sc,5)), int((sc<0.5).sum()), len(sc)
if __name__=='__main__':
    for name,label in (('BUST2_01_ch2','comet_magic_tower'),('BUST2_01_ch0','heat_the_heat_is_on')):
        out=render(name)
        print(name,'1-s windows vs game audio: median corr %.3f, 5th pct %.3f, bad %d/%d'%check(name,out),flush=True)
        tmp=os.path.expanduser('~/work/hq/_render.f32'); out.tofile(tmp)
        subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(OUT),'-ac','2','-i',tmp,'-c:a','libmp3lame','-q:a','2',os.path.expanduser(f'~/mnt/Dev/Recomp/BAG2JP/_work/hq_preview_{label}.mp3')])
