#!/bin/bash
# Test mod bag2jp.test.bag1-heat-stage: BAG1 ST_HEAT geometry + textures in BAG2 stage id 0 (Heat's
# BAG2 stage = archive stages/200, the asset folder label "wood_workshop" is wrong). Milestone 1: BAG2 cameras, BAG2 stage effects switched off.
# Stage DFS (both games): DBI, SEDT, TIM slots (table PTR 0x80054BDC[id], no coordinate overrides:
# TIMs upload at their header coords, meshes use the slot index), model, camera list, [anims].
set -e
P=~/mnt/Dev/Recomp/BAG2JP; T=$P/tools/bag1import; S=$P/_work/bag1_disc/STAGEE/ST_HEAT.DFS
W=~/work/bag1stage/assets; rm -rf "$W/archive"; mkdir -p "$W"; cp -r "$P/assets/archive" "$W/"
A=$W/archive/stages/200_wood_workshop; B=$P/assets/archive/stages/200_wood_workshop
python3 - <<PY
import sys, struct
sys.path.insert(0, '$T')
from animlib import dfs_entries
import model_bag1_to_bag2 as m, tim_retarget as t
es = dfs_entries(open('$S', 'rb').read())
# model
out, stats, tail = m.convert(es[8]); assert tail == 0 and m.check_bag2(out) == 0
import os
if os.environ.get('STAGE_MODEL', '1') == '1': open('$A/011.bin', 'wb').write(out)
# textures: BAG1 TIM k -> slot k (entries 002..007); slots 6-8 (008..010) re-upload BAG1 CLUTs so the
# BAG2 CLUT-only TIMs there do not overwrite BAG1 palette rows
if os.environ.get('STAGE_TEX', '1') == '1':
  for k in range(6):
    open(f'$A/{k + 2:03d}.tim', 'wb').write(es[2 + k])
  for slot, src in ((8, 7), (9, 6), (10, 2)):
    f, c, i = t.parse(es[src])
    open(f'$A/{slot:03d}.tim', 'wb').write(t.build(f, c, dict(i, w=0, h=0, data=b'')))
# stage code: BAG2 Heat-stage effects off (they index BAG2's 69 nodes). Callbacks for id 0 (main exe
# tables 0x80051B88/BBC/BF0, 0x80054C10): init 0x801E537C -> return 1, update 0x801E539C kept
# (only gameplay flags for attack effects),
# draw 0x801E53BC -> tail call main 0x80022FF4 (generic part it already called), setup 0x801E53E4 ->
# return a0 (no effect memory used)
d = bytearray(open('$B/000.dbi', 'rb').read()); base = 0x801DAF10
def put(addr, *words):
    for n, wd in enumerate(words): struct.pack_into('<I', d, addr - base + 12 + 4 * n, wd)
for a in (0x801E537C, 0x801E53BC, 0x801E53E4):
    assert struct.unpack_from('<I', d, a - base + 12)[0] == 0x27BDFFE8, hex(a)
put(0x801E537C, 0x03E00008, 0x24020001)   # return 1 (callbacks return 1)
put(0x801E53BC, 0x08000000 | ((0x80022FF4 >> 2) & 0x3FFFFFF), 0)
put(0x801E53E4, 0x03E00008, 0x00801021)
open('$A/000.dbi', 'wb').write(d)
print('stage files written')
PY
E="$HOME/mnt/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb"
cd ~/mnt/Dev/Tools/psx-asset-tools && python3 -m psxassets make-mod "$HOME/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue" "$W" "$E/mods/installed" \
  --id bag2jp.test.bag1-heat-stage --name "TEST BAG1 Heat stage" --author BAG2JP \
  --description "Test: BAG1 Heat stage geometry and textures in place of Heat's BAG2 stage"
