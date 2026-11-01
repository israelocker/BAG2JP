# BAG2JP: owner-approved working method
The owner chose on 2026-10-30 to continue Claude's existing project workflow and evaluate optimizations later. Preserve this workflow before introducing process or tooling changes.

## Start and scope
- Canonical project: D:/Dev/Recomp/BAG2JP.
- Build tree for Codex: D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP. Historical ~/work paths describe Claude's previous VM.
- Check Git status before edits. Preserve prior edits, staged files, personal saves, settings and active sessions.
- Use English names for files, folders and variables. Communicate with the owner in Spanish.

## Optimized Chat Startup (Token-Saving Protocol)
**NEW CHAT: Read ONLY these files in order (≈10 KB total):**

1. **AGENTS.md** (this file) — policies & workflow
2. **NOTES.md** — current index with frontmatter summaries
3. **_work/current-state.json** — compact state + `gaps` field (what needs attention)
4. **IMPORT_STANDARD.md** — ONLY if task is BAG1→BAG2 character import (8 KB)

**DO NOT READ** full notes/ files unless:
- The index + state + IMPORT_STANDARD don't answer your question
- You need historical evidence details
- You're doing a code review / audit

**PREFER DIGESTS** for files > 10 KB:
- `notes/digests/character_workflow.digest.md` instead of `tools/bag1import/character_workflow.py`
- `notes/digests/bag1-character.digest.md` instead of `notes/bag1-character.md`
- `notes/digests/bag1-stage-song.digest.md` instead of `notes/bag1-stage-song.md`
- `notes/digests/online.digest.md` instead of `notes/online.md`
- `notes/digests/project.digest.md` instead of `notes/project.md`

**MINIMAL CONTEXT RULE**: If NOTES.md frontmatter summary + current-state.json `gaps` answers the question, STOP. Don't open the full note.

## Implement and verify
- Make bounded changes in source/plugins or conversion tools. Verify original words and module/region before MIPS patches; keep guards and restoration.
- Keep framework/launcher pins. Save local framework changes as reproducible patches under patches/. Fix code generation at its source.
- Build with the verified WSL/llvm-mingw environment, two compile jobs, retaining the running process until it finishes.
- Default deployment/test target: D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb.
- Preserve D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win as the stable install; changes there require an explicit owner request.
- Back up and restore test settings. Preserve memory cards. Coordinate game instances with the task and the owner's session.
- Prefer D:/Dev/Tools/winshot/bag2_run.ps1 and tools/test/bag2_report.py. Verify actual behavior with frames, screenshots, logs and audio/cue analysis.
- A code change is complete after its relevant in-game flow passes, not merely after compilation. BAG1 tests include song end, solo/duet fever and return to selection.
- Distinguish fresh test evidence, historical notes and untested behavior. Use human listening for subjective audio judgments.

## Save completed work
- Update the relevant notes/ topic with decisions, addresses, causes and test evidence; keep NOTES.md as the short index.
- Copy completed plugin/mod sources into mods-src/ and framework patches into patches/.
- Use Windows Git with an explicit project path. Make a local commit containing only task-owned changes after appropriate verification.
- Keep the existing sequential local Git workflow and branch arrangement. Generic imported skills do not impose a new branch/rebase/push/PR process on this project.
- The main project currently has no remote. A commit is a local checkpoint; uploading or publishing is separate work.
- After code/content work, refresh BAG2JP-project-snapshot.tar.gz from the build tree, excluding build directories; snapshots and heavy assets are outside Git.
- Build release folders/installers when requested. Retain rejected or disabled experiments as such.

## Local efficiency (owner authorized 2026-10-30)
- Prefer verified local scripts and installed tools; use local models for bounded, reviewable bulk work, one GPU model at a time. Keep game-test GPU use separate.
- Start a BAG2JP task with `python tools/workflow/bag2_workflow.py preflight`: compact Git/pins/path/source/resource diagnostics. Read detailed files only for the current change or reported drift.
- The same helper provides `build`, `test-stage-select` and `report --tag <tag>` with full logs and per-phase timings in `_work/workflow/`. Source/resource drift is diagnostic, not automatic synchronization.
- Reuse a running process and its log. Do not repeat successful checks or reviews without relevant changes or new evidence; satisfy required hooks with the focused evidence already obtained.
- Build reusable automation when it removes a demonstrated repeated step. Preserve the local Git, experimental deployment and in-game acceptance workflow above; measure improvements before claiming savings.

## Shared character standard (owner requested 2026-10-31)
- Follow notes/character-pipeline.md for every character. Route to bag-character-pipeline, bag-animation-matching and bag-reference-cache.
- Keep engines and orchestration shared. Character profiles carry data/capabilities; only demonstrated, scoped exceptions may introduce an adapter. Never clone Heat's pipeline for another character.
- Match meaning, beat timing, required events and predecessor transitions; unknown mappings remain unresolved. Track all source/target coverage and stock-empty/reused entries.
- Reuse visual evidence only when motion, catalog, profile, runtime and evidence hashes match. Re-audit changed packages. Preserve the single-GPU schedule.
- Distinguish configured rules, implemented tools, legacy Heat adapters and unimplemented general matching/graph optimization. Do not claim cross-character support without exercising a second profile.
