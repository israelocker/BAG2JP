"""Compact report of a BAG2JP test run started with the winshot ``bag2_run.ps1`` runner.

Waits (up to --timeout s, keep < 170 for one device call; call again to keep waiting) until the game
frame reaches --frame N or the trace matches --until REGEX, then prints a short summary instead of raw logs:
  state (frame, phase, alive), phase timeline, fever anims, crash report, cue ids per phase (-Cues run),
  audio template hits (--find wav... on an -Audio run), and one contact sheet of the run's screenshots.
usage: bag2_report.py --tag T [--frame N | --until 'phase 2/'] [--timeout 160] [--find a.wav ...]
                      [--crop x0,y0,x1,y1 (fractions)] [--cols 4] [--local-config FILE]

The game directory, shots directory and audio probe are resolved from the shared host
configuration (config/project.toml + the ignored local overlay), never from machine literals.
"""
import argparse
import collections
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Documented usage runs this file by path, so the repo root may be missing from sys.path.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.workflow import project_config

# Aliases keep the resolver patchable in tests; the class is read from its module so a
# reloaded registry still raises the exception type this module catches.
load_config = project_config.load_config
require_paths = project_config.require_paths


def resolve_paths(config: project_config.ProjectConfig, *, need_audio: bool = False
                  ) -> tuple[Path, Path, Path | None]:
    """Return (game directory, shots directory, audio probe) for this run."""
    experimental, = require_paths(config, ("paths.experimental_install",))
    work_root, = require_paths(config, ("paths.work_root",))
    probe = config.values.get("tools.audio_probe")
    if need_audio:
        probe, = require_paths(config, ("tools.audio_probe",))
    return experimental, work_root / "shots", probe


def valid_tag(value: str) -> str:
    """Keep report reads/writes under one named shots directory, never caller paths."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise argparse.ArgumentTypeError("tag: use 1-64 ASCII letters, digits, _ or -")
    return value


def main(argv: list[str] | None = None) -> int:
    """Read a configured run and render its existing compact diagnostic summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', type=valid_tag, default='run'); parser.add_argument('--frame', type=int); parser.add_argument('--until')
    parser.add_argument('--timeout', type=float, default=160); parser.add_argument('--find', nargs='*')
    parser.add_argument('--crop'); parser.add_argument('--cols', type=int, default=4); parser.add_argument('--max', type=int, default=16)
    parser.add_argument('--local-config', type=Path, default=None,
                        help='local TOML overlay; relative selections anchor to the repository')
    a = parser.parse_args(argv)
    try:
        configuration = load_config(local_config=a.local_config)
        E, SHOTS, PROBE = resolve_paths(configuration)
    except project_config.ConfigError as exc:
        print(f'config error: {exc}', file=sys.stderr)
        return 2

    def frame_state():
        try:
            s = (E / 'bag2jp_frame.txt').read_text().split()
            return int(s[0]), s[1], time.time() - os.path.getmtime(f'{E}/bag2jp_frame.txt')
        except (OSError, UnicodeError, ValueError, IndexError): return -1, '?', 1e9

    def trace():
        try: return (E / 'bag2jp_anim_trace.log').read_text().splitlines()
        except (OSError, UnicodeError): return []

    t0 = time.time()
    while True:
        f, ph, age = frame_state(); tr = trace()
        done = (a.frame is not None and f >= a.frame) or (a.until and any(re.search(a.until, l) for l in tr[-50:]))
        if not a.frame and not a.until: done = True
        if done or age > 20 or time.time() - t0 > a.timeout: break
        time.sleep(2)
    f, ph, age = frame_state()
    try:
        # Select optional work after waiting, once, before any output or write.
        search_audio = bool(a.find) and (E / 'bag2jp_audio.wav').is_file()
        if search_audio:
            E, SHOTS, PROBE = resolve_paths(configuration, need_audio=True)
        d = SHOTS / a.tag
        imgs = sorted(d.glob('f*.png'))[:a.max]
        out = None
        if imgs:
            out = project_config.assert_write_target(
                configuration, SHOTS / f'{a.tag}_sheet.png', role='work')
    except project_config.ConfigError as exc:
        print(f'config error: {exc}', file=sys.stderr)
        return 2
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
            j = json.loads(Path(rp).read_text())
            if not isinstance(j, dict):
                raise ValueError('run report must be an object')
            keys = [k for k in ('status', 'reason', 'exception', 'pc', 'func') if k in j]
            print('run report: ' + ', '.join(f'{k}={j[k]}' for k in keys))
        except (OSError, UnicodeError, ValueError) as e: print('run report unreadable', e)

    # cues per phase (watch log of a -Cues run: 8005D3DC + 14 slot ids)
    wl = f'{E}/bag2jp_watch.log'
    if os.path.exists(wl):
        prev, per = None, collections.defaultdict(collections.Counter)
        for l in Path(wl).read_text().splitlines():
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
    if search_audio:
        r = subprocess.run([sys.executable, PROBE, 'find', f'{E}/bag2jp_audio.wav', *a.find, '--sync', f'{E}/bag2jp_audio_sync.log',
                            '--thr', '0.5'], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip()[-500:])

    # contact sheet
    if imgs:
        from PIL import Image, ImageDraw
        ims = []
        for image_path in imgs:
            with Image.open(image_path) as image:
                ims.append(image.convert('RGB'))
        if a.crop:
            x0, y0, x1, y1 = map(float, a.crop.split(','))
            ims = [im.crop((int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1))) for im in ims]
        w, h = ims[0].size; cols = min(a.cols, len(ims)); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (w * cols, h * rows))
        for i, (im, path) in enumerate(zip(ims, imgs)):
            sheet.paste(im, ((i % cols) * w, (i // cols) * h))
            ImageDraw.Draw(sheet).text(((i % cols) * w + 4, (i // cols) * h + 2), os.path.basename(path)[1:7], fill=(0, 255, 255))
        if sheet.width > 2000: sheet = sheet.resize((2000, int(sheet.height * 2000 / sheet.width)))
        sheet.save(out)
        print(f'sheet: {len(imgs)} shots -> {out}')
        sl = f'{d}/shots.log'
        if os.path.exists(sl): print('shots log: ' + ' | '.join(Path(sl).read_text().split('\n')[-4:]).strip(' |'))
    elif os.path.isdir(d): print('no shots yet')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
