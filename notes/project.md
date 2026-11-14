---
id: project-builds-folder
title: "Proyecto: entorno y build vigentes"
tags: ["project", "build", "saves"]
summary: "Entorno/build, conservación del snapshot e inventario de limpieza del 2026-11-13 sin borrado."
related: ["AGENTS.md", "docs/paths.md", "notes/character-alternate-entries.md"]
created: "2026-10-26"
updated: "2026-11-13"
edited: "2026-11-13"
doc_kind: reference
---

# Build y conservación

Fuente: `tools/workflow/bag2_workflow.py`, contrastada con preflight durante
la auditoría. Rutas efectivas en [paths](../docs/paths.md), políticas en AGENTS.

```powershell
$PY='D:/Dev/Tools/ghidra-mcp-python/python.exe'
& $PY tools/workflow/bag2_workflow.py preflight --tag <task>
& $PY tools/workflow/bag2_workflow.py build --tag <task>
```

Build usa WSL Ubuntu y el script local llvm-mingw fijado con dos jobs. Conservar
el proceso y leer el resultado, no iniciar builds paralelos para compensar una
espera. Logs/métricas quedan en `_work/workflow/`.

El helper compara fuentes, recursos, pins y exe desplegado; **no sincroniza**.
Antes de compilar usar el staging explícito de
[integración](character-alternate-entries.md). No copiar drift ajeno.
Un test solo se acredita con su resultado y alcance: build verde ≠ gameplay.

Saves/config son del usuario. No usar plantillas como estado vivo ni modificar
la instalación estable. Runner externo: `D:/Dev/Tools/winshot/bag2_run.ps1`;
reporter: `tools/test/bag2_report.py`. Para la navegación soportada usar el
harness con [gates observados](character-import-testing.md).

## Snapshot

`BAG2JP-project-snapshot.tar.gz` se conserva fuera de Git y se obtiene del árbol
de build sin directorios de compilación. Incluir docs/herramientas canónicas
actualizadas; verificar hashes internos antes de reemplazar el snapshot y
conservar el anterior. El snapshot no garantiza todos los assets/evidencias de
`_work/`: comprobarlos por separado. No extraerlo sobre un árbol con cambios.

[Historial anterior](archive/project-before-audit.md): versiones, paths VM y
configuraciones de octubre no describen automáticamente la instalación actual.

## Inventario de limpieza — 2026-11-13 (sin borrado)

Alcance: solo `D:/Dev/Recomp/BAG2JP`, no todo `D:/Dev` ni el árbol de build.
Inventario de metadatos: 47 709 archivos, 189,575 GB decimales lógicos;
8,205 s, sin errores de recorrido ni enlaces/junctions omitidos. No mide espacio
físico recuperable. Evidencia en `_work/cleanup-audit-20261113/`:
`files.json` SHA-256 `b05e2226e433d11849e858ff4ee284fe93950374ebab21dae501675eb177380a`,
`summary.json` SHA-256 `8a166439559d17ef83d25c657037a408b1f29ec7a1a41dbc53508b5fd752c11f`.

| Grupo | Tamaño observado | Interpretación / propuesta, no autorización |
| --- | --- | --- |
| `_work/_to_delete/hq_preview_comet_magic_tower.mp3.f32` | 59,666 MB | Candidato temporal; nombre no demuestra por sí solo que no tenga consumidores |
| `__pycache__` en el árbol | 3,007 MB / 205 archivos | Caché regenerable; no incluye `CMakeFiles` |
| `debug00.log`, `debug10.log`, `debug20.log`, `debug30.log`, `index.log`, `save.log` en raíz | 9560 bytes | Logs sueltos; revisar referencias antes de retirar |
| `tools/ffmpeg-skill` | 2,960 MB | Copia antigua v3.2.3, sustituida operativamente por `.agents/skills/ffmpeg-skill` v3.6.0; decisión pendiente en `notes/assets.md`, no son copias idénticas |
| `_work/recordings/*/review.mkv` | 72,564 GB / 34 archivos | Derivados de `raw.mkv` + WAV/logs; generación en `tools/test/bag2_record.py:726-779`; no borrarlos sin comprobar reconstrucción y referencias de manifests |
| `_work/recordings` completo | 151,873 GB / 35 carpetas | 17 manifests aceptados técnicamente (80,047 GB), 15 rechazados (71,456 GB), 3 sin aceptación (0,371 GB); rechazado no significa inútil |
| `_work/versus-runs` | 13,646 GB | Evidencia, RAM, capturas y copias protegidas; no es caché descartable en bloque |
| `_work/portable_test`, `_work/portable_test_v8`, `_work/netplay_peer2` | 1,756 GB en conjunto | Instalaciones de ensayo: revisar sesiones, saves y referencias antes de archivar |
| `releases` | 3,235 GB | Historial de entregas, no basura automática |
| Ocho `BAG2JP-project-snapshot.previous-*` en raíz | 658,955 MB | Respaldos históricos, no duplicados verificados; conservar snapshot vigente y anterior según AGENTS |

