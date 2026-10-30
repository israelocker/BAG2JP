# BAG2JP — Bust A Move 2: Dance Tengoku Mix (Japan), PS1 -> native Windows recompilation

## Game
- Disc: D:\Games\Bust A Groove 2 (Japan)\ISO\Bust A Move 2 - Dance Tengoku Mix (Japan).cue
- ID SLPM-86219, boot SLPM_862.19, entry 0x80035D98, load 0x80010000, text 0x4D000
- Track 01 MD5: e66918a9a2e5102464c60eab26e39169
- Stable build: D:\Games\Bust A Groove 2 (Japan)\BAG2JP-win\BAG2JP.exe
- Experimental 8 MB build: D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\BAG2JP.exe

## Folder contents
- BAG2JP-project-snapshot.tar.gz  full PSXRecomp project (no build dirs)
- ghidra\                         Windows Ghidra project (used by GhidraMCP)
- ghidra-project-linux.tar.gz     headless Ghidra project from Claude's VM
- ghidra-scripts\                 FuncStats.java, ExportSeeds.java
- mods-src\                       source of title mod packages
- releases\                       v1..v4 executables + configs
- assets\                         organized, extracted game data (see assets\README.md)
- SLPM_862.19                     game executable (for Ghidra)

## v1 base build (2026-10-26)
1. setup_project.sh (PSXRecomp 1a3fc0db, recomp-ui 3f1d6f1), --region JP --players 2.
2. Ghidra 12.1.4 + ghidra_psx_ldr: 1171 RAM functions, 878 named (PsyQ 4.4.0), 293 game functions.
3. ExportSeeds.java -> seeds/ghidra_funcs.txt (588 JAL seeds + 1130 Ghidra entries, union)
   and 876 names in symbols.toml. Generated functions: 1156 -> 1468.
4. Windows cross-compile from Linux with llvm-mingw 20261020:
   cmake -S . -B build-win -G Ninja -DCMAKE_BUILD_TYPE=Release \
     -DCMAKE_TOOLCHAIN_FILE=psxrecomp/cmake/toolchain-mingw-w64.cmake \
     -DCMAKE_FIND_ROOT_PATH=<llvm-mingw>/x86_64-w64-mingw32 -DPSX_ENABLE_VULKAN=OFF \
     -DCMAKE_CXX_FLAGS="-Wa,-mbig-obj -include exception"
   cmake --build build-win --target psx-runtime -j 2
   (-include exception: toml11 uses std::terminate without <exception>; libc++ is strict)
- First Windows test: intro FMV, title, menu, attract demo, character select, 1P match OK.
- Keyboard (keybinds.ini): Start=Enter, Circle=S (confirm, JP), Cross=X (cancel).

## v2 graphics (releases\v2-9x-pgxp-16x9)
Research: framework docs (config_schema [video], ENHANCEMENTS G1.x PGXP, WIDESCREEN),
BAG2 USA port (betinn notes/recomp.md 10-12), BAG1 USA port game.toml, DuckStation guides.
- CMakeLists: PGXP option on psxrecomp_add_game_runtime (hook flavor, overlay flavor 2) + src/bag2jp_mods.c.
- src/bag2jp_mods.c: plugin "bag2jp.widescreen" -> psx_mod_set_fixed_display_aspect(16,9).
- mods/preloaded: bag2jp.enhancement.widescreen (default on), psx.enhancement.pgxp override
  (default on, precise culling on).
- game.toml [video]: internal_resolution 4k (9x), render_thread, geometry_correction +
  perspective_texturing, pgxp_depth_buffer off, texture_filtering xbr, texture_lod mipmap +
  anisotropic 8, dithering off, FXAA off, linear present + fmv_filter bicubic + fmv_chroma_smoothing.
- Measured ~59.7 fps in a match.

## v3 widescreen squash mode (releases\v3-9x-pgxp-16x9-squash) — current stable
- Native-wide (v2) left floor polygons missing at the LEFT edge: the stage renderers reject x < 0.
  The user confirmed DuckStation's widescreen hack had no such holes.
- [widescreen] native_wide = false: GTE X-squash + wide present (same as DuckStation/Beetle);
  the game's own 4:3 culls land on the 16:9 edges. game.toml only, no rebuild.
- hud_sprt_squash / auto_ui_squash = true split the step bars (thirds pivot, both "edges" and
  "in_place"); left false: the in-match 2D HUD stretches 4/3, like DuckStation.
- Menus, character select and FMV stay 4:3 (gte_game_mode).

## v4 experimental 8 MB (D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb)
- Separate install (copy of v3 with its own memory card); the stable install is untouched.
- Package mods/installed/bag2jp.experimental.expanded-ram (source in mods-src):
  [[requirement]] psx.enhancement.8mb-ram + [[patch]] main_exe 0x80035E48 00 00 20 00 -> 00 00 80 00.
  0x80035E48 = RAM size read by stup1 (PsyQ 2MBYTE.OBJ): sp = 0x80000000|ramsize,
  InitHeap(0x8008E784, ramsize - 0x8000 (stack) - 0x8E780).
- Verified: sp at exit = 0x807EA458 (stack at the top of 8 MB), 1P match at 59.9 fps, save OK.
- The game loads characters/stages at fixed addresses and has no malloc of its own, so the extra
  RAM is free for mods; it changes nothing by itself.

## v5 experimental autoplay (releases\v5-exp-autoplay, installed in BAG2JP-exp-8mb)
- Package bag2jp.feature.autoplay (Gameplay > "Autoplay (P1)", default OFF; enabled only in the
  exp install via mods\state.toml). Native plugin "bag2jp.autoplay" in src/bag2jp_mods.c
  (copy in mods-src\bag2jp.feature.autoplay). Only acts in mode 1 (one-player game).
