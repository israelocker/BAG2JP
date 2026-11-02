---
id: bag1-stage-song-heat
title: "Escenario/canción: alcance del port Heat"
tags: ["bag1", "heat", "stage", "song"]
summary: "Adaptadores existentes y barreras para reutilizar investigación Heat; tablas/direcciones históricas no se generalizan."
related: ["notes/bag1-character.md", "notes/character-pipeline.md", "notes/character-import-testing.md"]
created: "2026-10-30"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Escenario y canción se verifican por separado del personaje

Fuentes existentes:
- `tools/bag1import/port_bag1_stage.py`: port especializado Heat, incluyendo
  `bag1_chart`; no relocador genérico validado con todos los escenarios.
- `mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_stage.c`: shim/XA y duración
  configurada Heat. Sus constantes no se copian para otro escenario.
- `tools/bag1import/build_heat_stage_test.sh`, `song_ending.py`: adaptadores,
  no comandos de build por defecto del workflow Windows actual.

El [registro original](archive/bag1-stage-song-before-audit.md) conserva tablas,
offsets, causas y pruebas fechadas de chart, escala, callbacks y audio. Sirve
para investigar; confirmar región/palabras originales y source hashes antes de un parche.
No se repitieron estos tests en esta auditoría. La afirmación histórica «2P autoplay
verificado» no acredita por sí sola voces, canción nueva, ending ni online.

Requisitos de reutilización: inventario de callbacks/datos/chart, referencias
sin resolver explícitas, comprobación de duración y audio, efectos/cámara y
final+retorno con mods activos. No deducir canción de memoria ni del nombre
de la carpeta extraída; comparar evidencia del audio y tablas.

Las partidas Strike actuales usan **Heat BAG2** como escenario/canción. No
constituyen importación del escenario o canción Strike BAG1.
