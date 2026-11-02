---
id: regional-content-launcher
title: "Regional Content & Launcher"
tags: ["regional", "launcher", "localization", "songs"]
summary: "Regional song options, CD-quality audio, announcer configurations and Launcher settings for BAG2JP"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-29"
updated: "2026-11-01"
---

# Regional content, songs and announcer options, CD-quality songs

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

## Defaults: Japanese songs and announcer (2026-10-29)
- Package bag2jp.localization.regional: options `songs` and `announcer` now default to "japanese"
  (were "international"). Changed in mods-src and in the installed copies (exp install, netplay_peer2).
  A state.toml with an explicit value keeps it (the exp install has songs = "cd", Japanese vocals).

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
