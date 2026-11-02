---
id: test-versus-navigation-digest
title: "Versus regression coverage digest"
tags: ["digest", "testing"]
summary: "Host regressions cover routing, gates, restoration, calibration review and guarded full-return/timeout; no visual certification."
related: ["tools/test/test_versus_navigation.py", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "tools/test/test_versus_navigation.py"
source_sha256: "c42b3aca297f34119ac186813968e31c80f02e6ea8ce342fc38c9672369c2922"
---

# Versus regression coverage

- Run: `py -3.13 -m unittest discover -s tools/test -p test_versus_navigation.py`.
- Real temporary files exercise exact-byte restore, immutable backups and isolated card paths. Refuse restore under a running process; rollback preparation after KeyboardInterrupt.
- Validate unknown names/versions/costumes, independent bindings, explicit shortest routes, stale or incomplete observations, native mode/overlay and actual costume flags.
- UI protocol fixtures specifically catch unsafe boot Start sequences and initialization-vs-active selector roots. External Windows/Pillow error seams are substituted only where needed; production parsers, file preparation and driver protocol execute.
- Catalog edit/image drift invalidates approval. Contact-sheet errors retain primary report. Measured helper calls are counted, not estimated.
- Host discovery covers these plus existing tests; actual game acceptance remains a separate requirement, recorded in the runbook and `_work/` evidence.
