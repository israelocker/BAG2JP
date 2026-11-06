---
id: endings-view-current
title: "Ending View: fuente y evidencia delimitada"
tags: ["endings", "acceptance", "reference"]
summary: "Identifica implementación, seam de tests y evidencia previa; no mezcla revisiones antiguas del ejecutable con estado actual."
related: ["notes/project.md", "notes/character-import-testing.md"]
created: "2026-11-01"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: reference
---

# Ending View

## Receta BAG1 y límites de reutilización

Hay dos piezas: `bag2jp_endings_view.c` incorpora el menú/routing;
`mods-src/bag2jp.feature.bag1-content/bag2jp_bag1_endings.c` sustituye vídeo y
modelo en créditos para versiones BAG1. Requiere **plugin registrado** y recurso
`ending_movies` en el manifest activo. Existencia de fuentes o copia en
`disabled_mods` no activa nada: así se perdió temporalmente Heat/Strike.

1. Verificar disco/región/extents y extraer STR **raw2352**, no solo los2048bytes
   de `iso_extract.py`. Método probado: `_work/endings/scripts/raw_sectors.py`;
   antes de reutilizarlo revisar inputs/rutas/guardas. HEAT_END JP se contrastó
   byte a byte con la referencia previa. Strike: LBA146533,3243sectores.
2. Convertir el raw a MPEG en un output nuevo. Receta histórica Strike:

   ```text
   ffmpeg -i STRI_END.STR -c:v mpeg1video -r 30 -g 15 -q:v 3 -c:a mp2 -b:a 192k -ar 44100 -ac 2 -f mpeg STRI_END.mpg
   ```

   Resultado registrado:2822144bytes,21.55s. Hashes/origen en
   [Strike](strike-recovery.md); no sustituir comprobación por nombre/tamaño.
   Los MPG están ignorados por Git: conservar fuente/hash y backup aparte.
3. Perfil de ending: Heat id0 modelos95/167, Strike id1 modelos109/181,
   grupos con paso14. No extrapolar IDs a otro personaje. Revisar guardas de
   módulo/palabras originales y restauración; generar callbacks desde la fuente
   de configuración, nunca parchear solo C generado.
4. Staging coherente de C/header, vídeo, plugin y recurso en canonical/preloaded/
   bundled/experimental según [integración](character-alternate-entries.md).
   Mantener backup/hash y rollback del conjunto. No tocar estable.
5. Prueba separada de vídeo correcto, modelo A/B durante baile/créditos,
   selección BAG2 intacta, salida natural y retorno. `movie`, `dance`, `exit`
   son señales del log, no revisión visual/auditiva automática. Aislar/restaurar
   settings y tarjetas; no interrumpir sesiones del propietario.

## Evidencia delimitada

- Ending View Strike BAG1 A/B y BAG2 stock, Heat BAG1 A observados históricamente;
  runs 20261105T194111/203530/203855 y regresiones 20261106T014236/014508/
  014745/015016 constan en las notas Strike/escenario. No se repitieron aquí.
- Salida natural: HeatB1/A `20261105T204502725335Z`, StrikeB1/A
  `20261105T204954184810Z`, stock `20261105T205447147749Z`, retorno al título;
  21tarjetas/settings restaurados. No prueba por sí sola salida natural B.
- `test_bag1_endings.py` compila lógica con RAM/player de vídeo **simulados**;
  cubre modo5 y modo1, versión stock y reset. Código admite0/1/5, pero ese test
  no recorre campaña ni prueba modo0 explícitamente. Los runs de Ending View
  tampoco son una campaña completada. Campaña real y revisión humana pendientes.
- `test_endings_view.py` no aporta casos al `unittest discover`: ejecutar aparte
  con WSL Python/gcc, comando desde Windows:
  `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py`.
  Sus nueve casos actuales son menú/guards/confirm/cancel/ending y lettering;
  no equivalen a nueve recorridos del roster en el juego.

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
