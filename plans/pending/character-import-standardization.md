---
id: character-standardization-proposal
title: "Character standardization: historical proposal"
tags: ["proposal", "character"]
summary: "Plan anterior con fases de implementación no certificadas conjuntamente; no representa estado actual Strike."
related: ["notes/documentation-audit.md", "notes/character-pipeline.md", "notes/strike-recovery.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: proposal
---

# Character Import Standardization Plan

**Estado: propuesta histórica que requiere revalidación antes de ejecutar.** No
marcada completa por esta auditoría. Algunas funciones existen, pero sus criterios
de aceptación no se heredan como hechos. Strike ya tiene ID=1 verificado e
integración/flujo parciales: el requisito antiguo «remains inventory» de abajo
no es estado vigente. Ver fuentes canónicas enlazadas y código real por fase.

## Goal
Provide one profile-driven, resumable BAG1→BAG2JP workflow and one compact entry document that a new chat can follow without reconstructing Heat's history.

## Phases

### Phase 1: Profile contract and resumable state
Verified when: schema-2 profiles validate, legacy schema-1 fixtures remain readable, and state writes are atomic and deterministic.
Files: `tools/bag1import/character_workflow.py`, `tools/test/test_character_workflow.py`

#### Step 1.1: Schema-2 validation and gap reporting (M)
- Acceptance: validate data-only assets/capabilities; report unresolved IDs, pending exceptions and missing contract data; never execute profile content.
- Verification: `py -3.13 tools/test/test_character_workflow.py`
- Blocked by: none

#### Step 1.2: Compact state lifecycle (S)
- Acceptance: `plan`, `prepare`, `status` and `acceptance-plan` share `_work/character-import/<slug>/state.json`; writes are atomic; `prepare` creates only a candidate workspace/manifest and never deploys.
- Verification: `py -3.13 tools/test/test_character_workflow.py`
- Blocked by: 1.1

### Phase 2: Acceptance matrix and profile migration
Verified when: Heat and Strike validate under schema 2 and produce capability-specific plans without claiming Strike imported.
Files: `tools/bag1import/profiles/heat.json`, `tools/bag1import/profiles/strike.json`, workflow tests

#### Step 2.1: Capability-derived acceptance cases (M)
- Acceptance: baseline model/game-flow cases plus conditional costume, mixed-version, fever, stage/song, ending, announcer and online cases; unresolved capabilities remain explicit.
- Verification: focused workflow tests plus both real profiles' `plan` and `acceptance-plan` commands.
- Blocked by: 1.2

#### Step 2.2: Migrate Heat and Strike profiles (S)
- Acceptance: Heat preserves its verified exception and historical capabilities; Strike remains inventory with unresolved target ID; no executable adapter is embedded in JSON.
- Verification: `validate-profile` and `plan` for both profiles.
- Blocked by: 2.1

### Phase 3: Compact operator documentation
Verified when: a fresh reader can start, resume, diagnose and close an import from one root document.
Files: `CHARACTER_IMPORT.md`, `AGENTS.md`, `NOTES.md`, `notes/character-pipeline.md`

#### Step 3.1: Write the canonical runbook (M)
- Acceptance: exact commands, gates, artifacts, matching rules, exception rules, acceptance matrix, cache policy, context/token policy and completion definition; clearly separates shared workflow from Heat adapters.
- Verification: command/path/link audit against the repository.
- Blocked by: 2.2

#### Step 3.2: Route new chats to the runbook (XS)
- Acceptance: root instructions and notes index point character-import requests to `CHARACTER_IMPORT.md`; detailed technical notes remain references.
- Verification: grep links and read the entry path as a new-session simulation.
- Blocked by: 3.1

### Phase 4: Regression and close-out
Verified when: host tests, real-profile checks and existing Heat audits pass; only task-owned files are committed; snapshot is refreshed after all related Ending View work is closed.

#### Step 4.1: Full focused verification (M)
- Acceptance: workflow unit suite, Heat policy/auditor seams and profile commands pass; generated state is compact; no deployment or personal data changes.
- Blocked by: 3.2

#### Step 4.2: Record evidence and local checkpoint (S)
- Acceptance: update relevant notes, focused review, local commit containing only owned files; preserve installer and unrelated changes.
- Blocked by: 4.1

## Decisions
| Decision | Choice | Reason |
| --- | --- | --- |
| Canonical entry | Root `CHARACTER_IMPORT.md` | Discoverable by a new chat and human reader. |
| Profiles | Data only | Character differences must not fork orchestration. |
| Prepare behavior | Candidate workspace only | Safe foundation; no automatic deployment or false general-converter claim. |
| Second character | Strike remains inventory | It validates the schema, not gameplay support. |
| Execution | Native current session | Owner requested lower token use; no delegation requested. |

## Always / Never
- Always preserve the stable install, active sessions, cards, settings, hashes and unresolved mappings.
- Always distinguish static validation, cached evidence and fresh gameplay acceptance.
- Never copy Heat's pipeline as another character pipeline, execute commands from a profile, auto-deploy, publish, or claim cross-character support before a second gameplay port.

## Progress
| Phase | Status |
| --- | --- |
| 1 | Pending |
| 2 | Pending |
| 3 | Pending |
| 4 | Pending |
