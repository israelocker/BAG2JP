---
name: "bag1-import"
description: "Port Bust A Groove 1 content (characters, dance moves, fever, voices, stages, songs, cameras) into the BAG2JP recompilation. Use when importing or fixing any BAG1 character, stage or song in BAG2."
---


## Codex compatibility
Use Desktop Commander for Windows files and processes. Project: D:/Dev/Recomp/BAG2JP; NOTES.md indexes its topic notes. Paths under ~/work and ~/mnt below belong to the previous Claude VM and require a verified Linux environment, mounts, source tree and cross-compiler. wsl.exe or an archive alone does not establish readiness. Do not provision a VM or extract archives over the existing project during migration. Preserve user edits and the stable game install. Use Codex's computer-use skill and documented APIs; Claude-specific tool names and VM process lifetimes below are historical examples.

# BAG1 -> BAG2JP import

For every character, first follow bag-character-pipeline and D:/Dev/Recomp/BAG2JP/notes/character-pipeline.md. Use bag-animation-matching for role/transition decisions and bag-reference-cache before visual capture. The Heat recipes below are historical adapters, not templates to clone for each new character.


Done so far: Heat (character, stage, song 2Bad). Details and every address: `D:\Dev\Recomp\BAG2JP\notes\bag1-character.md` and `notes\bag1-stage-song.md` (read the relevant one first). Tools: `D:\Dev\Recomp\BAG2JP\tools\bag1import` (VM path `~/mnt/Dev/Recomp/BAG2JP/tools/bag1import`). Build/test with the bag2jp-build-deploy-test skill (bag2_run.ps1 + bag2_report.py).

## Sources
- BAG1 discs: `D:\Games\Bust A Groove (USA)\ISO` and `D:\Games\Bust A Groove (Japan)` (its cue names a `(v1.1).bin` that does not exist: use a cue copy in ~/work pointing at the real bin). JP has DANCEXA1-4, US DANCEXA1-5. Extracted BAG1 files: `_work/bag1_disc`, main exe `_work/bag1/scus.bin` + decomp `bag1_decomp.txt`; BAG2 main exe `_work/mainexe/slpm.bin` + decomp, match module `_work/game/jp005*`.
- CD audio: `assets/music_cd/Bust a Move` (BAG1 OST, JP vocals) and `.../Bust a Move 2`.
- BAG1 character id order (stages, songs, charts): 0 Heat, 1 Strike, 2 Frida, 3 Hamm, 4 Kelly, 5 Shorty, 6 Pinky, 7 Kitty-N, 8 Hiro, 9 Gas-O, 10 Capoeira, 11 Robo-Z. Songs: verify by matching the XA against the CD (e.g. Heat = 2Bad, Gas-O = Chemical Love), never from memory.

## Character (build_heat_test.sh as template)
1. Model: `model_bag1_to_bag2.py` (BAG1 0x3C-word mesh header -> BAG2 0x48). Textures: costume A pages + 2P colours (costume B from PLAYER3E). DBI patch for the beanie bone slot (`patch_heat_dbi.py`).
2. Animations: `anim_remap.py` builds BAG2's 101-slot list. Dance moves follow BAG1's grid: BAG2 request = row base[level] + bar; BAG1 cell (bar s, level v<=s) = s(s+1)/2+(s-v)+1, bar 7 doubles; normal anim follows same level, alternate follows a level-up in both games. Fix type-16 attack events.
3. Fever: entries come from main exe table 0x8005510C[char id*2 + type-1]; the asset folders of archive entries 17-52 are NAMED BY ORDER, NOT BY CHARACTER (Heat = 22/40 = folders kelly/*). Use `fever_entries.py`. Solo = BAG1 fever anims (requests 160/161) with every char-bank cue muted (low values are bank-relative); duet = BAG2 duet with 0x10xx muted.
4. Voices: replace only pack bank 1 (char voices/SE). Never bank 3 (announcer: a missing cue hangs NOW LOADING).

## Stage (build_heat_stage_test.sh + port_bag1_stage.py)
1. Code: relocate the BAG1 stage DBI onto BAG2's stage DBI address, map calls (FUNCS) and globals (GLOBALS ranges), keep BAG2's DBI tail (song chart!) and bss, trampolines on BAG2's 4 per-stage callbacks; shim block for BAG1 beat flags/level fed by the bag1-content plugin; update helper copies level->prev after the update and adds a black sky TILE at OT[0xFFF].
2. Porter pitfalls: lui pairs through register copies and base+index adds; a lui in a branch delay slot reaches the branch target; BAG1 stage struct/bone layout differs (patch_struct_sites); voice slot >= 14 does not exist in BAG2 (use FUN_8002E478 free slot).
3. Assert that the port reports no unmapped refs, then grep the ported image for leftover BAG1 addresses (0x8005xxxx-0x8009xxxx loads) and check prims in a RAM dump (tpage/clut) when something renders wrong.
4. World scale: BAG1 stages draw at 3/8, BAG2 at 1/4 -> scale model nodes x1.5. Textures: TIM k -> slot k, CLUT-only slots re-upload BAG1 CLUTs. Camera: BAG1 track 0 (intro) + BAG2 dance tracks. Sounds: SEDT bank 0 <- BAG1 bank 0 (renumber cues away from BAG2's 0x4000 fever cue).
5. Score-driven effects: BAG1 thresholds are on its own score scale; use BAG2 dance-level thresholds (0x8005141C x play beats/256).

## Song
1. Chart: BAG1 table 0x800513DC[id] (start, frames, beats, sections mode<<8|beats; mode 0 = both), convert with `port_bag1_stage.bag1_chart()` (32 intro beats, mode 0->3) into the stage DBI tail (same 15 halfwords).
2. Audio: XA/DANCEXA<1+id/8> channel id%8. The plugin swaps the stage's BAG2 song channel through the XA host filter while the BAG1 stage is loaded. CD version: hq tools in `mods-src/bag2jp.feature.bag1-content/tools/hq_bag1` (match/segmap/blockmap/render2), then `song_ending.py` (game tail after the edit cut, fade) and set the song length entry 0x800555A8[song] in the plugin so fever does not wait for BAG2's longer slot.

## Checks before telling the user it works
- Full 2P match with bag2_run/bag2_report: phases reach 2/9 (back to select), fever solo AND duet (force solo by turning p2_2p off), shots at dance/level-up/fever.
- Sounds: -Cues and -Audio runs; no BAG1 voice in fever, expected SFX present (audio-probe find).
- Record findings in notes/bag1-*.md, commit with Windows git, refresh the snapshot.