---
id: versus-navigation
title: "Reliable generic versus navigation"
tags: ["testing", "controls", "workflow"]
summary: "Proposed bounded extension of existing Windows test harnesses: named characters, observed-state gates, reversible controls and compact evidence. Awaiting approval."
related: ["notes/game-controls.md", "tools/test/bag2_endings_view.ps1", "AGENTS.md"]
created: "2026-11-01"
updated: "2026-11-01"
edited: "2026-11-01"
---

# Reliable generic versus navigation

Status: proposed; implementation approval pending.
Ticket: local owner request; no external tracker or publication.

## Goal and boundaries

Select a local versus match using character names, versions and costumes, rather than blind relative offsets. A successful command must mean the requested state was observed, not merely that keys were sent. Extend the existing test workflow without changing runtime behavior, dependencies or the owner's permanent controls.

Recommended interface: `-P1Character Heat -P1Version BAG1 -P2Character Heat -P2Version BAG2`, optional costumes/stage, explicit experimental PID or authorized isolated start. Independent commands inspect, advance and capture; they do not run a full blind sequence.

## Approaches

1. Recommended: existing RAM-watch signals plus screenshots at semantic checkpoints. Reuses local harnesses, supports objective assertions and visual review.
2. Screenshots only: lowest runtime coupling, but more image calls and manual interpretation for every step.
3. New runtime automation plugin: richer telemetry, but adds build/deploy risk and is outside this first iteration.

## Decisions proposed

- Keep permanent controls untouched. A test session uses explicit opt-in temporary bindings and automatic byte-exact restoration after closing its own process.
- Use existing `postkey.ps1` and `winshot.ps1`. New reusable sources belong under `tools/test/`, not another untracked variant in the external winshot folder.
- Inspect `keybinds.ini` and `settings.toml` before input. Detect missing confirmations and shared keys; do not infer controls from comments.
- Reuse the observed main-menu root/cursor checks in `bag2_endings_view.ps1`. Verify watch freshness and target PID; validate character/version signals against the deployed plugin before trusting them.
- Character lookup contains names/IDs and validated navigation edges, not a Heat-specific recipe. Unknown characters, unavailable versions, locked slots or unverified edges stop with evidence instead of falling back silently.
- Capture menu selection, character identities, version popups, stage and live match. Keep full artifacts on disk; report one compact result and only relevant images in chat.
- A timeout stops the action and saves evidence. No automatic restart or repeated Enter sequence after failure.
- Acceptance for this iteration is correct selection and match start. Full-song, fever, audio and import acceptance remain separate tests.

## Phases

### Step 1: Validate observation and routing (Size: S)
- Blocked by: design approval.
- Files: `tools/test/versus_navigation.py`, `tools/test/test_versus_navigation.py`, data catalog under `tools/test/` only if needed.
- Acceptance: parse real bindings; resolve named characters without unknown fallbacks; reject stale or ambiguous observations.
- Verification: `py -3.13 -m unittest discover -s tools/test -p test_versus_navigation.py`.
- Test seams: pure parsing/routing fixtures, including missing P2 circle, shared keys, unknown names, unsupported versions and unchanged-state timeout.

### Step 2: Gate real inputs (Size: M)
- Blocked by: Step 1.
- Files: `tools/test/bag2_versus.ps1`, same tests/helpers where needed.
- Acceptance: target only the experimental task process; checkpoint each state transition; backup/restore controls, settings, mod state and saves with SHA256 verification even after errors.
- Verification: PowerShell parser check; fixture tests above; `bag2_versus.ps1 -Action inspect -GameId <task-pid>`; live navigation checkpoints.
- Test seams: process/path guards, bounded waits, unexpected-state stop, restoration after a deliberately rejected input request.

### Step 3: Demonstrate generality (Size: S)
- Blocked by: Step 2.
- Files: evidence under `_work/`; `notes/game-controls.md`; task-owned index line in `NOTES.md`.
- Acceptance: Heat BAG1 vs Heat BAG2 reaches gameplay; a second stock character pair reaches gameplay using names through the same flow; every required checkpoint and restoration is recorded.
- Recommended second pair: Comet BAG2 vs Strike BAG2, subject to actual availability. Unavailable entries are reported, not substituted.
- Verification: two live runs of `bag2_versus.ps1` using named requests; `result.json` records requested/observed mode, characters, versions, screenshots and restoration status.
- Test seams: deployed experimental UI plus popup logs and fresh watch data. Visually inspect critical images before reporting success.

### Step 4: Record standard and baseline (Size: S)
- Blocked by: Step 3 and owner agreement on retained rules.
- Files: `notes/game-controls.md`, `NOTES.md`, relevant project-config reference; snapshot only once after final sources are synchronized appropriately.
- Acceptance: short reusable runbook without pilot noise; local task-only commit; baseline includes wall time, actions, screenshots and tool calls. Exact tokens only if harness usage records are available.
- Verification: focused diff review; repeat no unchanged suites; inspect restoration records; local Git checkpoint and project snapshot per AGENTS.md.

## Always / Never

- Always: preserve prior edits, active sessions, cards and stable installation; save evidence for mismatches; English identifiers and Spanish owner communication.
- Never: force-kill all BAG2JP processes, publish, change pins, install tools, replace owner preferences permanently, claim automatic vision when only an image was saved, or infer fever failure from a stable gameplay phase.

## Not yet specified

- Full grid and locked/unlocked transitions are observable facts to inventory during Step 1/3, not guessed from campaign outcomes. Untested entries stay unsupported.
- Version and stage capabilities must be read from actual installed data; no universal BAG1 support is assumed.
- Runtime observation changes require a separate scope decision if current telemetry is insufficient. First iteration stops rather than modifying game plugins silently.

## Progress

| Phase | Status |
| --- | --- |
| Manual mixed-version Heat probe | Verified selection and match start; restoration recorded in notes |
| Design | Awaiting owner approval |
| Steps 1–4 | Not started |
