# project.md Digest

**Source:** `notes/project.md` (12 KB, 159 lines)

## Resumen
Historial de builds, estructura de carpetas, save data, y puntos de resume para BAG2JP.

## Builds History

| Build | Path | Estado | Descripción |
|-------|------|--------|-------------|
| v1 base | `releases/v1-base` | Historical | Base build 2026-10-26 |
| v2 graphics | `releases/v2-9x-pgxp-16x9` | Historical | 9x PGXP 16:9 |
| v3 widescreen squash | `releases/v3-9x-pgxp-16x9-squash` | **Current stable** | Widescreen squash mode |
| v4 experimental 8MB | `D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb` | **Active experimental** | 8MB RAM, main test target |
| v5 experimental autoplay | `releases/v5-exp-autoplay` | Installed in exp | Autoplay feature |
| v6 experimental HD intro | `releases/v6-exp-hd-intro` | Installed in exp | HD intro movie |

## Folder Contents
```
D:\Dev\Recomp\BAG2JP\
├── patches/              # Game.toml, CMakeLists patches
├── mods-src/             # Source mods (features)
├── tools/                # Build/test/conversion tools
├── notes/                # Documentation (THIS FILE)
├── _work/                # Working files (evidence, cache, temp)
├── installer/            # NSIS installer sources
└── assets/               # Extracted game assets
```

## Save Data
- `saves/card1.mcd` - Main memory card (DexDrive format)
- `saves/card2.mcd` - Secondary card
- Installer writes card1.mcd with SetOverwrite off (preserves player progress)
- Save IS fully unlocked (hidden chars = real icons, DANCE VIEW available)
- Game loads card at boot automatically

## Open Items (as of 2026-11-01)
1. Next character import (after Heat validation)
2. Stage import for remaining BAG1 characters
3. Song porting for remaining BAG1 tracks
4. Dance grid edge optimization (3 nonadjacent edges deferred)
5. Online regression testing (2 real PCs, different networks)
6. Audio latency: remove song-start stall, target buffer_ms 50

## Tools (D:\Dev\Tools, 2026-10-28)
- psx-asset-tools (Python + Pillow + ffmpeg)
- Ghidra (headless decompilation)
- winshot (PrintWindow capture, postkey, sendkey, focus)
- NSIS 3.08 (Ubuntu debs)

## Testing & Debugging (2026-10-30)
- `D:\Dev\Tools\winshot\bag2_run.ps1` - Run game with config
- `tools/test/bag2_report.py` - Generate test reports
- `BAG2JP_ANIM_TRACE=1` - Animation trace logging
- `BAG2JP_CPU_SKILL=200` - CPU attack in autoplay
- `BAG2JP_WATCH=addr:size` - Memory watch logging
- `BAG2JP_AUDIO_DUMP=1` - PCM hook final mix
- `BAG2JP_AUDIO_PROBE=1` - Audio latency probe

## Codex Build/Test Environment (2026-10-30)
- Build tree: `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP`
- WSL/llvm-mingw environment verified
- 2 compile jobs, retain running process

## Local Workflow Helper (2026-10-30)
- `python tools/workflow/bag2_workflow.py preflight` - Git/pins/path/source/resource diagnostics
- `python tools/workflow/bag2_workflow.py build` - Build
- `python tools/workflow/bag2_workflow.py test-stage-select` - Test stage select
- `python tools/workflow/bag2_workflow.py report --tag <tag>` - Full logs + per-phase timings in `_work/workflow/`

## Historical Resume Instructions (Claude's former VM - DO NOT RUN ON WINDOWS)
- Kept for reference only, not applicable to current Windows environment

## Referencias Rápidas
- Stable install: `D:\Games\Bust A Groove 2 (Japan)\BAG2JP-win` (preserve)
- Experimental target: `D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb`
- Snapshot: `BAG2JP-project-snapshot.tar.gz` (excludes build dirs)