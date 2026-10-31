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
  tools/bag1import/reqmap.py prints request -> slot for both. Do not assume semantic equivalence from equal request numbers (see the 2026-10-31 Dance View audit). BAG2 codes include:
  106 stand, 103/104 intro appeal, 110 attack, 170 dodge, 171 guard, 172 reflect, 123 tired, 124-129 miss,
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

## Character select popup: version + costume (2026-10-30)
- Character select = system/007.dbi (base 0x8008F890; decomp ~/work/charsel/007_decomp.txt, Ghidra
  headless on the payload). Per-player block 0x800971D4 + side*0x20: +0x18 timer, +0x19 side (= pad
  index), +0x1A cursor index (= char id, Heat 0), +0x1B previous index, +0x1C costume, +0x1E state
  (1 choosing, 2 difficulty popup, 3 done), +0x1F difficulty (-> 0x8005E6CC[side]). Main update
  FUN_80090258; state 1 input FUN_80091DB0: Circle = costume A, Triangle or Select/Start + Circle =
  costume B (BAG2's hidden costume choice), only if mask 0x80096FA8 has the index; state 2 =
  FUN_80091B78 (difficulty). Mirror rule FUN_80091AE8: same character + costume -> the later pick
  gets costume ^ 1 (`sb v0,0x1c(a2)` at 0x80091B6C). Results copied to 0x8005E6A0/A4, 0x8005E668/69.
- Plugin bag2jp.charsel_popup (src/bag2jp_charsel_popup.c, feature select-popup of bag1-content):
  pad transforms on both ports (port 1 chains the MODS menu; mods menu's own transform chains the
  popup, so install order does not matter; netsync reattaches it after an online link). Circle/Triangle on a selectable character in state 1 opens the popup and is
  kept from the game; Up/Down rows, Left/Right values (GAME BAG 1/BAG 2 for characters with a BAG1
  version, COSTUME A/B; Triangle starts on B); Circle confirms: version -> bag2jp_bag1_set_version,
  then 4 neutral + 6 pressed polls of Circle (A) or Triangle (B) replay the pick; Cross cancels.
  Mirror hook keeps the costume when the two players picked different versions.
- Drawing: new framework call gl_renderer_draw_host_overlay (alpha-blended BGRA over the frame, 4:3
  area; patches/psxrecomp-host-movie-layer.patch), canvas 1280x960, font 1 glyphs from RAM + HD
  atlas rows 5/6 (resource popup_assets = font_a05/a06.png copied from the mods menu assets).
- Test driver: bag2_2p_pick.ps1 -Popup 1 (default) presses one more Circle to confirm the popups;
  the popup starts on the launcher's version (heat_p1/heat_p2) and costume A.
- Verified: both popups open together, values change, P1 BAG1 + P2 BAG2 both costume B -> P2 keeps B
  (BAG2 Heat red jacket) on the BAG1 stage; full automated 2P match back to select.

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
- Online (2026-10-30, src/bag2jp_netsync.c): menus are not lockstep (each PC sends button changes),
  so the popup cannot be replayed from the other PC's buttons. Instead each PC runs the popup for its
  own side on its own pad inside ns_pad_transform (bag2jp_charsel_filter_side, before the buttons are
  sent); the costume travels as the replayed Circle/Triangle; the version is sent as M_PICK (u8 side,
  char, version, seq; repeated with every ping, latest seq wins). On link every version resets to BAG2
  (launcher defaults may differ); unpicked sides stay BAG2. M_CONTENT (FNV hash of the alt-entry
  index, repeated with pings): different content on the two PCs -> BAG2 versions only on both + toast.
  Verified with two copies on one PC (bag2_two.ps1 -BFocusAlways, LAN): picks sent/received, same
  entry switches and mirror decision on both, identical dance screens (P1 BAG2 B vs P2 BAG1 B).

## Heat victory announcer and popup feedback (2026-10-31)
- Victory names: JP main-exe table 0x80051424, Heat cue 0x1007. Match sys/005 phase 1/4 calls it on slot 14, then generic 0x100 (win). BAG1 voices had been rebased to 0x6000..6007, leaving the name absent.
- Character SEDT loading calls FUN_8002E08C with bank index 0; a second bank is not loaded. preserve_announcer.py merges just the stock name program/tones/ADPCM sample into the existing VAB, preserving BAG1 cues. This is opt-in for Heat in build_heat_test.sh; characters without a shared BAG2 name keep the generic announcement.
- restore_heat_winner.py audits the four current alternate voice packs (entries 59/60/131/132), requires the manifest payload hash, and can rebuild with --apply. Payload fits its existing slots; manifest line endings are preserved.
- WIN1 contributes to the online content identity because a newly present name changes result timing. Older peers use the existing stock fallback; no fresh two-PC test yet.
- Popup: original sys/007 confirm sound 0x201, navigation 0x200, cancel 0x202. Queue from pad filters; drain at guarded function entry 0x80090258 (word 0x27BDFFD8), calling 0x8002E478 through psx_mod_call_guest. Guest calls are not made from instruction callbacks.
- Opening uses the difficulty menu's eight-frame vertical unfold and a short +/-2-pixel horizontal shake. Captured both players; cue callbacks returned valid slots, cancel/reopen and selection worked. Captures: outputs/heat-popup-opening.gif in the Codex work folder.
- Unit command: py -3.13 tools/test/test_heat_announcer.py (five tests; same bank 0, original voices and original victory clip, all costumes/sides). Selector regression also checks the changed content identity.
- Fresh 2P test after bank-0 merge: both Heat BAG1 A/B, BAG1 stage/CD 2Bad. P2 wins; slot 14 requests 0x1007 at f12322 with a valid VAB handle, followed by generic 0x100. Dance f5642..12238; fever type 1 f12755..13799; return to selection f13801. The separate-bank attempt was rejected because it did not load the name. Settings/keybinds/mod state restored; personal cards verified unchanged.

### BAG1 native Dance View reference / role audit (2026-10-31)
- Opened the installed BAG1 USA PSXRecomp runtime through an isolated copy at D:/Dev/Scratch/bag1-native-reference, with its own settings, keyboard bindings and cards. No DuckStation is used for the reference. Original installations/cards remain untouched.
- JP save sources: D:/Games/Bust A Groove (Japan)/BISLPS-01232.mcs and bust-a-groove.23277.gme. The GME's final 131072 bytes are a raw MC card; its first save block equals the MCS payload after the 128-byte directory entry. In the reference card only, renamed slot-1 directory ID to BASCUS-94263 and recomputed directory XOR. Native game confirmed LOAD OK, unlocked Dance View and loaded Heat.
- Native controls: keyboard X confirms memory-card dialogs; Return enters menu choices; Triangle=A toggles Dance View display/controls. The left column is a 15-item playlist, initially empty (---), not missing text. Right/Left changes the selected item's animation, Up/Down changes the playlist row. Use ~70 ms key holds; longer holds repeat. Verified 54 Right taps at 100 ms gaps select TIRED from NEUTRAL.
- BAG1 VIEW.DBI payload base 0x8009CC50: English label pointers 0x8009F84C, request bytes 0x8009FD88, time parameters 0x8009FDCC. TIRED index54=req124=anim69; CAUGHT index55=req123=anim70; DODGE index50=req170=anim65; ATTACK2 index49=req111=anim64; HIT1/2/3 indices51..53=req120..122=anims66..68.
- BAG2 system/008.dbi payload base 0x8008F890: requests at 0x80092484. TIRED index71=req123=slot78; GUARD index69=req171=slot76; REFLECT index70=req172=slot77; DODGE index68=req170=slot75. Matching request numbers across games does NOT establish matching semantic roles.
- Read-only tool: tools/bag1import/audit_animation_roles.py --package "D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb/mods/bundled/bag2jp.feature.bag1-content/1.0.0" [--output existing-parent/report.json]. No extra dependencies. Reads original label tables and compares actual installed payload animation bytes after existing cue/event conversion, for model entries95/96/167/168.
- Audit of payload SHA256 1f4c72991a69465e005b106bbbbc630ce9d0a735e68c6ff74778495bdf865f50: checked roles agree across all four model lists. Current TIRED -> BAG1 CAUGHT70; GUARD -> HIT1 66; REFLECT -> HIT2 67; DODGE -> DODGE65; MISS1 -> TIRED69; MISS6 -> HIT3 68. Captured TIRED, DODGE, ATTACK2, HIT1 and CAUGHT in the original native Dance View.
- This task establishes the reference/diagnosis; it does not change BAG2 runtime or conversion mappings. Follow-up: TIRED should use original69 instead of70. BAG1 has no separately named GUARD/REFLECT; choose and document a defense/counter adaptation rather than assume req171/172 match BAG1 hit reactions. Audit remaining MISS/POSE roles as part of the fix; then regenerate assets and test BAG2 experimental Dance View/match before claiming corrected behavior.
- Evidence and save hashes: C:/Users/israe/Documents/Codex/2026-10-30/ho/work/bag1-reference; captures under ho/outputs/bag1-heat-*.png. Audit JSON records both complete label/request tables and installed role matches.

### Complete Heat animation comparison (2026-10-31)
- Extended tools/bag1import/audit_animation_roles.py to inventory all 84 BAG1 sources, all 101 model slots in four installed variants (404 checks), all 87 BAG2 Dance View choices, 42 dance cells, 10 alternate transitions, 9 internal slots, 5 solo-fever and 11 duet-fever entries (420 physical entries). Package manifest hash and complete conversion output are verified; no game data is written.
- Optional --bag1-japan <raw bin> compares original JP Heat A/B models on both player sides against extracted USA models. All four JP/USA animation lists are byte-identical (84 entries each; SHA256 1edf074381ffd6e878037ae28c987e4c33bd42ec470499c2702dea47803bdc9e).
- Full role classification: 25 direct equivalents, 42 adapted-grid entries, five reused variants (four extra SOLO choices and LOSE3), ten differing-role substitutions, one MISS6 adaptation, three stock-empty choices, one repeated fever variant. These are content classifications, not a claim of fresh gameplay acceptance.
- Differing-role substitutions: POSE1 -> ATTACK2 (64), POSE2 -> WALK (61); MISS1..5 -> TIRED (69); GUARD -> HIT1 (66); REFLECT -> HIT2 (67); TIRED -> CAUGHT (70). POSE1/2 and GUARD/REFLECT lack same-named BAG1 counterparts, so replacements need an explicit adaptation. MISS6 -> HIT3 (68) also has no direct six-way BAG1 MISS equivalent.
- Corrected an early suspicion during this task: all nine shared SOLO_4/8/16 actions belong to the correct family. BAG1 and BAG2 order their request codes differently. SOLO_8_D/E/F reuse SOLO_8_B/C/A, SOLO_16_D reuses 16_A, and LOSE3 reuses LOSE1.
- Dance-grid comparison: all 42 primary cells match the current independent cell formula using original executable request tables. Nine of ten alternate selections match BAG1's native predecessor dispatch. Slot20 after previous slot11 uses BAG1 alternate20 although the native BAG1 dispatch would choose19 (predecessor31). Three level-up edges skip backwards/nonadjacent BAG1 cells: destination alternate slots20,14,31. Data proves the dispatch/cell differences; a visible in-match jump was not newly measured.
- Twelve original entries have no exact installed reference: 3,6,7,10,12,13,24,26,28,30,36,42. Comparing only the motion prefix before info/events leaves eleven absent motions: the same list excluding36 (its motion is represented by another entry). Three absent primary dance moves are C/F/J; the remainder are transition variants.
- FEVER1/2 are original BAG1 animations82/83 with their established muted-cue policy; FEVER3 repeats82. The eleven duet animations remain BAG2 stock with muted Heat cues. WIN4 and FEVER4/5 are empty in stock BAG2 Heat too: they are not port regressions. FUN_800326D4 pads the duet table to slot126 using NEUTRAL references before appending the eleven entries; those virtual padding references are not missing asset records.
- Visual reference completed through native BAG1 Dance View: all 66 choices, 198 captures, continuous 268.266667-second 640px video (23,188,127 bytes). Pilot was corrected to unbox PowerShell ConvertFrom-Json's array before the full run; all 66 timeline indices/names and 198 image paths were validated. Reviewed the complete steps/specials/poses contact sheets; full images/video remain local.
- Deliverables: C:/Users/israe/Documents/Codex/2026-10-30/ho/outputs/heat-animation-comparison/comparison.md (complete 87-row comparison + 84-source inventory), comparison.html, comparison.csv, full-animation-audit.json, video and three contact sheets. Full timing/capture scripts are in ho/work/bag1-reference. The complete comparison is finished; conversion/runtime corrections are intentionally not applied in this task.

### Heat animation-role experiment (2026-10-31)
- Data policy: tools/bag1import/profiles/heat-animation-policy.json. Shared animation_policy.py applies held poses, required events and original predecessor dispatch; the legacy Heat adapter remains the caller. Input hashes pin the original executable/model evidence.
- Exact correction: BAG2 TIRED slot78 now uses BAG1 TIRED69, not CAUGHT70. Alternate slot20 now chooses source19 after predecessor31; all ten alternate choices agree with the native BAG1 table. The three nonadjacent grid edges remain unresolved; this does not claim full grid optimization or complete source-motion coverage.
- Explicit experimental adaptations (BAG1 lacks same-named counterparts): GUARD uses DODGE65 with original BAG2 event (1,1,902); REFLECT uses ATTACK2 64 with (1,1,903), without a type16 launch. Original Heat DBI handles 0x386/0x387 by calling 0x8009768C/0x80097694 in match modes. POSE1 uses ATTACK2's held final posture; POSE2 holds WAIT60 rather than walking. MISS1..6 use HIT1/HIT2/HIT3 twice, replacing five tired loops. These are adaptations for comparison, not recovered original BAG1 guard/miss variants.
- Shared alternate_payload.py and rebuild_animation_payload.py repack changed animation members into DUMMY.BIN, preserving unrelated archives, stock offsets/sizes and mesh bytes. Rebuild CLI takes explicit --package --index --animations --entries --output; it creates a new candidate directory and never deploys. Validate guest scratch capacity and native behavior separately before deployment.
- Candidate payload SHA256 9629d66cc72d2f7f2329069f4be3da59a26265d4c86fa087d49a0f800bc8ecad, 3018752 bytes (1474 sectors). Model A/B sizes 344168/343464; P1 scratch interval 0x800DDB18..0x80154DB4 is 488092 bytes. Stage, voices, solo/duet choreography and all four meshes are byte-identical to the prior package.
- The generated B1_ALT_CONTENT_TAG hashes payload bytes into online identity, including changes that keep entry sizes equal. make_alt_entries.py also emits the tag. Existing selector regression passes; no fresh two-PC test is claimed.
- Fresh full native 2P Heat BAG1 vs Heat BAG1 match: dance starts at frame4414, results12258, solo fever1 begins12891 (req161, slot102), return to selection13839. Test tag heat-animation-policy-duet is historical intent; the observed fever was SOLO. Unchanged duet assets reuse prior evidence, not a new duet run.
- Tests: eight original-data policy checks, five shared policy/repack checks and five announcer checks passed; selector/MIPS guards passed. Installed audit checks 404 model slots plus unchanged solo/duet entries; all four model lists agree with the converter. Remaining extra-role substitutions are reported as documented_adaptation.
- Evidence/backups: _work/animation-policy (baseline package, candidate, installed audit, preservation, isolated settings/cards and match logs); _work/shots/heat-animation-policy-duet_sheet.png.
- Native viewer testing required a debug-only unlock: BAG2JP_TEST_DANCE_VIEW_CHAR=0 (valid 0..13), gated by BAG2JP_ANIM_TRACE=1 and the original BUST_A_MOVE_2 RAM header. Nine compiled-C guard cases passed (absent/invalid ID, tracing off, mismatched header, existing flag). Main-menu availability is computed from original clear flags at 0x8004E2F7; the boot-only manifest attempt was rejected and retained under _work/animation-policy/rejected-startup-unlock-package, outside installed mods.
- Viewer controls must be isolated: separate P2 keys and disable duplicate P1 analog direction bindings during tests, restoring originals afterwards. Count-only pilot selected DODGE instead of TIRED and is NOT accepted evidence. capture_dance_view.ps1 can read the observed short index at 0x801BFA98 (row0) through BAG2JP_WATCH, mapping 0xFFFF to the blank choice; 88 total choices. This avoids guessing from key counts. Cross (X) plays the playlist. The observed-index TIRED pilot was visually verified against BAG1.
- Fresh observed-index Dance View batch: POSE1/2, MISS1..6, GUARD, REFLECT and TIRED, eleven verified indices and 33 captures. Visually reviewed the labeled contact sheet; TIRED matches original69, poses hold and defense adaptations render. _work/animation-policy/viewer-verified; user panel ho/outputs/heat-animation-fixes/result.html. Test process closed; settings, bindings and mod state restored byte-for-byte, personal cards unchanged. Debug environment unlock is absent on normal launches. The initial misindexed pilot is excluded.
