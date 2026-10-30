"""Compact report of a BAG2JP test run started with D:\\Dev\\Tools\\winshot\\bag2_run.ps1.
Waits (up to --timeout s, keep < 170 for one device call; call again to keep waiting) until the game
frame reaches --frame N or the trace matches --until REGEX, then prints a short summary instead of raw logs:
  state (frame, phase, alive), phase timeline, fever anims, crash report, cue ids per phase (-Cues run),
  audio template hits (--find wav... on an -Audio run), and one contact sheet of the run's screenshots.
usage: bag2_report.py --tag T [--frame N | --until 'phase 2/'] [--timeout 160] [--find a.wav ...]
                      [--crop x0,y0,x1,y1 (fractions)] [--cols 4]"""
import argparse, collections, glob, json, os, re, subprocess, sys, time
E = os.path.expanduser('~/mnt/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb')
SHOTS = os.path.expanduser('~/mnt/Dev/Recomp/BAG2JP/_work/shots')
PROBE = os.path.expanduser('~/mnt/Dev/Tools/audio-probe/audio_probe.py')
p = argparse.ArgumentParser()
p.add_argument('--tag', default='run'); p.add_argument('--frame', type=int); p.add_argument('--until')
p.add_argument('--timeout', type=float, default=160); p.add_argument('--find', nargs='*')
p.add_argument('--crop'); p.add_argument('--cols', type=int, default=4); p.add_argument('--max', type=int, default=16)
a = p.parse_args()

def frame_state():
    try:
        s = open(f'{E}/bag2jp_frame.txt').read().split()
        return int(s[0]), s[1], time.time() - os.path.getmtime(f'{E}/bag2jp_frame.txt')
    except Exception: return -1, '?', 1e9

def trace():
    try: return open(f'{E}/bag2jp_anim_trace.log').read().splitlines()
    except Exception: return []

t0 = time.time()
while True:
    f, ph, age = frame_state(); tr = trace()
    done = (a.frame is not None and f >= a.frame) or (a.until and any(re.search(a.until, l) for l in tr[-50:]))
    if not a.frame and not a.until: done = True
    if done or age > 20 or time.time() - t0 > a.timeout: break
    time.sleep(2)
f, ph, age = frame_state()
print(f'state: frame {f} phase {ph} ' + ('(running)' if age < 5 else f'(frame file {age:.0f}s old: game stopped/paused?)')
      + ('' if done else '  [wait condition NOT reached]'))

# phase timeline (a/b only) and fever
tl, last, fever = [], None, collections.OrderedDict()
for l in tr:
    m = re.match(r'f(\d+) mode(\d+) phase (\d+)/(\d+)/\d+ fever(\d+) \| P1 ch(\d+) anim(\d+) req\d+ \| P2 ch(\d+) anim(\d+)', l)
    if not m: continue
    fr, mode, pa, pb, fv = int(m[1]), m[2], m[3], m[4], m[5]
    if int(pa) > 9 or int(pb) > 20: continue
    key = f'{pa}/{pb}' + (f' fever{fv}' if fv != '0' else '')
    if key != last: tl.append(f'{fr}:{key}'); last = key
    if pa == '1' and pb == '7': fever.setdefault(f'P1 anim{m[7]} | P2 anim{m[9]}', fr)
if tl: print('phases: ' + '  '.join(tl[-24:]))
if fever: print('fever anims: ' + '; '.join(f'f{v} {k}' for k, v in fever.items()))

# crash report
rp = f'{E}/psx_last_run_report.json'
if os.path.exists(rp) and time.time() - os.path.getmtime(rp) < 1800:
    try:
        j = json.load(open(rp)); keys = [k for k in ('status', 'reason', 'exception', 'pc', 'func') if k in j]
        print('run report: ' + ', '.join(f'{k}={j[k]}' for k in keys))
    except Exception as e: print('run report unreadable', e)

# cues per phase (watch log of a -Cues run: 8005D3DC + 14 slot ids)
wl = f'{E}/bag2jp_watch.log'
if os.path.exists(wl):
    prev, per = None, collections.defaultdict(collections.Counter)
    for l in open(wl):
        vals = dict(re.findall(r'([0-9A-F]{8})=([0-9A-F]+)', l))
        if '8006D9F6' not in vals: break
        phase = int(vals.get('8005D3DC', '0'), 16)
        cues = [int(v, 16) for k, v in sorted(vals.items()) if k.startswith('8006D')]
        if prev:
            for x, y in zip(prev, cues):
                if x != y and y not in (0, 0xFFFF): per[phase][hex(y)] += 1
        prev = cues
    for ph_, c in sorted(per.items()):
        print(f'cues phase {ph_}: ' + ' '.join(f'{k}x{v}' for k, v in sorted(c.items())))

# audio template search
if a.find and os.path.exists(f'{E}/bag2jp_audio.wav'):
    r = subprocess.run([sys.executable, PROBE, 'find', f'{E}/bag2jp_audio.wav', *a.find, '--sync', f'{E}/bag2jp_audio_sync.log',
                        '--thr', '0.5'], capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip()[-500:])

# contact sheet
d = f'{SHOTS}/{a.tag}'
imgs = sorted(glob.glob(f'{d}/f*.png'))[:a.max]
if imgs:
    from PIL import Image, ImageDraw
    ims = [Image.open(x).convert('RGB') for x in imgs]
    if a.crop:
        x0, y0, x1, y1 = map(float, a.crop.split(','))
        ims = [im.crop((int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1))) for im in ims]
    w, h = ims[0].size; cols = min(a.cols, len(ims)); rows = (len(ims) + cols - 1) // cols
    sheet = Image.new('RGB', (w * cols, h * rows))
    for i, (im, path) in enumerate(zip(ims, imgs)):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
        ImageDraw.Draw(sheet).text(((i % cols) * w + 4, (i // cols) * h + 2), os.path.basename(path)[1:7], fill=(0, 255, 255))
    if sheet.width > 2000: sheet = sheet.resize((2000, int(sheet.height * 2000 / sheet.width)))
    out = f'{SHOTS}/{a.tag}_sheet.png'; sheet.save(out)
    print(f'sheet: {len(imgs)} shots -> D:\\Dev\\Recomp\\BAG2JP\\_work\\shots\\{a.tag}_sheet.png')
    sl = f'{d}/shots.log'
    if os.path.exists(sl): print('shots log: ' + ' | '.join(open(sl).read().split('\n')[-4:]).strip(' |'))
elif os.path.isdir(d): print('no shots yet')
