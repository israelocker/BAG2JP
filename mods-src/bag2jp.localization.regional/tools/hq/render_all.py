"""Pre-render every in-game song in CD quality, aligned to the game's XA timeline.
Output: music_hq/<XA>_ch<N>.flac (44.1 kHz stereo 16-bit). Unmapped blocks = the game's own XA audio
(decoded at full rate). Same interpolation/crossfade model as render.py."""
import numpy as np, os, json, subprocess, sys
sys.path.insert(0, os.path.expanduser('~/work/hq'))
import render as R
TOOLS=os.path.expanduser('~/mnt/Dev/Tools/psx-asset-tools'); sys.path.insert(0,TOOLS)
from psxassets import disc as D
OUT=44100
J=D.Disc(os.path.expanduser('~/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue'))
def xa_full(name):
    xaname, ch = name.rsplit('_ch',1); ch=int(ch)
    p=os.path.expanduser(f'~/work/hq/xafull/{name}.f32')
    if not os.path.exists(p):
        f=J.find(f'XA/{xaname}.XA'); raw=J.read_raw(f.lba,f.size//2048)
        part=b''.join(raw[i:i+2352] for i in range(0,len(raw),2352) if raw[i+18]&4 and raw[i+17]==ch)
        src=os.path.expanduser(f'~/work/hq/xafull/{name}.xa'); open(src,'wb').write(part)
        subprocess.run(['ffmpeg','-y','-v','error','-f','psxstr','-i',src,'-vn','-ac','2','-ar',str(OUT),'-f','f32le',p])
    return np.fromfile(p,dtype=np.float32).reshape(-1,2)
def run(names):
    for name in names:
        R_xa=xa_full(name)
        R.load_xa_override=R_xa
        out=R.render(name, xa_override=R_xa)
        n=len(R_xa)
        if len(out)<n: out=np.concatenate([out,R_xa[len(out):n]])     # tail shorter than a block
        tmp=os.path.expanduser('~/work/hq/_r.f32'); np.clip(out,-1,1).astype(np.float32).tofile(tmp)
        dst=os.path.expanduser(f'~/work/hq/music_hq/{name}.flac')
        subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(OUT),'-ac','2','-i',tmp,'-sample_fmt','s16','-compression_level','8',dst])
        print(name, round(n/OUT,2),'s ->', os.path.getsize(dst)//1024,'KB', flush=True)
if __name__=='__main__':
    run(sys.argv[1:] or list(R.bm))