- Game module system/005.dbi loads at 0x8008F890 (JP; the USA build uses 0x8008F6C0, -0x1D0).
  RAM: mode 0x8005D2C4 (0 demo, 1 1P, 2 2P), human 0x8005E6C8, CPU dancer state 0x8005CF08 + p*0x24
  (+0x10 step counter, +0x0C timing offset, +0x14 move id), skill byte 0x8005E661 (+10 per stage).
- How a match picks the input source each frame (0x8009A994..): s1/s2 = "P1/P2 reads the pad";
  pad route = FUN_80011e38, CPU route = FUN_80099c0c (scripted presses from timing tables).
- Patches (vblank plugin, re-applied whenever the module is reloaded; all guard words checked):
  0x8009A9A4 bnez -> b   (P1 never reads the pad in mode 1)
  0x8009A9CC beqz -> b   (same for P2 when the human uses controller 2)
  0x8009ADC8 beq $s4,$v0 -> nop (human also gets the CPU per-measure setup/judgement)
  Instruction hook 0x80099CD0 (bgtz $v1): blocks the random fumble (rand % ((skill+50)*8) == 0
  -> step = -1) for the human player only; the CPU opponent is unchanged.
- First attempt only nop'ed 0x8009ADC8: the player still read the (empty) pad, so only 1-key
  moves scored. Root cause found by disassembling 005.dbi with capstone.
- Verified: 1P Heat vs Kitty-N, no input: combos/COOL, YOU WIN 42530-18040, advances to stage 2;
  clean exit at frame 18618.
- Live switch (same session): hold Select + press R1 on controller 1 (keyboard default Right Shift + W).
  The vblank plugin watches P1 held buttons at 0x8005E870 (Select 0x0100, R1 0x0008) and patches /
  restores the stock words within one frame. Launcher option "Active at start" (boolean, default true)
  sets the initial state; it also has an option-changed callback for the in-game menu (F10 / Ctrl+L),
  but that menu could not be opened through computer-use key injection, so it is untested.
- Verified: autoplay on (Heat 4050) -> Select+R1 -> Heat stuck at 4680 with MISS while Strike scored
  -> Select+R1 -> 5 COMBO, 14380. Note: computer-use key taps are too short for the game; use hold_key.
- Launching tip: Explorer double-clicks on the exe are unreliable under computer use; open the exe
  path directly.

## v6 experimental HD intro (releases\v6-exp-hd-intro, installed in BAG2JP-exp-8mb)
- Package bag2jp.enhancement.hd-intro (Video > "HD Intro", default ON), plugin "bag2jp.hd_intro" in
  src/bag2jp_hd_intro.c (copy in mods-src). Movie file: <exe dir>\movies\BUST2_OP.mpg; without it the
  original intro plays.
- Source: D:\Dev\Bust a Groove 2 - Intro - HD.mp4 (1440x1080, 29.97 fps, 62.5 s). Converted with
  ffmpeg -i in.mp4 -c:v mpeg1video -q:v 2 -bf 0 -g 15 -c:a mp2 -b:a 256k -ar 44100 -ac 2 -f mpeg BUST2_OP.mpg
  (87 MB; copy in assets\video\BUST2_OP_hd.mpg). Decoder: pl_mpeg (MIT, third_party/pl_mpeg/pl_mpeg.h).
- How: the game still plays STR/BUST2_OP.STR (LBA 214715, 9320 sectors = 62.1 s at 2x). The vblank
  plugin starts when cdrom_get_delivered_lba() enters the first 600 sectors of the STR and stops when it
  leaves the extent or stalls 30 frames (Start skip). Video: worker thread decodes, HUD draw callback
  (psx_host_set_hud_draw_cb) shows it full-window 4:3 over the game. Audio: PCM plugin overwrites the
  SPU mix with the MP2 track; its sample count is the clock the video follows.
- Framework change (local, patches\psxrecomp-host-movie-layer.patch): gl_renderer_draw_host_movie() in
  gpu_gl_renderer.c/.h (own texture, linear, aspect fit, black clear). Re-apply after a framework update.
- Diagnostics: bag2jp_hd_intro.log next to the exe (activate/start/stop, frames shown/dropped).
- Verified: full play 61.55 s audio, 1845 frames shown / 0 dropped, then demo; plays again on the next
  attract loop; Start skips straight to the title menu.
- Next (user request): alternate intros. First boot always BAG2 intro; afterwards
  BAG1 intro -> demo -> BAG2 intro -> demo ... BAG1 HD source: D:\Dev\Bust a Groove - Intro - HD.mp4
  (40.4 s, shorter than the STR: will need to end the guest movie early).

## Regional content (Launcher) - bag2jp.localization.regional (installed in BAG2JP-exp-8mb)
- One feature, 4 choice options (japanese / international, default international):
  title_screen (system/016 002,003,005,006 + 004 subtitle hidden; system/012/004 ranking logo),
  boot_logos (system/011.bpe 000,001 Enix (R); 004,005 Frame Graphics: US TIMs re-headed to the JP
  VRAM/CLUT positions; 011 grows 314 bytes inside its slack -> BUST2.BIN header sector 179 updated),
  hiro_icon (pack_a_p1/pack_b_p1 000.tim of all 18 characters, system/015.bpe 001, Hiro packs a/b
  002/003 + p2 001/002 incl. his alt-outfit portraits), stage_signs (stages 199/002, 201/004,
  202/003,004,006,007, 203/007, system/015.bpe 033).
