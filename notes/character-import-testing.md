---
id: character-import-testing
title: "Pruebas y diagnóstico reutilizables de importación de personajes"
tags: ["bag1", "character", "testing", "acceptance", "debugging"]
summary: "Gates del harness, matriz lado/traje/CAUGHT y grabación WGC/audio por proceso; lecciones Strike/Gas-O sin aceptación automática."
related: ["notes/character-alternate-entries.md", "notes/character-pipeline.md", "notes/game-controls.md", "notes/strike-recovery.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Pruebas de un candidato, no aceptación por apariencia

Separar cuatro afirmaciones: conversión estructural, integración, flujo jugable
y fidelidad/aceptación. Una captura VS, un cache hit, un build verde o un retorno
al selector no demuestra por sí solo las demás.

## 1. Gates antes de arrancar

- Usar solo la instalación experimental, nunca la estable.
- Respetar sesiones del propietario: el harness rechaza otro proceso BAG2JP;
  no matar por nombre ni cerrar una partida ajena.
- Mantener mods y opciones anteriores. Los experimentos que ya estaban apagados
  no deben encenderse indiscriminadamente.
- Crear evidencia única; conservar baseline y hashes. El harness usa controles
  temporales y tarjetas aisladas y restaura keybinds/settings/state al cerrar
  su proceso. Revisar `restoration.verified`, no asumirlo por exit code.
- La identidad del proceso incluye ruta y tiempo de inicio: no aceptar PID
  reciclado, otra instalación ni logs de un arranque anterior.
- Una GPU local a la vez; no ejecutar modelos GPU durante capturas del juego.

## 2. Calibrar una vez por ejecutable cambiado

Desde `D:/Dev/Recomp/BAG2JP`:

```powershell
& tools/test/bag2_versus.ps1 -Action probe -Tag <probe-tag> -TemporaryControls
```

Revisar **todas** las capturas de aristas además de `selector.png` y la hoja.
La hoja actual no contiene necesariamente las cuatro aristas. Solo después:

```powershell
py -3.13 tools/test/accept_versus_calibration.py --run _work/versus-runs/<probe-run>
```

El helper registra una decisión visual y hashes; no hace visión automática ni
solicita aprobación por sí mismo. No invocarlo como bypass de revisión.
Un cambio de runtime exige probe/revisión nuevos. No editar el hash del catálogo
para forzar aceptación. También se verifican imágenes y grafo sin modificar.

**Cobertura actual limitada:** catálogo Heat=0, Strike=1, Comet=2; aristas
0→right→2, 2→left→0, 0→down→1 y 1→up→0. Otro personaje requiere ampliar datos y
aristas con evidencia del ID real; no asumir desplazamientos ni clonar harness.
Los nombres aceptados, versiones disponibles y capacidades de popup deben
mantenerse coherentes. Una prueba obsoleta que rechazaba Strike BAG1 llevó a
deshabilitarlo erróneamente: el requisito y la integración verificada prevalecen;
actualizar la prueba y añadir regresión, no romper la funcionalidad para ponerla verde.

## 3. Prueba de flujo completa

Ejemplo real de Strike, reutilizable cambiando datos **si están soportados**:

```powershell
& tools/test/bag2_versus.ps1 -Action run -Tag <unique-tag> -P1Character Strike -P1Version BAG1 -P1Costume A -P2Character Heat -P2Version BAG2 -TemporaryControls -Finish
```

`-Stage HeatBAG2|HeatBAG1`: solo esos dos destinos expuestos por el wrapper
PowerShell actual. El parser Python `versus_session.py --stage` sí admite además
`StrikeBAG2|StrikeBAG1` (filas 4/5, selector de 15 filas); no pasar esas opciones
al wrapper ni confundir sus validaciones. Reutilizar solo con calibración vigente.
No presentar el escenario por defecto como prueba del escenario/canción del
personaje nuevo. `-FinishTimeout` predeterminado 420 s; incluye canción y retorno.
Sin `-Finish` el test termina tras entrada a gameplay, no al finalizar canción.

El driver verifica cursor/otro jugador, popup exacto, traje, comandos NORMAL,
escenario y fase nativa de gameplay. `-Finish` guarda capturas periódicas, observa
salida del root de batalla y exige selector con guards válidos. Esas observaciones
acreditan flujo; no verifican puntuación, duración musical exacta, todos los pasos
ni sincronización audio/fever. No escribe RAM para saltar al resultado.

Estados de salida:

| Estado | Alcance real |
|---|---|
| `calibrated_awaiting_visual_review` | Capturas/grafo preparados, sin aprobación |
| `machine_verified_awaiting_visual_review` | Selección y entrada a gameplay |
| `complete_awaiting_visual_review` | Flujo completo y retorno observado |
| `failed` | Leer error y evidencia; no repetir sin hipótesis nueva |

## 4. Matriz mínima por personaje

Registrar evidencia por **P1/A, P1/B, P2/A y P2/B**. Dos casos diagonales no
certifican cuatro. Añadir BAG1/BAG2 mixtos, mirror y todas las capacidades aplicables.
La regla nativa mirror puede cambiar automáticamente el traje del segundo jugador;
el driver lo rechaza si no coincide con el solicitado, no lo oculta.

- Selección/popup: nombre, ID, versión, traje y puerto correctos.
- Identidad al compartir casilla (Bi-O/Gas-O; futuro Comet/Frida): retrato y nombre
  propios para cada versión, en ambos lados/trajes. Probar cambio y vuelta a BAG2,
  preview/confirmación/cancelación, stage select y retorno; dos jugadores con
  versiones opuestas de esa casilla no deben contaminarse. Comprobar assets nativos
  y sus reemplazos HD si están activos, sin afectar a otros personajes. Ver el
  contrato común «Identidad visual por versión» del pipeline, no copiar el parche.
- Nombre sobre la barra de puntuación: **gate independiente del selector/retrato**.
  Exigir que esté presente, completo, legible y en el lado correcto durante la
  partida, con el nombre de la versión activa (Gas-O, no Bi-O ni vacío). Cubrir
  P1/P2×A/B, mixtos y versiones opuestas de la misma casilla; al volver a BAG2,
  restaurar su nombre nativo. Revisar las fases relevantes del flujo grabado para
  detectar desapariciones, no darlo por válido solo porque se vea en el selector.
- Modelo/texturas: frente/espalda, UV, CLUT, accesorios, articulaciones y escala.
- Movimiento: normales/especiales, duración, transiciones y predecesores;
  ataques/defensas/reacciones, cansancio, caída y recuperación.
- Audio: voces/efectos, cues, announcer y mezclas; juicio subjetivo por escucha humana.
- Final: victoria/derrota, fever solo/dueto aplicable, retorno.
- Convivencia: mods activos conservados y regresión de personajes anteriores.
- Extras del alcance: escenario, canción, ending y online con identidad compatible.

Comparar con referencia nativa del **mismo personaje/traje/versión**. Compartir
coordenadas TIM o no colgarse no basta. Reutilizar video solo si coinciden hashes
de motion/profile/catalog/runtime/evidencia; audio cambiado exige prueba de audio.

### Aceptación ampliada tras Gas-O (2026-11-15)

- Cubrir los cuatro casos lado/traje, versiones mixtas y espejo, en al menos dos
  escenarios dentro del alcance. Si el harness no soporta una celda, dejarla
  pendiente; no simular cobertura. Incluir ambos actores/compañeros en parejas.
- CAUGHT debe revisarse en cada importado BAG1 y cada nativo BAG2: postura,
  raíz/pies, hold sin deriva, re-hit, liberación y retorno. Conservar variantes
  legítimas y no aceptar «fail-closed» como cobertura final.
- Cues/tono: comparar dump SPU con control nativo cuando haya remuestreo o sospecha
  de pitch; la escucha subjetiva no prueba el factor de resampling.
- Separar «fever2 ejecutado» de fidelidad/aceptación del dueto; registrar versión,
  contenido stock/adaptado y conformidad con alcance preciso.

## Grabación: procedimiento vigente tras Gas-O

Esta sección sustituye las recetas históricas basadas únicamente en dump/gdigrab.
No autoriza partidas nuevas: rigen los permisos de AGENTS.md.

1. Verificar exe instalado por hash y reutilizar calibración solo con inputs
   idénticos. Aislar settings/tarjetas, comprobar baseline y restauración también
   en fallos; no crear otro sistema de saves. No cerrar aplicaciones del owner.
2. Pasar explícitamente flags de diagnóstico por el harness: `Session.start`
   filtra `BAG2JP_*` heredadas. Comprobar allowlist y opciones realmente soportadas;
   para actores de RAM ampliada solicitar dump de 8 MiB, no asumirlo del default.
3. Elegir audio **por proceso** con `--audio-backend process`; el default del CLI
   sigue siendo `dump` (cambiarlo es tarea aparte). Grabar solo el proceso verificado
   del juego, nunca mezcla global. Mantener trace/heartbeat para ubicar eventos.
4. Preferir `--capture-backend wgc` instalado y verificado; `auto` puede caer a
   gdigrab, así que comprobar el backend real. WGC evita ventanas superpuestas, no
   garantiza frames exactos; gdigrab exige ventana sin tapar y su guard reversible.
   Visible, no minimizada, área completa y principal al 125 % siguen siendo el
   entorno probado. No mezclar modelos GPU con la captura.
5. Abrir el grabador antes del tramo relevante (normalmente selección de escenario)
   y mantenerlo hasta el retorno al selector. Muestrear combate tras observar su
   fase, no gastar todo el presupuesto en VS. Usar tags/ficheros únicos y ordenar
   fotogramas por número/tiempo, no lexicográficamente.
6. Esperar señales nativas observables, no sleeps fijos. Para save/load reutilizar
   menú nativo y su handshake: `.pst` nuevo no vacío y `.thumb` completa de 49164 B
   en el formato actual confirman guardado mejor que stderr bufferizado. No
   generalizar ese tamaño a otro formato. Parar/cerrar el grabador **antes** que
   el juego, también en la ruta de error.
7. Finalizar una vez y exigir manifest `accepted=true`. Nunca recortar,
   re-finalizar para rescatar, descartar pares a mano ni relajar gates. Si falla,
   conservar evidencia y diagnosticar reloj/audio/ventana offline antes de repetir.
   Pausas reales cerca de gf8000/12000/16000 se observaron repetidamente; causa
   raíz pendiente. Audio por proceso resolvió el caso save/load citado, no prueba
   que el emulador haya dejado de pausarse.
8. Revisar primero que se ve BAG2JP y luego los eventos fotograma a fotograma,
   contrastando trace/events y referencia nativa. `accepted=true` solo acepta la
   captura: no certifica cámara, HUD, pose, guardado ni audio subjetivo. No prometer
   precisión ±2; desfases observados de 3–4 frames no son calibración universal.
9. Entregar video, frames, logs y límites solo después de revisar; preguntar por
   conformidad del owner, no pedirle que haga la validación inicial del agente.

Comandos grabador (`py -3.13 tools/test/bag2_record.py`): `record --tag <fresh>
--capture-backend wgc --audio-backend process`, `finalize --tag <fresh>` y
`frames --tag <fresh> --frame <gf> --span 12 --step 2`. Lanzar `record` en background
con el harness existente y su política de cierre; no reconstruir un runner ad hoc.
Evidencia de las correcciones: [Gas-O](gaso-import.md#retrospectiva-incorporada-al-estándar-2026-11-15),
[grabador](tool-evidence/bag2-record.md) y [FFmpeg](tool-evidence/ffmpeg-skill.md).

## 5. Evidencia y señales de diagnóstico

| Archivo | Qué demuestra / qué no |
|---|---|
| `result.json` | Solicitud, picks, checkpoints, hashes, finish y restauración |
| `bag2jp_charsel_popup.log` | Confirmaciones de versión/traje/lado y escenario |
| `bag2jp_bag1_versions.log` | Filas conmutadas stock↔BAG1, opciones efectivas |
| `bag2jp_anim_trace.log` | Fases/solicitudes/slots; interpretar solo estructuras vivas |
| `bag2jp_watch.log`, `bag2jp_frame.txt` | RAM/heartbeat frescos, avance y gates |
| `psx_freeze_heartbeat.json` | Estado del runtime; copiarlo a evidencia antes de otro run |
| `gameplay.png`, `match-*.png`, `returned-selector.png` | Capturas para revisión, no aprobación automática |

No interpretar punteros/slots basura después de descargar el módulo como una
animación real. `req65535` tampoco es automáticamente un rol aceptado.

Direcciones JP verificadas (no exportar a otra región sin revalidar):
DF2_=0x8005D418; root=0x8005D3D4; fases=0x8005D3D8/DC/E0;
mode=0x8005D2C4; clock=0x800892EC. Gameplay local: root=0x13, mode=2,
phase1=1, phase2=3. Selector roots=12/13, guards
0x80091DB0=0x27BDFFC8 y 0x80093138=0x27BDFFB0. No confundir 13 decimal
(selector) con 0x13 (combate); no usar root sin identidad del overlay.

## 6. Fallos observados y siguiente comprobación

| Síntoma | Causa/evidencia de Strike | Comprobación reutilizable |
|---|---|---|
| No aparece GAME para personaje | Exe compilado desde fuentes antiguas | Hashes mods-src→src, log del plugin y filas del índice |
| Build verde pero paquete antiguo | Recursos vienen de mods/preloaded | Hashes preloaded→build bundled→experimental |
| VS visible, reloj avanza, no gameplay | Offsets DFS repetidos | Validar cada miembro, no solo tamaño total |
| Heat pierde entradas fever/escenario | Payload recompuesto desde stock por error | Conservar bytes `old_alt_size` del payload aceptado |
| Packs crecen +30/+62 B | CLUT añadida + compactación de huecos stock | No truncar: índice usa longitud exacta |
| Calibration stale | Cambió exe | Probe y revisión; no manipular hashes |
| Popup de run anterior | Log obsoleto o plugin no arrancó | Frescura, identidad del proceso y errores de paquete |
| Imagen de pecho sospechosa | P2/B llega al final, fidelidad pendiente | Comparar modelo/UV/CLUT con BAG1 nativo antes de cambiar |

No afirmar que truncado/retarget es la causa sin aislarlo. En Strike, quitar el
truncado no arregló el bloqueo: el defecto demostrado fueron offsets DFS iguales.
El rescate/errores intermedios quedan en `notes/strike-recovery.md`; no repetirlos.

## 7. Verificación y conservación

```powershell
py -3.13 -m unittest discover -s tools/test -p test_rebuild_dfs_members.py
py -3.13 -m unittest discover -s tools/test -p test_versus_navigation.py
```

Evidencia histórica del 02-11: 8 pruebas DFS y 49 de navegación; no es un conteo
actual de la suite. No acredita cobertura total
del generador de payload o del retarget. Logs completos fuera de notas; en la nota
del personaje conservar decisiones, causas, hashes y rutas a pruebas aceptadas.
Actualizar el índice corto y estado compacto sin borrar estado ajeno. Copiar
fuentes completadas a `mods-src`, checkpoint local solo del task y snapshot desde
el árbol de build sin directorios de compilación; no publicar ni mezclar archivos
ajenos. Para aceptación final siguen rigiendo `AGENTS.md` y `CHARACTER_IMPORT.md`.
