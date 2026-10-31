---
name: bag-reference-cache
description: Reuse verified native game animation references by motion, profile, catalog and runtime hashes; capture only changed or ambiguous actions.
---
Use D:/Dev/Recomp/BAG2JP/tools/bag1import/character_workflow.py and notes/character-pipeline.md.
- Use native PSXRecomp for this project; do not use DuckStation. Use the established local test harness through MCP for navigation/capture. Visual control is a fallback for necessary observations, not a substitute for available scripts.
- Validate a character profile before recording/checking a cache. Key it by character/profile, verified game catalog, reference runtime and ordered motion prefixes.
- Capture once for a new character/runtime/motion set. Preserve the isolated test card, verified navigation and clip timeline. For known unchanged movements reuse existing evidence.
- Re-run cheap file audits for each changed package. Cache visual evidence, not correctness checks of a newly generated package.
- A voice/event-only change may preserve the visual cache; it still requires the appropriate audio/event checks.
- cache-record requires explicit evidence files; cache-check verifies their hashes. Missing, changed or corrupt evidence cannot be called a cache hit.
- A valid cache/profile is not proof of a successful port. Gameplay acceptance remains required for modified code/content.
