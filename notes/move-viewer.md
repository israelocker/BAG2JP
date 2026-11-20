---
summary: Move viewer/editor (tools/move_viewer) state, motion reassignment and growth packages, evidence and limits.
updated: 2026-11-19
---
# Move viewer / editor

Plan and progress: `_work/move-viewer/gantt.md`. App: `py -3.13 tools/move_viewer/app.py`.

## F2 reassignment (WIP, not owner-accepted except copy take)
- Copy semantics: slot <- copy of an original motion (`swap_mod.py --copy`); take f2-copy-20261119a accepted, owner "si esta bien".
- Growth: the bank lives in place at the player base; struct follows align4(base+size).
  Measured budget Heat costume A: 912 B on P1 (entry 95, RAM dump heat-ramdump-20261119) and
  P2 (entry 96, heat-p2-ramdump-20261120; Strike P1 free 4388 B). Ghidra: DAT_80089230 block
  at the P2 region tail (FUN_800337b8) is consumed during P2 load (FUN_80033f14), so it does not
  reduce the budget. Costume 4 (167/168) keeps the stock bank when growing. P2 in-game take:
  f2-grow-p2-20261120c ACCEPTED (Strike P1, Heat P2, slots 72<-0x3A, 73<-0x54, +596 B):
  P2 plays req104 -> anim73 at f6084; stills `_work/move-viewer/f2/p2c_sheet.png` show the floor
  spin / handstand / stand-up of render `f2/render84/heat_m084_sheet.png`. Takes a/b were valid
  but did not show the patched slot on screen (WAIT off-camera; CPU picked 73 not 72).
- A grown entry patches its 4-byte DF2 size field (disc_user 366592 + 8 + 8*entry + 4).
- Regional localization now owns only header bytes 366692..366693 (see
  `mods-src/bag2jp.localization.regional/1.0.0/PAYLOAD_README.txt`); both compose.
- Evidence: take f2-grow-20261119d (capture accepted, p99 12.7 ms; regional + grow enabled):
  WAIT req106 period 128 fr (stock 108) = grown 0x06. f2-grow-20261119c rejected (jitter 21.2 ms), kept.
  f2-grow-20261119b (regional off) stills `_work/move-viewer/f2/grow_sheet.png`.
- Not verified: frames of take d, translated logos visible with boot_logos=international, other characters' budgets.

## Goldfish 2026-11-19 (requested gpt-6.1-sol, answered DeepSeek V4.1 Flash Free): OK con cambios
Applied: removed `--header-sector` (unsafe: collided or leaked regional bytes); UI notes state P1 costume A only;
host test for the 4-byte size overlay; regional sparse script versioned (`tools/move_viewer/regional_sparse179.py`).
Pending: `--max-growth` not tied to GROWTH_BUDGET in CLI; `.bak` manifests inside version dirs; visual review of take d.

- 2026-11-20 budgets (RAM dumps, P1=P2): Heat 912, Strike 4388, Comet 15568, Shorty 1516, Bi-O 672 B; GROWTH_BUDGET updated. Goldfish (asked gpt-6.1-sol, answered DeepSeek V4.1 Flash Free) on 045a867: OK con cambios; applied ValueError + argparse error, --max-growth only with --copy, tests moved to test_swap_mod. Not done: per-entry budgets (P1/P2 measured equal), other 13 characters unmeasured.

