---
id: test-versus-navigation-digest
title: "Versus regression coverage digest"
tags: ["digest", "testing"]
summary: "46 regression cases exercise parsing, fail-closed routing, UI-state gates, interrupted preparation, review integrity and compact reporting."
related: ["tools/test/test_versus_navigation.py", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-01"
edited: "2026-11-01"
---

# Versus regression coverage

- Run: `py -3.13 -m unittest discover -s tools/test -p test_versus_navigation.py`.
- Real temporary files exercise exact-byte restore, immutable backups and isolated card paths. Refuse restore under a running process; rollback preparation after KeyboardInterrupt.
- Validate unknown names/versions/costumes, independent bindings, explicit shortest routes, stale or incomplete observations, native mode/overlay and actual costume flags.
- UI protocol fixtures specifically catch unsafe boot Start sequences and initialization-vs-active selector roots. External Windows/Pillow error seams are substituted only where needed; production parsers, file preparation and driver protocol execute.
- Catalog edit/image drift invalidates approval. Contact-sheet errors retain primary report. Measured helper calls are counted, not estimated.
- Host discovery covers these plus existing tests; actual game acceptance remains a separate requirement, recorded in the runbook and `_work/` evidence.
