# Shared BAG1 -> BAG2JP character workflow

Owner standard (2026-10-31): one shared process, with data-only character profiles and narrowly justified exceptions. Avoid per-character forks of orchestration or conversion logic.

## Inputs and stages
1. Inventory: verify source discs/game catalogs, extract model/animation/event data, identify IDs and counts from executable tables, and validate the profile.
2. Contract: assign roles by meaning and musical duration. Preserve required effects/launches/voices, account for all source/target entries, and report ambiguity.
3. Sequence audit: validate original predecessor-dependent variants and adjacency/coverage in the adapted grid. Source cell continuity and native alternate dispatch are independent checks.
4. Experiment: regenerate only changed assets, update online content identity when behavior/timing changes, and deploy only to the experimental installation.
5. Acceptance: verify relevant poses/steps/attacks and a complete game flow (including applicable solo/duet fever and return). Review once, commit task-owned changes and refresh one verified snapshot.

Inventory and contract stages do not authorize claiming gameplay acceptance. A profile at verified stage requires hashed gameplay evidence and no pending exceptions.

## Shared facts vs character data
- tools/bag1import/contracts/bag1-usa-bag2jp.roles.json holds nominal base dispatch facts with exact input hashes. It is game/version-specific, not a Heat role map.
- tools/bag1import/profiles contains character data. IDs, source paths, capabilities and exceptions may vary; the command flow and rules do not.
- Exceptions require a character scope, rationale and status. Verified exceptions require unchanged hashed evidence. Never silently generalize a beanie/skeleton patch or a special attack handler to all characters.
- An ID/request is not a semantic role. Some labels/durations/order differ between games; unknown roles remain unresolved.
- Shared announcer names are a capability of any character present in both games. Imports without that capability retain the established generic announcement behavior.

## Animation contract rules
Group requests into normal dance, special by beat length, pose, intro, attack, defense, reaction, tired, fall/recovery, win/loss and fever. Prefer semantic identity, musical duration and necessary events before pose similarity.
A later graph optimizer must prioritize role/timing, native transition compatibility and original-motion coverage; report infeasibility rather than hide missing movements. Such an optimizer is not shipped yet.
For ambiguous comparisons, normalize skeleton, scale, root direction and beat phase before measuring start/end posture, feet and displacement. Local models can summarize bounded annotations; they do not certify equivalence.

## Profile initialization
Use the same command for every character, changing only data arguments. First unpack the model DFS with the established archive tools; compressed containers are not accepted.
```powershell
py -3.13 tools/bag1import/character_workflow.py init-profile --character <slug> --profile tools/bag1import/profiles/<slug>.json --source-archive <unpacked-model.dfs> --source-list _work/character_inventory/<slug>/001.bin --runtime <native-reference.exe>
```
The command preserves existing profiles and differing inventory, validates the animation member before writing, and leaves source/target IDs unknown for investigation. It never deploys game files.

## Reference cache commands
Use Python 3.13. From the canonical project:
```powershell
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile tools/bag1import/profiles/heat.json
py -3.13 tools/bag1import/character_workflow.py cache-check --profile tools/bag1import/profiles/heat.json --cache <cache.json>
py -3.13 tools/bag1import/character_workflow.py cache-record --profile tools/bag1import/profiles/heat.json --cache <cache.json> --evidence <verified-video.mp4> --evidence <timeline.json>
```
Cache-check exits 2 on a cache miss; other invalid inputs fail without generating runtime assets. A hit covers visual evidence only. Ordered motion prefixes exclude animation info/events, so a cue-only change can reuse video while still requiring audio tests.
Keys include the character/profile, catalog content, runtime executable and decoded motions. Evidence hashes are rechecked. Catalog input drift requires rebuilding/verifying the catalog.
All capture should use the native runtime, an isolated card/settings copy and a known target PID. The existing Heat reference is under D:/Dev/Scratch/bag1-native-reference and ho/work/bag1-reference; it is reference evidence, not a universal character profile.
Reuse unchanged references rather than navigating/re-recording all 66 choices. Read relevant functions and compact summaries; preserve raw logs. Do not reuse a failed pilot as evidence.

