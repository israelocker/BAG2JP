---
summary: Move viewer/editor (tools/move_viewer) state, motion reassignment and growth packages, evidence and limits.
updated: 2026-11-19
---
# Move viewer / editor

Plan and progress: `_work/move-viewer/gantt.md`. App: `py -3.13 tools/move_viewer/app.py`.

## F2 reassignment (WIP, not owner-accepted except copy take)
- Copy semantics: slot <- copy of an original motion (`swap_mod.py --copy`); take f2-copy-20261119a accepted, owner "si esta bien".
- Growth: the bank lives in place at the player base; struct follows align4(base+size).
  Measured budget only Heat P1 entry 95: 912 B (RAM dump heat-ramdump-20261119). P2 (96)
  and costume 4 (167/168) keep the stock bank when growing.
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
