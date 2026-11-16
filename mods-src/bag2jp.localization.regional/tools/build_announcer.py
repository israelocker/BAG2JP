"""Announcer option for bag2jp.localization.regional: menu narrator (XA/BUST2_02.XA ch 4-6) and
title voice (XA/BUST2_04.XA ch 6) from the US disc, as disc_raw overlays on the JP disc.

Raw Mode 2 Form 2 sectors are copied with the JP sector header (MSF) so the drive reports JP
positions. _02 has the same interleave on both discs, so whole ranges are copied (channels other
than 4-6 are identical anyway). _04 ch6: the 143 US sectors go into the first JP ch6 slots (JP
subheader kept), the remaining 45 JP ch6 slots become silent ADPCM; other channels untouched."""
import hashlib, os, sys
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
TOOLS = C.text('tools.psx_asset_tools'); sys.path.insert(0, TOOLS)
from psxassets import disc as D
JCUE = C.text('inputs.bag2_cue')
UCUE = C.text('inputs.bag2us_cue')
RAW = 2352
CHUNK = 2048   # sectors per overlay file

def sectors(raw): return [bytearray(raw[i:i+RAW]) for i in range(0, len(raw), RAW)]

def edc_form2(sec):
    # EDC over bytes 16..2347 (CRC32 poly 0xD8018001, reflected), stored little-endian at 2348
    crc = 0
    for b in sec[16:2348]:
        crc ^= b
        for _ in range(8): crc = (crc >> 1) ^ (0xD8018001 if crc & 1 else 0)
    return crc

def build(pkg_dir):
    J, U = D.Disc(JCUE), D.Disc(UCUE)
    out = []
    os.makedirs(f'{pkg_dir}/payload', exist_ok=True)
    def emit(name, jlba, secs, stock):
        for k in range(0, len(secs), CHUNK):
            part = b''.join(bytes(s) for s in secs[k:k+CHUNK])
            st = b''.join(stock[k:k+CHUNK])
            if part == st: continue
            fn = f'payload/xa_{name}_{jlba + k:07d}.bin'
            open(f'{pkg_dir}/{fn}', 'wb').write(part)
            out.append(['[[overlay]]', 'feature = "regional"', 'target = "disc_raw"',
                        f'offset = {(jlba + k) * RAW}', f'file = "{fn}"',
                        f'sha256 = "{hashlib.sha256(part).hexdigest()}"',
                        f'expected_sha256 = "{hashlib.sha256(st).hexdigest()}"',
                        'when = { announcer = "international" }', ''])
    # --- _02: whole file, US data with JP headers
    jf, uf = J.find('XA/BUST2_02.XA'), U.find('XA/BUST2_02.XA')
    js = sectors(J.read_raw(jf.lba, jf.size // 2048)); us = sectors(U.read_raw(uf.lba, uf.size // 2048))
    assert len(js) == len(us)
    secs = []
    for a, b in zip(js, us):
        b = bytearray(b); b[12:16] = a[12:16]; secs.append(b)
    emit('02', jf.lba, secs, [bytes(s) for s in js])
    # --- _04 ch6: title voice
    jf, uf = J.find('XA/BUST2_04.XA'), U.find('XA/BUST2_04.XA')
    js = sectors(J.read_raw(jf.lba, jf.size // 2048)); us = sectors(U.read_raw(uf.lba, uf.size // 2048))
    jpos = [i for i, s in enumerate(js) if s[18] & 4 and s[17] == 6]
    upos = [i for i, s in enumerate(us) if s[18] & 4 and s[17] == 6]
    assert js[jpos[0]][19] == us[upos[0]][19], 'coding info differs'
    last = jpos[-1] + 1
    secs = [bytearray(s) for s in js[:last]]
    for n, jp in enumerate(jpos):
        s = secs[jp]
        if n < len(upos):
            s[24:2348] = us[upos[n]][24:2348]
        else:
            s[24:2348] = bytes(2324)        # silent ADPCM sound groups
        e = edc_form2(s); s[2348:2352] = e.to_bytes(4, 'little')
    emit('04ch6', jf.lba, secs, [bytes(s) for s in js[:last]])
    return out

OPTION = ['[[option]]', 'feature = "regional"', 'id = "announcer"', 'label = "Announcer voice"',
          'description = "Menu narrator and title voice: DJ Dangerous (Japanese release) or DJ Mix Deadly (international)."',
          'type = "choice"', 'default = "international"', '',
          '[[option.choice]]', 'value = "japanese"', 'label = "Japanese"', '',
          '[[option.choice]]', 'value = "international"', 'label = "International"', '']

def append(pkg_dir):
    m = open(f'{pkg_dir}/manifest.toml').read()
    entries = build(pkg_dir)
    i = m.index('[[overlay]]')
    m = m[:i] + '\n'.join(OPTION) + '\n' + m[i:] + '\n' + '\n'.join('\n'.join(e) for e in entries)
    open(f'{pkg_dir}/manifest.toml', 'w').write(m)
    return len(entries)

if __name__ == '__main__':
    print('overlays', append(sys.argv[1]))
