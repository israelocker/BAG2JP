---
id: versus-navigation-digest
title: "Versus navigation validation digest"
tags: ["digest", "testing", "controls"]
summary: "Pure validation, limited roster graph, coherent watch parsing and reversible file preparation for versus tests."
related: ["tools/test/versus_navigation.py", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-01"
edited: "2026-11-01"
---

# Versus navigation core

- `tools/test/versus_navigation.py`: no game startup or input side effects on import.
- Lookup supports Heat=0, Strike=1, Comet=2; BAG1 only Heat. Unknown names/routes fail closed.
- Binding lookup rejects missing actions and same/other-pad collisions. Temporary keys affect only necessary P1/P2 actions.
- Graph reuse requires reviewed runtime-bound data, matching edge/evidence digest and unchanged images.
- Sixteen watches include both player structures, native identities/costumes, overlay guards and advancing native clock. Parse only newline-terminated complete observations; pair watch/heartbeat age and frame coherence.
- Native mode 2 required. Selector roots 12/13 plus exact JP overlay signatures; combat root decimal 19 plus native phases. Native mirror costume changes cannot silently satisfy a request.
- `Backup` preserves exact config bytes. `IsolatedFiles` copies cards, redirects temporary settings, rolls back even on preparation interruption and refuses restoration while the task process lives. Original saves are hash-checked, not overwritten.
- Verification and CLI: `notes/game-controls.md`; detailed error/pilot evidence stays under `_work/versus-navigation/`.
