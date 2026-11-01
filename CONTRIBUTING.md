# BAG2JP — Contributing Guide

Thank you for your interest in contributing to BAG2JP, a static recompilation of **Bust A Groove 2 (Japan)** for PC.

This document describes how to contribute code, documentation, and evidence to the project. Please read it before submitting any changes.

## 1. Project Principles

| Principle | Description |
|-----------|-------------|
| **Static recompilation** | MIPS → C++ → native executable. No interpreter, no JIT, no emulation loop on the hot path. |
| **Owner-approved workflow** | The project follows the workflow defined in `AGENTS.md`. Preserve it before introducing changes. |
| **Shared engine, per-character data** | Engines and orchestration are shared. Character profiles carry data/capabilities; only demonstrated, scoped exceptions may introduce an adapter. |
| **Evidence-based** | Every claim must be backed by in-game evidence (frames, screenshots, logs, audio/cue analysis). Human listening for subjective audio judgments. |
| **No secrets or personal paths** | Code and documentation must not contain user-specific paths, credentials, or personal information. |

## 2. Before You Contribute

### Check the Current State

Read these files in order (≈8 KB):

1. `AGENTS.md` — Project policies and workflow
2. `NOTES.md` — Current index with note summaries
3. `_work/current-state.json` — Compact state with `gaps` field (what needs attention)

### Identify What Needs Work

- Look at the `gaps` field in `_work/current-state.json` for pending tasks
- Check `NOTES.md` for notes that need updates
- Review `CHARACTER_IMPORT.md` for the canonical import runbook if working on character import

### Set Up Your Environment

| Requirement | Details |
|-------------|---------|
| OS | Windows (primary) with WSL/Ubuntu for C tests |
| Build tools | WSL/llvm-mingw environment (verified) |
| Python | Python 3.13+ for tools/workflow scripts |
| Git | Windows Git with explicit project path |
| Disk space | Sufficient for disc images and build output |

```bash
# Clone the repository
git clone <project-path>
cd BAG2JP

# Run preflight diagnostics
py tools/workflow/bag2_workflow.py preflight --tag <your-task>
```

## 3. Making Changes

### Step 1: Create Your Change

All changes must be **bounded** — one logical change per commit.

#### For C Code (plugins in `mods-src/`)

| Standard | Requirement |
|----------|-------------|
| No magic constants | Replace numeric literals with `#define` or `enum` |
| Validate input early | Check pointers, ranges, return values at function start |
| One purpose per function | Split functions longer than 30 lines |
| Comment the "why" | Code explains what; comments explain why |
| Group related `#define` | Place constants at top of file with comments |

Example of correct constant usage:

```c
/* Before: magic constant */
if (n < 20 || memcmp(b, "B2NS", 4) || b[4] != 2) return;

/* After: named constant */
#define NS_PKT_HDR 20  /* Protocol packet header size */
if (n < NS_PKT_HDR || memcmp(b, "B2NS", 4) || b[4] != 2) return;
```

#### For Python Code (scripts in `tools/`)

| Standard | Requirement |
|----------|-------------|
| Type hints | All public functions have parameter and return annotations |
| Logging over print | Use `logging` module (INFO, WARNING, ERROR) |
| pathlib over strings | Use `Path` for file path manipulation |
| Specific exceptions | Catch concrete exceptions, never bare `except` |
| Docstrings | Document purpose, parameters, return value |

Example of correct Python function:

```python
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("my_script")


def validate_file(path: Path, fix: bool = False) -> list[str]:
    """Validate a single note file.

    Args:
        path: Path to the markdown file to validate.
        fix: If True, auto-fill missing frontmatter fields.

    Returns:
        List of issue descriptions found during validation.
    """
    issues: list[str] = []
    # ... implementation
    return issues
```

#### For TOML Configuration

| Standard | Requirement |
|----------|-------------|
| Validate on load | Numeric values within documented ranges |
| Document defaults | Comment what each option does and its default |
| No secrets | No user-specific paths or credentials |

#### For Documentation (notes/)

| Standard | Requirement |
|----------|-------------|
| Frontmatter required | `id`, `title`, `tags`, `summary`, `related`, `created`, `updated` |
| Update `updated` | Refresh timestamp on any note modification |
| No test/debug noise | No frame numbers, PIDs, pilot results, personal paths |
| Digests for large files | Source >10 KB must have digest in `notes/digests/` |

### Step 2: Verify Your Change

Before committing, run all applicable checks:

```bash
# 1. Run maintenance checks
py tools/workflow/maintenance_check.py

# 2. Run Python unit tests
py -3.13 tools/test/test_character_workflow.py
py -3.13 tools/test/test_hd_menu_assets.py

# 3. Run C tests (via WSL)
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py

# 4. Verify in-game (if applicable)
# Run in BAG2JP-exp-8mb and verify the relevant flow passes
```

**A code change is complete only after the relevant in-game flow passes, not merely after compilation.**

### Step 3: Update Documentation

| Change Type | Documentation to Update |
|-------------|------------------------|
| New character import | `CHARACTER_IMPORT.md`, relevant note in `notes/`, `_work/current-state.json` |
| New plugin/mod | `mods-src/*/manifest.toml`, `ARCHITECTURE.md`, relevant note |
| Code change | `CHANGELOG.md`, relevant source file comments |
| Configuration change | `patches/BAG2JP-game.toml` or `installer/settings.toml` |
| New tool | `tools/` directory, relevant note |

