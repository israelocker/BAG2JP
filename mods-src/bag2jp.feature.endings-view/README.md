---
id: endings-view-package
title: "Ending View package"
tags: ["endings", "package"]
summary: "Package integration notes; media capabilities and actual acceptance are recorded separately."
related: ["notes/endings-view.md", "notes/character-alternate-entries.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Ending View (SLPM-86219)

Adds ENDING VIEW between DANCE VIEW and OPTIONS. Uses the existing single-player
character/costume selector in dance-view mode, then redirects only its accepted
transition to the native ending initializer. Cancel and the normal modes stay stock.
Heat retains the shared popup's GAME row to select his BAG1 or BAG2 ending.
Availability of GAME follows the shared popup/version capability, not an assumed
Heat-only roster. A version option does not prove the corresponding ending media
is imported. No difficulty selector is added.

## Build and install

- Runtime source: copy `bag2jp_endings_view.c` to the build tree's `src/`.
- The build tree's `CMakeLists.txt` must contain:
  `target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src/bag2jp_endings_view.c")`.
- Build with the project's `bag2_workflow.py build` helper (pinned WSL/llvm-mingw).
- Stage the changed package resources under mods/preloaded before build, then
  check bundled/staged output and actual selection. Install `1.0.0/manifest.toml` under
  `<experimental>/mods/installed/bag2jp.feature.endings-view/1.0.0/`.
  Check actual mods/state.toml; a default does not override all prior selections.
- Do not install a second bundled copy with the same package ID.

The selector redirection uses the game's own ending
loader consumes the character, costume and controller-side values written by its
selector. This does not add or alter BAG1 ending media or character profiles.
External movie presentation has separate framework/media requirements, documented
in notes/endings-view.md; do not assume zero framework changes for that path.

## Verification

`notes/endings-view.md` records the audited JP words and actual game evidence.
`tools/test/test_endings_view.py` tests the real C callbacks with a RAM/host seam;
`tools/test/bag2_endings_view.ps1` drives a supplied experimental game PID without
closing other sessions or editing settings/cards.
