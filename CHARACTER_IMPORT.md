---
id: character-import-runbook
title: "BAG2JP Character Import — Canonical Runbook"
tags: ["bag1", "character", "runbook"]
summary: "Shared character import stages and acceptance gates, linked to reusable exact-entry integration and observed-state testing recipes."
related: ["AGENTS.md", "IMPORT_STANDARD.md", "notes/character-pipeline.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-10-31"
updated: "2026-11-02"
edited: "2026-11-02"
---

# BAG2JP Character Import — Canonical Runbook

Follow the startup order in `AGENTS.md`; this is the canonical import runbook,
not a replacement for project policy. `notes/character-pipeline.md` records the
shared standard. Read only the recipe needed for the current phase:
- `notes/character-alternate-entries.md`: DFS rebuilding, exact payloads,
  preservation of prior imports, source/resource staging and deployment.
- `notes/character-import-testing.md`: calibration, full-song tests,
  side/costume matrix, diagnostic evidence and implementation limits.

## 1. What success means

A character is **not complete** when conversion code exists. It is complete only
when all required acceptance cases pass on the experimental installation and the
evidence is recorded with unchanged hashes.

A character is complete only when:

- its model, costumes and sides render correctly;
- all required motions and transitions are accepted;
- required audio cues do not collide;
- stage, song, fever and ending are verified;
- a full match returns to selection;
- settings and memory cards remain byte-identical;
- the local task commit and one verified snapshot are made.

No import claim is valid if the profile is still `inventory` or has pending
exceptions.

## 2. Non-negotiable rules

- Work only in `D:/Dev/Recomp/BAG2JP` and build only in
  `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP`.
- Deploy and test only in `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`.
- Never touch `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win` without explicit owner
  permission.
- Never publish or upload.
- Preserve `installer/LEEME.txt`, `installer/bag2jp_online.nsi`,
  `installer/build.sh`, `.opencode/`, caches, and personal saves.
- Do not claim a character is imported because a profile exists.
- Do not copy Heat's pipeline into another character.
- Do not execute commands stored in a profile.
- Do not auto-deploy candidate assets.
- Do not generalize Heat-specific bone, DBI, cue or stage fixes.
- Keep unresolved roles unresolved until a documented adaptation is chosen.

## 3. Standard tools

```powershell
$PY='D:/Dev/Tools/ghidra-mcp-python/python.exe'
$HELPER='D:/Dev/Recomp/BAG2JP/tools/workflow/bag2_workflow.py'
```

Always start with:

```powershell
& $PY $HELPER preflight --tag <task>
```

Use WSL Ubuntu and llvm-mingw for builds, always with two jobs:

```powershell
& $PY $HELPER build --tag <task>
```

## 4. Required command order

For every character, run these commands in order. Change only data arguments.

### 1. Initialize or validate the profile

```powershell
py -3.13 tools/bag1import/character_workflow.py init-profile `
  --character <slug> `
  --profile tools/bag1import/profiles/<slug>.json `
  --source-archive <unpacked-model.dfs> `
  --source-list _work/character_inventory/<slug>/001.bin `
  --runtime "D:/Dev/Scratch/bag1-native-reference/BustAGroove_Recompiled.exe" `
  --catalog tools/bag1import/contracts/bag1-usa-bag2jp.roles.json
```

Or, if the profile already exists:

```powershell
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile tools/bag1import/profiles/<slug>.json
```

### 2. Inspect the plan

```powershell
py -3.13 tools/bag1import/character_workflow.py plan --profile tools/bag1import/profiles/<slug>.json
py -3.13 tools/bag1import/character_workflow.py acceptance-plan --profile tools/bag1import/profiles/<slug>.json
```

If `gaps` is not empty, do not prepare.

### 3. Prepare a candidate only

```powershell
py -3.13 tools/bag1import/character_workflow.py prepare --profile tools/bag1import/profiles/<slug>.json
```

`prepare` creates a candidate workspace and manifest. It never deploys.

### 4. Record reference evidence

```powershell
py -3.13 tools/bag1import/character_workflow.py cache-record `
  --profile tools/bag1import/profiles/<slug>.json `
  --cache tools/bag1import/cache/<slug>.cache.json `
  --evidence <verified-video.mp4> `
  --evidence <timeline.json>
```

### 5. Check reference evidence

```powershell
py -3.13 tools/bag1import/character_workflow.py cache-check `
  --profile tools/bag1import/profiles/<slug>.json `
  --cache tools/bag1import/cache/<slug>.cache.json
```

A cache hit is evidence only. It is never gameplay acceptance.

## 5. Profile schema

Every profile must be data-only. It may contain IDs, paths, hashes, capabilities,
exceptions and evidence. It must not contain executable code or deployment
instructions.

Required fields:

- `schema`
- `character`
- `display_name`
- `source_character_id`
- `target_character_id`
- `stage`
- `exception_assessment`
- `source_animation_list`
- `game_catalog`
- `reference_runtime`
- `capabilities`
- `exceptions`
- `assets`
- `validation_evidence`

Capabilities determine the acceptance matrix. Use only capabilities that have been
verified. Do not copy Heat's capability set to another character.

## 6. Inventory rules

Before any conversion, verify:

- source archive is an unpacked DFS archive;
- animation list count matches the real source;
- model and animation layout;
- target character ID in BAG2;
- costume and side mappings;
- stage and song mapping;
- cue base;
- skeleton links and bone binding;
- character-dependent branches in the DBI;
- mesh and texture layouts.

Never assume Heat's counts, IDs, bones, fever folders or model layout.

## 7. Animation contract rules

- Match by semantic role first.
- Preserve musical duration in beats.
- Preserve required events: audio, effects, launches, voices.
- Separate normal steps, special durations, held poses, attacks, defenses, hit
  reactions, tired states, knockdown, recovery, wins, losses and fever.
- Keep original predecessor dispatch as an independent check.
- Report all source and target entries.
- Report duplicates, unused motions, missing counterparts, stock-empty entries and
  deliberate repetitions.
- If a target role does not exist in the source, mark it unresolved.
- Do not map an unsuccessful hit reaction to a successful defense silently.
- Normalize skeleton, scale, root orientation and beat timing before using pose
  similarity as a tie-breaker.

## 8. Audio rules

- Each character owns its cue base.
- Rebase BAG1 cues when needed.
- Detect collisions in mirror matches.
- Preserve required victory announcer names only when the character exists in both
  games and the capability is verified.
- Do not assume a second bank loads. Verify the actual BAG2 loader behavior.
- Keep fever cues muted when appropriate.

## 9. Asset and package rules

Use `notes/character-alternate-entries.md` for the executable recipe. Rebuild
members with `rebuild_dfs_members.py`; generate full payload/index from explicit
rows with `make_alt_entries_exact.py`. Keep old BAG1 bytes from the accepted
payload, not stock disc entries. Validate actual DUMMY byte capacity independently:
the exact generator's current capacity guard has a units defect. Never truncate
growing entries, reuse stale DFS offsets or assume preflight synchronizes sources.

- Generate candidates only.
- Preserve unrelated archive entries.
- Preserve stock offsets and sizes.
- Validate guest scratch capacity.
- Update online content identity when behavior, timing or assets change.
- Never deploy from `prepare`.
- Keep all generated payloads and heavy assets outside Git.

## 10. Acceptance matrix

Every import must define its applicable cases. Baseline cases:

- inventory validation;
- model on both sides and both costumes;
- game flow;
- song end;
- return to selection.

Conditional cases:

- costume selection;
- mixed-version match;
- solo fever;
- duet fever;
- stage load;
- ending video, credits, dance and return;
- announcer name;
- online content identity.

A case is not valid if its required capability is false.

## 11. Testing discipline

Use `notes/character-import-testing.md` for commands and evidence meanings.
`bag2_versus.ps1 -Finish` requires a full return; without it, a run stops at
gameplay entry. Heat/Strike/Comet routing is a limited observed catalog, not a
general roster driver. Extend it with verified data for another character.

- Run host-side tests before building.
- Use the experimental installation only.
- Use an isolated game process and unique evidence directory.
- Verify actual behavior with frames, screenshots, logs and audio/cue analysis.
- Reuse unchanged evidence by hash.
- Restore settings and memory cards in `finally`.
- Do not re-run a clean suite without relevant changes.
- A cache hit is not gameplay acceptance.

## 12. Evidence and context

Each import must maintain:

```text
_work/character-import/<slug>/state.json
_work/character-import/<slug>/candidate/
_work/character-import/<slug>/evidence/
```

State must contain:

- character;
- stage;
- status;
- pending exceptions;
- gaps;
- prepare readiness;
- acceptance count;
- updated timestamp.

Keep notes compact. Current state belongs at the top; history belongs in dated
sections. Never rely on a chat transcript as project state.

## 13. Known Heat-specific adapters

These are not general rules:

- `patch_heat_dbi.py`: head/beanie binding and outfit-B branches;
- `anim_remap.py`: Heat animation and cue policy;
- `audit_animation_roles.py`: Heat inventory and role classification;
- `make_alt_entries.py`: Heat entry table;
- `port_bag1_stage.py`: Heat stage port;
- `preserve_announcer.py`: Heat victory-name merge;
- `restore_heat_winner.py`: Heat voice packs.

Use them as examples and legacy adapters only. A second character must validate
its own equivalents.

## 14. Common failure modes

- Treating equal request numbers as equal roles.
- Treating a working conversion as a successful import.
- Hiding unresolved roles with plausible substitutions.
- Assuming a second VAB bank loads.
- Assuming BAG1 and BAG2 skeletons match.
- Assuming BAG1 has the same costumes, stages, songs or announcer names.
- Treating cached visual evidence as gameplay proof.
- Declaring completion before a full match returns to selection.
- Repeating manual navigation when observed indices are available.
- Re-running the same log or suite without new evidence.

## 15. Completion checklist

Before closing a character import:

- [ ] Profile validates.
- [ ] Plan has no gaps.
- [ ] Candidate prepared.
- [ ] Required acceptance cases pass.
- [ ] Fresh gameplay evidence recorded.
- [ ] Settings and cards preserved.
- [ ] Source and candidate hashes recorded.
- [ ] Notes updated with current state and evidence.
- [ ] Read-only review performed.
- [ ] Local commit contains only task-owned changes.
- [ ] Snapshot refreshed after all related work is complete.
- [ ] Stable installation untouched.

## 16. Minimum chat startup

When starting a new chat for an import, run:

```powershell
& $PY $HELPER preflight --tag <task>
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile tools/bag1import/profiles/<slug>.json
py -3.13 tools/bag1import/character_workflow.py plan --profile tools/bag1import/profiles/<slug>.json
```

Then read this runbook and only the relevant notes. Do not reconstruct the project
from old conversations.
