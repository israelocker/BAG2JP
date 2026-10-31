---
name: bag-animation-matching
description: Match BAG1 and BAG2 animation roles, timing and predecessor transitions across characters; audit coverage and unresolved adaptations before generating assets.
---
Use D:/Dev/Recomp/BAG2JP/notes/character-pipeline.md and tools/bag1import/contracts/bag1-usa-bag2jp.roles.json for verified base dispatch tables.
- Match semantic role first. Numerical requests are game-specific; equal numbers do not prove equal actions.
- Separate normal steps, special durations, held poses, attacks, successful defenses, hit reactions, tired states, knockdown/recovery, wins, losses and fever.
- Keep duration in musical beats and required events as constraints; frame counts alone do not identify a role. Motion hash equality proves identity, not appropriateness.
- For each proposed edge, evaluate the original native predecessor/alternate dispatch. Compare adjacent source cells separately: a correct individual clip can still create a discontinuity.
- Prefer original transitions and coverage under the timing/role constraints. A proposed optimizer must report infeasible requirements rather than silently relax them. No general optimizer is currently shipped.
- Report all source and target entries, motion-only and complete-entry duplicates, unused original motions, missing counterparts, stock-empty entries and deliberate repetitions.
- If a target role does not exist in the source game, mark it unresolved until a narrowly documented adaptation is chosen. Do not map an unsuccessful hit reaction to a successful defense as an unreported fallback.
- Pose similarity is a tie-breaker after semantic constraints. Normalize skeleton correspondence, scale, root orientation and beat timing before comparing start/end posture, foot support or displacement.
- Base catalogs describe nominal tables. Check character-dependent branches and skeleton bindings in actual code before applying them; exceptions belong to a character profile with evidence.
- Review shared narrator names as a capability of characters present in both games, not as a universal Heat rule.