- 015.bpe is shared by hiro_icon and stage_signs: one overlay per non-japanese combination.
  Re-encoded 015 is smaller than stock; the stock header size is kept (BPE has its own end offset).
- US disc layout: BUST2.BIN has 34 extra entries; JP entry i >= 53 == US entry i+34. US system
  modules: game module = US system/004.dbi (JP 005.dbi). US title = US system/014.
- Builder: mods-src/bag2jp.localization.regional/tools (groups.py, build_regional.py; needs the
  extracted US tree from: psxassets extract --profile profiles/bag2jp.json <US cue> <dir>).
- Verified in game: both values of title/boot logos/hiro icon; TV studio stage loads clean.
- Supersedes bag2jp.localization.us-title-logo (disabled in exp state.toml).
- The older regional-content package (previous session) and us-title-logo were removed from the exp build; sources kept in mods-src/_superseded.
- Option announcer (added): menu narrator = XA/BUST2_02.XA ch 4,5,6 (264 s each; same interleave on both
  discs, US raw sectors copied with JP MSF headers, 20 disc_raw overlays of 2048 sectors, 93 MB) and
  title voice = XA/BUST2_04.XA ch 6 (JP 188 sectors / US 143: US audio in the first JP slots, rest
  silent ADPCM, JP subheaders kept, EDC recomputed; 1 overlay). Builder tools/build_xa.py.
  User confirmed by ear that these channels are the narrators. In-game run OK (title/menu/select).
- Option songs (added): XA/BUST2_01.XA ch 2,4,5,7 (US takes 19/118/14/19 sectors shorter): US audio in
  the JP slots, silent ADPCM tail, JP subheaders/EOF kept, EDC recomputed (14 disc_raw overlays) +
  song names on character select (system/013 014,017,018,020). Builder tools/build_xa.py.
  Verified: practice on Comet's stage runs (audio by ear still to confirm); Sushi Planet shows the
  US menu sign (stage_signs ok). Package total 155 MB, 103 overlays.
- Songs third choice "cd" (CD quality, Japanese vocals): soundtrack CD AMCM-4432 (FLAC in
  assets/music_cd/Bust a Move 2) re-aligned offline to each in-game edit: match.py (which CD track),
  segmap.py (piecewise game->CD time map, Viterbi over splice offsets), blockmap.py (100 ms blocks +
  gain), render_all.py -> music_hq/<XA>_ch<N>.flac (44.1 kHz, unmapped blocks = game XA audio,
  5 ms crossfades at splices). 13 songs: BUST2_01 ch0-7, BUST2_02 ch0-3, BUST2_04 ch7; coverage
  72-96 % (BUST2_02 ch3 Acid Line lowest). Tools in mods-src/.../tools/hq.
  Runtime: framework hook cdrom_set_xa_host_filter (patches/psxrecomp-xa-host-filter.patch) hands
  each decoded XA sector (2352 frames at 44.1 kHz) to plugin bag2jp.hq_songs (src/bag2jp_hq_songs.c,
  dr_flac from libchdr), which copies the same span of the FLAC (sector k of channel = frames
  k*2352). SFX, music volume, pauses, timing stay the game's. Resource music_hq (directory, default
  inside the package). Log: bag2jp_hq_songs.log.
  Verified: activates, Heat vs Strike opens BUST2_01 ch1 (Strike) and the match runs; audio by ear
  pending.
