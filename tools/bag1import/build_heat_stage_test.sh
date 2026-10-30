#!/bin/bash
# Test mod bag2jp.test.bag1-heat-stage: BAG1 ST_HEAT geometry + textures in BAG2 stage id 0 (Heat's
# BAG2 stage = archive stages/200, the asset folder label "wood_workshop" is wrong). Milestone 1: BAG2 cameras and stage sounds, BAG1 stage program (ported).
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
# BAG1 draws stages at world scale 3/8 (its stage code places effects at point*0x600>>12), BAG2 at 1/4
# (stage node matrices 0x400): nodes are scaled by 1.5 so geometry and BAG1 effects line up.
out, stats, tail = m.convert(es[8], scale=(3, 2)); assert tail == 0 and m.check_bag2(out) == 0
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
# stage code: the BAG1 stage program ported to BAG2 (port_bag1_stage.py): relocated to 0x801DAF10,
# BAG1 calls/globals mapped to BAG2, trampolines at the 4 callback addresses BAG2 uses for stage id 0
import port_bag1_stage
# song: BAG1 Heat chart (2Bad) in the DBI tail; the audio is swapped by the bag1-content plugin
chart = port_bag1_stage.bag1_chart(open('$P/_work/bag1/scus.bin', 'rb').read(), 0); print('chart', chart)
d, st, n, unk = port_bag1_stage.build(es[0], open('$B/000.dbi', 'rb').read(), chart); assert not unk, unk
open('$A/000.dbi', 'wb').write(d)
# camera list (both games: blocks [u32 size][u32 flags|keys][keys: s16 pos xyz, target xyz], u32 0):
# BAG1 ST_HEAT has only the intro fly-in (track 0); BAG2's dance tracks 1.. follow the dancers.
if os.environ.get('STAGE_CAMERA', '1') == '1':
  c2 = open('$B/012.bin', 'rb').read(); n0 = struct.unpack_from('<I', c2, 0)[0]
  assert es[9][-4:] == bytes(4) and struct.unpack_from('<I', es[9], 0)[0] + 8 == len(es[9])
  open('$A/012.bin', 'wb').write(es[9][:-4] + c2[4 + n0:])
# stage sounds: SEDT = 5 banks x [VAB head][VAB body][cue table]; BAG2 loads bank 0 (stage sounds)
# + a random bank 1-4 (cue 0x4000, fever start). Bank 0 <- BAG1 bank 0 (fire burst, cue -> 0x5000).
if os.environ.get('STAGE_SOUND', '1') == '1':
  def sects(s):
    n = struct.unpack_from('<I', s, 4)[0]; o = list(struct.unpack_from('<%dI' % n, s, 8)) + [len(s)]
    return [s[o[k]:o[k + 1]] for k in range(n)]
  s1, s2 = sects(es[1]), sects(open('$B/001.sedt', 'rb').read())
  cue = bytearray(s1[10]); assert struct.unpack_from('<IH', cue, 0) == (1, 0x4000)
  struct.pack_into('<H', cue, 4, 0x5000)
  s2[0], s2[5], s2[10] = s1[0], s1[5], bytes(cue)
  hdr = 8 + 4 * 15; offs = []; o = hdr
  for x in s2:
    offs.append(o); o += len(x)
  out = b'SEDT' + struct.pack('<I', 15) + struct.pack('<15I', *offs) + b''.join(s2)
  open('$A/001.sedt', 'wb').write(out)
print('stage files written')
PY
E="$HOME/mnt/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb"
cd ~/mnt/Dev/Tools/psx-asset-tools && python3 -m psxassets make-mod "$HOME/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue" "$W" "$E/mods/installed" \
  --id bag2jp.test.bag1-heat-stage --name "TEST BAG1 Heat stage" --author BAG2JP \
  --description "Test: BAG1 Heat stage geometry and textures in place of Heat's BAG2 stage"