Los siete insumos de reconstrucción comprobados existen para los 34 reviews:
raw, WAV, audio-sync, session, ffmpeg.log, heartbeat y events.csv. Solo se comprobó
existencia, no integridad ni reproducción; no se ejecutó FFmpeg ni se reescribió
ningún manifest. No sumar potenciales ahorros de reviews y carpetas rechazadas:
se solapan. Proteger íntegra la toma activa `gaso-combined-ae-f2` y los originales.

Preflight `20261113T193334391870Z-cleanup-inventory` pasó en 0,342 s; conserva drift
previo de `bag2jp_gaso_caught.c` (42 fuentes coincidentes, una distinta y una sin
mapeo); build/deploy coinciden. Ninguna sincronización, juego, commit ni limpieza.
Se usaron scripts deterministas para tamaños y clasificación por manifest, no un
LLM local; grabación, RE adicional y recodificación no aportan a este inventario.
El primer script falló por escape de rutas JS; repetición con `/` correcta. Una
impresión posterior falló por cp1252 después de guardar ambos informes; la lectura
de la cola del log se repitió con JSON ASCII, sin regenerar informes ni evidencia.
Siguiente: el owner elige alcance; preparar lista exacta y comprobaciones antes de
cualquier eliminación. `active_task` de Gas-O no cambia por esta auditoría.

El owner respondió «okay procede» a preparar la lista conservadora. Se generaron
`_work/cleanup-audit-20261113/conservative-list.json` y `conservative-paths.txt`,
sin borrar nada: 205 archivos `.pyc` en `__pycache__` (3 007 488 bytes) y el temporal
de audio nombrado arriba (59 665 536 bytes), total lógico 62 673 024 bytes.
La lista JSON registra rutas exactas, tamaños, mtime y SHA-256; su SHA-256 es
`1fc2cdfcc5164da037dacce8c2de5787b52c21b932aacb7b23dcfdb0ffce8e7d`.
No contiene archivos versionados ni enlaces; una caché había cambiado desde el
inventario y se fijó su estado actual. No incluye logs, fuentes de la skill antigua,
grabaciones, respaldos, releases ni instalaciones de ensayo. Se verificó lectura
de retorno del JSON. Python determinista evita clasificación aproximada con LLM;
FFmpeg y juego siguen sin aportar a esta selección de metadatos.
Preflight `20261113T194115605466Z-cleanup-conservative-list` pasó en 0,393 s;
conserva el drift fuente anterior, pero ahora `deployed_exe_matches=false`:
no se intervino en build/deploy ni en sesiones activas para investigarlo.
Siguiente: confirmar eliminación de esta lista exacta, no limpieza recursiva;
revalidar hashes, seguimiento Git y enlaces antes de actuar. Ahorro real no medido.

El owner confirmó «si, autorizo» y se ejecutó únicamente esa lista con
`py -3.13 D:/Dev/Recomp/BAG2JP/_work/cleanup-audit-20261113/execute-conservative-cleanup.py`.
Comprobación previa: 206 archivos actuales válidos y cuatro guardas negativas
rechazan hash/mtime/ruta alterados y archivo versionado; sin borrados en esa prueba.
Resultado `deletion-result.json`: `completed`, 206 archivos eliminados,
62 673 024 bytes lógicos, cero restantes, 0,581 s. No se eliminaron directorios.
`deletion-journal.jsonl` registra cada eliminación; Git status y hashes del estado
activo y del manifest `gaso-combined-ae-f2` permanecieron iguales durante la limpieza.
No se midió espacio físico reclamado. Las cachés podrán regenerarse al usar Python.
Siguiente: no hay más limpieza autorizada; revisar derivados de video o respaldos
solo si el owner elige una nueva fase. `active_task` de Gas-O permanece intacto.
