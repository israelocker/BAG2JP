---
id: endings-view-current
title: "Ending View: fuente y evidencia delimitada"
tags: ["endings", "acceptance", "reference"]
summary: "Identifica implementación, seam de tests y evidencia previa; no mezcla revisiones antiguas del ejecutable con estado actual."
related: ["notes/project.md", "notes/character-import-testing.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Ending View

Fuente: `mods-src/bag2jp.feature.endings-view/bag2jp_endings_view.c`, manifest y
README del paquete. Tests: `tools/test/test_endings_view.py` y su seam C.
Menú y espaciado: `tools/test/test_hd_menu_assets.py`. Leer sus casos actuales
para saber qué verifican; los conteos antiguos 7/8/9 pertenecen a revisiones distintas.

El [ledger anterior](archive/endings-view-before-audit.md) preserva la secuencia
de diagnóstico/aceptación del menú y del vídeo negro Heat. No leer sus varios
«latest/deployed/not yet deployed» como estado simultáneo actual.
La copia de framework `patches/psxrecomp-disabled-display-hud-present.patch`
registra la intervención reproducible; no aplicar un parche sin comprobar base/pin.

Scope solicitado: ENDING VIEW entre DANCE VIEW y OPTIONS; selección de versión/
traje soportados, ending elegido y retorno, manteniendo modos normales. La
existencia del código no demuestra todas las combinaciones del roster aceptadas.
Audio subjetivo y cualquier caso no respaldado siguen pendientes.

Para retomar, comprobar hashes origen/build/exe y evidencia de la revisión a
probar. No seguir un PID o copia VM de octubre; no cerrar partidas ajenas.
