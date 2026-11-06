# Strike BAG1 stage and song import
Status: approved by owner ("sí", 2026-11-05) with all four recommendations: start phase 0;
game-disc song audio (CD version only if the owner supplies it); new Strike BAG1 selector row;
story mode stage follows the character's chosen version.
Owner extension (2026-11-05): continue autonomously until visual working evidence;
do not stop for interim questions. Listening gate 0.4 is deferred to that visual review.
Origin: owner deferred the real campaign ending test "despues de importar el escenario y canciones de strike del bag1".

## Goal and acceptance
- Choosing Strike BAG1 stage (BAG2 stage id 1, archive entry 209) plays the BAG1 Strike stage
  (model, textures, stage code, camera, SFX) with the BAG1 Strike song and its BAG1 chart.
- Choosing BAG2 keeps the stock 209 stage/song byte-identical.
- Heat BAG1 stage keeps working (regression).
- Final check: a real campaign with Strike BAG1 reaches its BAG1 ending (movie + BAG1 model credits).

## Facts from research (read-only, 2026-11-05)
- Heat port is Heat-hardcoded: `tools/bag1import/port_bag1_stage.py` (addresses, word patches,
  trampolines, `CODE_END`), `build_heat_stage_test.sh` (DFS indices, 6 TIMs, scale 3/2),
  `bag2jp_bag1_stage.c` (`stage==0`, `heat_2bad_*.flac`, `BUST2_01.XA` ch 0, duration 129),
  stage select (`row 1`, `chr 0`, `heat_bag*.png`, 14 rows, random `%13`).
- Stage version routing (`bag2jp_bag1_versions.c:85-88`) already follows the player's character
  version outside the selector, so a `{209, chr 1, kind 3}` alt row would follow Strike's version in
  story mode (code reading, unverified).
- Source: `_work/bag1_disc/STAGEE/ST_STRI.DFS`: 7 entries (DBI 4887 B, SEDT, 3 TIMs, entry 5 with
  header 0x2C = probable model in a different format, camera). Heat's DFS has 10 entries.
- BAG1 chart for index 1 read from the **US** exe (`_work/bag1/SCUS_942.63`): start 955, 6264 frames,
  192 beats, 10 sections. JP equality unverified. Song audio (probably `XA/DANCEXA1.XA` ch 1) is
  not extracted; identity must be confirmed by listening.
- Stage-byte audit supersedes the earlier "mode0xB" hypothesis: BAG2 loader writes
  stage id to byte0 and publishes the object at `0x80089200`. The renderer skips
  stage id11; Strike/209 is id1. Static evidence in `sprite_animation_checks.json`;
  imported-stage shot FX still require in-game acceptance. Preserve the guard.

## Phases

### Phase 0: inventory (read-only, no runtime change)
Verified when: `_work/stage_import/strike/inventory.json` lists every DFS entry, DBI call/global,
BAG2 id-1 callback and chart, each marked verified or unresolved.
- 0.1 (S) Extract JP boot exe and BAG1 XA files from the JP disc with `raw_sectors.py`; compare the
  JP chart for index 1 with the US one. Blocked by: none.
  **Done 2026-11-05:** JP exe `_work/stage_import/strike/disc/SLPS_012.32` and raw
  `DANCEXA1.XA.raw`. JP chart table `0x8004D980[id]` (+12 when byte `0x8006F700 != 0`, meaning
  unresolved), read at `0x80023024`. Heat idx0 JP = US. Strike idx1 JP start **920** vs US 955;
  frames 6264, beats 192 and sections identical; idx13 is 920 in both. The porter must read the JP
  exe for Strike. Audio verified from JP code (`0x800396D8`, `0x80039864`): song n →
  `DANCEXA<1+n/8>.XA` channel n%8, so Strike = DANCEXA1 ch1 (132.1 s). Scripts in
  `_work/stage_import/strike/scripts/`.
