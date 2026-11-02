# BAG2JP — Architecture

BAG2JP is a static recompilation project for the PlayStation 1 game **Bust A Groove 2 (Japan)** (SLPM-86219), translated from MIPS machine code to native C++ for Windows PC. It runs natively — no interpreter, no JIT, no emulation loop on the hot path.

## 1. Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   BAG2JP Native Executable                  │
├──────────────┬──────────────┬──────────────┬────────────────┤
│  Recompiled  │   Runtime    │   Plugins    │   Game Assets  │
│  Game Code   │   (PS1 HW    │  (bag2jp.*)  │   (disc/ISO)   │
│  (C++)       │   sim)       │              │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
         ▲              ▲              ▲
         │              │              │
    Disc overlay      SDL3/OpenGL   Feature mods
    capture           Audio/Input   (selectable per player)
```

### Core Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Recompiled game code | `disc/` (generated from MIPS→C++) | Original PS1 game logic, natively compiled |
| Runtime (PS1 HW sim) | `psxrecomp/` framework (submodule) | GPU, DMA, SPU, GTE, timers, CD-ROM, memory cards |
| Plugins | `mods-src/bag2jp.feature.*/` | Feature mods: BAG1 content, netplay, HD intro, endings view |
| Build system | `CMakeLists.txt`, `patches/` | Framework patches, build configuration |
| Tools | `tools/bag1import/`, `tools/workflow/` | Import conversion, maintenance scripts |

### Runtime Simulation Layers

The runtime simulates PS1 hardware through MMIO (Memory-Mapped I/O) handlers:

- **GPU**: Framebuffer, texture upload, double-buffering
- **CD-ROM**: Disc reading, XA audio streaming
- **SPU**: Sound effects, voice cues, VAB banks
- **DMA**: Memory transfers between CPU and peripherals
- **Memory cards**: Save data persistence (`.mcd` format)

---

## 2. Plugin System Architecture

Plugins are the extension mechanism for BAG2JP. Each plugin lives in `mods-src/bag2jp.feature.<name>/` and follows a declarative manifest format.

### Plugin Manifest Structure (`manifest.toml`)

```toml
format_version = 11
id = "bag2jp.feature.<name>"
version = "1.0.0"
name = "<Feature Name>"
author = "BAG2JP"
description = "<One-line description>"
resolver = "declarative"
save_compatibility = "shared"

[[target]]
game_id = "SLPM-86219"

[[feature]]
id = "<feature-id>"
name = "<Feature Name>"
description = "<What it does>"
group = "<Gameplay|Video|Audio|Online>"
default_enabled = true

[[plugin]]
feature = "<feature-id>"
id = "bag2jp.<plugin_id>"
```

### Plugin Lifecycle

| Phase | When | What Happens |
|-------|------|--------------|
| `init` | Plugin load | Register hooks, read configuration options |
| `activate` | Game start | Allocate resources, attach pad transforms |
| `vblank` | Every frame | Update state, send/receive network packets |
| `deactivate` | Game exit | Free resources, restore original code |

### Current Plugins

| Plugin ID | Feature | Status | Location |
|-----------|---------|--------|----------|
| `bag2jp.bag1_versions` | bag1-heat | Active | `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_versions.c` |
| `bag2jp.bag1_stage` | bag1-stage | Active | `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_stage.c` |
| `bag2jp.charsel_popup` | select-popup | Active | `mods-src/bag2jp.feature.bag1-content/bag2jp_charsel_popup.c` |
| `bag2jp.hd_intro` | hd-intro | Active | `mods-src/bag2jp.enhancement.hd-intro/bag2jp_hd_intro.c` |
| `bag2jp.hq_songs` | hq-songs | Active | `mods-src/bag2jp.feature.bag1-content/tools/hq_bag1/` |
| `bag2jp_netsync` | netsync | Active | `mods-src/bag2jp.feature.netsync/src/bag2jp_netsync.c` |

### Adding a New Plugin

1. Create directory: `mods-src/bag2jp.feature.<name>/`
2. Add `manifest.toml` with feature, plugin, and option definitions
3. Implement plugin C source with init/activate/vblank/deactivate
4. Add to build system (`CMakeLists.txt` or equivalent)
5. Document in `notes/` with frontmatter
6. Add digest if source >10 KB

---

## 3. Data Flow: Character Import (BAG1 → BAG2)

The character import pipeline follows 5 stages. Each stage produces artifacts used by the next.

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Inventory│───▶│ Contract│───▶│Sequence │───▶│Experiment│───▶│Acceptance│
│  Stage 1 │    │  Stage 2│    │ Stage 3 │    │  Stage 4 │    │  Stage 5 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
  profile.json  profile.json  gaps identified   candidate/    in-game
  source assets acceptance     (resolved)       manifest.json  evidence
```

