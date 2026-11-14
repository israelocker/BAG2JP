---
id: strike-comparison-graphics
title: "Strike: enhanced comparison sessions"
tags: ["strike", "graphics", "plan"]
summary: "Owner-approved paired Dance View sessions; runtime graphics limits verified, original cards preserved, restore pending after screenshots."
related: ["notes/strike-recovery.md"]
created: "2026-11-04"
updated: "2026-11-04"
doc_kind: plan
---

# Strike: enhanced comparison sessions

Status: sessions prepared and intentionally left open for owner screenshots2026-11-04.

## Objective
Leave BAG1 native reference and BAG2JP experimental open on Strike BAG1/B,
Dance View NEUTRAL/camera0, with loaded copied memory cards, for owner screenshots.
Do not accept visual fidelity or modify character assets in this cycle.

## Constraints verified
- BAG1 reference: `D:/Dev/Scratch/bag1-native-reference`; BAG2 experimental:
  `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`.
- RTX3090 display currently reports2560x1440 at143Hz; virtual display3840x1100
  at60Hz. Internal4K is not a physical4K screen or a guaranteed4K desktop capture.
- BAG1 bag.display offers144fps motion-adaptive frame blending, preserving
  guest59.94Hz. BAG2 runtime parses frame_interpolation/fps settings, but actual
  availability and sustained output must be verified; no speedup/overclock.
- Runtime versions differ. BAG2 settings texture_filtering is ignored: use
  Image Filtering mod. BAG1 title game.toml supplies its filtering/resolution.
- Installed BAG2 HD replacements cover UI/font, not Strike. No compatible
  faithful Strike HD replacement pack was verified by the bounded web search.
- Official DuckStation documentation lists upscaling/filtering/true colour/PGXP
  and discourages compatibility hacks. These are reference principles, not
  proof that a DuckStation pack/config works in PSXRecomp.
  Source: https://github.com/stenzek/duckstation (read2026-11-04).

## Proposed choices
- Internal2160lines (4K class), windowed display sized for actual desktop;
  preserve4:3 to avoid cropping/stretching the reference character.
- PGXP geometry/perspective correction where supported; depth-buffer hacks off.
- xBR if supported, otherwise demonstrated bilinear; no speculative sharpening,
  AI retextures, shader downloads, widescreen or forced guest frame-rate patches.
- Target144 presentation frames via existing interpolation only. Measure/inspect
  pacing; report unsupported/dropped output honestly. Motion smoothing may add
  ghosting and does not improve still-image texture detail.
- Keep settings reversible and games open when handing control to owner.

## Steps
1. Back up game/settings/mod/keybind files; copy cards; record original hashes,
   process identities and restoration commands in a new `_work` session directory.
   Verify: original-card hashes unchanged and no user-owned instances displaced.
2. Apply only supported graphics settings to each isolated session. No executable
   rebuild or replacement. Verify: effective startup logs and real output/pacing.
3. Load cards through normal game menus; choose StrikeB in both Dance Views.
   Verify: screenshots show yellow-shirt Strike, NEUTRAL and camera0 in each.
4. Leave both open; record PIDs, configuration, card locations and pending restore.
   Verify: both identities alive; owner can focus each window and take captures.

## Out of scope
Heat/VS regression, stable install, source/renderer changes, arbitrary texture
generation, unverified external pack installation, claiming144 native gamefps.

## Progress
| Phase | Status |
| --- | --- |
| Read installed capabilities and bounded external reference | Done |
| Approve internal4K / interpolated144 / existing verified enhancements | Approved |
| Configure and leave both Dance Views open | Done with runtime limits below |

## Execution evidence and deviations
- Session journal: `_work/character_import/strike/graphics-session.json`.
- BAG1 PID17936, run `graphics-run/20261104T123257-native`: LOAD OK captured,
  StrikeB/NEUTRAL/camera0 reviewed. Installed runtime rejects supersampling9
  (`123203-native/stdout.log`); failed launch restored, then maximum4x retained.
  PGXP remains enabled and bilinear retained; no4K claim for this executable.
- BAG2 PID40012, run `graphics-run/20261104T124350-candidate`: StrikeB/NEUTRAL/
  camera0 reviewed; copied enabled cards mounted (no separate manual LOAD OK
  capture). Internal9x confirmed. First boot `124027-candidate` ignored legacy
  interpolation settings and was closed/restored; final boot uses existing
  one-run env PSX_FRAME_INTERPOLATION=1 / PSX_FRAME_INTERPOLATION_FPS=144 after
  that clamp. No executable/plugin modification.
- Both logs confirm144presents/s target, native change-adaptive blend and BAG2
  linear blend. Sustained presenter144fps not measured; coarse guest heartbeat
  check59.7Hz each confirms no144Hz game-speed change during that sample.
- Verification: `graphics-run/verification.json`;3native and21experimental original
  save files unchanged. Restoration remains pending while owner uses the windows.
- Close/restore commands recorded in journal; never automatically close these
  handed-over sessions during a later preflight. No snapshot/release needed.
