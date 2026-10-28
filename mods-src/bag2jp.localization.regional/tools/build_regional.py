"""Build bag2jp.localization.regional: one Launcher choice (japanese/international) per group.

Each run applies a set of groups to a pristine copy of the JP asset tree, calls the toolkit's
make-mod, and the resulting disc_user overlays are split per BUST2.BIN entry. Entries touched
by several groups get one overlay per non-japanese combination (when = {...} on every group)."""
import csv, hashlib, itertools, json, os, shutil, struct, subprocess, sys
sys.path.insert(0, os.path.expanduser('~/work/regional'))
import groups as G

HOME = os.path.expanduser('~')
TREE = f'{HOME}/work/regional/tree'
JSRC = f'{HOME}/mnt/Dev/Recomp/BAG2JP/assets/archive'
TOOLS = f'{HOME}/mnt/Dev/Tools/psx-asset-tools'
CUE = f'{HOME}/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue'
OUT = f'{HOME}/work/regional/out'
BUST2_LBA = 179
GROUPS = ['title_screen', 'boot_logos', 'hiro_icon', 'stage_signs', 'songs']
LABELS = {
    'title_screen': ('Title screen', 'Title logo, side banners and copyright line (international: Bust A Groove 2, (c)2000; also the ranking-screen logo).'),
    'boot_logos': ('Boot logos', 'Enix and Frame Graphics logos at start-up (international: English Frame Graphics logo, Enix (R)).'),
    'hiro_icon': ('Hiro icon', "Hiro's cigarette icon (Japanese) or the I-love-ME icon (international), in every icon strip, character select and his portraits."),
    'songs': ('Songs', 'Kitty-N, Kelly and Shorty themes in Japanese or in English, Comet theme original or re-recorded (international), and the song names on character select.'),
    'stage_signs': ('Stage signs', 'Neon City shop signs, Sushi Planet menu, TV studio standby screen (international versions replace logos that resembled real brands).'),
}
groups = {k: v for k, v in G.groups().items() if k in GROUPS}

_cat_paths = [r['path'] for r in csv.DictReader(open(os.path.join(TREE, 'catalog.csv')))]
def entry_of(rel):
    full = 'archive/' + rel
    return max((p for p in _cat_paths if full.startswith(p + '/')), key=len)

def rehead(us_tim, jp_tim):
    u = bytearray(open(us_tim, 'rb').read()); j = open(jp_tim, 'rb').read()
    fl = struct.unpack_from('<I', u, 4)[0]; o = 8
    if fl & 8:
        L = struct.unpack_from('<I', u, o)[0]
        u[o+4:o+8] = j[o+4:o+8]           # clut x,y from JP
        jl = struct.unpack_from('<I', j, 8)[0]
        o += L; jo = 8 + jl
    else:
        jo = 8
    u[o+4:o+8] = j[jo+4:jo+8]             # image x,y from JP
    return bytes(u)

def transparent(jp_tim, index):
    b = bytearray(open(jp_tim, 'rb').read())
    fl = struct.unpack_from('<I', b, 4)[0]; o = 8
    if fl & 8: o += struct.unpack_from('<I', b, o)[0]
    L = struct.unpack_from('<I', b, o)[0]
    b[o+12:o+L] = bytes([(index << 4) | index]) * (L - 12)
    return bytes(b)

def apply(names):
    touched = []
    for g in names:
        for rel, (kind, *arg) in groups[g]:
            dst = os.path.join(TREE, 'archive', rel); src_jp = os.path.join(JSRC, rel)
            if kind == 'copy': data = open(arg[0], 'rb').read()
            elif kind == 'rehead': data = rehead(arg[0], src_jp)
            elif kind == 'transparent': data = transparent(src_jp, arg[0])
            open(dst, 'wb').write(data); touched.append(rel)
    return touched

def restore(touched):
    for rel in touched:
        shutil.copyfile(os.path.join(JSRC, rel), os.path.join(TREE, 'archive', rel))

