---
id: asset-toolkit-extracted-data
title: "Assets: inventario antes de nombres"
tags: ["assets", "archive", "reference"]
summary: "Disc/table/member hashes como identidad; nombres extraídos y resultados antiguos no son evidencia actual automática."
related: ["notes/character-alternate-entries.md", "notes/bag1-stage-song.md"]
created: "2026-10-26"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Assets

Inventario compartido actual: `tools/bag1import/inspect_character_entries.py`
y `iso_extract.py`. La tabla DF2_ del disco original define offsets/tamaños;
el contenedor DFS define los miembros. Ver [integración](character-alternate-entries.md)
para sus espacios de offset, región y validaciones.

Los nombres de carpetas no son IDs del juego. Especialmente choreography/fever
requiere tabla nativa; no elegir una animación por nombre de personaje de carpeta.
`fever_entries.py` es una referencia del disco JP, no una tabla universal BAG1/BAG2.
Registrar input hash, entrada, miembro y longitud antes de convertir.

La [investigación original](archive/assets-before-audit.md) conserva catálogo,
BPE, loader y repack byte-idéntico reportado en octubre. No se reejecutó ese
repack en la auditoría. Los assets pesados están fuera de Git y su presencia
debe comprobarse, no suponerse porque una nota los enumera.
