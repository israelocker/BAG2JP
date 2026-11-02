---
id: versus-session-digest
title: "Versus session driver digest"
tags: ["digest", "testing", "workflow"]
summary: "Windows process-owning driver with observed gates, independent inputs, evidence and full-return option; reporting still depends on available I/O."
related: ["tools/test/versus_session.py", "tools/test/bag2_versus.ps1", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "tools/test/versus_session.py"
source_sha256: "760e3bd07f852b75bfd17c94840e7c76437852ab83cd58f6fb2f4506fd128c0e"
---

# Versus Windows session

- Entry point: `tools/test/bag2_versus.ps1`, delegates to Python 3.13 `versus_session.py`. Actions: read-only inspect, calibration probe, named run.
- New runs refuse existing BAG2JP sessions and require temporary-controls opt-in. Own one experimental PID, validate path/start time, use existing postkey/winshot helpers, close gracefully and restore originals.
- Boot: wait for opening root5; one Start only; await menu7, target index1, confirm Circle. Never send keys on transitional root6.
- Selector: fresh root13/guards/mode2, explicit graph routes, independently confirm identity/version/costume from current-session popup logs and NORMAL commands.
- Stage: explicit Heat BAG2/BAG1 row, then native combat gate and exact character/costume flags. Current Strike flow evidence is in its ledger, not a universal roster acceptance.
- `--finish`: observes battle exit and guarded selector return, with periodic captures and bounded timeout. It does not validate every motion or judge texture/audio fidelity.
- Artifacts: unique `_work/versus-runs/` directory, immutable baseline, isolated cards, input history, logs, raw screenshots and six-panel contact sheet. Machine validation remains pending visual review.
- Save result before secondary image work; image failure cannot erase restoration status. Keep failed-run artifacts. Do not restart automatically.
- Baseline/helper counts are operational measurements, not cloud token usage. See runbook for commands, tested roster limits and evidence.
