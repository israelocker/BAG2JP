---
id: endings-view-current
title: "Endings View - Current State"
tags: ["endings", "acceptance", "ledger"]
summary: "Current continuation point, scope and verified evidence for BAG2JP endings view"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-11-01"
updated: "2026-11-01"
---

# Ending View — implementation and acceptance ledger

## Current continuation point (owner steering, 2026-11-01, updated)
- Priority: Heat BAG1 black ending video now; HD menu is implemented and
  acceptance evidence is present.
- Owner supplied the HD menu original at `assets/ui/ending-view-menu.png`
  (1306x816, six rows). It was cropped into the native 192x120 atlas cells,
  upscaled 8x, inset to 85% and centered to preserve vertical margins, and
  colored with the audited palette. Assets:
  `mods-src/bag2jp.feature.endings-view/1.0.0/menu_hd` (2 files, ready.txt),
  `_work/endings-view/hd-menu-preview.png`,
  `_work/endings-view/hd-ending-view-menu.png`,
  `_work/endings-view-hd/hd-ending-view-popup.png`,
  `_work/endings-view-hd/hd-options.png`,
  `_work/endings-view-hd/hd-menu-return.png`.
- Fresh spacing acceptance: `_work/hd-menu-margin-20261101-105041/` shows all
  six labels at 85% with clear row gaps, OPTIONS selected, Heat's GAME/COSTUME
  popup, and stock cancel return. Asset tests pass 2/2 and require at least four
  native transparent pixels above and below every label. Settings and both
  memory cards remained byte-identical.
- The HD path is a replacement for the audited native lettering, not a separate
  overlay or generated font. It uses the game's own textured quad routine
  (`0x8009B258`) and only the unused OPTIONS-row UVs for ENDING VIEW.
- Stock sound and confirmation fade are now retained. The confirm hook marks the
  pending transition, leaves the button intact, and dispatch later maps visual
  index4 to stock DANCE VIEW3. No button is swallowed. Live sound still needs
  the owner's confirmation.
- Latest source unit seam: 9/9 passed, including HD menu packet creation and stock
  confirmation/fade retention. Latest build `endings-view-hd-menu` passed and was
  deployed as SHA256 `49ECD14403FFB481E79EBF56499516DEA2EC94F379F9869AE0CE336F5EBDFB9C`.
  Earlier deployed executable and notes are no longer current.
- Heat BAG1 black video is fixed. Root cause: while the guest display is disabled,
  `main.cpp` presents one black frame and then suppresses later swaps. The external
  movie starts after that frame, so it decoded normally but its HUD callback was
  never reached (`draw_calls 0`). The host movie now requests continuous blank/HUD
  presentation only for its active lifetime; normal disabled-display behavior is
  unchanged before and after it. Reproducible framework change:
  `patches/psxrecomp-disabled-display-hud-present.patch`; synchronized title source:
  `mods-src/bag2jp.enhancement.hd-intro/bag2jp_hd_intro.c`.
- Fresh final acceptance: `_work/heat-bag1-final-present-20261101-110127/`.
  MPEG image is visible at 9s and 17s; log records 658 frames, 22.00s and 1320
  draw calls; Heat then visibly dances in native credits. Build
  `heat-ending-final-present` passed. Settings and both memory cards remained
  byte-identical.
- No task commit or snapshot refresh yet: remaining full task close-out pending.
- Heat MUST expose GAME (BAG1/BAG2) plus COSTUME; other current characters expose
  COSTUME only. The rejected hide-GAME experiment is removed and the shared
  character popup has no remaining task diff.
- Source currently uses a temporary native-lettering recipe from
  `assets/archive/system/016/001.tim` rather than the earlier unrelated font.
  The owner-supplied HD image supersedes this experiment. Preview only:
  `_work/endings-view/native-lettering-preview.png`; `tools/test/preview_endings_label.py`.
- Confirmation was corrected in source to retain the **stock sound and fade**:
  confirm hook marks pending, leaves the button intact; dispatch maps pending
  visual4 to stock DANCE VIEW3, while visual OPTIONS5 maps to stock4. This also
  retains stock side/mode initialization. Live sound verification still pending.
