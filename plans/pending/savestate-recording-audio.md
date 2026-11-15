# Audio alignment through native savestate loads

Status: proposal — owner decision pending; no recorder implementation authorized yet.
Topic: notes/gaso-import.md, Block 4. No external tracker/remote.

## Evidence and objective

Runtime94922aba, trial block4-recovery-ready completed the native F7 save/load,
CAUGHT recovered side2 and retired again; song ended and returned to selector.
Recording was REJECTED, not gameplay acceptance: audio window24.67ms > one frame.
Read-only clock replay localizes a persistent wall/audio step30.704ms around
loadgf8496..8502; producer excess32.498ms and native load log23.1ms.
Other stalls do not show that persistent step. Do not repeat unchanged runs.

Objective: represent a proven native-load pause without relaxing alignment
thresholds or accepting unmarked drift. This changes recording tooling, NOT the
game's existing save system. Original rejected recordings/manifests remain intact.

## Phases

### 1. Prove an explicit-pause model offline (S)
- Acceptance: distinguish the native load from unmarked stalls; demonstrate
  sample-preserving timing/correct gap semantics, or stop as unsupported.
- Acceptance: synthetic marked-load cases pass the existing per-window precision;
  unmarked drift, forged/incomplete markers and ambiguous boundaries fail closed.
- Verification: `py -3.13 _work/gaso/block2/analyze_recovery_ready.py` (baseline);
  a new throwaway replay under `_work/gaso/block2/` with measured results and hashes.
- Files: task-owned replay/prototype only; inspect tools/test/bag2_record.py,
  tools/test/test_bag2_record.py and the recorded producer clocks/load trace.
- Test seam: real capture clock/audio-placement functions on copies plus synthetic
  native-pause inputs; retain all original media/PCM and baseline rejection.
- Blocked by: owner approval of this proposal.

### 2. Integrate only the proven model (S)
- Acceptance: opt-in explicit native-load metadata, not automatic segmentation of
  arbitrary hitches; ambiguous or unavailable evidence remains rejected.
- Acceptance: ordinary capture behavior and its one-frame/window, rate, missing-data
  and window-identity guards remain unchanged. Output declares timing/gap handling.
- Verification: `py -3.13 -m unittest tools.test.test_bag2_record
  tools.test.test_audio_clock_probe tools.test.test_recording_window
  tools.test.test_anim_trace_samples`; negative/mutation checks on the new seam.
- Files: tools/test/bag2_record.py, tools/test/test_bag2_record.py; a small helper
  only if the validated model needs it. No speculative framework/module rewrite.
- Test seam: actual finalize path and media-filter output, not text assertions.
- Blocked by: phase1 feasibility demonstrated without invented audio or masked drift.

### 3. Review and one fresh recorded acceptance trial (S)
- Acceptance: Goldfish review per notes/goldfish-review.md before closing tools edits;
  apply verified findings and re-run only affected checks.
- Acceptance: one fresh experimental Gas-O/Heat BAG1A trial with the same runtime,
  complete save/load/recovered/retirement/end/selector and accepted=true.
- Acceptance: agent frame/audio review first, then evidence and owner conformity;
  no claim of visual recovery from the rejected historical take.
- Verification: existing recorded wrapper, `bag2_record.py finalize --tag <fresh>`,
  `frames --tag <fresh> --frame <event-gf> --span 12 --step 2`, ffmpeg-skill probe/look,
  independent restoration/config/saves hashes.
- Files: existing task wrapper/metadata as necessary; canonical Gas-O note/digest,
  current-state and per-tool evidence. No new runtime build/deploy.
- Blocked by: phase2 host proof and required cold review.

## Decision log
| Decision | Proposed choice | Why |
|---|---|---|
| Scope | Correct recording support for explicit native pauses | Gameplay trace already completes; unchanged runs cannot fix the affine mismatch |
| Safety | Preserve all original media/PCM/manifests; reject ambiguity | Acceptance must prove timing, not weaken a threshold |
| Runtime | Keep94922aba and canonical guard0 unchanged | No new save system/debug-server/rebuild required for this investigation |

## Not yet specified
- Phase1 measurement decides whether existing producer/load markers bound timing
  and the gap's audible content sufficiently. If not, stop; do not fabricate silence
  or silently change the meaning of “exact game audio”.
- Implementation shape/filter is deliberately conditional on that measurable proof;
  user preference is scope (recording fix versus defer and internal Block5), not an
  arbitrary numeric offset or a request to relax a gate.

## Always / Never
- Always: evidence before acceptance; local sequential Git; same experimental target;
  protect saves/settings; one GPU workload; precise scope and measured limitations.
- Never: raise thresholds, delete inconvenient sync samples, hide a pause by cropping,
  auto-accept failed historical captures, alter the save format/runtime/MODMEM,
  touch the stable install, install audio devices or capture unrelated desktop audio.
- Out of scope: character Block5, new save/load system, debug tools build, release,
  snapshot, subjective audio approval.

## Progress
| Phase | State |
|---|---|
| Diagnosis | Done: replay and native load log correlate the persistent timing step |
| 1 | Pending owner scope approval |
| 2 | Blocked by1 |
| 3 | Blocked by2 + Goldfish |
