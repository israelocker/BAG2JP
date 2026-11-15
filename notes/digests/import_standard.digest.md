---
id: import-standard-digest
title: "Import standard digest"
tags: ["digest", "bag1", "standard"]
summary: "Inicio compacto y enlaces a las recetas compartidas; los adaptadores Heat no son el importador de otros personajes."
related: ["IMPORT_STANDARD.md", "CHARACTER_IMPORT.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: digest
source: "IMPORT_STANDARD.md"
source_sha256: "b8032c6e8c0cc12c5dffa4edabe8c2effff9a8dd54b9fb6d6966c6faff405806"
---

# Estándar: resumen

1. AGENTS → NOTES → estado compacto; revisar perfil/inventario y gaps.
2. IDs, esqueletos, miembros y roles se verifican por personaje y versión.
3. Referencias con hashes; contrato semántico, beats, eventos y predecesores.
4. Candidato no implica despliegue ni aceptación.
5. Reconstruir DFS con `rebuild_dfs_members.py`; payload completo con
   `make_alt_entries_exact.py`. Preservar bytes BAG1 previos, no stock.
6. Revisar límites/tabla/capacidad DUMMY en bytes; guard por revisión/copia, no
   evidencia de automatización completa. Contrato regional de nueve campos y
   `regions` en integración; JP ausente no equivale a idéntico.
7. Sincronizar solo fuentes y recursos propios al build; WSL con dos jobs.
8. Experimental únicamente, mods conservados, cuatro casos lado/traje,
   canción/retorno con `-Finish`, fever, eventos del escenario por puntaje
   y demás capacidades aplicables.
9. Restauración, revisión de evidencia, notas y checkpoint local; snapshot solo al
   cierre de hito verificado según AGENTS.

CAUGHT se exige para todo importado BAG1 y nativo BAG2, lados/variantes/compañeros;
es requisito, no cobertura actual. Retrato/nombre por versión y lado y nombre HUD
son gates distintos. Escenarios: ficha por fase de cámara, texturas/render, eventos
por puntaje/props, música/SFX y modos en `notes/bag1-stage-song.md`; casos históricos
no autorizan copiar cámaras/escala/umbrales Heat/Gas-O a otros mapas.

Leer `character-alternate-entries.md` para integración y `character-import-testing.md`
para pruebas. Los scripts Heat son ejemplos/adaptadores, no defaults universales.
