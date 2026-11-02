# Context Optimization Plan

## Goal

Reduce the amount of context a new chat must load before it can act safely, while
preserving every durable fact and every verification rule.

## Current measured state

| File | Size | Lines | Main issue |
|---|---:|---:|---|
| `CHARACTER_IMPORT.md` | 10 KB | 314 | Runbook and historical details mixed together |
| `notes/bag1-character.md` | 31 KB | 227 | Too large; contains the entire Heat history |
| `notes/bag1-stage-song.md` | 13 KB | 137 | Stage, song, audio and tools mixed |
| `notes/online.md` | 12 KB | 144 | Online, audio latency, release and installer mixed |
| `notes/endings-view.md` | 11 KB | 163 | Current state and old evidence mixed |
| `notes/project.md` | 12 KB | 159 | Build history and open items mixed |
| `tools/bag1import/character_workflow.py` | 20 KB | 358 | Good candidate for splitting helpers |

The main problem is not the total size; it is that a chat may need to read all of
it to answer a small question.

## Phases

### Phase 1: Add a compact current-state layer (Size: M)

Verified when: a new chat can answer "what is the current state and what is next"
from one small JSON file, without reading any note.

Files:
- `tools/bag1import/character_workflow.py`
- `_work/current-state.json` (generated, not committed)

Tasks:

1. Add a `compact-status` command that writes `_work/current-state.json`.
2. Include only:
   - character
   - stage
   - status
   - pending exceptions
   - gaps
   - prepare readiness
   - acceptance count
   - latest evidence directory
   - next action
   - updated timestamp
3. Add a `read-state` command that prints the same object as one line.
4. Add tests for atomic write and compact output.

Blocked by: none.

### Phase 2: Split the largest notes (Size: L)

Verified when: each note has one topic and a short current-state block; no note
contains more than 120 lines unless it is an intentional ledger.

Files:
- `notes/bag1-character.md`
- `notes/bag1-stage-song.md`
- `notes/online.md`
- `notes/endings-view.md`
- `notes/project.md`

Tasks:

1. Split `bag1-character.md` into:
   - `bag1-character-model.md`
   - `bag1-character-animation.md`
   - `bag1-character-audio.md`
   - `bag1-character-combat.md`
2. Split `bag1-stage-song.md` into:
   - `bag1-stage.md`
   - `bag1-song.md`
3. Split `online.md` into:
   - `online-netsync.md`
   - `online-audio-latency.md`
   - `online-release.md`
4. Split `endings-view.md` into:
   - `endings-view-current.md`
   - `endings-view-evidence.md`
   - `endings-view-history.md`
5. Split `project.md` into:
   - `project-builds.md`
   - `project-tools.md`
   - `project-open-items.md`
6. Keep `NOTES.md` as the only index and update every link.

Blocked by: Phase 1.

### Phase 3: Add stable metadata to every note (Size: M)

Verified when: every note has frontmatter and `NOTES.md` can select notes by
summary without opening them.

Files:
- all files under `notes/`

Tasks:

1. Add frontmatter:
   - `id`
   - `title`
   - `tags`
   - `created`
   - `updated`
   - `summary`
   - `related`
2. Add a `Notes Index` section to `NOTES.md` with one line per note.
3. Add a maintenance rule: any note change must update `updated` and the index.

Blocked by: Phase 2.

### Phase 4: Create digests for large source files (Size: S)

Verified when: a chat can answer common questions from digests without reading
the full source.

Files:
- `tools/bag1import/character_workflow.py`
- `notes/digests/`

Tasks:

1. Generate `character_workflow.digest.md` with:
   - public command list
   - validation rules
   - cache behavior
   - state behavior
   - line ranges for each function
2. Generate digests for the three largest notes.
3. Add a rule: digests are regenerated when the source changes.

Blocked by: Phase 3.

### Phase 5: Reduce note loading by default (Size: S)

Verified when: `AGENTS.md` tells a new chat to read only the index, the current
state, and the relevant note.

Files:
- `AGENTS.md`
- `NOTES.md`

Tasks:

1. Change startup order to:
   - `AGENTS.md`
   - `NOTES.md`
   - `_work/current-state.json` if it exists
   - only the note required by the task
2. Add a rule: do not read full notes unless the index and state are insufficient.
3. Add a rule: prefer digests for files larger than 10 KB.

Blocked by: Phase 4.

### Phase 6: Verify and close (Size: S)

Verified when: all tests pass and the context size for a new chat is under 8 KB.

Tasks:

1. Run:
   - `tools/test/test_character_workflow.py`
   - `tools/test/test_hd_menu_assets.py`
   - `tools/test/test_endings_view.py`
2. Measure the startup context size.
3. Update notes with the new structure.
4. Make one local commit with only task-owned files.
5. Refresh the snapshot after all related work is complete.

Blocked by: Phase 5.

## Decisions

| Decision | Chosen option | Reason |
|---|---|---|
| Notes | Split by topic | Atomic notes are easier to select and load |
| State | JSON only | Machine-readable and compact |
| Digests | Generated on demand | Avoids stale summaries |
| Startup | Index first | Prevents loading large files by default |
| History | Keep, but separated | Preserves evidence without polluting current state |

## Always / Never

- Always preserve the stable install, active sessions, cards, settings and hashes.
- Always distinguish current state from historical evidence.
- Never delete notes; split them instead.
- Never claim a reduction in context size without measuring it.
- Never load a full note when the index and state answer the question.

## Progress

| Phase | Status |
|---|---|
| 1 | Pending |
| 2 | Pending |
| 3 | Pending |
| 4 | Pending |
| 5 | Pending |
| 6 | Pending |