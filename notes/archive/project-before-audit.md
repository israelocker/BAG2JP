---
id: project-builds-folder
title: "Project: Builds, Folders and Saves"
tags: ["project", "builds", "saves", "resume"]
summary: "Build history, folder structure, save data management and resume points for BAG2JP"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-26"
updated: "2026-11-01"
---

# Project: builds, folders, saves, resume

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

## Save data
- saves\card1.mcd = user's save (converted from a DexDrive .gme, header 3904 bytes stripped).
- saves\card1.original-empty.mcd = the empty card the runtime created first.

## Open items
- HD texture pack (dump + Real-ESRGAN); see betinn notes sec. 12 / 12.1 (needs the HD cache-cap
  patch in the framework).
- Native-wide cull sites in stage overlays (only if native-wide is wanted again).

## Historical resume instructions (Claude's former VM; do not run on Windows)
1. bash ~/mnt/Dev/Tools/vm-setup/setup_vm.sh
2. tar xzf BAG2JP-project-snapshot.tar.gz -C ~/work ; tar xzf ghidra-project-linux.tar.gz -C ~
3. game.toml disc= must point to the VM path for generate; to D:/... for the Windows build.

## Tools (D:\Dev\Tools, 2026-10-28)
- pcsx-redux: PS1 debugger (nightly 29906.20261028.31, SHA1 22E426A1..., portable config pcsx.json).
  Boots the JP disc with OpenBIOS. Use for breakpoints / memory watch on the original JP and US games.
- realesrgan-ncnn-vulkan (RTX 3090), ollama (qwen3-coder:30b, qwen3.8:27b), local-llm-mcp,
  local-vibes (bash disabled; always pass working_dir + read_only), ghidra_12.1.4_PUBLIC + ghidra-mcp-python,
  ghidra-scripts\DecompileExport.java (headless export). Git 2.56 at C:\Program Files\Git.

## Testing and debugging (2026-10-30)
- One-call test: Desktop Commander (powershell) `D:\Dev\Tools\winshot\bag2_run.ps1 -Tag t1 -Shots '6400,9000x4,11300' [-Cues] [-Audio] [-Env "A=1"] [-Watch "addr:size,..."]`
  closes the game, starts a 2P Heat-vs-Heat match on the exp build (trace on, autoplay p1_2p/p2_2p from state.toml), and
  starts a detached watcher (bag2_shots.ps1) that captures the window at those game frames ("FxN" = N back-to-back shots;
  frames from bag2jp_frame.txt, written every 6 frames by the debug plugin; shots land within ~6 frames).
- Historical VM command: `python3 tools/test/bag2_report.py --tag t1 --frame 11400` (or `--until 'phase 2/'`; waits <=160 s per
  call, call again to keep waiting). Prints state, phase timeline, fever anims, run report, cue ids per phase (-Cues),
  audio template hits (`--find x.wav ...` on an -Audio run) and writes one contact sheet `_work\shots\<tag>_sheet.png`
  (`--crop x0,y0,x1,y1` fractions to zoom into a region).
- Debug plugin env vars (bag2jp.anim_trace): BAG2JP_ANIM_TRACE, BAG2JP_WATCH, BAG2JP_RAM_DUMP, BAG2JP_AUDIO_DUMP,
  BAG2JP_CPU_SKILL; sound cue slots 0x8006D9F6 + 8*slot. Audio analysis: D:\Dev\Tools\audio-probe (README).

## Codex build/test environment (2026-10-30)
- Recovered build tree: D:\Dev\Recomp\BAG2JP-codex-build\BAG2JP; build-win-codex.
- Build: wsl.exe -d Ubuntu --exec bash /mnt/d/Dev/Tools/codex-integrations/build_bag2jp.sh (llvm-mingw 20261020, -j 2).
- Reports also run directly with Windows Python + Pillow: python D:\Dev\Recomp\BAG2JP\tools\test\bag2_report.py --tag <tag> --timeout 0.
  The report now resolves the Windows game/shot paths; legacy Claude VM defaults remain for Linux.
- Wait for the test game process to exit before copying BAG2JP.exe; verify the deployed SHA256.
- Independent Heat BAG1/BAG2 stage picker: see the latest section of notes/bag1-stage-song.md.

## Local workflow helper (2026-10-30)
- Current commands, interpreters and regression checks: `C:/Users/israe/.agents/skills/project-config/bag2jp.md`. The helper `tools/workflow/bag2_workflow.py` checks Git, pins, paths and drift without synchronizing files; `metrics.json` and full logs go under `_work/workflow/<UTC timestamp>-<tag>/` while stdout stays compact.
- The helper does not deploy, launch/close games or alter settings/cards. It records local durations, not cloud tokens or billing; game acceptance requires separate in-game evidence.
