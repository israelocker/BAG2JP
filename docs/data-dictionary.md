---
id: data-dictionary
title: "Diccionario de datos de configuración y datos nativos"
tags: ["config", "dictionary", "reference"]
summary: "Contrato mecánico de cada campo de config/project.toml y de los datos nativos/compartidos que no se editan como TOML; verificado contra el registro FIELDS."
related: ["system_config.md", "docs/paths.md", "docs/superpowers/specs/2026-11-15-host-configuration-design.md", "notes/character-pipeline.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: reference
---

# Diccionario de datos

Autoridad del esquema: `FIELDS` en `tools/workflow/project_config.py`. Los valores
por defecto viven en `config/project.toml`; las ubicaciones de esta máquina, en el
archivo local ignorado `config/project.local.toml`. Este documento no sustituye a
ninguno de los dos: los describe y
`tools/workflow/test_data_dictionary.py` comprueba que no diverjan.

Tres categorías que no deben mezclarse:

- **Datos de configuración**: campos de la tabla siguiente, validados por el cargador.
  La fuente operativa de las ubicaciones de esta máquina es el archivo local
  ignorado; `docs/paths.md` es el registro humano y puede repetirlas.
- **Datos nativos verificados**: contratos, perfiles y políticas con evidencia propia;
  se referencian, no se copian a TOML ni se editan aquí.
- **Evidencia pendiente**: lo que aún no está verificado no se rellena por analogía.

`Estado` = `base` significa que el cargador resuelve y valida el campo hoy; no
implica que un consumidor de juego/build ya lo use. Los consumidores aún no
migrados se marcan explícitamente como pendientes.

## Campos de configuración

| Clave | Significado | Tipo | Unidad | Origen | Fuente local | Validación | Operaciones | Consumidor | Estado |
|---|---|---|---|---|---|---|---|---|
| `schema_version` | Versión del esquema TOML que acepta el cargador | entero | schema version | común/local | sí | Entero exactamente 1; el valor local no adelanta un esquema futuro | — | `project_config.py` | base |
| `repo_root` | Raíz del repo usada para anclar rutas y configuración | ruta | native path | derivado | no | Derivada del propio módulo; configurarla es un error | workflow, workflow-report, report, report-audio, report-sheet, versus-inspect, versus-session, endings-view, endings-acceptance, dance-capture, recording-record, recording-finalize, recording-frames, native-capture, character-workspace, heat-character-prepare, heat-stage-prepare | `project_config.py`; `check_payload_manifest.py`; `bag2_workflow.py`; `versus_session.py`; `view_config.py`; `recording_config.py`; `character_workflow.py`; `heat_test_launch.py` | base |
| `build.jobs` | Paralelismo de compilación fijado por el owner | entero | compile jobs | común | no | Entero exactamente 2; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `pins.psxrecomp` | Revisión fijada de PSXRecomp | revisión | Git hex prefix | común | no | 7–40 caracteres hexadecimales; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `pins.recomp_ui` | Revisión fijada de Recomp UI | revisión | Git hex prefix | común | no | 7–40 caracteres hexadecimales; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `wsl.distribution` | Distribución WSL para comandos envueltos | cadena | distribution name | común/local | sí | Cadena no vacía sin NUL; sin charset porque los nombres registrados varían | workflow, workflow-report, heat-character-prepare, heat-stage-prepare, heat-test-package | `project_config.py`; `bag2_workflow.py`; `heat_test_launch.py` | base |
| `paths.work_root` | Raíz de evidencias, logs y fixtures locales | ruta | native path | común/local | sí | Ruta no vacía sin NUL; relativa anclada al repo | workflow, workflow-report, report, report-audio, report-sheet, versus-session, endings-view, endings-acceptance, dance-capture, recording-record, recording-finalize, recording-frames, native-capture, character-workspace, heat-character-prepare, heat-stage-prepare | `project_config.py`; `bag2_report.py`; `bag2_workflow.py`; `versus_session.py`; `strike_acceptance_batch.py`; `view_config.py`; `recording_config.py`; `character_workflow.py`; `heat_test_launch.py` | base |
| `paths.build_root` | Árbol de build del proyecto | ruta | native path | común/local | sí | Ruta no vacía sin NUL; relativa anclada al repo | payload-manifest, workflow, workflow-report | `project_config.py`; `check_payload_manifest.py`; `bag2_workflow.py` | base |
| `paths.experimental_install` | Instalación experimental usada en pruebas | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no puede solaparse con la estable al escribir | payload-manifest, workflow, workflow-report, report, report-audio, report-sheet, versus-inspect, versus-session, endings-view, endings-acceptance, heat-test-package | `project_config.py`; `check_payload_manifest.py`; `bag2_report.py`; `bag2_workflow.py`; `versus_session.py`; `strike_acceptance_batch.py`; `view_config.py`; `recording_config.py`; `heat_test_launch.py` | base |
| `paths.stable_install` | Instalación estable protegida | ruta | native path | común/local | sí | Ruta no vacía sin NUL; cualquier destino de escritura que la solape se rechaza | workflow, workflow-report, report-sheet, versus-inspect, versus-session, endings-view, endings-acceptance, dance-capture, recording-record, recording-finalize, recording-frames, native-capture, character-workspace, heat-character-prepare, heat-stage-prepare, heat-test-package | `project_config.py`; `bag2_workflow.py`; `bag2_report.py`; `versus_session.py`; `strike_acceptance_batch.py`; `view_config.py`; `recording_config.py`; `character_workflow.py`; `heat_test_launch.py` | base |
| `paths.tools_root` | Raíz común de herramientas locales | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | — | `project_config.py`; herramientas host (pendiente) | base |
| `inputs.bag1_usa_disc` | Imagen del disco BAG1 USA | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_usa_extraction` | Extracción completa del disco BAG1 USA | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | gaso-source-usa, heat-stage-prepare | `project_config.py`; `build_gaso_assets.py`; `heat_test_launch.py`; otros importadores (pendiente) | base |
| `inputs.bag1_jp_disc` | Imagen del disco BAG1 Japón | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_jp_extraction` | Extracción completa del disco BAG1 Japón | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | gaso-source-jp | `project_config.py`; `build_gaso_assets.py`; otros importadores (pendiente) | base |
| `inputs.gaso_profile` | Perfil de Gas-O con layout, regiones y anunciador | ruta | native path | común/local | sí | Ruta no vacía sin NUL; debe ser un archivo | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `inputs.gaso_stock_bio` | Directorio stock BAG2 Bi-O (pack_a_p1.dfs, pack_a_p2.dfs) | ruta | native path | común/local | sí | Ruta no vacía sin NUL; debe ser un directorio | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `inputs.gaso_stock_fever` | Directorio stock fever BAG2 Bi-O (000.bin, 001.bin) | ruta | native path | común/local | sí | Ruta no vacía sin NUL; debe ser un directorio | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `inputs.gaso_motions` | Archivo de motions de Gas-O (001.bin) | ruta | native path | común/local | sí | Ruta no vacía sin NUL; debe ser un archivo | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `paths.gaso_out_usa` | Directorio de salida de candidatos Gas-O para región USA | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no puede colapsar con entradas ni instalación estable | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `paths.gaso_out_jp` | Directorio de salida de candidatos Gas-O para región Japón | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no puede colapsar con entradas ni instalación estable | gaso-build | `project_config.py`; `build_gaso_assets.py` | base |
| `paths.heat_test_workspace` | Copia de trabajo del adaptador legado de personaje Heat | ruta | native path | común/local | sí | Dentro de `paths.work_root`; sin solapar estable, experimental, fuente, `assets/archive` ni `config`; su `archive/` se borra y recrea | heat-character-prepare | `project_config.py`; `heat_test_launch.py` | base |
| `paths.heat_stage_workspace` | Copia de trabajo del adaptador legado de escenario Heat | ruta | native path | común/local | sí | Dentro de `paths.work_root`; sin solapar estable, experimental, fuente, `assets/archive` ni `config`; su `archive/` se borra y recrea | heat-stage-prepare | `project_config.py`; `heat_test_launch.py` | base |
| `inputs.heat_bag1_members` | Miembros DFS extraídos de BAG1 Heat (PLAYER*_P_HEAT*) | ruta | native path | común/local | sí | Directorio con los diez archivos BAG1 leídos directamente por el adaptador; no valida su contenido ni todos los inputs transitivos | heat-character-prepare | `project_config.py`; `heat_test_launch.py` | base |
| `inputs.bag2_cue` | Imagen .cue del disco BAG2 Japón para make-mod | ruta | native path | común/local | sí | Ubicación de máquina (archivo local); debe ser un archivo; solo la exige el paso explícito `--package` | heat-test-package | `project_config.py`; `heat_test_launch.py` | base |
| `tools.psx_asset_tools` | Checkout de psx-asset-tools (make-mod) | ruta | native path | común/local | sí | Ubicación de máquina (archivo local); debe ser un directorio; solo lo exige el paso explícito `--package` | heat-test-package | `project_config.py`; `heat_test_launch.py` | base |
| `inputs.bag1_reference_runtime` | Runtime nativo de referencia para capturas BAG1 (S5b1: lectura/firma/cache/plan/prepare/CLI de character_workflow, no init-profile ni otros lectores) | ruta | native path | común/local | sí | Ruta no vacía sin NUL; lector exige archivo existente; ejecutarlo requiere autorización de prueba | — | `project_config.py`; `character_workflow.py`; referencia nativa (pendiente) | base |
| `tools.audio_probe` | Buscador de plantillas de audio usado por el reporte | ruta | native path | común/local | sí | Ruta no vacía sin NUL; requerida solo para report-audio cuando hay audio que buscar; no demuestra ejecución | report-audio | `project_config.py`; `bag2_report.py` | base |
| `tools.python_report` | Intérprete usado por el reporte del workflow | ruta | native path | común/local | sí | Ruta no vacía sin NUL; opcional en preflight, requerida para workflow-report; presencia no prueba PIL ni ejecución | workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `tools.winshot_root` | Directorio del runner de capturas | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no demuestra que el runner esté activo | versus-session, endings-view, endings-acceptance | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; `view_config.py` | base |
| `tools.build_script` | Script de build instalado | ruta | native path | común/local | sí | Ruta no vacía sin NUL; el script instalado fija su propio árbol y toolchain | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `tools.ffmpeg_review` | FFmpeg usado en revisión de video | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | recording-finalize | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `tools.ffmpeg_wgc` | FFmpeg usado en captura WGC | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | — | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `tools.ffmpeg_native` | FFmpeg usado en captura nativa BAG1 | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | native-capture | `project_config.py`; `bag1native/run_match_and_attack.py` (pendiente) | base |
| `tools.ffprobe_review` | FFprobe del grabador; sin ubicación común | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no exige existencia al cargar | recording-finalize | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `tools.ffmpeg_look` | Script look.py para inspección del grabador | ruta | native path | común/local | sí | Ruta no vacía sin NUL; relativa anclada al repo; no exige existencia | recording-frames | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `tools.recording_font` | Fuente de etiquetas del video de revisión | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no prueba disponibilidad ni altera texto/estilo | recording-finalize | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `tools.ghidra_launcher` | Lanzador de Ghidra instalado | ruta | native path | común/local | sí | Ruta no vacía sin NUL; su presencia no prueba que MCP responda | — | `project_config.py`; análisis (pendiente) | base |
| `tools.ghidra_project` | Proyecto Ghidra del binario principal | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no sustituye verificar el programa cargado | — | `project_config.py`; análisis (pendiente) | base |
| `harness.state_timeout_seconds` | Presupuesto de espera de estado o popup; default actual 25.0 s | número | seconds | común/local | sí | Número finito mayor que cero y ≤ 86400; bool, texto y no finitos prohibidos | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; discover_strike_id*.py legado (pendiente) | base |
| `harness.helper_timeout_seconds` | Deadline del helper PowerShell; default actual 35.0 s | número | seconds | común/local | sí | Número finito mayor que cero y ≤ 86400; no cambia las condiciones de identidad/PID | versus-inspect, versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; discover_strike_id*.py legado (pendiente) | base |
| `harness.startup_timeout_seconds` | Espera de telemetría al iniciar Session; default actual 40.0 s, no el boot de discovery | número | seconds | común/local | sí | Número finito mayor que cero y ≤ 86400; no acepta estado incompleto al vencer | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py` | base |
| `harness.finish_timeout_seconds` | Presupuesto para fin de canción y retorno al selector; default actual 420.0 s | número | seconds | común/local | sí | Número finito mayor que cero y ≤ 86400; conservar predicados de retorno y restauración | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py` | base |
| `harness.key_hold_ms` | Duración de pulsación del contrato de input observado; default 100 ms | entero | milliseconds | común | no | Entero exactamente 100; política bloqueada, override local prohibido | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; discover_strike_id*.py legado (pendiente) | base |
| `harness.key_gap_ms` | Separación entre inputs del contrato observado; default 350 ms | entero | milliseconds | común | no | Entero exactamente 350; política bloqueada, override local prohibido | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; discover_strike_id*.py legado (pendiente) | base |
| `harness.menu_fade_seconds` | Margen tras observar el menú (comentario de fade en la fuente); default 1.3 s | número | seconds | común | no | Número finito positivo exactamente 1.3; política bloqueada, override local prohibido | versus-session | `project_config.py`; `versus_session.py`; `strike_acceptance_batch.py`; discover_strike_id*.py legado (pendiente) | base |
| `recording.fps` | FPS solicitado al capturador; default 60 | entero | capture frames/second | común/local | sí | Entero positivo ≤ 240; bool y float prohibidos; techo de cordura host, no gate | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.max_seconds` | Duración máxima de captura; default 900.0 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; bool, texto y no finitos prohibidos | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.poll_seconds` | Intervalo de muestreo host; default 0.004 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; no modifica gates de sincronía | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.alive_check_seconds` | Intervalo para comprobar proceso/ventana; default 1.0 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; no cambia identidad ni aceptación | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.window_wait_seconds` | Presupuesto para encontrar la ventana; default 60.0 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; timeout no acepta una ventana inválida | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.window_poll_seconds` | Intervalo de búsqueda de ventana; default 0.5 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400 | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.ffmpeg_quit_seconds` | Presupuesto para cerrar FFmpeg; default 30.0 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; no cambia propiedad ni orden de cierre | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.ffmpeg_extra_seconds` | Margen entero de duración del capturador; default 5 s | entero | seconds | común/local | sí | Entero positivo ≤ 86400; bool y float prohibidos | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.ffmpeg_stop_poll_seconds` | Intervalo de espera de cierre FFmpeg; default 0.1 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400 | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |
| `recording.process_audio_extra_seconds` | Margen del backend process audio; default 60.0 s | número | seconds | común/local | sí | Número finito positivo ≤ 86400; no cambia reloj/productor/gates | recording-record | `project_config.py`; `bag2_record.py`; `recording_config.py` | base |

Los campos de política (`build.jobs`, `pins.*`) y el derivado `repo_root` no se
pueden sobrescribir desde el archivo local. Ningún campo demuestra por sí mismo que
un disco, montaje, ejecutable o servicio esté disponible.

Heat comprueba antes del runner sus fuentes BAG1 directas; para stage exige
`STAGEE/ST_HEAT.DFS` y `SCUS_942.63` con cabecera PS-X EXE y payload tras 0x800.
Rechaza enlaces/reparse points en el árbol `assets/archive` y en el workspace
preexistente antes de copiar/borrar. No es una defensa frente a cambios
concurrentes, un montaje WSL distinto ni las escrituras internas de make-mod.
Los helpers transitivos/perfiles conservan sus lectores pendientes de S5b/S7;
estas comprobaciones no certifican que una conversión vaya a terminar.

`Operaciones` declara requisitos del registro, no permisos de ejecución.
`payload-manifest` compara las cuatro copias. `workflow` escribe métricas y
ejecuta preflight; `workflow-report` además necesita `tools.python_report`.
`report` lee estado y busca capturas; `report-audio` añade el probe solo cuando
se solicita búsqueda y existe el WAV; `report-sheet` exige la instalación
estable para proteger el destino antes de escribir una hoja de capturas.
El runtime C y los scripts instalados no pasan a consumir TOML por esta tabla.

S4a consume los diez defaults host `recording.*` preparados en `1058670`.
`recording-record` exige esos presupuestos y las raíces de evidencia/protección;
la instalación por defecto y FFmpeg gdigrab se exigen condicionalmente si no hay
argumento explícito o backend WGC. `recording-finalize` exige FFmpeg, FFprobe y
fuente; `recording-frames` exige `look.py`. El adaptador `recording_config.py`
usa el único resolver y settings congelados, sin releer el overlay durante una toma.
CLI fps/duración/game-dir prevalece sobre TOML y se registra; el origen de
`BAG2JP_FFMPEG_WGC` también. Esa variable explícita vacía o inexistente desactiva
el WGC configurado: `auto` solo puede pasar al FFmpeg gdigrab configurado;
`wgc` explícito se rechaza. No hay rutas heredadas ni selección de binarios por PATH
en el grabador; el helper instalado `look.py` aún posee sus dependencias externas
(S7), no se modifica. Cada herramienta usada debe existir como archivo.

Las salidas viven bajo work/recordings y se guardan antes de escribir, incluyendo
artefactos de takes existentes; las guardas no son race-safe. `--game-dir` conserva
una fuente explícita de solo lectura, sin permiso para escribir en esa instalación.
Sesión y manifest incluyen procedencia y hashes del TOML; finalize copia la fuente
configurada a `clock-font.ttf` para no interpolar rutas host en el filtergraph.
Los límites
240 FPS y un día son techos de cordura del esquema, no calibración ni condiciones
de aceptación. Audio, clocks, PID/HWND, máscaras, formatos y gates quedan fuera
de estos knobs. Los defaults de selección de frames (span/step), estilo de etiquetas
y truncamiento diagnóstico permanecen identificados en el inventario; no se declara
migración global de parámetros de presentación. Las rutas no tienen default de máquina.

Cobertura S1: rutas, pins, distribución WSL y comprobación de jobs del script
legacy. Defaults numéricos de espera/layout del reporte y otras herramientas
siguen siendo candidatos de la auditoría semántica ampliada; no se declara
migración integral de todos los valores por cerrar las rutas de este lote.

S3a migró el harness de versus. `versus_session.py` resuelve una vez por ejecución
un `HarnessSettings` inmutable (operación `versus-session`): instalación
experimental protegida físicamente como destino `experimental`, `tools.winshot_root`,
catálogo `versus-navigation/catalog.json` y runs `versus-runs` bajo
`paths.work_root` (rol `work`), más los siete `harness.*`. `--action inspect` usa
solo `versus-inspect` (identidad del proceso y deadline del helper). Los deadlines
son presupuestos de espera, no predicados de aceptación. El hold/gap/fade observado
es política versionada y bloqueada por esquema; no pasa a ser un knob local, y
ningún documento local prueba su calibración. Las guardas resuelven ancestros y
enlaces existentes, pero no eliminan carreras de filesystem. `--finish-timeout` explícito
prevalece sobre el TOML; el default del parser es el valor resuelto y
`bag2_versus.ps1` solo reenvía `-FinishTimeout` si el llamador lo enlaza.
`strike_acceptance_batch.py` recibe los mismos settings, usa el presupuesto de fin
resuelto en su bucle propio y declara por sesión el fixture
(`BAG2JP_TEST_STRIKE_ATTACK` o `BAG2JP_TEST_HEAT_STRIKE_DUEL`) y el calendario
VRAM, sin sustituir `subprocess.Popen`; el entorno heredado sigue filtrado por
`DEBUG_ENV_ALLOWLIST`. Las esperas 60/30/60, cierre 15000 ms/2 s, sondeo 0.5 s,
intervalo de capturas 20 s, cola 65536 y layout de hoja siguen como candidatos de
auditoría sin registrar. `discover_strike_id.py` y `discover_strike_id_p1.py` son
lectores legacy que ya fallaban al importar (`vs.SELECT_ROOTS` ausente) y ahora
tampoco encuentran `GAME`/`REPO`/`TIMEOUT`/`WINSHOT`; no se ejecutan, borran ni
copian, y su migración o retiro queda pendiente de decisión.

El batch y el driver consumen estas claves a través de `resolve_settings`/`Session`,
no con lecturas propias del TOML. Un rechazo de guarda del directorio de run o de
batch sale con código 2 antes de crear nada; una sesión activa se rechaza con
código 1 sin escribir. `copy_current` exige inicio propio y `mtime` posterior para
cuatro logs del driver y las copias del batch; audio/RAM/SPU del driver conservan
sus controles legacy. El batch registra fixtures y calendario VRAM programado,
no demuestra por ese registro que cada captura haya ocurrido.

S3b: los wrappers de endings y Dance View reciben JSON de `view_config.py`, adaptador
de `load_config`/`export_config`/`assert_write_target`; PowerShell no analiza TOML.
`endings-view` y `endings-acceptance` requieren instalación experimental, estable,
work y helpers. `dance-capture` conserva `ExpectedExe` explícito y requiere work y
estable; exige `tools.winshot_root` solo si falta algún override `KeyTool`/`ShotTool`.
Los overrides explícitos, incluidos `.<separador>helper.ps1`, prevalecen sin perder
su texto de ejecución; no hay fallback de máquina. Tags relativos y
`Output` se anclan a work; rutas absolutas solo se admiten dentro de work y sin
solapar estable. El padre pasa al hijo destino absoluto, overlay seleccionado y
hashes, identidad de archivos y destinos efectivos: una divergencia bloquea el hijo
antes de sus efectos. Acceptance exige una salida nueva, por lo que no reutiliza
backups preexistentes; las operaciones de archivos usan rutas literales (incluidos
corchetes), sin interpretación de comodines. No es una garantía contra carreras.
Son guardas de configuración, no permisos para ejecutar una partida. Los tiempos
de input, esperas, direcciones y estados nativos de estos scripts permanecen
versionados en su fuente; no consumen los valores `harness.*` del contrato versus.

Precedencia de los `inputs.*`: la configuración local selecciona los insumos de las
herramientas host. Los valores equivalentes de `source_layout.regions` en los
perfiles siguen siendo evidencia del importador y mandan al reconstruir su pack con
el contrato correspondiente; el cargador no los lee. Una divergencia se investiga
como discrepancia de inventario, no se resuelve en silencio a favor de uno de los dos.

`character-workspace` reutiliza repo_root/work_root/stable_install para plan,
prepare y estado de character_workflow.py; settings resueltos una vez, salidas
guardadas y provenance en estado/manifiesto. No migra lectores de perfiles,
caché/init-profile ni builders Gas-O/Heat. El llamador directo de write_state
debe aportar protected_inputs si desea proteger inputs de un perfil que no recibe.

### S5a: lector regional de Gas-O (parcial)

`build_gaso_assets.py` toma las raíces USA/JP de las dos claves existentes;
`source_layout.regions.*.extraction` ya no selecciona ubicación en este lector.
El perfil sigue mandando sobre directorios internos, región del anunciador,
miembros, IDs, cues y límites nativos. Una configuración resuelta y un perfil
leído una vez se comparten entre modelo y anunciador antes de crear salida.
La operación `gaso-source-*` exige solo su región; un build USA con anunciador JP
necesita ambas. La raíz configurada debe ser un directorio existente; si no,
`ConfigError` antes de crear salida. No se valida la identidad por hash del disco.
`--local-config` selecciona el overlay del resolver único; no hay fallback al
campo antiguo. Siguen pendientes las demás rutas del builder (stock, motions,
glyphs, perfil y salida), sus guardas de escritura y los scripts Heat/S5b.
No se declara migración completa del archivo ni generación validada de paquetes.

## Datos nativos y compartidos

Datos con autoridad propia y evidencia verificable. Se referencian desde el código
o la documentación; **no** se convierten en claves de TOML ni se editan aquí.

| Dato nativo | Referencia | Unidad | Editable en TOML | Estado |
|---|---|---|---|---|
| Perfil de personaje (esquema 2) | `tools/bag1import/profiles/gaso.json` | identidad, capacidades, assets | no | verificado |
| Contrato de roles BAG1→BAG2 | `tools/bag1import/contracts/bag1-usa-bag2jp.roles.json` | entradas, índices, reemplazos | no | verificado |
| Estándar de importación compartido | `notes/character-pipeline.md` | reglas, identidad, residencia, aceptación | no | verificado |
| Contrato de escenario y canción por fases | `notes/bag1-stage-song.md` | cámaras, geometría/VRAM, eventos | no | verificado |
| Procedimiento de prueba en juego | `notes/character-import-testing.md` | grabación, matriz, identidad | no | verificado |
| Rutas locales verificadas | `docs/paths.md` | ubicaciones de esta máquina | no | verificado |
| Configuración del título | `patches/BAG2JP-game.toml` | ajustes del título, no del usuario | no | verificado |
| Ajustes efectivos de la instalación | `system_config.md` | settings, keybinds y estado por instalación | no | verificado |

Los símbolos nativos citados en las notas (por ejemplo, direcciones de Ghidra o
tablas de entradas) son hechos verificados con su propia evidencia; no son valores
de configuración ni direcciones editables desde TOML.

## Mantenimiento

1. Añadir el campo a `FIELDS` con tipo, unidad, permiso local, rol, operaciones y
   valor esperado si es entero.
2. Añadir su valor por defecto a `config/project.toml` solo si es portable; si es de
   esta máquina, al archivo local ignorado.
3. Añadir la fila aquí con significado, validación y consumidor real; marcar
   `pendiente` mientras el consumidor no esté migrado.
4. Ejecutar `py -3.13 -m unittest tools.workflow.test_data_dictionary tools.workflow.test_project_config tools.test.test_payload_manifest_config -v`.

Las unidades deben coincidir con `FIELDS`; el test falla si divergen los tipos,
orígenes, secciones o si aparece una ruta absoluta de máquina en este documento.
