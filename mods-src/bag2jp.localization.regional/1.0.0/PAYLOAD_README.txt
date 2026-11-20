payload omitted (155 MB): regenerate with tools/build_regional.py (script not present in this tree).

2026-11-19: the LBA179 (BUST2.BIN DF2_ header) overlay was reduced from the full
2048-byte sector (003_0000179.bin) to its only 2 changed bytes at disc_user offset
366692 (payload/003_0000179_logo.bin = 50 3c; stock 16 3b = size field of DF2 entry 11),
so move-viewer packages that patch other header size fields compose with it.
Reapply after any regeneration: py -3.13 tools/move_viewer/regional_sparse179.py
(it expects the full-sector payload and edits manifest.toml in mods-src and exp-8mb).
