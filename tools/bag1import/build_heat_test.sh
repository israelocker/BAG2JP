#!/bin/bash
# Rebuild the test mod bag2jp.test.bag1-heat-model: BAG1 Heat (outfit A) in place of BAG2 Heat outfit A.
# Needs: the BAG2 asset tree (assets/archive), the extracted BAG1 Heat files (_work/bag1_assets/heat),
# psx-asset-tools. Works on a copy of the archive tree in ~/work/bag1import.
set -e
P=~/mnt/Dev/Recomp/BAG2JP; T=$P/tools/bag1import; S=$P/_work/bag1_assets/heat
W=~/work/bag1import/assets; rm -rf "$W/archive"; mkdir -p "$W"; cp -r "$P/assets/archive" "$W/"
A=$W/archive/characters/heat; B=$P/assets/archive/characters/heat
# model: BAG1 mesh converted to the BAG2 layout + BAG1 animations
python3 $T/model_bag1_to_bag2.py $S/PLAYER2_P_HEATA2/000.bin $A/model_a_p1/000.bin
python3 $T/model_bag1_to_bag2.py $S/PLAYER4_P_HEATA4/000.bin $A/model_a_p2/000.bin
# animations: BAG1 anims rebuilt into BAG2's 101-slot order (+ BAG1 fever dances in choreography_a)
python3 $T/anim_remap.py $S/PLAYER2_P_HEATA2/001.bin $A/model_a_p1/001.bin $B/choreography_a/000.bin $A/choreography_a/000.bin
cp $A/model_a_p1/001.bin $A/model_a_p2/001.bin
# character code: BAG2 Heat outfit-A bone->slot table adjusted to the BAG1 skeleton (head 12, beanie 13)
python3 $T/patch_heat_dbi.py $B/pack_a_p1/001.dbi $A/pack_a_p1/001.dbi
python3 $T/patch_heat_dbi.py $B/pack_a_p2/000.dbi $A/pack_a_p2/000.dbi
# textures: BAG1 pages 004/005/006 -> BAG2 slots in order, at the BAG2 VRAM spots; BAG2 name label kept
python3 - <<PY
import sys; sys.path.insert(0, '$T'); import tim_retarget as t
for side, b1dir, slots in [('p1', 'PLAYER1E_P_HEATA1', ['002', '003', '004']), ('p2', 'PLAYER3E_P_HEATA3', ['001', '002', '003'])]:
    for src, slot in zip(['004', '005', '006'], slots):
        b2 = open(f'$B/pack_a_{side}/{slot}.tim', 'rb').read()
        out = t.retarget(open(f'$S/{b1dir}/{src}.tim', 'rb').read(), b2)
        if src == '005':
            out = t.paste_rect(out, b2, 54, 165, 124, 177)   # HEAT name label used by the HUD
        open(f'$A/pack_a_{side}/{slot}.tim', 'wb').write(out)
PY
E="$HOME/mnt/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb"
cd ~/mnt/Dev/Tools/psx-asset-tools && python3 -m psxassets make-mod "$HOME/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue" "$W" "$E/mods/installed" \
  --id bag2jp.test.bag1-heat-model --name "TEST BAG1 Heat model" --author BAG2JP \
  --description "Test: BAG1 Heat (mesh, animations, textures) in place of BAG2 Heat outfit A"
