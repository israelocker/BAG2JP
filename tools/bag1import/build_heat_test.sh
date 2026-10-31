#!/bin/bash
# Rebuild the test mod bag2jp.test.bag1-heat-model: BAG1 Heat in place of BAG2 Heat (both costumes,
# both player sides). Costume A = BAG1 1P colours, costume B = BAG1 2P colours (PLAYER3 page 004;
# BAG2 gives P2 costume B in a mirror match, like BAG1's 2P colours).
# Needs: the BAG2 asset tree (assets/archive), the extracted BAG1 Heat files (_work/bag1_assets/heat),
# psx-asset-tools. Works on a copy of the archive tree in ~/work/bag1import.
set -e
P=~/mnt/Dev/Recomp/BAG2JP; T=$P/tools/bag1import; S=$P/_work/bag1_assets/heat
W=~/work/bag1import/assets; rm -rf "$W/archive"; mkdir -p "$W"; cp -r "$P/assets/archive" "$W/"
A=$W/archive/characters/heat; B=$P/assets/archive/characters/heat
# animations: BAG1 anims rebuilt into BAG2's 101-slot order (+ BAG1 fever dances in choreography_a)
read CA CB < <(python3 $T/fever_entries.py $P 0); echo "fever choreography: $CA $CB"
python3 $T/anim_remap.py $S/PLAYER2_P_HEATA2/001.bin $A/model_a_p1/001.bin $P/assets/archive/$CA/000.bin $W/archive/$CA/000.bin \
  $P/assets/archive/$CB/000.bin $W/archive/$CB/000.bin
for o in a b; do
  # model: BAG1 mesh converted to the BAG2 layout (p1 / p2 files) + the remapped animations
  python3 $T/model_bag1_to_bag2.py $S/PLAYER2_P_HEATA2/000.bin $A/model_${o}_p1/000.bin
  python3 $T/model_bag1_to_bag2.py $S/PLAYER4_P_HEATA4/000.bin $A/model_${o}_p2/000.bin
  for s in p1 p2; do cp $A/model_a_p1/001.bin $A/model_${o}_$s/001.bin 2>/dev/null || true; done
  # character code: bone->slot table for the BAG1 skeleton (head 12, beanie 13); costume B runs the A path
  F=""; [ $o = b ] && F=--outfit-b
  python3 $T/patch_heat_dbi.py $B/pack_${o}_p1/001.dbi $A/pack_${o}_p1/001.dbi $F
  python3 $T/patch_heat_dbi.py $B/pack_${o}_p2/000.dbi $A/pack_${o}_p2/000.dbi $F
  # sounds: bank 1 (cues 0x1000+, voice + SE fired by the anim events) from BAG1 (English). Bank 3 (BAG2
  # 006/005: announcer name + VS calls, waited on by the stage intro) stays BAG2's: a missing cue hangs.
  # Its cue ids move from 0x1000 to the BAG1 range 0x6000 (rebase_cues.py; the anims are rebased too).
  python3 $T/rebase_cues.py $S/PLAYER1E_P_HEATA1/007.sedt $A/pack_${o}_p1/005.sedt 1000 6000
  python3 $T/rebase_cues.py $S/PLAYER1E_P_HEATA1/007.sedt $A/pack_${o}_p2/004.sedt 1000 6000
  # Heat exists in both games: retain BAG2's victory name cue alongside rebased BAG1 voices.
  python3 $T/preserve_announcer.py $A/pack_${o}_p1/005.sedt $B/pack_${o}_p1/005.sedt $A/pack_${o}_p1/005.sedt --cue 1007
  python3 $T/preserve_announcer.py $A/pack_${o}_p2/004.sedt $B/pack_${o}_p2/004.sedt $A/pack_${o}_p2/004.sedt --cue 1007
  touch $A/pack_${o}_p1/_force_layout $A/pack_${o}_p2/_force_layout   # exact entry sizes for the shrunk SEDTs
done
# textures: BAG1 pages 004/005/006 -> BAG2 slots in order, at the BAG2 VRAM spots; BAG2 name label kept
python3 - <<PY
import sys; sys.path.insert(0, '$T'); import tim_retarget as t
for o, body in [('a', 'PLAYER1E_P_HEATA1'), ('b', 'PLAYER3E_P_HEATA3')]:
    for side, slots in [('p1', ['002', '003', '004']), ('p2', ['001', '002', '003'])]:
        for src, slot in zip(['004', '005', '006'], slots):
            b2 = open(f'$B/pack_{o}_{side}/{slot}.tim', 'rb').read()
            b1dir = body if src == '004' else 'PLAYER1E_P_HEATA1'
            out = t.retarget(open(f'$S/{b1dir}/{src}.tim', 'rb').read(), b2)
            if src == '005':
                out = t.paste_rect(out, b2, 54, 165, 124, 177)   # HEAT name label used by the HUD
            open(f'$A/pack_{o}_{side}/{slot}.tim', 'wb').write(out)
PY
E="$HOME/mnt/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb"
cd ~/mnt/Dev/Tools/psx-asset-tools && python3 -m psxassets make-mod "$HOME/mnt/Bust A Groove 2 (Japan)/ISO/Bust A Move 2 - Dance Tengoku Mix (Japan).cue" "$W" "$E/mods/installed" \
  --id bag2jp.test.bag1-heat-model --name "TEST BAG1 Heat model" --author BAG2JP \
  --description "Test: BAG1 Heat (mesh, animations, textures, voices) in place of BAG2 Heat, both costumes"
