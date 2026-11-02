---
id: versus-navigation-digest
title: "Versus navigation validation digest"
tags: ["digest", "testing", "controls"]
summary: "Pure validation, limited roster graph, coherent watch parsing and reversible file preparation for versus tests."
related: ["tools/test/versus_navigation.py", "notes/game-controls.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "tools/test/versus_navigation.py"
source_sha256: "754f6acc77cd0a1a4b44b96d59041b6545cb26921eabc135eb6552acaa2ec90c"
---

# Versus navigation core

- `tools/test/versus_navigation.py`: no game startup or input side effects on import.
- Lookup supports Heat=0, Strike=1, Comet=2; BAG1 Heat and Strike, not Comet. Unknown names/routes fail closed. Support in the driver is not final character acceptance.
- Binding lookup rejects missing actions and same/other-pad collisions. Temporary keys affect only necessary P1/P2 actions.
- Graph reuse requires reviewed runtime-bound data, matching edge/evidence digest and unchanged images.
- Sixteen watches include both player structures, native identities/costumes, overlay guards and advancing native clock. Parse only newline-terminated complete observations; pair watch/heartbeat age and frame coherence.
- Native mode 2 required. Selector roots 12/13 plus exact JP overlay signatures; combat root decimal 19 plus native phases. Native mirror costume changes cannot silently satisfy a request.
- `Backup` preserves exact config bytes. `IsolatedFiles` copies cards, redirects temporary settings, rolls back even on preparation interruption and refuses restoration while the task process lives. Original saves are hash-checked, not overwritten.
- Verification and CLI: `notes/game-controls.md`; detailed error/pilot evidence stays under `_work/versus-navigation/`.
