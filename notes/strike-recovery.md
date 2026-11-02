---
id: strike-import-recovery
title: "Strike: recuperación de mods y límites del candidato"
tags: ["strike", "bag1", "mods", "recovery"]
summary: "Mods y ejecutable experimental restaurados; Strike BAG2/Heat BAG1 llega a gameplay. Strike BAG1 sigue sin aceptación y requiere integración en el mecanismo alternativo compartido."
related: ["notes/character-pipeline.md", "notes/game-controls.md", "CHARACTER_IMPORT.md"]
created: "2026-11-01"
updated: "2026-11-01"
edited: "2026-11-01"
---

# Recuperación y evidencia

Se restauraron los ocho paquetes movidos a `disabled_mods`, sus opciones anteriores
y el paquete bundled `bag2jp.feature.bag1-content` desde el árbol de compilación.
Los paquetes installed y bundled del mismo ID se conservaron como entidades distintas.
Los mods de pruebas Heat y red-menu mantienen su estado anterior desactivado;
no se habilitaron indiscriminadamente experimentos que ya estaban desactivados.

El ejecutable experimental volvió al backup verificado SHA-256
`935f4a9bc23ca5ed64aed7b9cf09d2810fbca4d11f147519b9f38393baa94393`.
El parche de halfword en offset de archivo `0x00840F03` carecía de validación
como tabla de recursos y queda rechazado, conservado en el backup de recuperación.
El paquete candidato Strike se conservó fuera del catálogo de mods, sin borrar sus assets.

Evidencia: `_work/mods-recovery/20261102T013725Z/recovery.json` y
`_work/versus-runs/20261102T013757152569Z-restored-mods-strike-bag2-heat-bag1/`.
La prueba nueva verificó Strike **BAG2** P1 / Heat **BAG1** P2, traje A,
popup, selección de escenario Heat BAG2 e inicio de gameplay. La hoja de capturas
fue revisada por el agente principal. El harness comprobó restauración de tres
configuraciones y preservación de los 21 archivos de guardado originales.
No acredita canción completa, fever, retorno, funcionamiento individual de cada mod
ni importación de Strike BAG1.

## Corrección del diagnóstico anterior

- La ausencia del popup era coherente con haber retirado el paquete que lo proporciona.
  No demostraba que Strike no fuese seleccionable.
- La supervivencia del proceso no valida un parche ni la carga del modelo.
- Una diferencia de tamaño no demuestra por sí sola corrupción por bytes sobrantes.
- El contrato por igualdad de requests, el parche DBI por analogía con Heat y el
  slideshow del selector no acreditan semántica, adaptación de esqueleto ni referencia nativa.
- Los commits previos conservan experimentos; no son checkpoints de aceptación.

## Datos originales comprobados, sin despliegue

`stock-tables.json` registra hashes, tablas originales y 24 inventarios DFS obtenidos
mediante `iso_extract.Disc`, respetando sectores raw de 2352 bytes con 2048 bytes
de datos a partir de +24. ISO9660 sitúa `BUST2.BIN` en LBA 179,
`SLPM_862.19` en LBA 24 y `DUMMY.BIN` en LBA 224035.
El disco original conserva SHA-256
`fe8285f2ee5737680abe4ba20e53be9e029e0ab65ff2aa35c4695709bb0e5268`.

Las entradas 97/98 son contenedores DFS de tres miembros, no un modelo y una lista
de animaciones independientes. Sus offsets `0xF9A000`/`0xFE5000` son relativos
al archivo BUST2.BIN. Para `disc_user` hay que incorporar el inicio del archivo;
para acceso físico raw hay además que traducir sectores. Las entradas 133/134
tienen offsets `0x1A1C000`/`0x1A58800`, no los valores truncados anteriores.

Las tablas en RAM `0x80055180` (packs) y `0x80055258` (modelos), leídas desde el
PS-X EXE original, contienen 73/109 en índice 1 y 61/97 en índice 8.
No se equipara todavía el ID 1 observado en el selector con un índice de estas
tablas: falta trazar el índice que usa el cargador. Por tanto, las etiquetas
anteriores de entradas «Strike» permanecen sin verificar.

## Continuación obligatoria para convivencia

La infraestructura existente ya ofrece assets alternativos en DUMMY.BIN:
`make_alt_entries.py`, `bag2jp_bag1_alt_index.h` y `bag2jp_bag1_versions.c`.
El plugin selecciona por personaje/jugador y solo cambia entradas cuyo offset
coincide con stock o alternativo conocido. Reutilizarlo, no clonar el pipeline Heat.

Antes del próximo candidato:

1. Trazar identidad del selector → índice de tabla → entradas y miembros reales.
2. Verificar contrato semántico, texturas y necesidades reales del DBI Strike;
   no reutilizar el parche de cabeza Heat por analogía.
3. Preparar contenedores completos y un índice/payload conjunto o rangos alternativos
   no solapados con Heat. Comprobar límites, hashes esperados y espacio reservado.
4. Integrar versión/costume y opciones mediante el mecanismo compartido;
   actualizar identidad de contenido online si cambian assets/comportamiento.
5. Solo entonces desplegar overlays reversibles y probar ambos lados/trajes,
   versiones mixtas, canción completa, fever aplicable y retorno con los mods activos.

Los perfiles/caches y mensajes históricos que declaren etapas completas no sustituyen
estas verificaciones. Strike BAG1 permanece **no aceptado**.
