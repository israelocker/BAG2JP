---
id: ui-hd-fonts-mods
title: "HD Fonts & UI MODS"
tags: ["ui", "fonts", "mods", "keyboard"]
summary: "HD font texture packs, in-game MODS menu configuration and keyboard rebinding for BAG2JP"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-27"
updated: "2026-11-01"
---

# HD fonts/UI packs, in-game MODS menu, keyboard rebinding

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
