"""Command buttons (Japanese / international) for bag2jp.localization.regional.

JP draws the face-button command icons (Triangle/Circle/Cross/Square) with the yellow command
palette (system/010/004.tim row 0). The international build loads an extra 4-row palette
(US system/008/010.tim at VRAM 1008,64: green/blue/pink/red) and picks one row per button.
JP has no such file, so the four US rows go into rows of system/010/005.tim (VRAM 1008,71) that
are all-zero in both versions (7, 11, 12, 13); row 14 (Up/Left arrows) gets the US pink tint.
Plugin bag2jp.command_buttons points the icon CLUT at those rows (005.dbi 0x80098398)."""
import hashlib, os, struct, sys
import sys as _sys, pathlib as _pathlib  # configured locations: tools/workflow/configured.py
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[3]))
from tools.workflow import configured as C  # noqa: E402
sys.path.insert(0, C.text('tools.psx_asset_tools'))
from psxassets import disc as D
JCUE = C.text('inputs.bag2_cue')
US010 = C.text('inputs.bag2us_assets') + '/archive/system/008/010.tim'
US005 = C.text('inputs.bag2us_assets') + '/archive/system/008/005.tim'
BUST2_LBA = 179
ENTRY_OFF = 573440          # archive/system/010 inside BUST2.BIN (catalog.csv)
TIM_OFF = 67812             # 005.tim inside system/010 (_container.json)
ROWS = {0: 7, 1: 11, 2: 12, 3: 13}   # US row (Triangle, Cross, Square, Circle) -> JP 005 row

OPTION = '''[[option]]
feature = "regional"
id = "command_buttons"
label = "Command buttons"
description = "Face-button icons in the dance commands: all yellow (Japanese) or PlayStation colours, green triangle, red circle, blue cross, pink square (international)."
type = "choice"
default = "international"

[[option.choice]]
value = "japanese"
label = "Japanese"

[[option.choice]]
value = "international"
label = "International"

[[plugin]]
feature = "regional"
id = "bag2jp.command_buttons"
'''

def append(pkg):
    J = D.Disc(JCUE)
    pos = ENTRY_OFF + TIM_OFF
    sec = BUST2_LBA + pos // 2048
    stock = bytes(J.read_user(sec, 1)); b = bytearray(stock)
    t = pos % 2048
    us10 = open(US010, 'rb').read(); us5 = open(US005, 'rb').read()
    for r in range(15):            # sanity: JP target rows are zero
        pass
    for ur, jr in ROWS.items():
        assert b[t + 20 + jr * 32: t + 20 + jr * 32 + 32] == bytes(32), jr
        b[t + 20 + jr * 32: t + 20 + jr * 32 + 32] = us10[20 + ur * 32: 20 + ur * 32 + 32]
    b[t + 20 + 14 * 32: t + 20 + 15 * 32] = us5[20 + 14 * 32: 20 + 15 * 32]
    fn = f'payload/buttons_{sec:07d}.bin'
    open(f'{pkg}/{fn}', 'wb').write(b)
    ov = ('[[overlay]]\nfeature = "regional"\ntarget = "disc_user"\n'
          f'offset = {sec * 2048}\nfile = "{fn}"\nsha256 = "{hashlib.sha256(b).hexdigest()}"\n'
          f'expected_sha256 = "{hashlib.sha256(stock).hexdigest()}"\n'
          'when = { command_buttons = "international" }\n')
    m = open(f'{pkg}/manifest.toml').read()
    if 'id = "command_buttons"' in m:
        return 0
    i = m.index('[[plugin]]')
    m = m[:i] + OPTION + '\n' + m[i:].rstrip('\n') + '\n\n' + ov
    open(f'{pkg}/manifest.toml', 'w').write(m)
    return sec

if __name__ == '__main__':
    print('buttons overlay sector', append(sys.argv[1]))
