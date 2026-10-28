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