## Current implementation boundary
The generic helper validates profiles, checked catalog inputs and reference caches. Heat and Strike both pass real animation-inventory validation (84 entries each). Strike remains inventory only, with its BAG2 target ID unresolved; it has not been imported or validated in gameplay. The existing complete Heat auditor and conversion recipes remain legacy, specialized adapters; do not present them as a general importer for untested characters.
The new semantic/transition/coverage requirements are mandatory workflow rules. General assignment generation and automatic graph optimization still need implementation and cross-character validation before they can replace the legacy converter.
No new character is claimed imported by installing these skills.

## Resource routing
- Files, hashes, extraction and objective checks: local deterministic scripts through MCP.
- MIPS listing: installed Capstone; bulk decompilation: installed Ghidra headless with a separate read-only project when the GUI project is open.
- Native video/capture validation: existing FFmpeg/ffprobe and test harness; source-version cache prevents unnecessary recapture.
- Bounded, reviewable bulk annotation: existing local-vibes/local-llm; one RTX 3090 model at a time, no competition with game tests.
- Consult pinned framework source first. Context7 is configured for this OpenCode project and answered a public Capstone lookup; use it for external library documentation of the matching version, not as authority over a pinned local fork.
- Keep one focused code review per changed version. Reuse evidence for unchanged hook-listed files. Full logs remain on disk; do not repeatedly dump notes, catalogs or disassembly.

## Measurements
The prior complete Heat audit measured 0.144 s in one warm-filesystem run, including Python startup and JP comparison. Native reference capture measured 271.64 s. Snapshot creation measured 39.41 s. These are baselines, not promised savings or timings for other characters.


## Online catalog decisions (2026-10-31)
- Context7 (historical Codex check): connected and queried successfully for public Capstone documentation. No private project files sent. This does not establish an OpenCode connection. Upstream: https://github.com/upstash/context7 .
- Ghidra headless: reuse the installed tool for batch scripts, without adding another plugin. Official reference: https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md .
- Capstone: reuse installed MIPS disassembly support; https://www.capstone-engine.org/ .
- Hypothesis: optional future property tests for decoder bounds and graph invariants; not installed because the current stdlib regression tests cover this change. https://hypothesis.readthedocs.io/en/latest/ .
- Reviewed external skill binary-re (https://github.com/2389-research/binary-re): not installed; its ELF/ARM/x86 focus overlaps existing reverse-engineering skills and does not directly solve PS1 animation semantics.
- Do not add duplicate skill libraries or unrelated service integrations. Reconsider a tool when a measured bottleneck or missing capability justifies it.

## Shared policy/repack implementation (2026-10-31)
animation_policy.py provides data-defined role adaptations and native predecessor dispatch; alternate_payload.py provides bounded repacking. rebuild_animation_payload.py prepares candidates for any explicit model-entry list from an already converted animation list. Heat exercises these through its legacy adapter; a second character's conversion and gameplay are still unverified. This is not a general assignment or graph optimizer.
Policy classifications distinguish exact roles from deliberate adaptations. Preserve required target events and hold flags; retain original duplicate event ordering. Never classify an adaptation as an original action merely because it renders.

Native capture now supports tools/test/capture_dance_view.ps1 with --style PowerShell parameters: -GameId -ExpectedExe -Cases -Output -CurrentIndex -ItemCount and optional -WatchLog/-IndexAddress. Prefer observed indices to counted key presses; validate a pilot label before a batch. Use distinct pad bindings and avoid duplicate analog/digital directions. Wait for task-owned processes to exit before editing state. The runtime expects package selections before feature records in state.toml; restore the byte-exact baseline after tests. BAG2JP_TEST_DANCE_VIEW_CHAR is a bounded debug-only native test option, requiring trace and isolated cards; do not save temporary unlock flags.
