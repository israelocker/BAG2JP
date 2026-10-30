# BAG2JP: owner-approved working method
The owner chose on 2026-10-30 to continue Claude's existing project workflow and evaluate optimizations later. Preserve this workflow before introducing process or tooling changes.

## Start and scope
- Canonical project: D:/Dev/Recomp/BAG2JP. Read NOTES.md, then only the relevant notes/ topic and project-specific skills.
- Build tree for Codex: D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP. Historical ~/work paths describe Claude's previous VM.
- Check Git status before edits. Preserve prior edits, staged files, personal saves, settings and active sessions.
- Use English names for files, folders and variables. Communicate with the owner in Spanish.

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
- Evaluate workflow, token or tooling optimizations later with the owner; do not change the adopted method as part of ordinary feature work.
