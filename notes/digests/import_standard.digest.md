---
id: import-standard-digest
title: "Import standard digest"
tags: ["digest", "bag1", "standard"]
summary: "Inicio compacto y enlaces a las recetas compartidas; los adaptadores Heat no son el importador de otros personajes."
related: ["IMPORT_STANDARD.md", "CHARACTER_IMPORT.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "IMPORT_STANDARD.md"
source_sha256: "a308e9cc8aefffef707f25f87d18aa7034e63dd158a8660c2064ccf897593e5c"
---

# Estándar: resumen

1. AGENTS → NOTES → estado compacto; revisar perfil/inventario y gaps.
2. IDs, esqueletos, miembros y roles se verifican por personaje y versión.
3. Referencias con hashes; contrato semántico, beats, eventos y predecesores.
4. Candidato no implica despliegue ni aceptación.
5. Reconstruir DFS con `rebuild_dfs_members.py`; payload completo con
   `make_alt_entries_exact.py`. Preservar bytes BAG1 previos, no stock.
6. Revisar límites/tabla/capacidad DUMMY en bytes (guard actual defectuoso).
7. Sincronizar solo fuentes y recursos propios al build; WSL con dos jobs.
8. Experimental únicamente, mods conservados, cuatro casos lado/traje,
   canción/retorno con `-Finish`, fever, eventos del escenario por puntaje
   y demás capacidades aplicables.
9. Restauración, revisión de evidencia, notas, checkpoint local y snapshot.

Leer `character-alternate-entries.md` para integración y `character-import-testing.md`
para pruebas. Los scripts Heat son ejemplos/adaptadores, no defaults universales.
