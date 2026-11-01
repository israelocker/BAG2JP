---
id: bag1-stage-song-heat
title: "BAG1 Stage Song: Heat"
tags: ["bag1", "stage", "song", "heat"]
summary: "Port Heat stage and song chart from BAG1 to BAG2JP with audio conversion"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-30"
updated: "2026-11-01"
---

# BAG1 import: stage port, song chart and audio, camera, sounds, destruction, testing/debug tools

## BAG1 stage import: findings (2026-10-30)
- Heat's BAG2 stage is archive stages/200 (asset folder label "wood_workshop" is wrong), stage id 0.
  Stage id -> archive: 0=200, 1=209, 2=199, 3=210, 4=202, 5=208, 6=204/205/206, 7=203, 8=201,
  9=197, 10=198, 11=207, 12=211 (matched via the callback tables below).
- Stage DBI loads at 0x801DAF10 (BAG1: 0x801E17B0). Stage struct pointer BAG2 0x80089200 (BAG1
  0x800979D4): [0] id, [1]/[2] node counts, +0x20 bone list (0xB0 structs), +0x28 node transforms
  (0x20 each), +0x2C/+0x30 base pos/scale, +0xA0/+0xA4 camera list, +0xA8.. anim list (ids 1-2 only).
- Loader FUN_8003398C: DFS entry 0 DBI, 1 SEDT, TIM slots (table PTR 0x80054BDC[id], 0x30-byte
  entries, coordinate overrides all -1 for id 0/1: TIMs upload at header coords, meshes use slot
  index), then FUN_80032A40: model, camera list, [anims]. BAG1 ST_HEAT has the same order (DBI, SEDT,
  6 TIMs, model, 1 camera track); its model converts with model_bag1_to_bag2.py (13 meshes + 1 type 3).
- Per-stage callbacks (main exe tables, 13 ids): 0x80051B88 init, 0x80051BBC update (before the
  generic node draw in FUN_80030458), 0x80051BF0 draw (after), 0x80054C10 setup(heap) -> end ptr.
  BAG1 has 2: 0x80056D7C update (FUN_800379D8), 0x80058FC4 setup.
- Test mod bag2jp.test.bag1-heat-stage (tools/bag1import/build_heat_stage_test.sh): first try, BAG2
  Heat-stage callbacks stubbed + BAG1 model/textures -> everything black, even with the BAG2 model
  (STAGE_MODEL=0 STAGE_TEX=0): BAG2's Heat stage code (moving cage, lights, node setup) is required.
- Plan: run BAG1's own stage code: relocate the 12.9 KB BAG1 DBI to 0x801DAF10, map its ~15 main
  exe calls (mostly PsyQ GTE/GPU: 0x8004xxxx) and ~16 globals to BAG2, adapt the BAG1 stage struct /
  bone struct (0x100 vs 0xB0) layout with a mirror struct, and wire BAG2's 4 callbacks for id 0.
  Decomps: _work/stagedbi/{bag1_st_heat,bag2_200,bag2_209}_decomp.txt.
- Debug: BAG2JP_RAM_DUMP=n (anim_trace plugin) dumps 2 MB RAM at trace frame n.
- DONE (milestone 1, verified 2P autoplay): tools/bag1import/port_bag1_stage.py relocates the BAG1
  ST_HEAT DBI (delta 0x801DAF10-0x801E17B0), maps 17 main-exe calls (incl. lights setup/update
  0x80023724/0x80022FF4) and globals, aliases lui pairs through register copies/base+index adds,
  patches 2 stage-struct sites, and puts trampolines at BAG2's 4 id-0 callbacks. BAG1 beat flags /
  level live in a shim (0x801E0100 'B1ST', +4 flags, +8 level, +9 prev) fed each vblank by
  src/bag2jp_bag1_stage.c (package bag2jp.feature.bag1-content).