def make_mod(tag):
    out = f'{OUT}/run_{tag}'
    shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    r = subprocess.run([sys.executable, '-m', 'psxassets.cli', 'make-mod', CUE, TREE, out,
                        '--id', 'tmp.run', '--name', 'tmp', '--game-id', 'SLPM-86219'],
                       cwd=TOOLS, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    m = open(f'{out}/tmp.run/1.0.0/manifest.toml').read()
    ovs = []
    for blk in m.split('[[overlay]]')[1:]:
        kv = dict(l.split(' = ', 1) for l in blk.strip().splitlines() if ' = ' in l)
        ovs.append((int(kv['offset']), f"{out}/tmp.run/1.0.0/" + kv['file'].strip('"')))
    return ovs

catalog = list(csv.DictReader(open(os.path.join(TREE, 'catalog.csv'))))
spans = []
for r in catalog:
    s = BUST2_LBA + int(r['offset']) // 2048
    e = BUST2_LBA + (int(r['offset']) + int(r['size']) + 2047) // 2048
    spans.append((s, e, r['path']))

def split(ovs):
    """-> {entry_path: [(sector, bytes)]}"""
    res = {}
    for off, f in ovs:
        data = open(f, 'rb').read(); sec0 = off // 2048
        for i in range(len(data) // 2048):
            sec = sec0 + i
            ent = next((p for s, e, p in spans if s <= sec < e), None)
            if ent is None:
                ent = '__header__'
            res.setdefault(ent, []).append((sec, data[i*2048:(i+1)*2048]))
    return res

# which groups touch each entry
touch = {}
for g in GROUPS:
    for rel, _ in groups[g]:
        touch.setdefault(entry_of(rel), set()).add(g)
shared = {e: sorted(gs) for e, gs in touch.items() if len(gs) > 1}
print('shared entries:', shared)

pieces = []   # (when-dict, entry, [(sector, bytes)])
def run(active, tag, only_entries=None):
    t = apply(active)
    try:
        per = split(make_mod(tag))
    finally:
        restore(t)
    for ent, secs in per.items():
        if ent == '__header__':
            # Only system/011.bpe grows (boot logos, still inside its sector slack): its size
            # field must change. Other runs only shrink 015.bpe; the stock (larger) size is kept
            # there, the BPE stream carries its own end offset.
            if active == ['boot_logos']:
                pieces.append(({'boot_logos': 'international'}, ent, secs))
            print(tag, 'header sectors', [x for x, _ in secs], 'kept' if active == ['boot_logos'] else 'dropped')
            continue
        gs = touch.get(ent)
        if gs is None: raise SystemExit(f'unexpected change in {ent}')
        if only_entries is not None and ent not in only_entries: continue
        if only_entries is None and ent in shared: continue
        when = {g: ('international' if g in active else 'japanese') for g in sorted(gs)}
        pieces.append((when, ent, secs))

for g in GROUPS:                       # single-group entries, one run per group
    run([g], g)
for ent, gs in shared.items():         # every non-japanese combination of a shared entry
    for k in range(1, len(gs) + 1):
        for combo in itertools.combinations(gs, k):
            run(list(combo), 'x_' + '_'.join(combo), only_entries={ent})

# write the package
PKG = f'{OUT}/bag2jp.localization.regional/1.0.0'
shutil.rmtree(f'{OUT}/bag2jp.localization.regional', ignore_errors=True); os.makedirs(f'{PKG}/payload')
import hashlib
stock_manifest = open(f'{OUT}/run_title_screen/tmp.run/1.0.0/manifest.toml').read()
disc_sha = [l for l in stock_manifest.splitlines() if l.startswith('disc_sha256')][0]
L = ['format_version = 11', 'id = "bag2jp.localization.regional"', 'version = "1.0.0"',
     'name = "Regional content"', 'author = "BAG2JP"',
     'description = "Choose the Japanese or the international (Bust A Groove 2, SLUS-01159) version of each localized element."',
     'resolver = "declarative"', '', '[[target]]', 'game_id = "SLPM-86219"', disc_sha, '',
     '[[feature]]', 'id = "regional"', 'name = "Regional content (JP / International)"',
     'description = "One choice per element. Changes apply the next time the game loads that screen or stage."',
     'group = "Localization"', 'default_enabled = true', '']
for g in GROUPS:
    lab, desc = LABELS[g]
    L += ['[[option]]', 'feature = "regional"', f'id = "{g}"', f'label = "{lab}"', f'description = "{desc}"',
          'type = "choice"', 'default = "international"', '',
          '[[option.choice]]', 'value = "japanese"', 'label = "Japanese"', '',
          '[[option.choice]]', 'value = "international"', 'label = "International"', '']
sys.path.insert(0, TOOLS)
from psxassets import disc as D
_disc = D.Disc(CUE)
def stock_sha(sec, count):
    return hashlib.sha256(_disc.read_user(sec, count)).hexdigest()
n = 0
for when, ent, secs in pieces:
    secs.sort()
    runs = []                         # contiguous runs
    for sec, b in secs:
        if runs and runs[-1][0] + len(runs[-1][1]) // 2048 == sec: runs[-1][1].extend(b)
        else: runs.append([sec, bytearray(b)])
    for sec, data in runs:
        n += 1
        fn = f'payload/{n:03d}_{sec:07d}.bin'
        open(f'{PKG}/{fn}', 'wb').write(data)
        cond = ', '.join(f'{k} = "{v}"' for k, v in when.items())
        L += ['[[overlay]]', 'feature = "regional"', 'target = "disc_user"', f'offset = {sec * 2048}',
              f'file = "{fn}"', f'sha256 = "{hashlib.sha256(data).hexdigest()}"',
              f'expected_sha256 = "{stock_sha(sec, len(data)//2048)}"', f'when = {{ {cond} }}', '']
open(f'{PKG}/manifest.toml', 'w').write('\n'.join(L))
print('overlays', n, 'pieces', len(pieces))

import build_xa
print('xa overlays', build_xa.append(PKG))
import build_buttons
print("buttons overlay sector", build_buttons.append(PKG))
import build_vs_option
print("vs screen", build_vs_option.append(PKG))