### Stage Details

| Stage | Purpose | Output | Authorization |
|-------|---------|--------|---------------|
| 1. Inventory | Verify source, extract model/animation/event data | `profile.json` (schema 1) | ❌ No gameplay acceptance |
| 2. Contract | Assign roles by meaning and musical duration | Updated profile | ❌ No gameplay acceptance |
| 3. Sequence audit | Validate predecessor-dependent variants | Gaps list | ❌ No gameplay acceptance |
| 4. Experiment | Regenerate changed assets, update online identity | `candidate/manifest.json` | ❌ No gameplay acceptance |
| 5. Acceptance | Verify poses/steps/attacks, full game flow | Verified evidence | ✅ Gameplay acceptance |

### Key Rules

- **Profiles are data-only**: No executable code or deployment instructions
- **Request ≠ Role**: Equal request numbers in BAG1 and BAG2 do not imply equal semantic roles
- **No generalization**: Heat-specific patches (beanie, skeleton, special attacks) must not be cloned to other characters
- **Gaps block progress**: If `character_plan` reports gaps, `prepare` cannot run
- **Cache hit ≠ acceptance**: Visual evidence cache hit is not gameplay acceptance

---

## 4. Audio Architecture

### Sound Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Game Code     │────▶│   SPU Runtime   │────▶│   Output Mixer  │
│  (cue events)   │     │   (VAB banks)   │     │   (44.1 kHz)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         │                       │
    Cue ID 0x1000+         Bank 0: Stage sounds
    (character bank)       Bank 1: Voices + SE
                           Bank 3: Announcer
