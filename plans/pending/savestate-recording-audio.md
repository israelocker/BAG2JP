---
id: savestate-recording-audio-plan
title: "Audio alignment through native savestate loads"
tags: ["plan", "audio", "recording", "savestate"]
summary: "Approved process-only WASAPI recorder; host integration/review verified, one experimental audiovisual acceptance trial pending."
related: ["notes/gaso-import.md", "tools/test/bag2_record.py"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: plan
---

# Audio alignment through native savestate loads

Status: approved — owner selected «Corregir grabador (Recomendado)» on 2026-11-15.
Execution gate: offline feasibility first; no new game trial before that proof.
Native process-audio refinement approved: owner selected «Integrar audio por proceso
(Recomendado)» on2026-11-15, including brief quiet owned-process tone tests and
one experimental game recording only after host tests/review pass.
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

## Phase1 offline result (2026-11-15)

- Read-only replay `_work/gaso/block2/probe_explicit_pause_model.py` produces
  explicit-pause-model-feasibility.json without modifying media or manifests.
  Before/after fits have window6.63/6.82ms, but producer boundaries8496..8502
  leave5sync rows unmodeled. Fitted jump at common sample6243834 is34.228ms;
  compare at the same sample, not affine intercepts with different rates.
- Feasibility NOT demonstrated: gap boundary and audible gap content are not
  proven. Do not delete those rows or invent silence. Phases2/3 have not started.
- Source audit: anim-trace at_pcm writes mixer output; main.cpp4386..4394 flushes
  queued output on load,4420..4451 applies host fade/volume and queue/DRC after
  that dump. Thus mixer sample counts alone do not prove audible pause contents.
- Existing audio_trace T3 could observe host PCM, but audio_trace.c4..7/16/195
  compiles PCM history/WAV dumping out under PSX_NO_DEBUG_TOOLS; this build is OFF.
  No activation, rebuild or unrelated audio capture attempted. winshot tools have
  no installed audio collector in their current directory inventory.
- Next frontier: bounded research for precise audio-block timing/provenance in
  the unchanged runtime, or a game-process-only host capture source that needs
  no device install. Prove feasibility offline/host before changing the recorder
  or launching another game. A larger helper/new capture backend is a scope
  decision, not silently authorized implementation.

## Native process-audio capability trial (2026-11-15)

- Machine: Windows11Pro10.0.26200, SDK headers22621/26100; existing pwsh7.6.9
  and .NET10.0.14. No install or runtime change. Microsoft ApplicationLoopback
  sample restricts capture to the target process tree and supports silence when
  that tree has no rendering streams. Docs mention min20348(sample)/20438(API);
  local26200 exceeds both, and actual activation/initialization returned S_OK.
- Context7 returned unrelated WindowsAppSDK/WinRT libraries; used official
  learn.microsoft.com sample/API docs and installed SDK ABI, not guessed wrappers.
- Scratch prototype ProcessAudioActivationProbe.cs + probe_process_audio_activation.ps1
  always targets its OWN PID, INCLUDE_TARGET_PROCESS_TREE; no arbitrary PID option,
  no game, no microphone/system loopback, no audio files. Temp uses approved folder.
- self-activation-a:721ms, successful activation/init, no Start or packets.
  self-packets-a/b:699/606ms, exact-zero test failed under PCM16; b recorded
  peak1LSB/199nonzero samples in441frames, Stop succeeded. Retained failures.
  Changing only sample representation to float32 at the SAME44100Hz returned
  5exact-zero441-frame packets, each10ms apart by native QPC(100ns units),624ms
  including compilation. Consistent with conversion dither, not proof of its cause.
- DevicePosition remained0 for all5packets; never assume it is a usable sample
  counter. QPC advances and locally accumulated frame counts are the candidate.
  Capability JSON and versioned source/report backups under _work/gaso/block2/process-audio/.
- Proven: API availability and native silent packet timing on own process.
  NOT proven: non-silent signal fidelity, two-process exclusion, target exit,
  stream faults, full recording alignment, game behavior or accepted video.

## Approved scope refinement: process-audio backend in existing recorder

This is a different source, not a piecewise repair of pre-host mixer PCM.
It adds a native helper/backend; owner confirmation is now recorded above.

1. Host proof with two OWNED processes and two brief quiet synthetic tones:
   capture target only, verify wanted signal and excluded sibling signal, then
   pause/stop/resume rendering and require genuine native silence/continuous QPC.
   No unrelated-app capture, master-volume change or device installation.
2. Opt-in adapter within existing tools/test/bag2_record.py; likely files
   process_audio_capture.cs/.ps1 or a smaller demonstrated equivalent,
   process_audio_capture.py, test_process_audio_capture.py and test_bag2_record.py.
   Native helper verifies game PID/path/start-time and lifetime; NEVER default
   endpoint/system capture, EXCLUDE mode, PID0 or silent fallback to another source.
3. Preserve original float32PCM and packet flags/QPC metadata. The review artifact
   must use a truly lossless float-capable audio codec, not silently quantize to
   FLAC16. Owner delivery remains AAC. DevicePosition0 is diagnostic, not trusted.
4. Declare audio_source in manifest; use clock anchors/packet timestamps to prove
   the existing one-frame window bound, rate/data/identity checks and complete
   coverage. Reject lost packets, TIMESTAMP_ERROR, unmarked discontinuity, bad
   anchors, unknown gaps and target exit. No estimated silence or discarded PCM.
5. Existing mixer dump remains default/historical diagnostic; unchanged captures
   keep their behavior. Do not change/re-finalize historical rejected evidence.
6. Run new seam tests, existing recorder/window/audio tests and relevant regression
   suite; Goldfish review per repo before closing tools changes; then ONE fresh
   authorized experimental recovery trial and frame/audio review before conformity.

Only the host proof and recorder's audio capture path change. No game save system,
runtime/EXE/framework/MODMEM, stable install, device drivers or other applications.
If the native source cannot pass these tests, leave the capture rejected.

### Host proof and implementation contract (2026-11-15)

- Owner approval is definitive; no further scope gate is open. signal-proof-a/b/c
  rejected QPC jumps when PlaySound closes/recreates streams. b: buffer441frames,
  max processing832us; c requested100ms but actual441frames, still rejected.
  Keep failures: no missing packets may be replaced with estimated silence.
- Persistent one-second owned PCM reference (88244B,44100frames; tone120ms,
  zero pause100ms, tone120ms; fixed peak98/32768,5ms fades) passed both directions:
  signal-persistent-a:440Hz/exclude880Hz -73.96dB,2.367s;
  signal-persistent-b:880Hz/exclude440Hz -60.32dB,2.851s.
  Each60packets/26460frames,9internal zero packets,QPC residual0us;9validator
  tests pass. Sources and hashes retained in each trial directory. No game run.
- Ruling: model a pause within a persistent source, as the unchanged runtime
  keeps its SDL stream during load; stream recreation remains fatal. This proof
  does not establish timing on the real game or full-length capture.
- Minimal contract: isolated C# helper hosted by installed pwsh/MTA, Python
  adapter/validator, existing recorder opt-in. Only INCLUDE tree of verified
  PID/path/creation-time on held handles. Parent stdin STOP with session token;
  EOF/target death/timeout/helper crash never counts as clean completion.
- Version1 JSONL: READY(identity,token,format,mode); ANCHOR(native QPC-before,
  precise UTC FILETIME,QPC-after,frequency); PACKET(seq,byte offset,frames,flags,
  QPC100ns,device position diagnostic); TERMINAL(clean STOP token,totals,PCM SHA).
  Anchors at start/periodically/end; all integer clock values decimal strings.
  Preserve source float32 bytes; SILENT flag authorizes only its declared frames.
- Validator checks complete journal/PCM, identity/token, clock conversion and
  sample-level continuity (1sample+200ns), finite float data and exact silence.
  Require full video coverage and existing one-frame clock/rate bounds; no padding,
  resampling, sample removal or reuse of the dump's outlier-dropping model.
- Execution ledger: host proof, helper, strict validator and recorder opt-in done.
  Goldfish2 found cancellation/reaping and native/fractional coverage defects;
  reproduced, fixed,58targeted tests PASS16.098s,8assertion mutants killed6.829s.
  Actual backend-signal-a passed(-73.9579dB sibling exclusion,4345silent frames,
  282packets/QPC0us residual); corrected validator replays retained capture PASS.
  Native fault matrix6cases PASS; actual parent death reaps helper170.79ms while
  target lives. Next: fresh authorized full experimental recording with process
  opt-in, audiovisual acceptance/review. Historical rejection untouched.

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
| 1 | Persistent owned-source signal/isolation/pause passed both directions; stream recreation rejected |
| 2 | Integrated opt-in;58tests/8mutants, real backend signal and lifecycle proof PASS |
| 3 | Goldfish findings fixed/tested; fresh experimental recording + audiovisual review pending |