- 0.2 (M) Decompile ST_STRI DBI (Ghidra) and BAG2 `209` callbacks (`_work/stagedbi/bag2_209_*`);
  inventory calls, globals, jal targets outside `FUNCS`, texture table, mode byte (0xB?). Blocked by: none.
  **In progress 2026-11-05:** `inventory.json` and disassembly listings generated under
  `_work/stage_import/strike/`. These include embedded data: branch targets and LUI pairs are
  candidates, not a completed relocation audit. BAG2 id-1 callback table words verified from
  `_work/mainexe/slpm.bin`: `0x801E33D0`, `0x801E33D8`, `0x801E3400`, `0x801E3420`
  (tables `0x80051B88`, `0x80051BBC`, `0x80051BF0`, `0x80054C10`, each at index 1).
  Source comparison extracted `STAGE/ST_STRI.DFS` directly from JP disc (LBA 16850, 228288 bytes).
  Its DBI differs from the prior `STAGEE/ST_STRI.DFS`; entries 1..6 match exactly. Do not apply
   the US code addresses/base to this JP DBI. JP base now verified as `0x801DCDF8`: loader
   `0x80037228` reads destination word `0x80010D30`, then `0x8001C024` copies payload+12 and
   clears BSS. JP update `0x801DDC60` and setup `0x801DDED8` are selected by stage byte0
   through tables `0x80052AA8`/`0x80054CDC` (index1); see `jp_base_evidence.json`.
   `call_matches.json` audits nine external targets: five have unique byte-identical bodies
    in BAG2 (three helpers, SetPolyFT4 and the BIOS rand stub). Three further calls have
    reviewed semantic/ABI mappings: MoveImage `49ADC→46C7C`, stage-light setup
    `28284→23724`, stage-light update `277F8→22FF4` (prefix `0x800`). Sprite `32BDC`
    remains open: rotated `2F824` has an incompatible extra argument; `2EE10` has the
     correct camera setup/ABI but a dynamic perspective scale (`0x8006D98C`).
     Static arithmetic probe:576 bounded positive cases, zero extent differences at
     perspective384,476/501 differences at256/512. This is not MIPS execution or
     visual acceptance. Prefer investigating a stage-local helper preserving JP
      arithmetic, never a global perspective override. Evidence: `sprite_animation_checks.json`.
      Scratch prototype now generated:660-byte local copy,9 guarded word changes,
     5 external calls and3 internal relative branches preserved; no global perspective
      read. Limited integer-instruction comparison against JP:10600cases,0differences,
      including signed32 overflow. Reproduce with
      `py -3.13 -I _work/stage_import/strike/scripts/prototype_local_sprite.py D:/Dev/Recomp/BAG2JP`.
      Evidence `sprite_local_prototype.json`; not deployed, no overlay placement chosen,
       no GTE/camera/primitive or visual acceptance yet. Remaining globals still block0.2.
       Global audit: JP trig table0x8004E114 (8192bytes) uniquely identical to
       US0x80051B74/BAG2 0x8004E488; preserve reference offsets. Evidence
       global_candidates.json. JP0x8006F63C is the frame accumulator, not beat flags;
       JP0x8006F638/0x8006EACC are current/previous level. JP0x8006EA80 is the
       72-byte target lighting config (BAG2 0x8005F220), not target matrices.
       Include indexed globals missed by lexical LUI scan. Native sprite uses shared
       kyotu12.tim CLUT and kyotu00.tim tpage, not only stage textures: equivalent
        JP common resources are now extracted and bound by loader cursor1:
        G_COMMON.DFS entry1 is kyotu00 image(512,256,64,256), entry4 is kyotu12 CLUT.
        CLUT+0x2C0 selects row75 atx992 (id0x12FE). No nonempty image matches among
        671 extracted BAG2 TIMs; compressed/unextracted assets are not covered.
        Safe BAG2 VRAM placement and helper binding remain unresolved. Evidence
        common_atlas_audit.json; canonical details in notes/bag1-stage-song.md.
   Masked-only matches are not relocation rules. See `source_comparison.json`; no runtime files changed.
- 0.3 (S) Decode ST_STRI entry 5 and TIM/CLUT layout against BAG2 `209` slots. Blocked by: none.
  **Partial 2026-11-05:** entry 5 is a 44-bone model; existing converter produces 16196 bytes
  without trailing data (`dfs_stri.json`). TIM entries 2/3/4 are **4 bpp**, not 8 bpp;
  image XYWH in VRAM words: `(512,0,64,256)`, `(576,0,64,256)`, `(640,0,8,256)`;
  CLUT XYWH `(960,32,16,8)`, `(976,32,16,2)`, `(992,32,16,1)`.
   Image block lengths independently checked against width*height*2.
   Loader audit: JP table `0x80053E0C` has three descriptors plus terminator, BAG2
   `0x800538EC` has nine plus terminator (pointer tables `0x80054CAC`/`0x80054BDC`, id1).
   Both callers start at DFS2; loaders consume one entry per descriptor, so JP TIM2/3/4
   map to BAG2 slots002/003/004. XY overrides are−1 (retain TIM coordinates).
   DBI descriptor1 image XY maps to `0x80053944/46`. Evidence `texture_loading_audit.json`
   and `texture_caller_*.txt`. Remaining six slots and model/camera/animation loading
   still require a coherent package decision; no package generated.
   Model loader `0x80032A40` consumes the returned cursor, then model, camera and
   an extra animation file for ids1/2 (`0x80032B00..3C`). With nine textures this is
   slots011/012/013. Do not shorten the descriptor table without changing that package
    layout, or assume stock animations are compatible with the 44-bone BAG1 model.
    `013.bin` parsed completely: two length-prefixed records (3616/1220bytes), then
    u32=0; total4848bytes. `125FC` returns count0 for a four-zero-byte list; bind
    `329EC` and init `126A4` skip their loops for count0. Other consumers and native
    BAG1 motion remain unverified; this does not authorize declaring an empty list safe.
