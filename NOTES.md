---
id: bag2jp-notes-index
title: "BAG2JP notes index"
tags: ["index", "workflow", "project"]
summary: "Short project index. Character integration recipes cover exact DFS/payload construction, explicit staging, observed-state tests and acceptance limits."
related: ["AGENTS.md", "CHARACTER_IMPORT.md", "notes/character-pipeline.md", "_work/current-state.json"]
created: "2026-10-31"
updated: "2026-11-02"
edited: "2026-11-02"
---

# BAG2JP — Bust A Move 2: Dance Tengoku Mix (Japan), PS1 -> native Windows recompilation

Notes are split by topic in notes/ (read only the file you need; grep across them for addresses):

- notes/project.md — Project: builds, folders, saves, resume
- notes/agent-handoff.md — Claude→Codex→OpenCode handoff, current scope, tools and profile-safety warning
- notes/regional.md — Regional content, songs and announcer options, CD-quality songs
- notes/assets.md — Asset toolkit, archive layout, extracted data
- notes/ui-mods.md — HD fonts/UI packs, in-game MODS menu, keyboard rebinding
- notes/game-controls.md — Named versus harness, actual P1/P2 bindings, visual gates, restoration and limited Heat/Comet/Strike catalog
- notes/endings-view.md — Direct character/costume endings menu, JP hooks and acceptance ledger
- notes/online.md — Online play, netsync, audio latency, v7 release and installer
- notes/character-pipeline.md - Shared character workflow, profiles, role contracts, reference cache and implementation boundaries
- notes/character-alternate-entries.md - Reusable DFS/payload integration, preservation of prior imports, manifest offsets and explicit source/resource staging; tool limits included
- notes/character-import-testing.md - Runtime calibration, full-song harness, side/costume matrix, active-mod preservation and diagnosis of observed failures
- notes/strike-recovery.md - Strike BAG1 integrated; P1/A and P2/B complete song and return, visual fidelity and remaining acceptance cases pending
- CHARACTER_IMPORT.md - Canonical compact runbook for importing a BAG1 character into BAG2JP
- notes/bag1-character.md — BAG1 import: Heat character (model, anims, dance grid, fever, voices), 2P autoplay, planned popups
- notes/bag1-stage-song.md — BAG1 import: stage port, song chart and audio, camera, sounds, destruction, testing/debug tools

Quick facts:
- Disc D:\Games\Bust A Groove 2 (Japan)\ISO\...cue, SLPM-86219, load 0x80010000. Stable build BAG2JP-win (do not touch),
  experimental BAG2JP-exp-8mb (default). Build tree: see AGENTS.md; snapshot: BAG2JP-project-snapshot.tar.gz.
- Tests: D:\Dev\Tools\winshot\bag2_run.ps1 + tools/test/bag2_report.py (see notes/project.md, "Testing and debugging").
- Audio analysis: D:\Dev\Tools\audio-probe. BAG1 import pipeline: tools/bag1import (skill bag1-import).
