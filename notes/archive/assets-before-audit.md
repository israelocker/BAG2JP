---
id: asset-toolkit-extracted-data
title: "Asset Toolkit & Extracted Data"
tags: ["assets", "archive", "extraction", "layout"]
summary: "Asset toolkit layout, extracted data structure and verification for BAG2JP archives and BAG1 imports"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-26"
updated: "2026-11-01"
---

# Asset toolkit, archive layout, extracted data

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
- WARNING: the asset folders of archive entries 17-52 (choreography_a/b) were named by order, not by character. The game
  picks them with main exe table 0x8005510C[char id*2 + fever type-1]: Heat (id 0) = entries 22/40 = folders
  "kelly/choreography_a|b". Use tools/bag1import/fever_entries.py.
