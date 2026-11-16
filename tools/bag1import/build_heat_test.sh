#!/bin/bash
# Prepare the workspace for test mod bag2jp.test.bag1-heat-model: BAG1 Heat in place of BAG2 Heat (both
# costumes, both player sides). Costume A = BAG1 PLAYER1/2, costume B = BAG1 PLAYER3/4;
# the A/B filename suffix selects player side, not costume.
# Run through tools/bag1import/heat_test_launch.py, which resolves the shared host configuration:
#   BAG2JP_REPO      repository holding the BAG2 asset tree (assets/archive)
#   BAG2JP_SOURCE    extracted BAG1 Heat members (inputs.heat_bag1_members)
#   BAG2JP_WORKSPACE work copy (paths.heat_test_workspace); its archive/ is deleted and recreated
# Packaging into the experimental install is the launcher's separate --package step.
set -euo pipefail
P="${BAG2JP_REPO:?run via heat_test_launch.py}"; S="${BAG2JP_SOURCE:?run via heat_test_launch.py}"
W="${BAG2JP_WORKSPACE:?run via heat_test_launch.py}"; T="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$W/archive"; mkdir -p "$W"; cp -r "$P/assets/archive" "$W/"
A="$W/archive/characters/heat"; B="$P/assets/archive/characters/heat"
export T S A B
# animations: BAG1 anims rebuilt into BAG2's 101-slot order (+ BAG1 fever dances in choreography_a)
read CA CB < <(python3 "$T/fever_entries.py" "$P" 0); echo "fever choreography: $CA $CB"
python3 "$T/anim_remap.py" "$S/PLAYER2_P_HEATA2/001.bin" "$A/model_a_p1/001.bin" \
  "$P/assets/archive/$CA/000.bin" "$W/archive/$CA/000.bin" \
  "$P/assets/archive/$CB/000.bin" "$W/archive/$CB/000.bin"
for o in a b; do
  # Native folder 2/4 selects costume; filename A/B selects player side.
  N=2; [ "$o" = b ] && N=4
  python3 "$T/model_bag1_to_bag2.py" "$S/PLAYER${N}_P_HEATA${N}/000.bin" "$A/model_${o}_p1/000.bin"
  python3 "$T/model_bag1_to_bag2.py" "$S/PLAYER${N}_P_HEATB${N}/000.bin" "$A/model_${o}_p2/000.bin"
  for s in p1 p2; do cp "$A/model_a_p1/001.bin" "$A/model_${o}_$s/001.bin" 2>/dev/null || true; done
  # character code: bone->slot table for the BAG1 skeleton (head 12, beanie 13); costume B runs the A path
  F=(); [ "$o" = b ] && F=(--outfit-b)
  python3 "$T/patch_heat_dbi.py" "$B/pack_${o}_p1/001.dbi" "$A/pack_${o}_p1/001.dbi" "${F[@]}"
  python3 "$T/patch_heat_dbi.py" "$B/pack_${o}_p2/000.dbi" "$A/pack_${o}_p2/000.dbi" "${F[@]}"
  # sounds: bank 1 (cues 0x1000+, voice + SE fired by the anim events) from BAG1 (English). Bank 3 (BAG2
  # 006/005: announcer name + VS calls, waited on by the stage intro) stays BAG2's: a missing cue hangs.
  # Its cue ids move from 0x1000 to the BAG1 range 0x6000 (rebase_cues.py; the anims are rebased too).
  python3 "$T/rebase_cues.py" "$S/PLAYER1E_P_HEATA1/007.sedt" "$A/pack_${o}_p1/005.sedt" 1000 6000
  python3 "$T/rebase_cues.py" "$S/PLAYER1E_P_HEATA1/007.sedt" "$A/pack_${o}_p2/004.sedt" 1000 6000
  # Heat exists in both games: retain BAG2's victory name cue alongside rebased BAG1 voices.
  python3 "$T/preserve_announcer.py" "$A/pack_${o}_p1/005.sedt" "$B/pack_${o}_p1/005.sedt" "$A/pack_${o}_p1/005.sedt" --cue 1007
  python3 "$T/preserve_announcer.py" "$A/pack_${o}_p2/004.sedt" "$B/pack_${o}_p2/004.sedt" "$A/pack_${o}_p2/004.sedt" --cue 1007
  touch "$A/pack_${o}_p1/_force_layout" "$A/pack_${o}_p2/_force_layout"   # exact entry sizes for the shrunk SEDTs
done
# textures: BAG1 pages 004/005/006 -> BAG2 slots in order, at the BAG2 VRAM spots; BAG2 name label kept
python3 - <<'PY'
import os, sys
T, S, A, B = (os.environ[name] for name in ('T', 'S', 'A', 'B'))
sys.path.insert(0, T); import tim_retarget as t
for o, body in [('a', 'PLAYER1E_P_HEATA1'), ('b', 'PLAYER3E_P_HEATA3')]:
    for side, slots in [('p1', ['002', '003', '004']), ('p2', ['001', '002', '003'])]:
        for src, slot in zip(['004', '005', '006'], slots):
            b2 = open(f'{B}/pack_{o}_{side}/{slot}.tim', 'rb').read()
            b1dir = body if src == '004' else 'PLAYER1E_P_HEATA1'
            out = t.retarget(open(f'{S}/{b1dir}/{src}.tim', 'rb').read(), b2)
            if src == '005':
                out = t.paste_rect(out, b2, 54, 165, 124, 177)   # HEAT name label used by the HUD
            open(f'{A}/pack_{o}_{side}/{slot}.tim', 'wb').write(out)
PY
echo "workspace prepared: $W"