- Latest unit seam: 8/8 passed, including native packet lettering and stock
  confirmation/fade retention (RED first: both failed, 6/8). Latest compiled build
  is `endings-view-movie-probe`, NOT yet deployed. Earlier deployed executable
  still has the old-font/immediate-confirm draft. Do not confuse these revisions.
- Heat BAG1 black reproduced twice, including BOTH PrintWindow and real screen:
  `_work/endings-view-heat-bag1/movie-12s.png` and
  `_work/endings-view-heat-bag1-repro/movie-{screen,printwindow}.png`.
  Actual movie file is valid: `source-frame-8s.png` extracted with
  `D:/ffmpeg/bin/ffmpeg.exe` shows real picture. Player logs decode 658 frames over
  22 seconds, but presentation is black. Afterwards Heat BAG1 visibly dances in
  the native credits (`movie-or-dance-40s.png`); logs say `movie 0 0`, `dance 0 0`.
- Diagnostic-only edits in build `src/bag2jp_hd_intro.c`: reset `s_draw_calls` at
  movie start and include draw_calls at stop. Not yet exercised. Pre-edit build
  source preserved at `_work/endings-view/hd-intro-before-movie-debug.c`.
  IMPORTANT: this file already differed from canonical before the task (shared
  movie-player additions); do NOT overwrite it with the older canonical copy.
  Root cause remains unproven. Hypothesis: frozen guest ending update prevents
  host presentation; alternatively GL/HUD state. Obtain draw-call evidence before
  fixing. `gl_swap_with_osd` normally calls HUD; no framework fix made.
- Task-owned game PID12912 was requested to close gracefully. Preserve unrelated
  installer edits, `.opencode/`, cache and original trace/HD-intro drift.
- No task commit or snapshot refresh yet: final HD menu/movie acceptance pending.

## Scope (2026-11-01)
- Approved flow: main menu > DANCE VIEW > ENDING VIEW > OPTIONS in that order;
  ENDING VIEW opens the stock single-character/costume selector, no difficulty,
  and launches that selection's ending directly. Keep normal modes unchanged.
- Continue the existing canonical/build-tree local workflow; no new worktree,
  branch, remote push, framework-pin change or stable-install change.
- Prior session built/deployed a draft but only ran a 2P match. That is NOT
  ENDING VIEW acceptance. Preserve installer edits and unrelated source drift.

## Verified JP evidence
- `assets/archive/system/002.dbi`, base `0x8008F890`: main menu routine
  `0x80099C50` starts `0x3C028019`. Live title/menu root state is **7**, not 9.
- Four wrap/limit words: `0x80099F48/0x8009A024 = 0x24020004`,
  `0x8009A0C0/0x8009A1A0 = 0x28420005` (4->5 and 5->6 respectively).
- P1/P2 confirm: `0x8009A23C/0x8009A28C = 0x30420820`.
- Menu dispatch `0x80099D30 = 0x2C620005`: map visual index 5 to stock OPTIONS 4
  in v1 only. Highlight setup `0x8009A814 = 0x24060001`: swap a1 4/5 only.
- Stock menu label sprite y immediates at `0x8009A894/0x8009A9C4/0x8009AAC4/0x8009ABF0`
  are `0x24020068/0x2402007E/0x240C0094/0x240200A7`; shift up 20 pixels.
  OPTIONS remains y187; new text is y167. Final sprite setup call
  `0x8009AD30 = 0x0C012649` calls `0x80049924`; replay before adding text.
- Draft hook `0x8009A800` was not the per-frame label call. Draft guest function
  `0x0F000100` collided with MODS; Ending View now uses `0x0F000200`.
- `system/007.dbi`: selector exit `0x8008FDE0 = 0xAC51D3D4`, then writes
  module from s2 and state from s3. Accept in dance mode is module1/state0x18
  (`0x80090D70..80`); do not redirect cancel. Redirect accepted ending to
  module3/state0x1A. Keep the selected controller side.
- `system/004.dbi`, `0x8009269C`: ending initializer sets mode5; reads side
  at `0x800926F0`, char `0x8005E6A0/A4`, costume `0x8005E668/69`; costume1
  adds 0x20 to the ending resource index. State becomes 0x1B at `0x800928E8`.
- Disassemblies retained under `_work/ending-{menu,select,play}-dis.txt`.