```

### Audio Rules

| Rule | Description |
|------|-------------|
| Each character owns its cue base | Heat owns `0x1000`, Strike owns `0x1100`, etc. |
| Rebase BAG1 cues when needed | BAG1 0x1000 series can be remapped to avoid collisions |
| Detect collisions in mirror matches | Two players with same character voice bank |
| Preserve victory announcer names | Only when character exists in both games |
| Keep fever cues muted when appropriate | Fever animations use muted cues (0x1FFF) |
| Never assume second bank loads | Verify actual BAG2 loader behavior |

### Audio Files

| File | Format | Purpose |
|------|--------|---------|
| `XA/DANCEXA1-5.XA` | XA audio | BAG1 game songs |
| `assets/music_cd/*.flac` | FLAC 44.1 kHz | CD-quality song replacements |
| `*.VAB` | VAB | Voice/SE banks per character |

---

## 5. Online/Netplay Architecture

### Step Sync Model

Based on StepMania/SMOnline: each PC plays the match itself against its own music clock; only bar results travel between PCs.

```
PC 1                              PC 2
┌─────────┐                    ┌─────────┐
│ Own music│                   │ Own music│
│ clock    │                   │ clock   │
└────┬─────┘                    └────┬─────┘
     │                             │
     ▼ Bar result                  ▼ Bar result
┌─────────────────────────────────────────────┐
│         Network (UDP / MQTT / Direct IP)    │
└─────────────────────────────────────────────┘
```

### Transport Options

| Transport | Mechanism | Port | Use Case |
|-----------|-----------|------|----------|
| LAN | UDP broadcast | 47300 | Same local network |
| INTERNET | MQTT 3.1.1 + STUN + UDP punch | 1883 | Different networks |
| DIRECT IP | UDP host/listen | 47100 | Direct IP connection |
| LOOPBACK | Local mirror | — | Single PC testing |

### Message Types

| ID | Name | Payload | Purpose |
|----|------|---------|---------|
| 1 | M_HELLO | Address + nonce | Peer discovery |
| 3 | M_PAD | Button states | Pad input sync |
| 4 | M_STEP | Bar result | Dance step result |
| 5 | M_PING | Timestamp | RTT measurement |
| 6 | M_READY | Match ID | Start barrier |
| 7 | M_PUNCH | — | UDP hole punch |
| 8 | M_PONG | Timestamp | RTT response |
| 9 | M_FOCUS | Focus state | Window focus pause |
| 10 | M_PICK | Side, char, version | Character version selection |
| 11 | M_CONTENT | Content hash | BAG1 content identity |

### Audio Latency

| buffer_ms | Fill While Dancing | Underruns | Status |
|-----------|-------------------|-----------|--------|
| 180 ms | avg 164 ms (124-174) | None | Default, safe |
| 90 ms | avg ~80 ms | One burst at song start | Current exp install |
| 50 ms | avg 42 ms (26-92) | One burst at song start | Target (needs stall fix) |

---

## 6. Build System

### Build Environments

| Environment | Purpose | Location |
|-------------|---------|----------|
| Stable install | Preserved, do not modify | `D:/Games/.../BAG2JP-win` |
| Experimental install | Default test target | `D:/Games/.../BAG2JP-exp-8mb` |
| Build tree (Codex) | Compilation environment | `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP` |

### Build Commands

```bash
# Preflight diagnostics (Git, pins, paths, sources)
py tools/workflow/bag2_workflow.py preflight --tag <task>

# Build (WSL/llvm-mingw, 2 jobs)
py tools/workflow/bag2_workflow.py build --tag <task>

# Test stage select
py tools/workflow/bag2_workflow.py test-stage-select

# Generate report
py tools/workflow/bag2_workflow.py report --tag <tag>
```

### Build Rules

- Use verified WSL/llvm-mingw environment
- Two compile jobs
- Retain running process until build finishes
- Never modify stable install without explicit owner request

---

## 7. Testing Architecture

### Test Categories

| Type | Location | Purpose |
|------|----------|---------|
| Unit tests | `tools/test/test_*.py` | Logic validation without game execution |
| In-game acceptance | `tools/test/bag2_run.ps1` | Actual gameplay verification |
| Audio analysis | `tools/test/bag2_report.py` | Audio cue and timing verification |
| C guard tests | `tools/test/endings_view_stubs/` | Compiled-C guard cases (9 cases) |

### Test Rules

| Rule | Description |
|------|-------------|
| Descriptive names | `test_buffer_ms_rejects_out_of_range` not `test1` |
| Edge cases | Test boundary values (min, max, zero, empty) |
| One assertion per test | Each test verifies one behavior |
| In-game acceptance | Code change complete only after in-game flow passes |
| Cache hit ≠ acceptance | Visual evidence cache hit is not gameplay acceptance |
| Restore settings | Settings, keybinds, mod state restored byte-for-byte after tests |

### Running Tests

```bash
# Python tests
py -3.13 tools/test/test_character_workflow.py
py -3.13 tools/test/test_hd_menu_assets.py

# C tests (via WSL)
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py
```

---

## 8. Directory Structure

```
D:/Dev/Recomp/BAG2JP/
├── AGENTS.md                  # Owner-approved working method
├── CHARACTER_IMPORT.md        # Canonical runbook for character import
├── IMPORT_STANDARD.md         # Standard task guide for BAG1→BAG2 import
├── MAINTENANCE_GUIDE.md       # Maintenance checklist
├── NOTES.md                   # Short index of notes
├── NOTES.idx                  # Semantic index for keyword search
├── CHANGELOG.md               # Change log (Keep a Changelog format)
├── docs/
│   ├── index.md               # Documentation master index
│   ├── paths.md               # Centralized project paths
│   ├── workflows.md           # Workflows for common tasks
│   └── templates/
│       └── note-template.md   # Template for new notes
├── patches/                   # Framework patches (game.toml, CMakeLists)
├── mods-src/                  # Plugin/mod source code
│   ├── bag2jp.feature.bag1-content/   # BAG1 characters, stages, songs
│   ├── bag2jp.enhancement.hd-intro/   # HD intro movie
│   ├── bag2jp.feature.autoplay/       # 2P autoplay
│   ├── bag2jp.feature.netsync/        # Online step sync
│   ├── bag2jp.localization.regional/  # Regional content
│   ├── bag2jp.feature.mods-menu/      # In-game MODS menu
│   ├── bag2jp.feature.endings-view/   # Ending View menu
│   ├── bag2jp.debug.anim-trace/       # Animation trace
│   └── bag2jp.experimental.expanded-ram/ # Expanded RAM
├── tools/
│   ├── bag1import/            # BAG1 import conversion tools
│   └── workflow/              # Maintenance scripts
├── notes/                     # Documentation notes
│   ├── *.md                   # Original notes (with frontmatter)
│   ├── *-clean.md             # Clean versions without test noise
│   └── digests/               # Summaries of large source files
├── installer/                 # NSIS installer sources
├── _work/                     # Working files (not committed)
│   ├── current-state.json     # Compact state with gaps
│   ├── character-import/      # Per-character import work
│   └── workflow/              # Workflow logs and timings
└── assets/                    # Extracted game assets
```

---

## 9. Configuration Files

| File | Purpose | Validation |
|------|---------|------------|
| `patches/BAG2JP-game.toml` | Game configuration (video, audio, controller) | `validate_toml_config.py` |
| `installer/settings.toml` | User settings (launcher, hotkeys, window) | `validate_toml_config.py` |
| `mods-src/*/manifest.toml` | Plugin manifest | Declarative resolver |
| `_work/current-state.json` | Compact project state | Maintenance check |

### TOML Validation Rules

| Section | Key | Type | Min | Max | Required |
|---------|-----|------|-----|-----|----------|
| `[audio]` | `buffer_ms` | numeric | 30 | 500 | Yes |
| `[video]` | `internal_resolution` | string | — | — | No |
| `[video]` | `anisotropic_filtering` | numeric | 1 | 16 | No |
| `[video]` | `window_width` | numeric | 640 | 7680 | No |
| `[controller]` | `p1_deadzone` | numeric | 0 | 32767 | No |
| `[controller]` | `p2_deadzone` | numeric | 0 | 32767 | No |

---

## 10. Maintenance and Automation

### Maintenance Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `validate_frontmatter.py` | Validate and auto-fill note frontmatter | `py tools/workflow/validate_frontmatter.py --fix` |
| `generate_digests.py` | Generate/update digest files | `py tools/workflow/generate_digests.py --all` |
| `measure_context.py` | Measure startup context size | `py tools/workflow/measure_context.py --detailed` |
| `maintenance_check.py` | Run all maintenance checks | `py tools/workflow/maintenance_check.py` |
| `validate_toml_config.py` | Validate TOML config ranges | `py tools/workflow/validate_toml_config.py` |

### Context Size Target

| Scenario | Size | Target |
|----------|------|--------|
| Minimal startup (AGENTS.md + NOTES.md + current-state.json) | ~7.8 KB | < 8 KB ✅ |
| With import guide (adds IMPORT_STANDARD.md) | ~16.1 KB | Acceptable |
| Reading all notes | 144.5 KB | Avoid |

---

## 11. Coding Standards Summary

### C (plugins in `mods-src/`)

| Standard | Description |
|----------|-------------|
| No magic constants | Replace numeric literals with `#define` or `enum` |
| Validate input early | Check pointers, ranges, return values at function start |
| One purpose per function | Split functions >30 lines |
| Comment the "why" | Code explains what; comments explain why |
| Group related `#define` | Place constants at top of file with comments |

