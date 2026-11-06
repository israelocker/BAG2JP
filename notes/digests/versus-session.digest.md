---
id: versus-session-digest
title: "Versus session driver digest"
tags: ["digest", "testing", "workflow"]
summary: "Windows process-owning driver with observed gates, independent inputs, evidence and full-return option; reporting still depends on available I/O."
related: ["tools/test/versus_session.py", "tools/test/bag2_versus.ps1", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "tools/test/versus_session.py"
source_sha256: "80edd7452a07f70a16556c1b1417d2ecd4628a0385337e926555e31488712719"
---

# Versus Windows session

- Entry point: `tools/test/bag2_versus.ps1`, delegates to Python 3.13 `versus_session.py`. Actions: read-only inspect, calibration probe, named run.
- New runs refuse existing BAG2JP sessions and require temporary-controls opt-in. Own one experimental PID, validate path/start time, use existing postkey/winshot helpers, close gracefully and restore originals.
- Boot: wait for opening root5; one Start only; await menu7, target index1, confirm Circle. Never send keys on transitional root6.
- Selector: fresh root13/guards/mode2, explicit graph routes, independently confirm identity/version/costume from current-session popup logs and NORMAL commands.
- Stage: Python accepts Heat BAG2/BAG1 and Strike BAG2/BAG1 (rows 0/1/4/5); the PowerShell wrapper still validates Heat only. Then native combat gate and exact character/costume flags. Strike flow evidence is in its ledger, not a universal roster acceptance.
- `--finish`: observes battle exit and guarded selector return, with periodic captures and bounded timeout. It does not validate every motion or judge texture/audio fidelity.
- Artifacts: unique `_work/versus-runs/` directory, immutable baseline, isolated cards, input history, logs, raw screenshots and six-panel contact sheet. Machine validation remains pending visual review.
- Save result before secondary image work; image failure cannot erase restoration status. Keep failed-run artifacts. Do not restart automatically.
- Baseline/helper counts are operational measurements, not cloud token usage. See runbook for commands, tested roster limits and evidence.