## Tests and commands
- WSL Ubuntu has Capstone 5.0.7; embedded Ghidra Python does not. Use
  `wsl.exe -d Ubuntu --exec python3 <WSL-path-to-mipsdis.py> <DBI> 8008f890`.
- Unit seam (real plugin C, stubbed RAM/host calls, not guest execution):
  `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py`.
  RED on draft: guest address, order, overlay guard, confirmation and cancellation
  fail; ending redirect and untouched stock selector pass (2/7).
- Fresh preflight: `_work/workflow/20261101T083413178676Z-endings-view-resume/`.
- Test-owned baseline process PID37860; backups of settings, state and cards in
  `_work/endings-view/`. Baseline screenshot `baseline-menu2.png` shows stock
  five-item menu, no ENDING VIEW. Debug watch confirms state7.
- GREEN: 7/7 unit cases. Build helper passed in 22.916 seconds (two jobs), log
  `_work/workflow/20261101T084245369426Z-endings-view-fixed/build.log`.
  Deployed executable SHA256 `A7F292AC512D87B708FA9A9B654F2E38DD12EA86AC188BA4FDB324F2428AF954`.
- Fresh experimental PID27044 evidence in `_work/endings-view/`:
  `fixed-menu2.png` six rows in the requested order; `options-selected.png` and
  `options.png` demonstrate visual index5 opens OPTIONS (including MODS).
  `selector-ready.png` stock one-player character selector; `cancel-return.png`
  and `cancel-plugin.log` show cancel retains module4/state6, then root7.
  `costume.png` shows Comet's COSTUME-only popup (no difficulty). `accept-plugin.log`
  records char2/costume1/side0 -> ending; root becomes 0x1B, module3/state0x1A.
  `comet-b-ending.png` and `_work/shots/endings-view-comet-b/f021504_00.png` show
  the actual story; `f025002_00.png` shows Comet B dancing during native credits.
  End-of-credits return observed at frame33640: module4/state6 (native ranking/title
  flow). `comet-b-menu-return.png` actually shows Score Ranking; the second run's
  `selector-selected.png` proves the main menu can subsequently be used again.
  `ending.png` was only NOW LOADING, not proof
  of playback; `selector.png` in the first attempt was still a black loading frame.
- Read-only independent review found no demonstrated critical/important defect.
  Unit seam does not execute the draw, dispatch/highlight MIPS instructions or
  full guest register preservation; those are covered only by live evidence and
  the verified host-call API implementation, not by the seven unit assertions.
- Second selection: `_work/endings-view-second/costume-a.png` is Strike with
  COSTUME A only; log confirms char1/costume0/side0 -> ending. `ending-a.png`
  shows native story playback without a campaign. Only Comet B was watched through
  all credits; do not extrapolate full-ending acceptance to every character or BAG1.
- Owner clarification: Heat MUST retain GAME to choose BAG1 or BAG2 endings.
  The brief experiment hiding that row was rejected and removed, including its
  lifetime API and dedicated unit assertion. The shared popup remains unchanged.
  `_work/endings-view-heat/costume-only.png` belongs to the REJECTED experiment,
  not the accepted feature. `normal-dance-view-popup.png` demonstrates the stock
  GAME/COSTUME behavior to retain in Ending View too. Other characters need no
  GAME row unless their existing shared capabilities provide multiple versions.
- Configuration/card hashes matched the pre-test backups while running (game.toml,
  keybinds.ini, mods/state.toml, saves/card1.mcd and card2.mcd). Final post-exit
  preservation check and snapshot recorded below when complete.
- Reusable UI harness:
  `& D:/Dev/Recomp/BAG2JP/tools/test/bag2_endings_view.ps1 -GameId <task-owned-PID> -Action options|selector|cancel|accept`.
  Requires `BAG2JP_ANIM_TRACE=1` and `BAG2JP_WATCH=8005D3D4:4,8005F7CC:1,8005F7C8:4,80192028:4,8005E6A0:4,8005E668:2`.
  Polls observed root/cursor; root12 is selector init, root13 is interactive. Does
  not start/kill processes or change configuration. Screenshots are not acceptance
  by themselves; inspect them after loading. Test artifacts remain outside Git.
