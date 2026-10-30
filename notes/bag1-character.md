# BAG1 import: Heat character (model, anims, dance grid, fever, voices), 2P autoplay, planned popups

## BAG1 import (started 2026-10-29): Heat first
- BAG1 disc: D:\Games\Bust A Groove (USA)\ISO (SCUS-94263, ISO9660 files, not one archive):
  PLAYER1x/P_HEATA1.DFS (pack: TIMs, 003.dbi char code 8908 B, 2 SEDT), PLAYER2/P_HEATA2.DFS (model:
  000.bin 54044 + 001.bin 261224), PLAYER3x/PLAYER4 = player-2 copies, STAGEx/ST_HEAT.DFS (stage:
  000.dbi 12933 B code, SEDT, 6 TIMs, 2 bins), XA/DANCEXA1-5.XA (songs), BIN1/*.DBI (game modules),
  x = E/F/G/I/S language. Extracted Heat files: _work/bag1_assets/heat/ (psx-asset-tools works as is).
- BAG2 Heat (assets/archive/characters/heat): pack_a/b_p1/p2 (TIMs, 001.dbi char code 19556 B,
  SEDT), model_a/b_p1/p2 (000.bin 60308 + 001.bin 280484), choreography_a/b (BAG2-only split).
- Same engine family: model 000.bin = bone table (u32 count 38, then per-bone links) and 001.bin
  animation header ("35 00 02 13", 0x13 = 19...) have the same layout in both games, but Heat's
  skeleton links differ (BAG2 adds child bones) and BAG2 moved dance moves to choreography files.
- Test 1 (mod bag2jp.test.bag1-heat-model, now disabled in state.toml): BAG1 000+001 in place of
  BAG2 Heat outfit A -> crash at dance load (frame ~2146, PC 0, REGIMM at 0x801CFC1C). Mesh only
  (BAG1 000, BAG2 001) -> same crash. So the BAG2 character code/choreography need BAG2's skeleton;
  a straight file swap does not work. Note: in-place repack keeps the DFS entry sizes (60308) with
  BAG1 data at the start of the slot.
- Character packs and stages carry their own DBI code compiled for each engine (BAG1 vs BAG2
  functions), so BAG1 code cannot be loaded as is; data must go through BAG2's code (converter or
  loader changes). Next: RE model/animation/choreography formats and what the BAG2 Heat DBI reads.

### BAG1 Heat: model format solved, Heat renders and dances (2026-10-29)
- Main exe decompiled: _work/mainexe/slpm_decomp.txt (headless Ghidra on Windows:
  D:\Dev\Tools\ghidra-scripts\run_headless.ps1 -Bin -Base -ProjDir -Out). BAG1: _work/bag1/bag1_decomp.txt.
- Dancer setup BAG2 FUN_80031d3c (char id low 5 bits, player 0/1; per-character handler tables with
  stride 0x4c = 19 chars: init 0x800535DC, 0x80053544, per-frame 0x80053674 (jalr at 0x80032694),
  0x8005369C, 0x800536AC). Model: FUN_80022410 (bone links -> 0xB0-byte bone structs), FUN_80022518
  (record per bone, tree order: roots via link[3], recursion link[1] then link[2]), FUN_800220B8 (mesh
  header sizes). Animations: FUN_800125FC = list of {u32 size, data}, ends with size 0 (same in BAG1:
  FUN_800159C4). BAG1 equivalents: FUN_800298DC / FUN_800299A4 / FUN_80029624 (bone struct 0x100).
- Only difference in the model file: the type-1 mesh header (BAG1 0x3C words, BAG2 0x48 words: 8 more
  runtime pointer slots, 4 more count words for new primitive kinds). Converter:
  tools/bag1import/model_bag1_to_bag2.py (also check_bag2() walks a BAG2 model; stock BAG2 Heat and
  Strike and the converted BAG1 Heat all parse to the exact end). Heat: 24 meshes + 14 type-4 nodes.
- Textures: BAG2 relocates the pack TIMs; mapping BAG1 pack 004/005/006 -> BAG2 slots 002/003/004 (p2:
  001/002/003), at the BAG2 TIM coordinates; BAG1 CLUT rows + BAG2's extra rows
  (tools/bag1import/tim_retarget.py). BAG2's HUD name label lives in slot 003 at x54-124 y165-177:
  pasted back over the BAG1 page.
- Result (mod bag2jp.test.bag1-heat-model, enabled in the exp install; rebuild with
  tools/bag1import/build_heat_test.sh): BAG1 Heat (white suit, red flames, F beanie) in a BAG2 match,
  BAG1 001 animations, BAG2 choreography, no crash, label OK. Screenshots _work/bag1_heat_test_*.png.
- Still BAG2: choreography (dance moves are anim files too: choreography_a/b 000.bin start like an
  anim list; 001.bin = move table), character code DBI (BAG2 Heat effects), sounds, outfit B.
  Next: map BAG1 dance moves (BAG1 001 anims + BAG1 move tables) into BAG2 choreography files.

### BAG1 Heat: animation slots, beanie, fever (2026-10-30)
- Dancer anim list (model 001.bin) is indexed by "motion request" tables in the main exe:
  BAG2 FUN_8002a090 (tables 0x8005180C / 0x8005182E / 0x8005181C / 0x800518E4, alternates 0x80051838),
  BAG1 FUN_80030090 (0x80055830 / 0x80055838 / 0x80055850..5E / 0x800558EC, alternates 0x80055854).
  tools/bag1import/reqmap.py prints request -> slot for both. Codes 100+ mean the same in both games:
  106 stand, 103/104 intro appeal, 110 attack, 170-172 attack variants/counter, 123/124-129 miss,
  130-135 + 200-210 hit by attack, 140-142 win, 150-152 lose, 160-164 fever (BAG2: slots 101+ =
  choreography_a/000 appended after the model list; duet fever type 2 pads to 126 and appends
  choreography_b). Fever type 0x8005E6C0 (1 solo, 2 duet) is set by the match module (jp005 ~0x80098C00).
  BAG1 Heat (84 anims) in BAG2's 101 slots shifted every index -> intro played a hit reaction, fever
  read past the list (hang). Fixed by tools/bag1import/anim_remap.py (101 slots in BAG2 order, BAG1
  fever dances 82/83 into choreography_a). Dance moves matched by length in difficulty order.
- Anim format: u32 0x1C, u16 frames, u8 interp, u8 channels (19), channel->slot bytes; info block at
  0x1C + u32[0x1C]: u16 ?, u16 beat count, beat frames, then events (u16 type, frame, value) until 0:
  type 2/3 sound cue (0x1000+ = character bank), 1 = character effect (char DBI handler table
  0x80054FE4), 16 = attack launch (table 0x8005507C). Byte 5 of the info = hold (1) / loop (0).
  BAG1 cue 0x1006 (step sound) became a Japanese voice in BAG2's bank: remapped to 0x1000/0x1001,
  other BAG1 0x10xx cues dropped until the BAG1 voice banks are ported.
- Floating beanie: char DBI init (Heat p1 0x801CEDA8, outfit A) fills dancer+0x7CC[bone] = anim slot.
  BAG2 Heat A has an extra chest bone 12 and the head at 13; BAG1 has head 12 + beanie 13. Patch
  tools/bag1import/patch_heat_dbi.py (sb v0,0xd(t8) -> sb v0,0xc(t8)) in both pack DBIs.
- Debug plugin src/bag2jp_anim_trace.c (package bag2jp.debug.anim-trace): env BAG2JP_ANIM_TRACE=1
  logs anim index / request per dancer; BAG2JP_CPU_SKILL=200 makes CPUs (and autoplay) attack.
  Heat DBI decompiled: _work/heatdbi/heat_p1_decomp.txt (base 0x801CC090).
- Verified in game (autoplay, 2 stages): intro pose, dances, beanie on the head, attack given and
  received (counter exchange), win pose, solo fever time completes and the next stage loads.
- Sounds (2026-10-30): SEDT = 'SEDT', u32 3, offsets [VAB head, VAB body, cue table]; cue table =
  u32 count + {u16 cue id, u16 flags, u32 params}. Loader FUN_8002DE5C (VAB head pool 0x116C1 bytes,
  max 110 cues). Pack bank 1 (BAG2 Heat 005 / BAG1 Heat 007, cues 0x1000+) = voices + SE fired by
  anim events and the char DBI (0x1008-0x100A, fire). Pack bank 3 (BAG2 006, p2 005: 0x3000 name call,
  0x3130 "VS" in p1 only) is the announcer for the stage intro FUN_800342DC, which waits for the cue
  slot to free: a missing cue returns -1 and the intro hangs on NOW LOADING (seen when BAG1 008 =
  bank 2 replaced it). So only bank 1 is swapped (BAG1 English 007), bank 3 stays BAG2.
  BAG1 anim cue ids are now kept as is; hand-swap effects 1-6 work (same hand bones 15/16/20/21,
  18/19/22/23 in BAG2 Heat A and BAG1 Heat). psx-asset-tools: a "_force_layout" file in an unpacked
  archive dir forces a full re-layout (exact entry sizes).
- Costume B + player 2 (2026-10-30): BAG1 has no second costume (P_HEATB* = same model and pages,
  only the select icon and the DBI load address differ); BAG1's P2-side pack (PLAYER3) has different
  colours on page 004 (red suit). BAG2 gives P2 costume B in a mirror match, so costume B = BAG1 2P
  colours, costume A = BAG1 1P colours, both sides (build_heat_test.sh builds all 4 slots).
  patch_heat_dbi.py --outfit-b also nops the costume branches (init 0x801CEDC8, setup 0x801CFC10) so
  the B packs use the A tables (same BAG1 skeleton). Verified: 2P Heat vs Heat (A p1 + B p2) loads,
  both BAG1 models, intro anims 73/72. Test driver: D:\Dev\Tools\winshot\bag2_2p_pick.ps1 (needs
  settings p2_device = "keyboard" and player2 J/L + K extra binds; restore afterwards).

## Two-player autoplay (testing, 2026-10-30)
- Autoplay package options p1_2p / p2_2p (default off; exp install: p2_2p on): in a 2-player game the
  chosen players are danced by the CPU timing. Mode 2 takes its own branches in the match module, so
  it uses register hooks (src/bag2jp_mods.c): 0x8009A9DC clears $s1/$s2 (pad readers) and keeps
  $a2 = $s2; 0x8009ADB4 (bne mode,1) falls through and 0x8009ADC8 (beq player,human) misses for the
  autoplayed player, so it gets the CPU per-measure setup; the fumble hook covers mode 2 too.
  No attacks (the CPU attack choice only runs in modes 0/1). Verified: BAG1 Heat vs BAG1 Heat, both
  dancing with combos, specials, win/lose poses, solo fever, results screen.

## Planned: selection popups in character select
- BAG1/BAG2 version popup for shared characters (Heat, Strike), like the difficulty popup.
- Costume popup (user request 2026-10-30): BAG2 never lets the player choose the costume (P2 gets
  costume B only in a mirror match; costume = char id >> 5). Add a popup to pick costume A/B (and with
  BAG1 Heat: 1P colours / 2P colours). Needs RE of how character select builds the char id.

## BAG1 and BAG2 versions side by side (2026-10-30)
- All archive reads go through FUN_8001F874(entry, dest) (also FUN_8001F94C sync wrapper, FUN_8001F9AC
  seek): offset/size come from the RAM copy of the DF2_ header at 0x8005D418 ('DF2_', count, then
  {offset rel. to BUST2.BIN, size} per entry; copied at boot from LBA 179, 0xEA0 bytes).
- DUMMY.BIN (LBA 224035, 13500 Mode-2 Form-1 sectors, all zero) is never read: alternate (BAG1)
  copies of archive entries live there (package overlay, feature bag1-heat). Heat set = 11 entries,
  1468 sectors (about 9 characters fit). Built by tools/bag1import/make_alt_entries.py from the old
  test mods (reconstructs each touched entry = stock + overlay sectors; sizes stay stock), which also
  writes src/bag2jp_bag1_alt_index.h and prints the [[overlay]] block for the manifest.
- Per-player tables in the main exe (halfword entry ids, [costume A p1 x18 | A p2 | B p1 | B p2]):
  packs 0x80055180, models 0x80055258, fever 0x8005510C[char*2 + type-1], stage 0x80055360[stage id].
  Heat = BAG2 char id 0: packs 59/60/131/132, models 95/96/167/168, fever 22/40, stage 200.
  Selection: char per side u32 0x8005E6A0/0x8005E6A4, costume B flag u8 0x8005E668/0x8005E669,
  stage id u16 0x8005E666. Loader bytes 0x80089250/51 = char | costume<<5. Mode 5 uses other tables
  (0x80055318, 0x80055210) - not covered.
- Plugin bag2jp.bag1_versions (src/bag2jp_bag1_versions.c) rewrites those RAM table entries every
  vblank: player-side entries follow that player's version; the stage follows the player using the
  character (P1 first); fever choreography follows the fever dancer: jp005 sets the winner pointer
  0x80089254 (= *(0x8005F808 + side*8)) and calls FUN_800326D4(0), the load happens in
  FUN_800326D4(1) on the next game frame, so a vblank always runs in between (log: flip at f12739,
  load after). Options heat_p1/heat_p2 (bag1/bag2) until the select-screen popup exists.
- Verified (2P autoplay): P1 BAG1 + P2 BAG2 Heat on the BAG1 stage with 2Bad, duet fever, back to
  select; P1 BAG2 + P2 BAG1 on the BAG2 stage, BAG2 song, P2 wins solo fever with BAG1 fever (req 161).
- The old test mods (bag2jp.test.bag1-heat-model/-stage) stay installed but disabled.
- Sound ids (2026-10-30): all loaded banks share one cue table (0x8007F180, 12-byte records, count
  0x8006D9A0) and FUN_8002E2D0 plays the FIRST record with the id. Each character owns 0x1000 + n*0x100
  (Heat 0x1000, Strike 0x1100, ... Hustle Kong 0x2100; 0x22xx endings, 0x3xxx announcer, 0x4000 fever,
  0x5xxx stage banks). Anim events type 2 play the id as is (FUN_8002E478), type 3 on slot 0x11+side.
  Mixed Heat match bug: both voice banks had 0x1000-0x1007, P1's bank won, so P2's BAG2 Heat shouts
  (0x1000/0x1001, ~20 each per dance) played BAG1's 0.5 s / 1 s phrases (heard as phrase spam). Fix:
  BAG1 versions use 0x6000 + BAG2 char id*0x100 (tools/bag1import/rebase_cues.py: bank ids + anim
  events, applied in anim_remap.py and build_heat_test.sh). Fever lists keep their muted 0x1FFF.
  Verified with -Cues/-Audio: BAG1 Heat fires 0x6006 steps, BAG2 Heat 0x1000/0x1001 from its own bank,
  no BAG1 phrase hits (was 9 per dance).
- Rebuild order for a BAG1 character version: build_heat_test.sh + build_heat_stage_test.sh (test mods,
  left disabled) -> make_alt_entries.py (payload + index header + overlay block) -> manifest overlay
  sha256 -> build the exe.