- IMPORTANT: the song chart for each stage lives at the END of its stage DBI, not in the main exe:
  0x8004DF08[stage id] -> chart (id 0: 0x801E5410), plus tables 0x80051AC8.. (4 x 12 ids) pointing
  into it. A replacement stage DBI must keep that tail (and the stock bss). Without it the beat table
  0x8005E2F0 is garbage: beat 0x8005E2D0 sticks at 1, beats-left 0x8005E658 = 0 and the match jumps
  to the result (phase 1/5/6) with both dancers standing. The BAG1 song import will replace this tail.
- Stage world scale: BAG1 draws stages at 3/8 (stage code and main exe place effects at
  point*0x600>>12), BAG2 at 1/4 (stage node matrices diag 0x400). The ported model gets node scale
  and translation x1.5 (model_bag1_to_bag2.convert(scale=(3, 2))); then barrel flames (type-3 node 4
  points 64-75), windows (points 0-63) and lava line up. Type-3 data stays raw.
- Dance moves (anim_remap.py): BAG2 request = row base[level] + bar (rows 1/5/11/17/23, levels 5-7
  from bar 2/4/6, last bar = double); BAG1 cell (bar s, level v<=s) = request s(s+1)/2+(s-v)+1, bar 7
  double 29+(7-v). In both games the normal anim follows the same level and the alternate follows a
  level-up. Each BAG2 row maps to a BAG1 path (bar + offset so it ends on the BAG1 double, level
  min(L, bar)), so consecutive moves are designed BAG1 transitions.
- BAG1 song (2026-10-30): Heat's BAG1 song is "2Bad" (CD track 02), not Chemical Love (Gas-O).
  BAG1 song index = character id (Heat 0): audio XA/DANCEXA<1+id/8>.XA channel id%8 (JP disc has
  DANCEXA1-4; the +16 variant when 0x8006157C != 0), chart = main exe table 0x800513DC[id] (+12 variant):
  start frame, frames, beats, sections u16 (mode<<8|beats), -1; BAG1 mode 0 = both players, 1/2 = solo,
  after -1 both play to the end; time = vblank frames from XA start (0x80097A68). Heat: 816, 6565, 256
  (140 BPM), 0x40,0x108,0x208,0x110,0x210,0x108,0x208. JP/US audio identical (US +3.6 dB).
  BAG2 chart (stage DBI tail, 0x8004DF08[stage]): start, frames, beats, intro beats, sections
  (mode 0 = no commands, 1/2 solo, 3 both). port_bag1_stage.bag1_chart() converts (32 intro beats from
  the pre-roll, start -5): [-5, 7386, 288, 32, 32, 0x340, 0x108, 0x208, 0x110, 0x210, 0x108, 0x208,
  0x340, 0x340, -1] (same 15 halfwords as stock). Verified 2P autoplay: intro, both, solos, fever, result.
  Audio: plugin bag2jp.bag1_stage wraps the XA host filter (after bag2jp.hq_songs) and replaces
  BUST2_01 ch0 sectors with <bag1_music>/heat_2bad_<cd|game>.flac while the B1ST stage is loaded
  (option bag1_song_audio, default cd; log bag2jp_bag1_content.log). CD version re-aligned with the hq
  tools (mods-src/bag2jp.feature.bag1-content/tools/hq_bag1, coverage 90 %, score 0.74).
- Stage camera list (both games): blocks [u32 size][u32 flags 0x4000|keys][keys: s16 pos xyz, target
  xyz], u32 0. BAG1 ST_HEAT entry 9 = only the intro fly-in (180 keys); BAG2 has ~28 tracks (0 = intro,
  rest follow the dancers). Ported: BAG1 track 0 + BAG2 tracks 1.. (same world units; verified in game).
