# Changelog

All notable changes to BAG2JP are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Documentation index (`docs/index.md`) with navigation by category
- Centralized paths reference (`docs/paths.md`)
- Workflow guides (`docs/workflows.md`) for common tasks
- Note template (`docs/templates/note-template.md`) for consistent documentation
- Frontmatter standardization on all notes (`id`, `title`, `tags`, `summary`, `related`, `created`, `updated`)
- Digest files (`notes/digests/`) for source files >10 KB
- Semantic index (`notes/NOTES.idx`) for keyword-based search
- Compact state file (`_work/current-state.json`) with `gaps` field
- Maintenance scripts (`tools/workflow/`):
  - `validate_frontmatter.py` - validate and auto-fill note frontmatter
  - `generate_digests.py` - regenerate digest files
  - `measure_context.py` - measure startup context size
  - `maintenance_check.py` - run all maintenance checks
  - `validate_toml_config.py` - validate TOML config ranges
- Clean versions of notes (`*-clean.md`) without test/debug noise

### Changed
- `AGENTS.md` - Added optimized chat startup protocol (≈7.8 KB vs ≈80 KB)
- `notes/bag1-character.md` - Added frontmatter, standardized structure
- `notes/bag1-stage-song.md` - Added frontmatter, standardized structure
- `notes/online.md` - Added frontmatter, standardized structure
- `notes/endings-view.md` - Added frontmatter, standardized structure
- `notes/project.md` - Added frontmatter, standardized structure
- `notes/character-pipeline.md` - Added frontmatter, standardized structure
- `notes/regional.md` - Added frontmatter, standardized structure
- `notes/ui-mods.md` - Added frontmatter, standardized structure
- `notes/assets.md` - Added frontmatter, standardized structure
- `notes/agent-handoff.md` - Removed migration/chat history, kept only essential info
- `tools/workflow/generate_digests.py` - Added type hints, logging, argparse
- `tools/workflow/validate_frontmatter.py` - Added type hints, logging
- `tools/workflow/measure_context.py` - Added type hints, logging
- `tools/workflow/maintenance_check.py` - Added type hints, logging

### Removed
- Personal file paths (`C:/Users/israe/...`, `D:/Dev/Tools/...`) from notes
- Test execution details (frame numbers, PIDs, pilot results) from notes
- Chat/conversation history references from notes
- Magic constants in `bag2jp_netsync.c` replaced with named `#define`

### Fixed
- Magic constants in `bag2jp_netsync.c`: added `NS_PKT_HDR`, `NS_MQ_BUF`, `NS_EV_BUF`, `NS_BROKER_MAX`, `NS_STUN_MAX`, `NS_LINE_MAX`

## [1.0.0] - 2026-10-31

### Added
- Initial BAG2JP project structure
- Heat character import (model, animations, fever, voices)
- Stage port and song chart conversion
- Online netplay with step sync
- Ending View implementation
- Regional content options
- HD fonts and UI mods

[Unreleased]: https://github.com/upstash/context7
[1.0.0]: https://github.com/upstash/context7
