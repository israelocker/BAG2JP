---
id: gaso-import-plan
title: "Gas-O BAG1 import into the Bi-O slot"
tags: ["gaso", "bio", "character", "import", "plan"]
summary: "Plan to import BAG1 Gas-O as the alternate version of BAG2 Bi-O (char id 9), following the shared pipeline proven with Heat and Strike."
related: ["IMPORT_STANDARD.md", "CHARACTER_IMPORT.md", "notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/strike-recovery.md", "notes/bag1-stage-song.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: plan
---

# Gas-O BAG1 import into the Bi-O slot
Status: approved 2026-11-06 (gate answered: Q1 yes, Q2 own row; region rule added). Phase 0 in progress.
Origin (owner, 2026-11-06): «procedamos con la importación del personaje Gas-O ... en la casilla
de Bi-O, en game en lugar de decir BAG1 y BAG2, dira Gas-O y Bio-O, arma la planificación
documentada ... y sigue el paso a paso con lo que ya hemos probado y a funcionado con las otras
importaciones». Strike's chest emblem and stage holes are deferred (notes/bag1-stage-song.md).

## Goal and acceptance
- Selecting Bi-O with GAME = `GAS-O` loads BAG1 Gas-O (model, textures, motions, voices/SFX,
  fever choreography) for P1/A, P1/B, P2/A, P2/B; GAME = `BI-O` keeps stock entries byte-identical.
- The character-select popup shows `GAS-O` / `BI-O` in the GAME row for char 9 only; Heat and
  Strike keep `BAG 1` / `BAG 2`.
- Baseline acceptance (CHARACTER_IMPORT.md §10): inventory, model both sides and costumes, full
  song to end, results and return to selection; conditional: mixed versions (Gas-O vs Bi-O),
  solo/duet fever, announcer name, online content identity.
- Heat and Strike BAG1 regressions still load (same alt-index entries, same payload hashes).
- Stage/song phase (if approved, gate Q1): Bi-O stage entry 197 gets a Gas-O BAG1 alternate with
  Chemical Love, score-driven stage events and stock 197 unchanged when BAG2 is selected.

## Facts (read-only research, 2026-11-06)
- BAG2 Bi-O = char id 9 (Ghidra 20261106-ghidra-016: pack/model tables 0x80055180/0x80055258 read
  by FUN_800342dc). BAG1 Gas-O is also id 9.
- BAG2 Bi-O entries (`_work/gaso/bio-native-entries.json`, raw disc read):
  - packs A 53/54, B 125/126 (B identical to A in size/members); P1 pack 6 members
    (TIM 7296, DBI 24076, TIM 33216, TIM 32864, SEDT 77568, SEDT 40232); P2 pack 5 members
    (DBI 13448, TIM, TIM, SEDT, SEDT).
  - models A 89/90, B 161/162: 3 members (model 70332 / 42 nodes, motions 219032, extra
    model 10988 / 3 nodes).
  - fever choreography 17/35; stage entry 197 (table 0x80055360).
- BAG1 Gas-O sources: full USA disc extraction `_work/bag1_disc_full` (dumpsxiso-002).
  - packs PLAYER1E/P_GAS_A1, P_GAS_B1 (costume A), PLAYER3E/P_GAS_A3, P_GAS_B3 (costume B); 8
    members each (TIM, TIM, TIM, DBI 10196, TIM, TIM, SEDT 88208, SEDT 41472).
  - models PLAYER2/P_GAS_A2/B2 (A), PLAYER4/P_GAS_A4/B4 (B): model 41 nodes (26 type1, 1 type0,
    14 type4; converts to BAG2 layout with 0 trailing bytes), motions 266776 (identical A/B), and
    an extra 1460-byte single-node model (identical A/B and costumes).
  - stage STAGEE/ST_GAS.DFS 7 members (DBI, SEDT, 3 TIM, probable stage model, probable camera).
- BAG2 Bi-O and BAG1 Gas-O both carry a third model member. BAG2 loader `FUN_80031d3c`
  (ghidra-017) reads it as an accessory model for chars 3,4,5,8,9,10,0xb,0xc,0xe,0x10 (one
  instance; 7/0xf two), stored at `0x8005f7f8`/`0x8005f800`, so Bi-O id 9 loads Gas-O's 1-node
  member structurally. Its attachment/render is per-character hook code (tables indexed
  `side*0x13+char`, no reader found in the main exe); behaviour must be observed in game.
- Label: `bag2jp_charsel_popup.c` line ~225 hard-codes `"BAG 1"`/`"BAG 2"`; glyph coverage of
  `-` and `O` must be checked.
- Selector note: notes/bag1-stage-song.md lists a "Gas-O" carousel row; BAG2 has no Gas-O stage,
  so that label must be verified before the stage phase.

## Phases (each ends with its own check; evidence under `_work/character-import/gaso/`)
0. Prerequisites — done: Bi-O id/entries, full BAG1 disc, DFS inventories, tool logs
   (ghidra-016/017, dumpsxiso-002/003), USA/JP region comparison, BAG2 accessory-member
   consumer. Open: accessory behaviour in game (phase 5).
1. Profile: `character_workflow.py init-profile` for `gaso`, then manual schema-2 bootstrap
   (source_layout A: PLAYER1E/1 + PLAYER2/2, B: PLAYER3E/3 + PLAYER4/4; target_character_id 9;
   side suffixes A/B), `validate-profile`, `plan`, `acceptance-plan`. Check: validate passes.
   Done 2026-11-06: `tools/bag1import/profiles/gaso.json` (schema 2, USA+JP regions, target
   entries, inventory `_work/character_inventory/gaso{,-jp}/` via `_work/gaso/extract_inventory.py`,
   which first re-validates Strike's 000/001 convention). validate-profile OK: 84 animations;
   plan gaps contract_not_approved, exception_assessment, three pending exceptions (animation
   contract, accessory member, region variants); 13 acceptance cases.
2. Animation contract — done: BAG1 Gas-O request list (001.bin inventory) vs Bi-O roles with the shared
   role catalog; `tools/bag1import/contracts/gaso-animation-contract.json` (110 entries, 52 mapped,
   58 duplicate, 0 unresolved, 0 unused); `tools/bag1import/profiles/gaso-animation-policy.json`
   (cues 0x1800 -> 0x6900, single projectile trigger frame 20 normalised); remap builder
   `tools/bag1import/anim_remap_gaso.py` produces verified 289,548 bytes test_001.bin with 99 active slots;
   exception `semantic-animation-contract` verified in `profiles/gaso.json`. Logged ghidra-018.
3. Assets — done: Gas-O models A2/A4 converted via `model_bag1_to_bag2.convert()` (41 nodes, 0 trailing bytes),
   single-node accessory model converted; textures retargeted via `tim_retarget.retarget()`;
   SEDT voice bank rebased `0x1800` -> `0x6900` and merged with stock Bi-O announcer cues
   `0x1907`/`0x1908` via `preserve_announcer.append_cue()`. Candidate DFS entries generated via
   `tools/bag1import/build_gaso_assets.py`. Combined payload built with 28 entries (5,978,112 bytes,
   SHA256 `148fa447...`), well within DUMMY.BIN capacity.
4. Payload and plugin — done: append rows for 53/54/125/126, 89/90/161/162 to combined spec;
   alt index generated via `make_alt_entries_exact.py`; options `gaso_p1/p2` wired in `bag2jp_bag1_versions.c`;
   popup labels `"GAS-O"` / `"BI-O"` wired for char 9 in `bag2jp_charsel_popup.c`; `manifest.toml` updated;
   compiled and deployed to experimental install `BAG2JP.exe` (SHA256 `1c963fb...`).
5. In-game, experimental install only — done: Dance View verified (PID 26596); versus match calibration
   and routing established to Bi-O (char 9); P1/A, P1/B, P2/A, P2/B versus matches executed; full battle
   played to finish (`gaso-p1a-full-finish`, 166.6s, anim0->6->11->21->53->66->74->89->solo fever 96->return fever->victory 102),
   clean return to character selection screen (`return_root: 13`). Original settings and saves verified restored.
6. Stage/song (gate Q1): port ST_GAS + Chemical Love to entry 197 with port_bag1_stage.py data
   profile, score-driven events, selector row; same acceptance as Strike's stage.
7. Close: notes (new `notes/gaso-import.md` canonical ledger), current-state next_action,
   tool logs, local Git checkpoint, snapshot only at the verified milestone.

## Decisions (owner, 2026-11-06)
- Q1 and Q2, owner: «Si correcto». Stage and Chemical Love are imported after the character,
  with their own "GAS-O" stage row like Strike BAG1.
- Region rule, owner: «tambien importa de la versión japonesa, tanto canciones, modelos y
  escenarios, porque en la versión japonesa no tiene censura como la versión americana ... si no
  lo hiciste con heat y strike ponlo como pendiente para hacerlo despues de la importación de
  gas-o, y esta regla se debe mantener para las proximas importaciones». Gas-O therefore gets
  USA and JP sources for packs, models, stage and song; the in-game version choice must expose
  both. Heat and Strike used USA sources (only Strike's ending STR came from the JP disc), so
  their JP variants are pending after Gas-O (`_work/current-state.json` `pending_tasks`). The
  rule is recorded in IMPORT_STANDARD.md.
- Owner decision, follow-up 2026-11-06: selector remains `BI-O / GAS-O`.
  The proposal `BI-O / GAS-O US / GAS-O JP` is rejected. A separate mod, using
  the existing mod-options workflow, must choose International versus JP models
  and likewise stages; region does not become another character-selector version.
  Exact owner wording: «con respecto al selector sera BI-O / GAS-O, debes crear
  un mod aparte que te permita cambiar que modelos quieres usar, si los de
  Internacional o JP, asi como tenemos los otros mods, igual con los escenarios».
   Global region options are approved below. Song region and CD/XA quality must
   not be conflated with models.
- Owner clarification, 2026-11-06: songs must use the **existing song mod** with
  `International / Japanese / CD quality`; do not add a separate BAG1 audio
  choice as the user-facing regional/quality selector. The new separate mod
  requested above is for models and stages, not songs.
- Owner follow-up: «okay continua, si no lo habias hecho para Heat y Strike
  aprovecha y hazlo ahora». Include their missing regional/CD work now rather
  than deferring all of it until Gas-O closes. Fresh preparation is recorded
  only in notes/gaso-import.md; no full regional/runtime acceptance implied.
- Approved visual-mod design: two independent global options (models and stages),
  International/JP. Owner: «De acuerdo, así como recomiendas continua».
  Subsequent correction: «Que Inicialmente sean su versión japonesa».
  Both defaults are therefore Japanese, not International. No new
   character-selector rows for regional variants; songs remain independent.
- Visual implementation sequence (approved design, bounded integration):
  1. Shared exact-entry generator accepts both regional paths and emits exact
     JP offsets/sizes; legacy payload bytes remain unchanged. Separate visual
     manifest and existing versions plugin read independent global choices.
     Host seam: `py -3.13 -m unittest -v tools.test.test_bag1_visual_regions`.
     Candidate implemented, five cases green; evidence/limits in canonical note.
  2. Supply real regional resources for Heat/Strike/Gas-O, compare/deduplicate
     hashes and regenerate the combined index/payload. Blocked by resource
     conversion and native regional semantics. Existing index has no JP bytes:
     **do not build/deploy it as usable content**; verify character hooks and
     buffer selection together with the final index, not only DF2 routing.
  3. Full-plugin build and experimental regional/gameplay acceptance under the
     existing phase6 gates. No acceptance is implied by host tests or UI options.
- Song implementation slice: query the existing explicit package/feature/songs
  option, route all three BAG1 profiles through that value, retain B1ST/native
  stage guards and chained filters, support the second XA extent for Gas-O.
  Verify at tools/test/test_bag1_stage_audio.py: three choices × three songs,
  missing-resource handling, decoder switching, stock isolation and duration
  restoration. Before deployment verify region-specific native duration tables
  and CD edits; then full-song/return and listening in experimental install.
- Song slice host candidate implemented: three profiles/choices, two XA extents,
  isolated/restorable lengths and removal of the competing BAG1 audio UI.
  Four host tests pass (`_work/gaso/regional-audio-tests.json`); no full-plugin
  build, staging/deployment or game acceptance. Visual-mod implementation and
  Japanese visual resources are still pending, with defaults already approved.
- CD source located after that clarification:
  `assets/music_cd/Bust a Move/06 Chemical Love.flac`, SHA256
  `a3b982a6abce37a1e6cbdf184c6d5865d9db4e87df4f2bdc8c6f1ee225b94e09`.
  ffprobe confirms FLAC44100Hz, stereo16bit,280.066667s. It is already present,
   not extracted in this continuation. CD-only candidates now generated:
   Strike129s/Gas-O150s, `_work/gaso/cd-edits-candidate/`, hashes/verification
   in report.json/verification.json. No deployment/listening acceptance;
   Strike intro/outro are extrapolated, Gas splices provisional. See canonical
   notes/gaso-import.md for exact limitations and next checks.

## Region comparison (2026-11-06, `_work/gaso/region-comparison.json`)
- JP disc extracted to `_work/bag1jp_disc_full` (dumpsxiso-003). JP folder names have no
  language suffix (PLAYER1..4, STAGE); JP has DANCEXA1-4 (USA 1-5).
- Packs A1/B1/A3/B3: members 1, 2, 3 (DBI 10196 USA / 10872 JP) and 5 (TIM 32864, same size)
  differ; members 0, 4, 6, 7 identical. Costume B packs repeat the same differences.
- Models A2/B2: only member 0 differs, same size, 176 words in node 26 (60 vertices, child of
  25), offsets 0xd600..0xe158. Motions and the extra member are identical. A4/B4 identical.
- Stage ST_GAS: only member 0 (DBI 15702 USA / 16594 JP) differs.
- XA: DANCEXA1/2 differ in size between regions, DANCEXA3/4 match in size; Chemical Love's
  channel and its JP/USA difference are still to be verified.
- Rendered (`_work/gaso/render_region_tims.py`, sheets `labels-usa-jp.png`,
  `a1-m5-usa-jp-diff.png`): pack members 1/2 are text graphics only: "GAS-O" name logo
  (yellow USA, red/blue JP), member 2 "VS" (A) and "NOW LOADING" (B; USA multilingual, JP
  single). Member 5 (256x256 4bpp, VRAM 512,0) differs only in its top-left 116x17 "GAS-O"
  lettering. No body texture differs. DBI member 3 change is unexamined (probably text layout).
- Node 26 (`_work/gaso/diff_node26.py`, `node26-diff.json`, `node26-usa-jp.png`): 24 of 60
  vertices moved plus 136 words after the vertex block; it is the last segment of the
  separate root chain 20..26 (not the body tree 0..19). Real geometry difference; which
  visible part it is and whether it is censorship remains unverified until seen in game.

## Risks
- Third model member role unknown (Bi-O 3 nodes vs Gas-O 1 node).
- DUMMY.BIN capacity with a third character's eight packs/models; must be measured.
- Bi-O pack layout (P1 6 members, P2 5) differs from Gas-O (8 members); DBI/TIM mapping must
  follow the shared contract, not Strike's offsets.
