---
id: strike-skeleton-motion-recovery
title: "Strike skeleton and motion recovery"
tags: ["strike", "plan", "animation"]
summary: "Owner-approved recovery; loading regression recovered, skeleton/motion implementation and visual/audio acceptance pending."
related: ["notes/strike-recovery.md"]
created: "2026-11-03"
updated: "2026-11-03"
doc_kind: plan
---

# Strike skeleton and motion recovery — approved, in progress

Status: **Approved by owner in chat; not complete**. Claims below from the failed
ad-hoc reconstruction are superseded by notes/strike-recovery.md's current audit.

## Objective and acceptance

Recover complete hands, native BAG1 proportions and grounded transitions for
both costumes on both player sides, while preserving Heat and existing settings/saves.
Acceptance requires visible hands/arms, no sinking between consecutive normal
steps, correct attacks/defenses, applicable fever, song end and return to selection.
Compilation and host tests alone do not satisfy this requirement.

## Approved implementation boundaries

Preserve full native BAG1 44-bone models and their matching motions. Adapt only
proved runtime contracts for BAG1 Strike, leaving BAG2 and Heat unchanged. Never
infer equivalence from frame counts, compensate with arbitrary height offsets,
or copy a Heat-specific adapter without native evidence.

1. Audit native hand initialization, mesh substitutions, events, root/bind scaling
   and channel ordering by costume and side. Record overlay identity, base and
   original words before guarded runtime edits.
2. Reconstruct motion policy by semantic role, beats, required events and native
   predecessor dispatch. Reject empty required slots and report unresolved roles.
3. Implement a narrowly guarded adapter with restoration. Rebuild one coherent
   experimental package, verifying all eleven unrelated Heat entry hashes.
4. First test hands, neutral and two consecutive steps. Only after that seam
   passes, validate four side/costume flows, applicable fever, song end/return and
   human audio review. Checkpoint experimental work honestly.

## Current verified seam

Loading regression recovered with separate pack/model containers and 19 entries.
Fresh P1/B vs Heat BAG1 P2/A enters actual gameplay; 3 asset and 49 harness tests
pass. Evidence is linked in the canonical Strike note. Earlier claims of song
completion, fixed sinking, 16-bone conversion failure and accepted motion policy
were incorrect. Announcer audio, Heat texture fidelity and Strike visuals remain
open. Do not promote exceptions to verified.
