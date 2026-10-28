"""XA audio options for bag2jp.localization.regional (disc_raw overlays on the JP disc).

announcer: menu narrator XA/BUST2_02.XA ch 4-6 (same interleave on both discs) + title voice
           XA/BUST2_04.XA ch 6.
songs:     XA/BUST2_01.XA ch 2,4,5,7 (Kitty-N, Kelly, Shorty, Comet; US takes are a little shorter).

Channel swap rule: the n-th US sector of a channel goes into the n-th JP slot of that channel;
JP slots left over get silent ADPCM. JP subheaders (incl. the EOF on the last JP slot) and JP
MSF headers are kept, EDC is recomputed for every rewritten sector."""
import hashlib, os, sys
TOOLS = os.path.expanduser('~/mnt/Dev/Tools/psx-asset-tools'); sys.path.insert(0, TOOLS)
from psxassets import disc as D
JCUE = os.path.expanduser('~/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue')
UCUE = os.path.expanduser('~/mnt/Bust A Groove 2 (USA)/ISO/Bust A Groove 2 (USA).cue')
RAW, CHUNK = 2352, 2048

_T = []
for i in range(256):
    c = i
    for _ in range(8): c = (c >> 1) ^ (0xD8018001 if c & 1 else 0)
    _T.append(c)
def edc(sec):
    crc = 0
    for b in sec[16:2348]: crc = _T[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return crc

def sectors(d, f): raw = d.read_raw(f.lba, f.size // 2048); return [bytearray(raw[i:i+RAW]) for i in range(0, len(raw), RAW)]
def slots(secs, ch): return [i for i, s in enumerate(secs) if s[18] & 4 and s[17] == ch]

def channel_swap(J, U, name, chans):
    jf, uf = J.find(name), U.find(name)
    js, us = sectors(J, jf), sectors(U, uf)
    out = [bytearray(s) for s in js]
    end = 0
    for ch in chans:
        jp, up = slots(js, ch), slots(us, ch)
        assert js[jp[0]][19] == us[up[0]][19], f'{name} ch{ch} coding differs'
        for n, i in enumerate(jp):
            s = out[i]
            s[24:2348] = us[up[n]][24:2348] if n < len(up) else bytes(2324)
            s[2348:2352] = edc(s).to_bytes(4, 'little')
        end = max(end, jp[-1] + 1)
    return jf.lba, out[:end], [bytes(s) for s in js[:end]]

def whole_copy(J, U, name):
    jf, uf = J.find(name), U.find(name)
    js, us = sectors(J, jf), sectors(U, uf)
    assert len(js) == len(us)
    out = []
    for a, b in zip(js, us):
        b = bytearray(b); b[12:16] = a[12:16]; out.append(b)
    return jf.lba, out, [bytes(s) for s in js]

def emit(pkg_dir, tag, option, lba, secs, stock):
    entries = []
    for k in range(0, len(secs), CHUNK):
        part = b''.join(bytes(s) for s in secs[k:k+CHUNK]); st = b''.join(stock[k:k+CHUNK])
        if part == st: continue
        fn = f'payload/xa_{tag}_{lba + k:07d}.bin'
        open(f'{pkg_dir}/{fn}', 'wb').write(part)
        entries.append('\n'.join(['[[overlay]]', 'feature = "regional"', 'target = "disc_raw"',
            f'offset = {(lba + k) * RAW}', f'file = "{fn}"', f'sha256 = "{hashlib.sha256(part).hexdigest()}"',
            f'expected_sha256 = "{hashlib.sha256(st).hexdigest()}"', f'when = {{ {option} = "international" }}', '']))
    return entries

ANNOUNCER_OPTION = '\n'.join(['[[option]]', 'feature = "regional"', 'id = "announcer"', 'label = "Announcer voice"',
    'description = "Menu narrator and title voice: DJ Dangerous (Japanese release) or DJ Mix Deadly (international)."',
    'type = "choice"', 'default = "international"', '',
    '[[option.choice]]', 'value = "japanese"', 'label = "Japanese"', '',
    '[[option.choice]]', 'value = "international"', 'label = "International"', ''])

HQ_BLOCKS = '\n'.join(['[[resource]]', 'feature = "regional"', 'id = "music_hq"', 'label = "CD-quality songs"',
    'description = "Folder with the in-game songs re-built from the original soundtrack CD (FLAC, 44.1 kHz). Used when Songs = CD quality."',
    'format = "directory"', 'default = "music_hq"', 'required = false', '',
    '[[plugin]]', 'feature = "regional"', 'id = "bag2jp.hq_songs"', ''])

def append(pkg_dir):
    os.makedirs(f'{pkg_dir}/payload', exist_ok=True)
    J, U = D.Disc(JCUE), D.Disc(UCUE)
    e = []
    e += emit(pkg_dir, '02', 'announcer', *whole_copy(J, U, 'XA/BUST2_02.XA'))
    e += emit(pkg_dir, '04ch6', 'announcer', *channel_swap(J, U, 'XA/BUST2_04.XA', [6]))
    e += emit(pkg_dir, '01songs', 'songs', *channel_swap(J, U, 'XA/BUST2_01.XA', [2, 4, 5, 7]))
    m = open(f'{pkg_dir}/manifest.toml').read()
    i = m.index('[[overlay]]')
    m = m[:i] + ANNOUNCER_OPTION + '\n' + HQ_BLOCKS + '\n' + m[i:] + '\n' + '\n'.join(e)
    # songs: third choice "cd" (soundtrack CD re-aligned to the in-game edits, plugin bag2jp.hq_songs)
    k = m.index('id = "songs"'); k = m.index('[[option.choice]]\nvalue = "international"', k)
    k = m.index('\n\n', k) + 2
    m = m[:k] + '[[option.choice]]\nvalue = "cd"\nlabel = "CD quality (soundtrack, Japanese vocals)"\n\n' + m[k:]
    open(f'{pkg_dir}/manifest.toml', 'w').write(m)
    # bundle the pre-rendered songs
    import shutil
    src = os.path.expanduser('~/work/hq/music_hq')
    if os.path.isdir(src):
        shutil.copytree(src, f'{pkg_dir}/music_hq', dirs_exist_ok=True)
    return len(e)

if __name__ == '__main__':
    print('xa overlays', append(sys.argv[1]))