- 0.4 (S) Owner listening check: candidate song excerpt WAV(s). Blocked by: 0.1.

### Phase 1: shared stage porter (Heat must stay byte-identical)
Verified when: rebuilt Heat stage blob SHA equals the current `heat_200_3.bin`; new host test passes.
- 1.1 (M) Move Heat constants into `tools/bag1import/profiles/stages/heat.json`; porter and build
  script read a stage profile. Test: `tools/test/test_stage_port.py` (Heat byte-identity). Blocked by: 0.2.
- 1.2 (M) Add `strike.json` stage profile; build Strike stage package; host test checks relocation
  (no unresolved jal/lui, chart tail present, size within slot). Blocked by: 1.1, 0.3.

### Phase 2: payload
Verified when: alt index has `{209,1,3}`, payload builds, independent DUMMY byte-capacity check passes.
- 2.1 (S) Add row to `make_alt_entries_exact.py` spec; regenerate index/payload; capacity check. Blocked by: 1.2.

### Phase 3: song audio per stage
Verified when: plugin uses a stage table {stage id, XA file/channel, duration index/value, FLAC};
Heat entry unchanged; host test passes.
- 3.1 (M) Generalize `bag2jp_bag1_stage.c`; add Strike FLAC (game XA conversion, CD version if
  supplied) to `bag1_music`; set chart-matched duration. Blocked by: 0.1, 0.4.

### Phase 4: stage selector
Verified when: carousel shows 15 rows (Heat BAG2/BAG1, Strike BAG2/BAG1, ...), random covers all,
guarded patch words verified against originals; stage-select test passes.
- 4.1 (M) Generalize selector rows/thumbnails/labels by profile; new patch table. Blocked by: 2.1.

### Phase 5: in-game acceptance (exp-8mb, state restored)
Verified when all pass with settings + 21 saves restored:
- 5.1 Versus Strike BAG1 vs X on Strike BAG1 stage: intro camera, full song, fever, result, return.
- 5.2 Same on stock Strike BAG2 stage (unchanged) and Heat BAG1 stage (regression).
- 5.3 Strike shot FX on the new stage (id1; retain the existing id11 guard).
- 5.4 Real campaign with Strike BAG1 to its BAG1 ending (deferred owner test).
Blocked by: 3.1, 4.1.

## Decision log
| Decision | Chosen option | Why |
| --- | --- | --- |
| Porter shape | Shared, profile-driven; Heat byte-identical | AGENTS.md shared standard: never clone Heat's pipeline |
| First visual candidate | Stage-local sprite helper; relocated common atlas; empty animation list | Preserve native math and avoid applying stock 31-bone animations to a 44-bone model. Experimental, not native-motion acceptance. |
| First visual test routing | Use existing Strike row4 with Strike BAG1 picked | Existing kind3 routing exercises the imported stage before the separate 15-row selector work. |

## Not yet specified
- Phase 1: whether ST_STRI entry 5 converts with the existing model converter (answered by 0.3).
- Phase 3: BAG2 index in `0x800555A8` for stage 1 and the stock XA channel of Strike's song (0.2).
- Phase 5: whether stage 209 is the 0xB-mode stage (0.2).
- Online two-PC behaviour: fog, not tested in this plan.

## Always / Never
- Always: exp-8mb only; restore settings/keybinds/state/21 saves; guard and verify original words.
- Never: touch BAG2JP-win; change Heat behaviour; claim online support; guess the song by name.

