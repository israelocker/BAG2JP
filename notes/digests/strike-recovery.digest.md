---
id: strike-recovery-digest
title: "Strike recovery and current acceptance digest"
tags: ["digest", "strike", "recovery"]
summary: "Strike integrado y dos partidas completas verificadas; fidelidad y matriz restante aún pendientes."
related: ["notes/strike-recovery.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: digest
source: "notes/strike-recovery.md"
source_sha256: "5f8c88ff2ad2425abfdaf0ec7ba612c15b9cf5d2f3914ff62d7d1565009e40af"
---

# Strike: estado vigente

- ID JP=1. Packs 73/74/145/146; modelos 109/110/181/182. Datos Strike, no plantilla.
- Enlaces de 44 huesos BAG1/BAG2 idénticos; parche DBI por analogía Heat rechazado.
- Modelo/lista convertidos y TIMs retargeteados integrados mediante payload alternativo.
- Bloqueo VS corregido: el script ad-hoc escribió offsets iguales por miembro.
  Sustituido por `rebuild_dfs_members.py`, sin truncar packs y conservando DBI/SEDT.
- Heat se recuperó de payload original verificado; conservar sus 11 filas al añadir
  ocho Strike. Payload final SHA `f267f1bba4bdf8a6e71b7bc583dcf60b2f75bfb49587ee136f4e4c3dde85deec`.
- Build necesita staging manual de fuentes/recursos. Exe actual SHA
  `d22b3e4e8d80bb0b1e3c7bf3170c97c45cbf2b2ff7c162fc0434d328f14f3ab4`.
- P1/A `20261102T102131125467Z-strike-bag1-full-a` y P2/B
  `20261102T102625676713Z-strike-bag1-full-p2-b` completan canción Heat BAG2 y retorno.
  Runs bajo `_work/versus-runs/`; ajustes y 21 saves restaurados.
- Posible artefacto en pecho P2/B: comparar referencia nativa antes de aceptar.
- Falta P1/B, P2/A, fidelidad animaciones y fever aplicable; logs fever1/2 no
  certifican contenido BAG1 propio. No aceptación final ni canción/escenario Strike.
- Validación del harness corregida: permitir Strike BAG1; rechazo no implementado
  se prueba con Comet. 49 pruebas navegación + 8 DFS, no cobertura universal.