All notes must have frontmatter:

```markdown
---
id: <unique-kebab-case-id>
title: "<Descriptive Title>"
tags: ["tag1", "tag2", "tag3"]
summary: "One-paragraph summary (max 2 lines)."
related: ["RELATED_NOTE.md", "_work/current-state.json"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---

# <Title>
```

### Step 4: Commit Your Changes

Use Windows Git with an explicit project path. Make a **local commit** containing only task-owned changes.

```bash
# Check status before committing
git status

# Stage only your task-owned files
git add <your-changed-files>

# Commit with descriptive message
git commit -m "<type>: <description>

<Optional body with details>
```

**Commit message format:**

| Type | Description |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `refactor` | Code refactoring without behavior change |
| `test` | Adding or modifying tests |
| `chore` | Maintenance tasks |

Example:
```
feat: add buffer_ms validation to TOML config script

Add validate_toml_config.py to check that audio buffer_ms
stays within 30-500 ms range. Validates game.toml and
settings.toml on load.
```

## 4. Pull Request Process

The main project currently has **no remote**. A commit is a local checkpoint; uploading or publishing is separate work.

When the owner requests a publish:

1. Ensure all tests pass (35/35)
2. Ensure maintenance checks pass
3. Update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/) format
4. Refresh `BAG2JP-project-snapshot.tar.gz` (excluding build directories)
5. Create release folders/installers when requested

## 5. Character Import Workflow

If you are importing a BAG1 character to BAG2JP, follow the 5-stage pipeline:

| Stage | Purpose | Command |
|-------|---------|---------|
| 1. Inventory | Verify source, extract data | `character_workflow.py init-profile` |
| 2. Contract | Assign roles by meaning/duration | `character_workflow.py validate-profile` |
| 3. Sequence audit | Validate predecessor variants | `character_workflow.py plan` |
| 4. Experiment | Regenerate assets, update identity | `character_workflow.py prepare` |
| 5. Acceptance | Verify full game flow | In-game testing + evidence |

**Critical rules:**

- Profiles are data-only (no executable code)
- Request ≠ Role (equal request numbers ≠ equal semantic roles)
- Never clone Heat's pipeline to another character
- Gaps block progress (if `gaps` is not empty, do not prepare)
- Cache hit ≠ acceptance (visual cache is not gameplay acceptance)

See `CHARACTER_IMPORT.md` for the full runbook and `IMPORT_STANDARD.md` for the standard task guide.

## 6. Code Review Process

### Before Submitting

- [ ] All tests pass (35/35)
- [ ] Maintenance checks pass
- [ ] Frontmatter present on all modified notes
- [ ] No magic constants in C code
- [ ] Type hints on all public Python functions
- [ ] TOML values within validated ranges
- [ ] In-game flow verified (not just compilation)
- [ ] Settings, keybinds, mod state restored byte-for-byte
- [ ] Personal memory cards unchanged
- [ ] Stable install (`BAG2JP-win`) untouched

### Review Criteria

| Criterion | What Reviewers Check |
|-----------|---------------------|
| Correctness | Does the change do what it claims? |
| Standards | Does it follow coding standards? |
| Evidence | Is there in-game evidence for gameplay claims? |
| Scope | Is the change bounded to one task? |
| Documentation | Are notes and CHANGELOG updated? |
| Testing | Are there tests for new behavior? |

## 7. Repository Structure

```
D:/Dev/Recomp/BAG2JP/
├── AGENTS.md                  # Owner-approved working method
├── ARCHITECTURE.md            # System architecture (this project)
├── CHARACTER_IMPORT.md        # Canonical import runbook
├── CONTRIBUTING.md            # This file
├── IMPORT_STANDARD.md         # Standard task guide
├── MAINTENANCE_GUIDE.md       # Maintenance checklist
├── NOTES.md                   # Notes index
├── CHANGELOG.md               # Change log
├── docs/                      # Documentation (index, paths, workflows, templates)
├── patches/                   # Framework patches
├── mods-src/                  # Plugin/mod sources
├── tools/                     # Import and workflow tools
├── notes/                     # Documentation notes
├── installer/                 # NSIS installer
├── _work/                     # Working files (not committed)
└── assets/                    # Extracted game assets
```

## 8. Communication

- **Language**: Communicate with the owner in Spanish; use English for code identifiers and file names
- **Questions**: Ask before making structural changes or modifying the stable install
- **Evidence**: Share test evidence (frames, screenshots, logs) when claiming gameplay behavior
- **Status**: Keep `_work/current-state.json` updated with your progress and `gaps`

## 9. License and Legal

- Game assets and disc images remain copyrighted by their respective owners
- This project does not include retail PS1 BIOS or game disc images
- Users must provide their own legally obtained game files
- Plugin code is project-specific; check individual file headers for license information

## 10. Getting Help

| Resource | Location |
|----------|----------|
| Project policies | `AGENTS.md` |
| System architecture | `ARCHITECTURE.md` |
| Import runbook | `CHARACTER_IMPORT.md` |
| Standard task guide | `IMPORT_STANDARD.md` |
| Maintenance checklist | `MAINTENANCE_GUIDE.md` |
| Notes index | `NOTES.md` |
| Centralized paths | `docs/paths.md` |
| Workflows | `docs/workflows.md` |
| Change log | `CHANGELOG.md` |

---

*Thank you for contributing to BAG2JP. Your help preserves and enhances this classic game for modern PC.*

*Last updated: 2026-11-01*