## Progress
| Phase | Status |
| --- | --- |
| 0 | static inventory used for experimental candidate; listening/native motion review pending |
| 1 | three host tests pass; Heat DBI byte-identical; Strike profile/package generated; legacy Heat adapter retained |
| 2 | candidate deployed: row209/1/3; 19 admitted entries preserved exactly; 4270080 bytes < 27648000 capacity |
| 3 | song done: profile Strike stage1/XA ch1/length index1/native129s, `strike_game.flac` 44.1kHz; gameplay-root 0x13 guard; live runs `20261106T000303289538Z` and `20261106T002321415753Z` full song→results→select, 21 saves verified. Human listening pending |
| 4 | stage selector done: 15-row carousel in `system/007.dbi` (Heat B2/B1, Hiro, Kelly, Strike B2/B1, stock stages, Random % 14). Row 5 is Strike BAG1, Row 4 is Strike BAG2. Thumbnail `strike_bag1.png` and `< STRIKE BAG1 >` label verified. Independent stage choice verified in `test_stage_version.c` and in live run `20261106T004800028681Z-strike-15row-selector`. 21 saves verified |
| 5 | native stage SFX Bank 0 merged into `001.sedt` (4 banks total: Bank 0 native cues 4100-4102, Banks 1-3 stock fever cues 4000); package test passes; live probe running. Owner accepted visual environment ("si corresponde"); campaign pending |

## Experimental execution evidence (2026-11-05)
- Host check: `wsl.exe -d Ubuntu --exec python3 -m unittest tools.test.test_stage_port`:
  3 passed. Heat DBI remains SHA256 `e4551322b1d96eaf9e781613633aa1bebd966510e807b070d0f3fb9f974fb85f`.
- Strike DFS `candidate/strike_209.dfs`: 317760 bytes, SHA256
  `ec04215bf96f0d1972b08527eeb50b553c6d23f9c56ff13f120c21714e08c6df`.
  Profile-driven builder: `tools/bag1import/build_stage_package.py`; nine texture slots,
  native model scale3/2, native intro + stock dance cameras, four-byte empty animation list.
  Stage sound bank is still stock; atlas placement remains visually experimental.
- Payload SHA256 `5acc109af8814ef86f710868bc9d1157c7164975f15af0c71f64c4350619465b`;
  `payload_report.json` verifies all 19 admitted entries byte-identical and independent capacity.
- Build passed `_work/workflow/20261105T232349974070Z-strike-stage-candidate/`.
  Executable `ecc257e45e58719d3b64b81c12f387fd381d8ac1211b3e101ce66eee7eac57f1`, experimental only.
  Previous executable/index/manifests/payloads retained in `_work/stage_import/strike/candidate/baseline/`.
- Navigation calibration `20261105T232431127931Z-strike-stage-calib` reviewed and accepted.
- Gameplay `_work/versus-runs/20261105T232648082595Z-strike-stage-candidate`:
  selector row4 through normal input; log confirms `entry 209 -> BAG1`; twelve frames over36s,
  both dancers active. `stage-sheet.jpg` shows the floor grid but black surroundings.
  This proves load/gameplay, not full visual fidelity. Settings/keybinds/mod state and21cards restored.
- Next: compare visible environment against native Strike; investigate absent background/geometry
  before acceptance, then song/SFX/duration and selector; campaign remains deferred.

### Shim correction and second visual probe
- `test_bag1_stage_shim.py` exercises actual C shim with host RAM: ids0/1 receive
  flags and score level, id2 stays untouched, previous level stays DBI-owned.
  RED before extending the stage guard, GREEN after; audio remains Heat-only.
- Build `20261105T233345251626Z-strike-stage-shim` passed. Experimental executable
  `4624122f3435f5f3664050489f3d729957b100367391a8c2308f66d115f181ea`;
  previous candidate exe backed up as `candidate/BAG2JP.pre-shim.exe`.
- Calibration `20261105T233443293596Z-strike-stage-shim-calib` reviewed and accepted.
- Probe `20261105T233632011571Z-strike-stage-candidate`: twelve gameplay shots at7s
  intervals show dancers, attacks, fog, and green/red stage lighting. This is visual
  operation evidence, not native fidelity/song/end-of-song acceptance.
- Wrapper timed out at240s after capturing; task processes were gone. Recovery
  restored three config files with exact baseline hashes. Pre-run hashes for21saves
  were only in the killed process, so full save verification is unavailable; the
  configured cards were isolated copies. No successful full-run claim. Use background
  execution or sufficient timeout for subsequent long game tests.
