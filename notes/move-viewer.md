---
summary: Move viewer/editor (tools/move_viewer) state, motion reassignment and growth packages, evidence and limits.
updated: 2026-11-20
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

- 2026-11-20 budgets (RAM dumps, P1=P2): Heat 912, Strike 4388, Comet 15568, Shorty 1516, Bi-O 672 B; GROWTH_BUDGET updated. Goldfish (asked gpt-6.1-sol, answered DeepSeek V4.1 Flash Free) on 045a867: OK con cambios; applied ValueError + argparse error, --max-growth only with --copy, tests moved to test_swap_mod. Not done: per-entry budgets (P1/P2 measured equal).
- 2026-11-20 full roster: harness `versus_session.py --action explore [--explore-seed]` mapped the select grid (18 ids, mask 3FFFF, 56 edges; runs roster-explore-20261120b/c, 54 stills reviewed, calibration accepted; `accept_versus_calibration.py` now requires one still per edge). Budgets (one side measured each, applied to both costume-A entries): Tsutomu 8268, Kelly 68, Pander 6132, Kitty-N 5424, Hiro 41052 (matches earlier Ghidra estimate), Capoeira 0, Robo-Z 11316, Columbo 94708, Sushi Boy 33756, Chichi&Sally 37684, Michael Doi 43108, McLoad 12280, Hustle Kong 1192 B; Heat P2 re-measured 912. Kelly/Capoeira effectively no growth. Not verified: second side for these 13; costume 4 entries.


- 2026-11-20 BAG1 regrid 'escalado' (tools/bag1import/anim_remap.py B1_LEVEL; L4 row = BAG1 level-0 combo): Heat/Strike payload 3A9D9D70 deployed to exp-8mb only. Take regrid-heat-20261120a ACCEPTED (Heat BAG1 vs Strike BAG1): row-4 requests 23-27 -> slots 2,7,13,23,30 at f12998-14636; stills _work/move-roles/regrid/l4_sheet.png show both dancing distinct moves, no glitches. Calibration re-accepted after rebuild (seeded explore roster-recal-20261120; edge stills reused from run c, exe change = mod payload only). Pending: Goldfish review, Gas-O regrid, visual per-move identity vs BAG1 (C/F/J) not checked frame-by-frame.
- 2026-11-20 row-0 clap: anim_remap b1_path row 0 cell 0 = BAG1 (0,0) A (request 1 = slot 6). Payload B80770CE deployed exp-8mb only. Take regrid-clap-20261120a ACCEPTED (owner watched owner.mp4: "si esta bien"): request 1 -> BAG2 slot 6 (= BAG1 anim 1, cell A) at f6962/f7592; stills _work/move-roles/regrid2/clap_sheet.png show upright arms-out then hands together at chest, matching BAG1 clap_heat.png. test_strike_import_safety slot 6 expectation 21 -> 1 per owner requirement. Gas-O not regridded.
- 2026-11-20 Goldfish (requested gpt-6.1-sol, answered DeepSeek V4.1 Flash Free) on 3c9df3a/388eb9b: OK con cambios, no ALTA. Applied: ScaledGridTests (row levels, valid transitions, 34/35 anims; reverting B1_LEVEL now fails), B1_LEVEL domain check, b1_path docstring/types, corrected comments. Clap identity of A is inferred from stills (trace proves req1 -> anim 1 only). Accepted limit: BAG2 level-ups across row 4 (e.g. alt slot 44) have no BAG1 level-up variant and replay the normal anim (L4 is level 0); documented in anim_remap.py. Accepted payload B80770CE lives in uncommitted mods-src manifest/index together with pre-existing Gas-O tank edits; commit pending separation.

- 2026-11-20 Gas-O regrid (escalado + aplauso): payload C8C0B4F1 en exp-8mb; toma regrid-gaso-20261120a aceptada; P1 Gas-O req1 -> anim6 f7057, req2/7/8/9/10 -> 11/20/26/36/52. Fotogramas _work/move-roles/regrid3/gaso_clap_sheet.png: pose erguida con brazos al pecho; aplauso no concluyente a esta resolución. Fila 4 de Gas-O sin comprobar.
- 2026-11-20 Goldfish sobre b2011ed + rebuild_regrid.py (pedido DeepSeek, respondió Beam Free): OK. Tercer miembro Gas-O intacto, índice/manifest coinciden con regrid3, Heat/Strike sin cambios. BAJA: rebuild_regrid sale con 1 en éxito parcial; regrid3 en _work no versionado. El exe instalado incluye ediciones no guardadas de bag2jp_gaso_tank.h.
- 2026-11-20 Pestaña Combos (b790f04). Goldfish (pedido DeepSeek, respondió Beam Free): OK con cambios. Aplicado: anotación showEvent. Pendiente BAJA: acceso tables['characters'] sin .get, load_remap cachea fallo y muta sys.path, KeyError si cambia LEVEL_LENGTHS; la MEDIA 'sin test de app' es errónea (tools/move_viewer/test_app.py existe) aunque no cubre la pestaña Combos. Previsualización desde Combos sin probar.