- CD songs v2 (2026-10-27, tools/hq/render2.py, previous files kept in ~/work/hq/music_hq_v1): user
  heard "scratched record" cuts and shouts that come and go (most in Hiro's song). Causes in v1:
  blockmap anchors flipping between repeated CD passages (Strike 114 jumps, Robo-Z 378, Capoeira 39),
  a gain step every 100 ms block (zipper / dips), short game-audio inserts cutting shouts in half,
  5 ms crossfades. v2: mode-filtered offsets (+-1.2 s, 15 ms tol.), continuous gaps filled with CD,
  splices refined by xcorr + least-disagreement switch point, 25 ms equal-power crossfades, smooth
  gain curve (2 s median), and game audio for whole spans where the game has content the CD lacks
  (shouts; e.g. Hiro 1.87-3.13 s, 12.42-12.78 s). Runtime verified clean: a full Hiro song in Dance
  View logged no seeks/slow reads (log now reports jumps and reads > 4 ms).
- Command buttons (option command_buttons, default international) - DONE 2026-10-27.
  Arrows were never different: Right red / Down blue / Up green / Left pink come from palette indices
  in the shared texture (system/010/001 + 010/004 row 0; Up/Left use 010/005 row 14). What differs is
  the face-button icons (Triangle/Circle/Cross/Square): JP draws them with 010/004 row 0 (yellow),
  US with its extra palette US system/008/010.tim (VRAM 1008,64, 16x4: green/blue/pink/red), one row
  per button. Found by dynamic trace (temporary plugin hooking every `sh rt,0xE(rs)` in 005.dbi):
  icon loop in 005.dbi, CLUT store at 0x80098398 `sh $v0,0xE($s0)` (US 004.dbi same loop uses image
  slot field 0x1C4 + row 0..3). Image table at 0x80054C44 (+0xE/+0xF u/v base, +0xA4 clut of 010/004,
  +0xD4 clut of 010/005, stride 0x30). Icon kind from $s5=u: 0x80 Circle, 0x96 Square, 0xAC Triangle,
  0xC2 Cross (v=0x40), 0xD8 Right arrow; Down u0x80 v0x4D; Up/Left u0xB6/0xCC v0x4D.
  Patch: overlay (sector 492) writes the 4 US rows into all-zero rows 7/11/12/13 of JP 010/005.tim
  (same file size) + the US pink tint of row 14; plugin bag2jp.command_buttons
  (src/bag2jp_command_buttons.c, instruction hook at 0x80098398) sets $v0 = clut(0xD4)+row<<6
  (Triangle 7, Cross 11, Square 12, Circle 13). Applied at game start (no live switch, the rows come
  from the overlay). Tool: tools/build_buttons.py (called by build_regional.py). Verified in a match:
  red circle, blue cross.
- 2P VS loading screen (option vs_screen, default international) - DONE 2026-10-27.
  US (SLUS-01159, decompiled with Ghidra headless: _work/vs/us_decomp.txt; JP: jp_decomp.txt):
  FUN_80033324 draws for game modes 0 and 2 (2P) a static picture from US BUST2.BIN entries 51-86
  (P1 entry: red flames, blue flames, VS, P1 portrait, name [, extra]; P2 entry: portrait, name
  [, extra]); char -> entry tables 0x80056990 / 0x800569b4 (alphabetical files). Screen 512x240:
  flames x 0/256, portraits x 0/256 (P2 mirrored except chars 9-11), names centred (112,204) /
  (400,204) with CLUT row = command difficulty (US 0x8005FBBC = JP 0x8005E6CC), VS centred (256,204),
  extras chars 11 (Robo-Z) / 13 (Sushi Boy) additive. Announcer "P1 VS P2" voices + wait are already
  in JP (FUN_800342dc, sound ids 0x30x0/0x30x1, 0x3130), so only the picture is ported.
  Implementation: plugin bag2jp.vs_screen (src/bag2jp_vs_screen.c): HD layers (resource vs_hd,
  tools/build_vs.py: TIM decode + Lanczos to a 2048x1536 4:3 canvas), composed on a worker thread as
  soon as both characters are known, drawn full-window on the host HUD layer while the JP loading
  function runs (timer 0x80089210 / counter 0x80089214 changing, hide when state 0x80089215 == 0x0C
  and announcer step 0x80089234 > 3). HUD layers share src/bag2jp_hud.c (mux; HD intro uses it too).
  Verified: Heat vs Comet, Chichi&Sally vs Michael Doi, shown during the whole load, no flicker.
- Phase 1 (Launcher regional choices) complete. Endings XA (BUST2E01-24) identical JP/US.
- Difference sheet: mods-src/bag2jp.localization.regional/jp_vs_us_differences.png

## US title logo (installed in BAG2JP-exp-8mb\mods\installed)
- US disc: D:\Games\Bust A Groove 2 (USA)\ISO (SLUS-01159). Its BUST2.BIN has 501 entries (JP 467);
  the title menu is US system/014 (JP system/016). Same SEDT and same TIM sizes/VRAM/CLUT positions.
- Package bag2jp.localization.us-title-logo (Localization group): JP system/016 002/003/005/006 replaced
  by the US TIMs (logo halves, (c)2000 line, side banner); 004 (katakana "Dance Tengoku Mix" subtitle,
  identical in the US disc but not drawn there) made fully transparent (CLUT index 11 = 0x0000).
  make-mod: 1 overlay, 13 sectors at disc_user offset 1775616. Source PNGs + package in mods-src.
- The toolkit demo bag2jp.demo.red-menu is disabled in the exp state.toml (still installed).
- Verified in game: title menu shows the US logo, no subtitle.

## Asset toolkit and extracted data (2026-10-26)
- Toolkit: D:\Dev\Tools\psx-asset-tools (Python + Pillow; ffmpeg for XA/STR). Profile bag2jp.json.
- BUST2.BIN = DF2_ archive, 467 entries, 2048-aligned (sector slack per entry).
  BPE decoder = Philip Gage BPE at 0x8001F560 (header 'BPE_' + big-endian end offset).
  Module loader 0x8002BAC8 (table 0x80051934: module -> archive index; idx<5 DBI, else BPE->DBI).
- Layout (JP): 0-16 system | 17-34 / 35-52 choreography a/b | 53-88 character packs a (p1,p2 pairs) |
  89-124 models a | 125-160 packs b | 161-196 models b | 197-211 stages | 212-466 endings.
  Character order (from texture name labels): bi_o, capoeira, comet, heat, hiro, kelly, kitty_n,
  pander, robo_z_gold, shorty, strike, tsutomu, chichi_sally, columbo, hustle_kong, mcload,
  michael_doi, sushi_boy.
- system/016 = title menu (001 menu text, 002 logo); system/015.bpe = character select art.
- Extracted tree: assets\ (archive\, music\ 74 WAV channels, video\, disc_files\, catalog.csv).
- Verified: repack of the untouched tree == original BUST2.BIN (byte-identical).
- Verified end to end: palette edit of system/016/001.png -> make-mod -> 1 changed sector ->
  bag2jp.demo.red-menu in BAG2JP-exp-8mb\mods\installed -> visible in game (red menu item).

## Save data
- saves\card1.mcd = user's save (converted from a DexDrive .gme, header 3904 bytes stripped).
- saves\card1.original-empty.mcd = the empty card the runtime created first.

## Open items
- HD texture pack (dump + Real-ESRGAN); see betinn notes sec. 12 / 12.1 (needs the HD cache-cap
  patch in the framework).
- Native-wide cull sites in stage overlays (only if native-wide is wanted again).

## Resume in a new session (Claude's VM)
1. bash ~/mnt/Dev/Tools/vm-setup/setup_vm.sh
2. tar xzf BAG2JP-project-snapshot.tar.gz -C ~/work ; tar xzf ghidra-project-linux.tar.gz -C ~
3. game.toml disc= must point to the VM path for generate; to D:/... for the Windows build.

## HD fonts (texture pack, 2026-10-27)
- Text is drawn by FUN_8001fbfc (JP exe): per ASCII char 0x21-0x7F a 3-byte glyph record (u, v, width)
  from the font table 0x8005E2B8[font], common height; one SPRT per glyph from the system atlas
  system/000/000.tim (4bpp 256x240, VRAM 896,0); colour = CLUT row (000.tim rows at 896,240 or the
  palette-only 000/001.tim rows at 944,240). Several fonts share the atlas (thin, block, graffiti).
- HD: PSXRecomp HD texture packs (DuckStation texupload names). Source hash 0A12DA7F2427B35A (XXH3 of
  the upload), palette hash = XXH3 of the 16 CLUT words. tools/font_hd.py upscales the INDEX map
  (each index a layer, bicubic field, argmax, 2x supersampled AA, cutout alpha) x6 and colours it
  with all 32 palettes -> 31 unique replacements (whole atlas, P0-15). Real-ESRGAN (D:\Dev\Tools\
  realesrgan-ncnn-vulkan) tested on the dumps: noisy on tiny glyphs, not used for fonts.
- Installed: <exp>\mods\texture-packs\SLPM-86219\replacements\bag2jp_system_font; feature
  psx.enhancement.hd-textures enabled in mods/state.toml (replacements on, dump off; OpenGL).
  Source: mods-src\bag2jp.hd-texture-pack. Verified: character-select stats text smooth.

## Tools (D:\Dev\Tools, 2026-10-28)
- pcsx-redux: PS1 debugger (nightly 29906.20261028.31, SHA1 22E426A1..., portable config pcsx.json).
  Boots the JP disc with OpenBIOS. Use for breakpoints / memory watch on the original JP and US games.
- realesrgan-ncnn-vulkan (RTX 3090), ollama (qwen3-coder:30b, qwen3.8:27b), local-llm-mcp,
  local-vibes (bash disabled; always pass working_dir + read_only), ghidra_12.1.4 + ghidra-mcp-python,
  ghidra-scripts\DecompileExport.java (headless export). Git 2.56 at C:\Program Files\Git.

## Phase 2: in-game MODS menu (bag2jp.feature.mods-menu, 2026-10-28)
- OPTION MODE = module system/002.dbi (base 0x8008F890), FUN_80093388: labels via the text routine
  0x8001FBFC (font 1, colour 5 / 6 selected = 000.tim CLUT rows), cursor byte 0x80191EBD, per-menu
  cursor limit 0x8009C794[menu], cursor positions 0x8009C83C + idx*8 + menu*0x30 (x,y halves),
  label positions 0x8009C7AC (x,y words). Pads in RAM: held 0x8005E870/78, pressed 0x8005E872/7A
  (Circle 0x20, Cross 0x40, Up 0x1000, Down 0x4000).
- Patch (plugin bag2jp.mods_menu, src/bag2jp_mods_menu.c): limit 2->3, cursor slot 3 = (70,170),
  VIBRATION text `jal 0x8001FBFC` at 0x80093764 -> mod guest function 0x0F000100 that draws VIBRATION
  and then "MODS" (y 172; string placed in unused stack 0x400 below sp for the call; the Expansion-1
  guest allocation read back empty). Circle on MODS: instruction hooks on `andi v0,v0,0x20` at
  0x8009355C / 0x80093570 clear the bit and open the screen. While open (and until all buttons are
  released after closing) a pad transform feeds the game a neutral pad (SIO order bits: Up 0x10,
  Right 0x20, Down 0x40, Left 0x80, Circle 0x2000, Cross 0x4000).
- Screen: host HUD layer, 1280x960 canvas, text = game font 1 glyph table (0x8005E2B8[1] ->
  0x80050F44, height 10) over the HD font atlases (resource menu_assets: font_a/b NN.png = 000/001.tim
  rows). Items: regional options (8), HD intro / HD font (feature switches), autoplay (live).
  Saving: psx_mod_feature_set_option / psx_mod_feature_enable + psx_mod_save_selection (the
  emulation thread is the main thread); autoplay also psx_mod_set_option_live. Orange dot = applies
  on next start. Verified: label, cursor wrap, open/close without the game reacting, changes written
  to mods/state.toml and reverted.

## HD UI texture pack (menus and interface)
- Tools: mods-src/bag2jp.hd-texture-pack/tools/gen_ui_pack.py (plan, prepall, finishall),
  esr_each.ps1 (Real-ESRGAN anime x4, one process per file), validate_pack.py.
- 589 replacements (every archive/system TIM of the JP disc plus the US files used by the regional
  overlays, one per palette), installed in mods/texture-packs/SLPM-86219/replacements/bag2jp_ui.
- Real-ESRGAN in one long batch hits VK_ERROR_DEVICE_LOST and leaves black, inverted or striped
  outputs (this broke the title logo: black box). finishall now checks every upscale against the
  source (box-downscaled mean RGB error on opaque pixels, limit 30), queues failures in in_retry2
  for another per-file GPU pass, and uses the palette-index label upscale when it still fails.
  Final pack: ~530 ESRGAN, ~60 label. validate_pack.py: worst error 51 (a label image), all others <40.
- Checked in game: title screen (logo, menu items, side banners) and character select.
- STATUS: set aside (user not happy with the look; try another upscaler later). The pack was moved
  out of the install to _work/uipack/bag2jp_ui_removed; only bag2jp_system_font stays installed.

## Online play (generic PSXRecomp netplay vs BAG1-style step sync)
- Generic netplay enabled in BAG2JP (CMakeLists: PSX_NETPLAY ON + ENABLE_NETPLAY_IF_PRESENT, lobby
  ws://netplay.retcomm.net:8765). Launcher gets a NETPLAY button: LAN / Direct IP (no account) or
  Online Netplay (Discord sign-in, lobby server). LAN keeps vanilla content: our mods are off in the
  match (JP title, no HD intro / international VS). Both players need the same .cue/.bin (disc
  fingerprint in game.toml [netplay]).
- Tested on one PC with two copies (second copy: _work/netplay_peer2): Join Direct 127.0.0.1:7777 works
  (joining from the LAN list did not on one PC). CLI test: --no-launcher --netplay --net-slot 0|1
  --net-bind --net-peer (delay-sync). 2P VS: character select, stage select and the dance stayed in
  sync, host and guest inputs both applied, no desync lines (PSX_RB_PAD_TRACE=1 logs to stderr).
- Test helpers in D:\Dev\Tools\winshot: winshot.ps1 (PrintWindow capture of covered windows),
  postkey.ps1 (posts key messages to a window; works when another app holds the foreground),
  sendkey.ps1, focus.ps1, np_cli.ps1 (starts the two CLI peers), dbg.ps1.
- BAG1 step sync (bag.netsync, colleague's port, source not public): BAG1 FUN_800207bc(player) is the
  per-player bar update; CPU player = bits 2-3 of 0x80068704; CPU decision FUN_80020e10 returns the
  bar result (0x46/0x3c/0x32 judged, -1 miss, 0x6e attack, 0xaa dodge); human FUN_80020a7c; apply
  FUN_80022884 (CPU) / FUN_80022130 (human). The plugin replaces the CPU decision with results that
  arrive from the other PC. Decompile: _work/bag1/bag1_decomp.txt.
- BAG2 JP: the same logic is inlined in the game module system/005.dbi (base 0x8008F890), giant
  FUN_80099e90; per-bar 2-player loop around 0x8009B000: CPU path when mode 0x8005D2C4 == 0 or
  (== 1 and player != human 0x8005E6C8); result code at 0x8005CF1C + p*0x24 (0x6e attack, 0xaa
  dodge), timing at 0x8005CF14 + p*0x24, per-player block 0x8005E728 + p*0x32. Decompile:
  _work/game/jp005_decomp.txt.
- Current BAG2JP CMakeLists.txt (with netplay on) copied to patches/BAG2JP-CMakeLists.txt.

## Online step sync (bag2jp.feature.netsync)
- Plugin src/bag2jp_netsync.c (copy + manifest + default server list in mods-src/bag2jp.feature.netsync).
  Same model as StepMania/SMOnline: each PC plays against its own music; only bar results travel.
- MODS menu: ONLINE = OFF / LOCAL NETWORK / INTERNET / DIRECT IP / TEST (MIRROR) (option transport,
  next start) and ROOM CODE (4 letters/digits, pad editor: Circle edit, Up/Down letter, Left/Right move,
  Circle/Cross save; stored in line 1 of bag2jp_online.txt; re-read live while not linked).
- LAN: UDP broadcast on 47300 with the room code hash. P1 = higher random id.
- INTERNET: MQTT 3.1.1 (QoS 0, plain TCP 1883) meeting point, topic bag2jp/v1/<room hash>; servers in
  bag2jp_online_servers.txt (written with defaults on first run: HiveMQ, EMQX, Mosquitto; STUN Google,
  Cloudflare), tried in order on a worker thread. HELLO carries the STUN public address and the LAN
  address; both sides punch UDP holes for 10 s; until a UDP packet arrives everything goes through the
  broker (relay). Test switch BAG2JP_NETSYNC_RELAY_ONLY=1.
- DIRECT IP: host (line 2 of bag2jp_online.txt empty) listens on UDP 47100 and shows its public address;
  join = line 2 "ip:port". Host is P1. Needs the port forwarded on the host's router.
- Menus routed as before (port 2 = controller source + transform; MODS screen still works through the
  netsync transform via bag2jp_mods_menu_pad_filter / _reattach).
- Per bar: gate 0x8009ABC4 closes the local bar (FUN_800120F8) and sends it; the bar waits (max 180
  frames) for the other result. NEW: 0x8009A0C0 (bnez v0, beat advance) holds the beat that starts the
  next bar until the waiting bar is resolved (before this, a late result dropped the bar on one PC).
  Hold even when the result arrives that frame (the advance runs before the resolve).
- Out-of-sync check: STEP carries COOL/right-bar counts (0x8005E798 / 0x8005E7A8, P1/P2) at the close;
  a difference shows a toast. (Scores 0x8005E6F8 count up over time, so they differ by timing: log only.)
- Start barrier (READY) when the match module loads; ping/pong RTT on the status line ("slow" > 250 ms).
- Tests on one PC with two copies (keep both windows in the background: the copy behind the foreground
  game window was throttled to ~35 fps): LAN, internet with direct path (HiveMQ meeting, STUN, punch),
  internet relay-only (~400 ms RTT through HiveMQ from Lima): 40 bars, all identical on both PCs, waits up
  to 34 frames held correctly. Direct IP link OK (127.0.0.1:47100).
- Not tested yet: two real PCs on different networks (hole punching through real NATs), rematch/results.
- Tools: D:\Dev\Tools\winshot (bag2_two.ps1 [-RelayOnly] [-BArgs], bag2_vs_flow.ps1 [-FromTitle],
  winshot.ps1 [-Screen], postkey.ps1, focus.ps1).

### Auto pause when a window loses focus (online dance)
- During an online dance (after the start barrier), if either PC's game window loses keyboard focus
  (`SDL_GetKeyboardFocus() == NULL`: alt-tab, minimize, another app), BOTH PCs pause with the runtime
  host pause (`psx_host_pause_push("online")`: guest and audio frozen, last frame kept on screen).
- Message `M_FOCUS` (9): u8 focused, u8 paused, u16 match, u32 dance frame of the pause. Sent on every
  focus change and every 20 frames with the ping.
- OSD: "ONLINE  PAUSED - come back to the game window to continue" (this PC) or "... - the other player
  left the game window"; when both are back, "ONLINE  resuming in 3..." and both resume. The PC whose own
  window came back waits half a ping more so both resume together; leftover drift (half a ping) is
  absorbed by the bar hold.
- The vblank plugin does not run during a host pause, so an SDL timer (16 ms) keeps the link alive
  (net poll, pings, focus) and pops the pause. `s_mu` (SDL mutex) serializes the timer with the vblank
  plugin and the three instruction hooks. If the link drops or the dance ends, the pause is released.
- A first version compensated the "dance frames ahead" between PCs; removed: hold frames make that
  count run ahead without the song being ahead (it made one PC wait 2 s more).
- No-step-in-time on a bar where this PC has no steps either (result 0xFFFF) now writes "no bar" for
  the rival instead of a miss (result 0).
- Test switch `BAG2JP_NETSYNC_FOCUS=always` (this PC counts as always focused);
  `bag2_two.ps1 -BFocusAlways` sets it for copy B. `focus.ps1` now attaches to the foreground thread and
  falls back to minimize/restore (Windows foreground lock). New `keys_shot.ps1 -Ids "a,b" -Keys ... -Wait`.
- Tested on one PC (LAN): pause at dance start, mid-dance pause from either side, countdown in step on
  both, bar results identical through two pauses. Same-PC caveat: the background copy runs ~35-45 fps,
  so long songs pile up bar holds and the faster copy can leave the bar section before the slow one.

## Defaults: Japanese songs and announcer (2026-10-29)
- Package bag2jp.localization.regional: options `songs` and `announcer` now default to "japanese"
  (were "international"). Changed in mods-src and in the installed copies (exp install, netplay_peer2).
  A state.toml with an explicit value keeps it (the exp install has songs = "cd", Japanese vocals).

## Audio latency (game.toml [audio] buffer_ms)
- The runtime keeps an output buffer (DRC ring, target `buffer_ms`, default 180, allowed 30..500)
  plus the SDL device buffer (1024 samples = 23 ms at 44.1 kHz) plus Windows. The game's judge runs
  on its own clock, so the music heard lags the game by roughly fill + 23 ms + the OS.
- Probe: `BAG2JP_AUDIO_PROBE=1` (in bag2jp_netsync.c) writes bag2jp_audio_probe.log next to the exe:
  once a second fill/target/underruns, plus every frame gap > 40 ms ("stall"). `bag2_1p.ps1 -SetEnv`.
  Logs: _work/np_logs/audio_probe_*.log.
- Results, 1P autoplay, window focused:
  | buffer_ms | fill while dancing | underruns while dancing |
  | 180 | avg 164 ms (124..174) | none |
  | 90  | avg ~80 ms | one burst at song start (~6 s into the stage) |
  | 50  | avg 42 ms (26..92) | one burst at song start |
- The burst comes from a frame stall at song start: ~50 ms with the HD texture pack off, ~220 ms with
  it on (the pack holds only the HD system font, 31 images, preloaded at boot in 119 ms, so the stall
  is not PNG decode; likely the first upload/composition when that text appears). FLAC open is 0.2 ms.
  180 ms hid it; with less buffer it is a short audio gap at the start of each song.
- Set to 90 in the exp install and in the project game.toml (patches/BAG2JP-game.toml). Next: find
  and remove the song-start stall; then 50 (about 75 ms total) should be safe.

## In-game keyboard rebinding (MODS > KEYBOARD)
- New last row KEYBOARD in the MODS screen (kind 2) opens a second page: two columns with UP, DOWN,
  LEFT, RIGHT, CROSS, CIRCLE, SQUARE, TRIANGLE | L1, R1, L2, R2, START, SELECT, DEFAULT KEYS.
- O on a row: "PRESS A KEY"; the first keyboard key that goes down (SDL_GetKeyboardState, compared
  with a snapshot taken when the wait starts) becomes the binding. Esc or 10 s cancel. Esc, Tab and
  F1-F12 are refused (runtime hotkeys). After a bind, input is ignored until every key is released.
- Uses the runtime rebind API (psx_keybinds_set_button / _reset_player / _save, player 1): the change
  applies at once and is saved to keybinds.ini, the same file the launcher's Controls page edits.
  A key already used by another listed button swaps (that button gets the old key). D-pad rebinds
  also move the matching left-stick direction (ls_*), like the default map.
- The MODS rows shrink to fit the panel when there are more than fit at the natural size.
- SONGS / ANNOUNCER defaults in the menu model now match the package (Japanese).
- Tested by posting keys: bind Circle to D (live: D then opened menus), Circle to X (Cross swapped
  to D), DEFAULT KEYS restored the original map. Tool: winshot\bag2_kb_page.ps1.

## CD songs v3: CD audio only (2026-10-29, tools/hq/render3.py)
- User asked to drop the parts that blended in the game's own XA audio. v3 never plays game audio:
  unmapped blocks continue the CD from the previous offset; before the first reliable match (30-block
  window with 20 agreeing raw matches) blocks take that offset; no "game-only" spans; game-silent
  unmapped blocks stay silent. Only exception: a game intro before the CD track starts (pos < 0).
- Rendered and installed in the exp install for Heat (BUST2_01_ch0), Comet (ch2), Shorty (ch5) and
  Hiro (BUST2_02_ch0); v2 files kept in _work/music_hq_v2_backup. Game audio removed: Heat 5.5 s in
  9 pieces, Comet 3.1 s / 2, Hiro 3.4 s / 2. Shorty keeps its first 11.4 s from the game: the CD track
  has no such intro (CD starts at game 11.39 s; xcorr of the intro vs the whole CD < 0.03).
- Runtime: a full Comet song in 1P played with no seeks or slow reads. Previews (v2 then v3):
  _work/hq_v3_preview/*.mp3. Other 9 songs still v2: run `python3 render3.py <name>` and copy.
- 2026-10-29 (later): user approved v3 by ear ("mucho mejor el after"). All 13 songs rendered with v3
  and installed in the exp install (all v2 files in _work/music_hq_v2_backup). Added: in unmapped
  blocks the CD follows the game's level (gain = min(median, game rms / CD rms)), so game fades and
  endings fade the CD too. Songs with game-only intros/endings now play the CD's continuation there
  (largest: Kelly last ~12 s, Robo-Z last ~26 s partly, Capoeira 0.5-13.7 s and 135-141 s, Bi-o
  0-10 s, Strike 0-5 s); previews in _work/hq_v3_preview. Shorty keeps its 11.4 s game intro (CD
  has none).

## Release v7: online portable (2026-10-29)
- releases/v7-online-portable/BAG2JP-online(.zip, 457 MB, 537 MB unpacked): exe + configs + mods
  (CD songs included), no personal paths (game.toml disc line removed, settings.toml [disc] empty,
  no disc.cfg), no logs/saves/test files. Defaults: ONLINE = INTERNET, room code 2GWE, autoplay off,
  songs/announcer Japanese, [audio] buffer_ms 90, player_name "Player". LEEME.txt (Spanish how-to).
- First run with no disc: the launcher shows "No disc selected"; PLAY answers "Select a valid Disc
  first"; "Browse For Disc / SBI" opens the file dialog, then "Disc verified" and PLAY saves the
  path to settings.toml and disc.cfg (not asked again).
- Tested from the extracted zip (_work/portable_test): launcher > Browse > PLAY, joined room 2GWE
  on broker.hivemq.com, linked with netplay_peer2 (direct after the broker), both into 2PLAYER GAME,
  match start barrier and the focus pause on both PCs.
- New tools: winshot\realclick.ps1 (real mouse click at window fractions), typetext.ps1 (SendKeys),
  postclick.ps1 (posted click; does not work on the launcher), bag2_vs_flow.ps1 -AD/-BD.

## Windows installer (2026-10-29): releases/v7-online-portable/BAG2JP-Online-Setup.exe (451 MB)
- NSIS 3.08 (Ubuntu debs extracted into ~/tools/nsis, no root; added to Tools/vm-setup/setup_vm.sh).
  Sources: installer/bag2jp_online.nsi, settings.toml (disc path "disc_image/game.cue"), LEEME.txt
  (installed-game version), build.sh (payload = the portable zip extracted to ~/work/installer).
- Pages (Spanish): welcome (what you need) -> folder (default %LOCALAPPDATA%\Programs\Bust A Move 2
  Online, per-user, no admin) + "desktop shortcut" checkbox -> game disc (.cue + .bin; picking the
  .cue fills the .bin if it sits next to it; checks: files exist, .cue, single FILE line, .bin >= 100
  MB) -> install -> finish ("Abrir el juego ahora", optional LEEME).
- Install: game files (FLAC/MPG stored, rest zlib), .bin copied to disc_image\, game.cue written from
  the user's .cue with its FILE line pointing at the copied .bin, disc.cfg + settings.toml point at
  disc_image/game.cue (relative, resolved against the exe folder). Shortcuts: desktop + start menu
  "Bust A Move 2 Online" (BAG2JP.exe --no-launcher), "BAG2JP - Configuracion" (launcher),
  "Instrucciones", "Desinstalar"; HKCU uninstall entry. Uninstaller asks whether to delete saves.
- Tested end to end with real clicks (winshot\bag2_setup_test.ps1, bag2_uninstall_test.ps1,
  check_shortcuts.ps1): install into _work\installer_test, game opened from the finish page straight
  into the intro (disc found), joined room 2GWE; uninstall removed folder, shortcuts and entry.
- Bug found and fixed in testing: ${GetSize} is for folders; .bin size now via FileSeek END.
- 2026-10-29 (later): the zip and the installer now carry the user's memory card (saves\card1.mcd,
  the DexDrive save). The installer writes it with SetOverwrite off (a reinstall never replaces a
  player's card). LEEME: if the game does not pick it up, OPTIONS > MEMORY CARD > LOAD DATA > YES
  (tested: "LOAD OK").
- Correction (user): the save IS fully unlocked. The "?" cells are the real icons of the hidden
  characters; on an empty card those cells and DANCE VIEW do not appear at all. All my char-select
  tests had card1.mcd in place (copied before the first test), and the game loads the card at boot
  by itself. So shipping the card = everything unlocked, and both online players get the same grid.
  The CodeBreaker plugin attempt was therefore not needed; source kept in _work/bag2jp_unlock_all_wip.c
  (untested on an empty card). LEEME now says the save comes fully unlocked and loads by itself.

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
- Debug: BAG2JP_WATCH=addr:size,... logs value changes to bag2jp_watch.log.
