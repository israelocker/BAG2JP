---
name: bag-character-pipeline
description: Import or fix BAG1 characters in BAG2JP using a shared profile-driven workflow, validated evidence and explicit character exceptions.
---
Read D:/Dev/Recomp/BAG2JP/AGENTS.md and NOTES.md, then notes/character-pipeline.md. Use the same workflow for every character.
- Keep game-format logic, role catalogs, conversion, audit and test orchestration common. Character profiles contain IDs, paths, capabilities and evidence; they do not contain executable code.
- Do not clone a Heat script into a new per-character pipeline. Keep existing Heat scripts as legacy adapters until a shared replacement is validated.
- Record an exception only for demonstrated character-specific behavior: narrow scope, reason, status and immutable input/evidence hashes. A pending exception permits investigation, not publication or a claim of completion.
- Start with the common game catalogs and a character inventory; verify actual counts and skeleton bindings. Never assume Heat's counts, IDs, fever folders or model layout for another character.
- Use bag-animation-matching for assignment/transition decisions and bag-reference-cache before scheduling visual capture.
- Prefer deterministic local scripts. Delegate only bounded, reviewable bulk work to an available local model; one GPU model at a time, outside game tests. Keep final reasoning and acceptance with the primary agent.
- Read only relevant functions/diffs; put full logs on disk and return compact summaries. Stop and diagnose after a repeated failure with the same signature rather than cycling shell variations.
- Verify changed behavior in the experimental installation, then perform one focused review, local commit and verified snapshot. Preserve personal cards, existing changes and the stable installation.
- Infrastructure status matters: character_workflow.py provides generic profile validation/cache; audit_animation_roles.py and current conversion scripts still contain Heat adapters. A general automatic matching/optimization solver is not implemented merely because these skills are installed.