- Stage SEDT = 'SEDT', 15 sections = 5 banks x [VAB head][VAB body][cue table]. BAG2 loader (main exe
  ~0x8003xxxx, FUN_8002E08C(sedt, bank)) loads bank 0 (stage sounds; stage ids in mask 0xFBF) + a random
  bank 1-4 whose cue 0x4000 jp005 plays before fever. BAG1 ST_HEAT bank 0 = cue 0x4000 fire burst,
  played by the stage code on voice slot 20 (BAG2 has 14 slots, table 0x8006D9F0). Port: bank 0 <- BAG1
  bank 0 with the cue renumbered 0x5000, call site 0x801E2230.. patched to BAG2 FUN_8002E478(0x5000,-1,
  -1,-1) (free slot). Full 2P match OK.
- Song end (2026-10-30): BAG2 stops a song when play time (0x800892EC frames / 60) reaches the main
  exe table 0x800555A8[song] (u16 s: 152,136,164,...; FUN_80035BF8); phase 5 (FUN_80098E58) waits for
  0x800892E8 == -1 before fever. BAG1 2Bad's dance ends at 123 s but BAG2 Heat's slot says 152 s -> ~25 s
  of silence before fever. The BAG1 edit cuts the song at 123.37 s (short gap, soft tail); the CD render
  kept playing the CD there and stopped hard at 132 s. Fix: tools/bag1import/song_ending.py (CD render
  switches to the level-matched game tail at the cut, both versions fade to 0 by 129 s) and the plugin
  sets 0x800555A8[0] = 129 while the BAG1 stage is loaded (restored after). Verified (game and cd):
  dance end f10635, song stop f10994, fever f11132 (was f12401).
- Stage destruction (2026-10-30): BAG1 stage update breaks window panels (fire -> night city) when its
  level (BAG1 0x80068714: 1 at 15000, 2 at 45000 BAG1 points) differs from the previous one (0x800979D0,
  copied by BAG1 main after the stage update): +32 panels at level 1, +64 at level 2. Bug: the plugin
  copied prev every vblank, so the update never saw the change. Now a helper at SHIM+0x10 (the update
  callback jumps there) calls the BAG1 update and then copies level -> prev. Thresholds use BAG2's
  dance-level table (0x8005141C x play beats 0x8005E2E8 / 256): level 1 at 9300, level 2 at 18900 (a BAG2
  match ends ~25-30k). Verified: panels break, city visible behind.
- Fever voices: BAG1 anims 82/83 (requests 160/161) fire Heat voice cue 0x1006 8x; BAG2 fever has none.
  anim_remap.mute_voices() points bank-1 cues of the fever anims at missing cue 0x1FFF.
- Broken-window flicker (2026-10-30): the night-city backdrop behind broken panels (stage update, tiles
  $fp -4..1, clut/tpage from texture table entries 4/5) used tpage 0x0FF3 on odd tiles: the pair
  `lui v0,0x8006` in the delay slot of `bnez` at 0x801E3A0C + `addiu s3,v0,-0x7F6C` at the branch
  target 0x801E3F64 was never relocated (the porter paired lui only along linear flow), so those tiles
  sampled the framebuffer (live dancers / stale frames flickering in the windows). port() now carries a
  delay-slot lui to its branch target (shared entry). Also: tiles widened to -8..5 and the update
  helper adds a black TILE at OT[0xFFF] (sky above the city strip, never stale). Verified stable.
- Fever choreography entries (2026-10-30): BAG2 loads them by main exe table 0x8005510C[char id*2 +
  fever type-1] (archive entry index). The asset folders of entries 17-52 were named by order and are
  NOT the character: Heat (char id 0) uses 22/40 = folders "kelly/choreography_a|b"
  (tools/bag1import/fever_entries.py). Before this fix the BAG1 fever dances were never used: Heat
  danced BAG2 Heat's fever, whose cues 0x1000/0x1001 played BAG1 hit shouts from the swapped voice
  bank. Now: solo = BAG1 82/83/82 with every char-bank cue muted, duet = BAG2 duet with 0x10xx muted.
  Verified with a cue watch (slot table 0x8006D9F6 + 8*slot): no 0x10xx during fever, both types.
