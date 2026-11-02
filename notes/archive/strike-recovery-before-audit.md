---
id: strike-import-recovery
title: "Strike: recuperación de mods y límites del candidato"
tags: ["strike", "bag1", "mods", "recovery"]
summary: "Strike BAG1 integrado: offsets DFS corregidos; P1/A y P2/B completan canción y retornan al selector con mods. Aceptación visual, cobertura restante y fever propio pendientes."
related: ["notes/character-pipeline.md", "notes/game-controls.md", "CHARACTER_IMPORT.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
---

# Recuperación y evidencia

Recetas reutilizables extraídas de esta investigación:
`notes/character-alternate-entries.md` y `notes/character-import-testing.md`.
Separan la infraestructura compartida de datos Strike y experimentos rechazados.
Para estado vigente leer la sección final fechada 2026-11-02; las anteriores
conservan el histórico, no son instrucciones de reconstrucción actuales.

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

Las tablas en RAM `0x80055180` (packs) y `0x80055258` (modelos) se verificaron
contra el PS-X EXE original. El cargador en `0x8003439C` y `0x8003464C` toma el
byte de personaje de `0x80089250`, usa los cinco bits bajos directamente como
ID, y calcula `table + (byte >> 5) * 72 + (id * 2)`. Los cuatro bloques de
36 halfwords son A-P1, A-P2, B-P1 y B-P2. Por tanto, el ID 1 observado para
Strike resuelve sin permutación a packs 73/74/145/146 y modelos
109/110/181/182. El cargador pasa el halfword resultante a `FUN_8001F874`.

`tools/bag1import/inspect_character_entries.py` automatiza esta lectura sin
modificar el disco y valida límites DF2/DFS. El inventario reproducible está en
`_work/character_inventory/strike/bag2jp-native-entries.json`. Los packs A-P1
y A-P2 contienen 6 y 5 miembros respectivamente; los cuatro modelos contienen
dos miembros. En modelo A, el miembro 0 mide 63.976 bytes y el miembro 1
272.300 bytes; modelo B usa 56.884 y 272.300 bytes. Esto invalida las antiguas
etiquetas 61/62/97/98 como entradas Strike.

También se extrajeron del disco BAG1 USA los ocho contenedores fuente reales:
packs `PLAYER1E/P_STRIA1|B1` y `PLAYER3E/P_STRIA3|B3`, y modelos
`PLAYER2/P_STRIA2|B2` y `PLAYER4/P_STRIA4|B4`. Su inventario está en
`_work/character_inventory/strike/bag1-source-inventory.json`. Los modelos P1
de ambos trajes son idénticos entre sí (59.948 bytes); los P2 también
(51.828 bytes). Comparten una lista de 84 animaciones de 288.048 bytes.

Las texturas BAG1 no están comprimidas ni usan una firma ASCII: cinco miembros
por pack comienzan con el magic little-endian `0x00000010` de TIM. Las páginas
corporales 004/005 ya coinciden en tamaño de imagen y coordenadas VRAM con las
páginas corporales BAG2; varían las filas CLUT. Las otras tres páginas BAG1 son
gráficos auxiliares. El candidato deberá retargetear 004/005 a los slots
corporales stock y conservar el gráfico stock de nombre/HUD hasta demostrar
otra necesidad. Esto resuelve la identificación del formato, no la aceptación
visual de ambos trajes.

Los modelos BAG1 y BAG2 Strike tienen **44 huesos** y tablas de enlaces
idénticas para P1 y P2. Ambos modelos convertidos recorren exactamente hasta su
final; P1 queda en 61.244 bytes y P2 en 53.076 bytes. El parche DBI experimental
`0x0D -> 0x0C`, copiado por analogía con Heat, queda rechazado: no hay evidencia
de que Strike necesite cambiar el hueso de cabeza. Se mantendrá el DBI BAG2
stock salvo que una prueba posterior demuestre una adaptación más estrecha.
La comparación reproducible está en
`_work/character_inventory/strike/structure-comparison.json`.

## Continuación obligatoria para convivencia

La infraestructura existente ya ofrece assets alternativos en DUMMY.BIN:
`make_alt_entries.py`, `bag2jp_bag1_alt_index.h` y `bag2jp_bag1_versions.c`.
El plugin selecciona por personaje/jugador y solo cambia entradas cuyo offset
coincide con stock o alternativo conocido. Reutilizarlo, no clonar el pipeline Heat.

Antes del próximo candidato:

1. Verificar el contrato semántico y transiciones de animación; no tratar el
   slideshow del selector como referencia nativa de movimientos.
2. Retargetear las dos páginas corporales por traje/lado y auditar visualmente
   el resultado; mantener el DBI stock en el primer candidato.
3. Preparar contenedores completos y un índice/payload conjunto o rangos alternativos
   no solapados con Heat. Comprobar límites, hashes esperados y espacio reservado.
4. Integrar versión/costume y opciones mediante el mecanismo compartido;
   actualizar identidad de contenido online si cambian assets/comportamiento.
5. Solo entonces desplegar overlays reversibles y probar ambos lados/trajes,
   versiones mixtas, canción completa, fever aplicable y retorno con los mods activos.

Los perfiles/caches y mensajes históricos que declaren etapas completas no sustituyen
estas verificaciones. Strike BAG1 permanece **no aceptado**.

## Progreso actual (2026-11-02)

Perfil `strike.json`: stage=`candidate`, 1 excepción pendiente (`alternate-entry-integration`).

Completado:
- target_character_id = 1 resuelto empíricamente (selector P1)
- Entradas nativas verificadas: packs 73/74/145/146, modelos 109/110/181/182 (vía ISO9660 + tablas RAM)
- Modelo convertido: P1 (61.244 bytes), P2 (53.076 bytes), ambos parsean hasta el final
- Animaciones: política semántica con 79 roles (48 equivalent, 31 adaptación), targets únicos 0-100, validada con animation_policy.load_policy
- Texturas: 8 TIMs retargeteadas con tim_retarget.py (cuerpo 004/005 por pack/lado), guardadas en _work/character_import/strike/retargeted_tims/
- Esqueleto: 44 huesos idénticos BAG1/BAG2, tablas de enlaces iguales. Parche DBI de Heat rechazado.
- Mods restaurados: 8 paquetes + bundled bag1-content, ejecutable original, state.toml baseline
- Prueba en juego: Strike BAG2 vs Heat BAG1 llega a gameplay (popup, selección, inicio)
- Suite host: 99 pruebas aprobadas, incluidas seguridad de conversión de animación y inspección de entradas de tabla

Pendiente (alternate-entry-integration):
- Reconstruir 8 contenedores DFS con miembros convertidos (modelos convertidos + texturas retargeteadas + DBI/SEDT stock)
- Integrar con make_alt_entries.py + bag2jp_bag1_versions.c (mecanismo DUMMY.BIN)
- Agregar overlay a manifest de bag1-content
- Probar en juego: ambos lados, ambos trajes, canción completa, retorno

Bloqueador: la integración de entradas alternativas requiere reconstruir contenedores DFS
completos con miembros convertidos y crear overlays sector-alineados para make_alt_entries.py.
Esta es ingeniería inversa de disco que requiere tiempo dedicado.

El perfil `strike.json` pasó de `candidate/complete` a `contract/pending`, luego a `candidate`
con excepciones explícitas. La política de animación anterior está marcada
`rejected_request_equality_only`; `anim_remap_strike.py` falla cerrado y no escribe
salida mientras su estado no sea `accepted_local` o `verified`. Esta barrera tiene
regresión automatizada. Suite host tras el cambio: 99 pruebas aprobadas.

## 2026-11-02: integración y partidas completas (no aceptación final)

Esta sección reemplaza los bloqueadores históricos de integración anteriores.
El generador ad-hoc mantenía `current_offset` constante al escribir la tabla DFS:
todos los miembros apuntaban al comienzo del primero (56/48/24). El tamaño total
parecía correcto, pero los miembros de animación y textura eran inaccesibles.
`tools/bag1import/rebuild_dfs_members.py` usa la longitud efectiva al añadir cada
miembro, valida límites/solapes y comprueba lectura posterior. Hay ocho pruebas
unitarias. Se conservan DBI/SEDT stock; no se aplica el experimento DBI de Heat.

`make_alt_entries_exact.py` empaqueta los bytes completos y registra `alt_size`,
sin truncar entradas mayores que stock. El payload mantiene las once entradas
Heat originales y añade ocho Strike; 3.889.152 bytes, SHA-256
`f267f1bba4bdf8a6e71b7bc583dcf60b2f75bfb49587ee136f4e4c3dde85deec`.
Offset absoluto `disc_user`: 458823680. SHA-256 del ejecutable experimental:
`d22b3e4e8d80bb0b1e3c7bf3170c97c45cbf2b2ff7c162fc0434d328f14f3ab4`.

Se corrigió una regresión posterior del harness: una prueba obsoleta rechazaba
Strike BAG1 y se había cambiado erróneamente la implementación para satisfacerla.
Ahora se prueba explícitamente que Strike BAG1 está permitido y que Comet BAG1
sigue rechazado. Suite de navegación: 49 pruebas aprobadas, incluyendo espera
de retorno con guards y timeout sin falso éxito.

Evidencia fresca en `_work/versus-runs/`:

- `20261102T102131125467Z-strike-bag1-full-a`: Strike BAG1 P1/A vs Heat BAG2
  P2/A; canción y retorno al selector, 161,2 s desde gameplay al retorno.
- `20261102T102625676713Z-strike-bag1-full-p2-b`: Heat BAG2 P1/A vs Strike BAG1
  P2/B; canción y retorno, 162,2 s. Posible anomalía de textura en el pecho del
  traje B visible en `gameplay.png`; pendiente comparar con referencia BAG1.

Ambos resultados son `complete_awaiting_visual_review`, no aceptación final.
Restauración verificada de keybinds/settings/state y los 21 saves originales.
Primera captura de retorno revisada visualmente. No se han probado todavía
P1/B ni P2/A con este runtime. Los logs muestran fases fever1/fever2, pero esto
no acredita fidelidad de fever propio BAG1 ni sincronización de duetos.
La canción es Heat BAG2; no acredita importación de canción/escenario Strike.

Prueba repetible: `tools/test/bag2_versus.ps1 -Action run -Tag <tag>
-P1Character Strike -P1Version BAG1 -P2Character Heat -P2Version BAG2
-TemporaryControls -Finish`. El flag `-Finish` observa salida del módulo de
combate y exige módulo selector con guards válidos; no salta fases mediante RAM.
Pendiente: revisar texturas/animaciones con referencia nativa, completar las otras
dos combinaciones lado/traje y verificar fever aplicable antes del checkpoint final.
