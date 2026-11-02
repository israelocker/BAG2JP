# Ending View (SLPM-86219)

Adds ENDING VIEW between DANCE VIEW and OPTIONS. Uses the existing single-player
character/costume selector in dance-view mode, then redirects only its accepted
transition to the native ending initializer. Cancel and the normal modes stay stock.
Heat retains the shared popup's GAME row to select his BAG1 or BAG2 ending.
Other characters currently expose only COSTUME; no difficulty selector is added.

## Build and install

- Runtime source: copy `bag2jp_endings_view.c` to the build tree's `src/`.
- The build tree's `CMakeLists.txt` must contain:
  `target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/src/bag2jp_endings_view.c")`.
- Build with the project's `bag2_workflow.py build` helper (pinned WSL/llvm-mingw).
- Install `1.0.0/manifest.toml` under
  `<experimental>/mods/installed/bag2jp.feature.endings-view/1.0.0/`.
  The feature is enabled by default on the next game launch.
- Do not install a second bundled copy with the same package ID.

No framework patch or animation-role mapping is needed: the game's own ending
loader consumes the character, costume and controller-side values written by its
selector. This does not add or alter BAG1 ending media or character profiles.

## Verification

`notes/endings-view.md` records the audited JP words and actual game evidence.
`tools/test/test_endings_view.py` tests the real C callbacks with a RAM/host seam;
`tools/test/bag2_endings_view.ps1` drives a supplied experimental game PID without
closing other sessions or editing settings/cards.
