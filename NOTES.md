# BAG2JP — Bust A Move 2: Dance Tengoku Mix (Japan), PS1 -> native Windows recompilation

Notes are split by topic in notes/ (read only the file you need; grep across them for addresses):

- notes/project.md — Project: builds, folders, saves, resume
- notes/agent-handoff.md — Claude→Codex→OpenCode handoff, current scope, tools and profile-safety warning
- notes/regional.md — Regional content, songs and announcer options, CD-quality songs
- notes/assets.md — Asset toolkit, archive layout, extracted data
- notes/ui-mods.md — HD fonts/UI packs, in-game MODS menu, keyboard rebinding
- notes/online.md — Online play, netsync, audio latency, v7 release and installer
- notes/character-pipeline.md - Shared character workflow, profiles, role contracts, reference cache and implementation boundaries
- notes/bag1-character.md — BAG1 import: Heat character (model, anims, dance grid, fever, voices), 2P autoplay, planned popups
- notes/bag1-stage-song.md — BAG1 import: stage port, song chart and audio, camera, sounds, destruction, testing/debug tools

Quick facts:
- Disc D:\Games\Bust A Groove 2 (Japan)\ISO\...cue, SLPM-86219, load 0x80010000. Stable build BAG2JP-win (do not touch),
  experimental BAG2JP-exp-8mb (default). Build tree: see AGENTS.md; snapshot: BAG2JP-project-snapshot.tar.gz.
- Tests: D:\Dev\Tools\winshot\bag2_run.ps1 + tools/test/bag2_report.py (see notes/project.md, "Testing and debugging").
- Audio analysis: D:\Dev\Tools\audio-probe. BAG1 import pipeline: tools/bag1import (skill bag1-import).