- Audio analysis (2026-10-30): BAG2JP_AUDIO_DUMP=1 (debug plugin bag2jp.anim_trace, PCM hook on the
  final mix) -> bag2jp_audio.wav + bag2jp_audio_sync.log (vblank frame -> sample). D:\Dev\Tools\
  audio-probe extracts SEDT cues to WAV templates and finds them in the recording. Validated against
  the cue-slot watch (0x8006D9F6 + 8*slot): voices 0x1001/0x1003/0x1007 found 1-2 frames after the
  request; BAG1 Heat fever (frames 11121-11999) has no Heat voice, no 0x10xx requests.
- Debug: BAG2JP_WATCH=addr:size,... logs value changes to bag2jp_watch.log.

## Independent Heat stage selection (2026-10-30)
- Current behavior supersedes the earlier character-driven stage rule in selectable modes:
  Stage Select has HEAT BAG2 followed by HEAT BAG1, with distinct original thumbnails.
  Characters/versions/costumes are independent; story mode keeps its automatic character-based default.
- Implementation: bag2jp_charsel_popup.c includes bag2jp_stage_select.inc and the guarded
  bag2jp_stage_select_patches.h. sys/007 at 0x8008F890: order 0x800963D0, inverse 0x800963E0;
  14 cursor rows = 13 choices + RANDOM (index 13). Both Heat rows still map to character/stage id 0.
  The second Heat row is index 1; existing other-stage ids and gameplay tables are unchanged.
- 23 original-word-checked patches widen cursor bounds and change random selection from %12 to %13.
  Random's native label comparison hook is 0x80093DB0; it keeps the arrow size constant 12.
  Hook 0x800917A8 records the random row. Hook 0x80093E38 hides only Heat's old native caption;
  the host HUD draws the chosen Heat thumbnail and caption at the native preview coordinates.
- bag2jp_bag1_set_stage_version(-1/0/1) selects automatic/BAG2/BAG1 for entry 200 only.
  Per-player character packs, costume and fever routing remain separate. The choice survives loading
  and resets on character selection/session/online-link transitions.
- Thumbnails: BAG1 DFS1/ST_SEL.BPE entry 23 (154x64, fitted to 186x60); BAG2 system/015.bpe entry 029.
  Rebuild: python tools/bag1import/build_stage_previews.py. Files heat_bag1.png / heat_bag2.png live
  in the select-popup resource popup_assets. The active experimental resource is under mods/bundled.
- The expanded-menu capability contributes STG1 to the existing online content identity. Peers with
  different capability fall back to stock content and the 13-row menu. Identity checks are unit-tested;
  the new selector has not yet been retested between two PCs.
- Fresh tests: Practice with BAG1 Heat on BAG2 stage; native carousel forward/back, Comet and RANDOM wrap.
  2P P1 BAG2 A + P2 BAG1 B on BAG1 stage: CD 2Bad opened, song length 129 s, dance/fever/return to select
  (fever f19092..20136, return f20138). Same session, both BAG1 A/B on BAG2 stage: stock stage restored,
  CD BUST2_01 ch0 used, dance/fever/return (f38342..39386, return f39388). Both runs were fever type 1.
- Evidence: _work/shots/stage_select_bag1{,_sheet.png}, stage_select_bag2{,_sheet.png}.
  Unit command (WSL): bash /mnt/d/Dev/Recomp/BAG2JP/tools/test/stage_select/run.sh.
  Checks real version-routing C, online menu identity, original MIPS words, all row mappings and random
  arithmetic for all 0..32767 values plus large int boundaries. Both tests failed on stock behavior first.
- Tests used copied memory cards; settings, keybinds and mod state restored byte-for-byte, original
  cards verified unchanged by SHA256. With both pads sharing keyboard arrows, J/L move P2 alone
  by one stage; shared arrows can produce two native moves in 2P.