### Python (scripts in `tools/`)

| Standard | Description |
|----------|-------------|
| Type hints | All public functions have parameter and return annotations |
| Logging over print | Use `logging` module (INFO, WARNING, ERROR) |
| pathlib over strings | Use `Path` for file path manipulation |
| Specific exceptions | Catch concrete exceptions, never bare `except` |
| Docstrings | Document purpose, parameters, return value |

### Documentation (notes/)

| Standard | Description |
|----------|-------------|
| Frontmatter required | `id`, `title`, `tags`, `summary`, `related`, `created`, `updated` |
| Update `updated` | Refresh timestamp on any note modification |
| No test/debug noise | No frame numbers, PIDs, pilot results, personal paths |
| Digests for large files | Source >10 KB must have digest in `notes/digests/` |

### Testing

| Standard | Description |
|----------|-------------|
| Descriptive names | `test_buffer_ms_rejects_out_of_range` not `test1` |
| Edge cases | Test boundary values (min, max, zero, empty) |
| One assertion per test | Each test verifies one behavior |
| In-game acceptance | Code change complete only after in-game flow passes |

---

## 12. Release Process

| Step | Action | Who |
|------|--------|-----|
| 1. Verify tests | All unit tests pass | Developer |
| 2. Verify in-game | Relevant flow passes in BAG2JP-exp-8mb | Developer + Owner |
| 3. Update notes | Update relevant note with decisions/evidence | Developer |
| 4. Update state | Update `_work/current-state.json` | Developer |
| 5. Commit | Local commit with task-owned changes only | Developer |
| 6. Refresh snapshot | Update `BAG2JP-project-snapshot.tar.gz` | Developer |
| 7. Build release | Release folders/installers when requested | Developer + Owner |

---

*Last updated: 2026-11-01*
