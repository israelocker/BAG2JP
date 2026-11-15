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
| `repo_root` | Raíz del repo usada para anclar rutas y configuración | ruta | native path | derivado | no | Derivada del propio módulo; configurarla es un error | workflow, workflow-report, report, report-audio, report-sheet | `project_config.py`; `check_payload_manifest.py`; `bag2_workflow.py` | base |
| `build.jobs` | Paralelismo de compilación fijado por el owner | entero | compile jobs | común | no | Entero exactamente 2; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `pins.psxrecomp` | Revisión fijada de PSXRecomp | revisión | Git hex prefix | común | no | 7–40 caracteres hexadecimales; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `pins.recomp_ui` | Revisión fijada de Recomp UI | revisión | Git hex prefix | común | no | 7–40 caracteres hexadecimales; override local prohibido | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `wsl.distribution` | Distribución WSL para comandos envueltos | cadena | distribution name | común/local | sí | Cadena no vacía sin NUL; sin charset porque los nombres registrados varían | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `paths.work_root` | Raíz de evidencias, logs y fixtures locales | ruta | native path | común/local | sí | Ruta no vacía sin NUL; relativa anclada al repo | workflow, workflow-report, report, report-audio, report-sheet | `project_config.py`; `bag2_report.py`; `bag2_workflow.py` | base |
| `paths.build_root` | Árbol de build del proyecto | ruta | native path | común/local | sí | Ruta no vacía sin NUL; relativa anclada al repo | payload-manifest, workflow, workflow-report | `project_config.py`; `check_payload_manifest.py`; `bag2_workflow.py` | base |
| `paths.experimental_install` | Instalación experimental usada en pruebas | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no puede solaparse con la estable al escribir | payload-manifest, workflow, workflow-report, report, report-audio, report-sheet | `project_config.py`; `check_payload_manifest.py`; `bag2_report.py`; `bag2_workflow.py` | base |
| `paths.stable_install` | Instalación estable protegida | ruta | native path | común/local | sí | Ruta no vacía sin NUL; cualquier destino de escritura que la solape se rechaza | workflow, workflow-report, report-sheet | `project_config.py`; `bag2_workflow.py`; `bag2_report.py` | base |
| `paths.tools_root` | Raíz común de herramientas locales | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | — | `project_config.py`; herramientas host (pendiente) | base |
| `inputs.bag1_usa_disc` | Imagen del disco BAG1 USA | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_usa_extraction` | Extracción completa del disco BAG1 USA | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_jp_disc` | Imagen del disco BAG1 Japón | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_jp_extraction` | Extracción completa del disco BAG1 Japón | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no se exige salvo para la operación que la usa | — | `project_config.py`; importadores (pendiente) | base |
| `inputs.bag1_reference_runtime` | Runtime nativo de referencia para capturas BAG1 | ruta | native path | común/local | sí | Ruta no vacía sin NUL; ejecutarlo requiere autorización de prueba | — | `project_config.py`; referencia nativa (pendiente) | base |
| `tools.audio_probe` | Buscador de plantillas de audio usado por el reporte | ruta | native path | común/local | sí | Ruta no vacía sin NUL; requerida solo para report-audio cuando hay audio que buscar; no demuestra ejecución | report-audio | `project_config.py`; `bag2_report.py` | base |
| `tools.python_report` | Intérprete usado por el reporte del workflow | ruta | native path | común/local | sí | Ruta no vacía sin NUL; opcional en preflight, requerida para workflow-report; presencia no prueba PIL ni ejecución | workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `tools.winshot_root` | Directorio del runner de capturas | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no demuestra que el runner esté activo | — | `project_config.py`; harness (pendiente) | base |
| `tools.build_script` | Script de build instalado | ruta | native path | común/local | sí | Ruta no vacía sin NUL; el script instalado fija su propio árbol y toolchain | workflow, workflow-report | `project_config.py`; `bag2_workflow.py` | base |
| `tools.ffmpeg_review` | FFmpeg usado en revisión de video | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | — | `project_config.py`; revisión (pendiente) | base |
| `tools.ffmpeg_wgc` | FFmpeg usado en captura WGC | ruta | native path | común/local | sí | Ruta no vacía sin NUL; sin valor verificado para esta máquina | — | `project_config.py`; captura (pendiente) | base |
| `tools.ghidra_launcher` | Lanzador de Ghidra instalado | ruta | native path | común/local | sí | Ruta no vacía sin NUL; su presencia no prueba que MCP responda | — | `project_config.py`; análisis (pendiente) | base |
| `tools.ghidra_project` | Proyecto Ghidra del binario principal | ruta | native path | común/local | sí | Ruta no vacía sin NUL; no sustituye verificar el programa cargado | — | `project_config.py`; análisis (pendiente) | base |

Los campos de política (`build.jobs`, `pins.*`) y el derivado `repo_root` no se
pueden sobrescribir desde el archivo local. Ningún campo demuestra por sí mismo que
un disco, montaje, ejecutable o servicio esté disponible.

`Operaciones` declara requisitos del registro, no permisos de ejecución.
`payload-manifest` compara las cuatro copias. `workflow` escribe métricas y
ejecuta preflight; `workflow-report` además necesita `tools.python_report`.
`report` lee estado y busca capturas; `report-audio` añade el probe solo cuando
se solicita búsqueda y existe el WAV; `report-sheet` exige la instalación
estable para proteger el destino antes de escribir una hoja de capturas.
El runtime C y los scripts instalados no pasan a consumir TOML por esta tabla.

Cobertura S1: rutas, pins, distribución WSL y comprobación de jobs del script
legacy. Defaults numéricos de espera/layout del reporte y otras herramientas
siguen siendo candidatos de la auditoría semántica ampliada; no se declara
migración integral de todos los valores por cerrar las rutas de este lote.

Precedencia de los `inputs.*`: la configuración local selecciona los insumos de las
herramientas host. Los valores equivalentes de `source_layout.regions` en los
perfiles siguen siendo evidencia del importador y mandan al reconstruir su pack con
el contrato correspondiente; el cargador no los lee. Una divergencia se investiga
como discrepancia de inventario, no se resuelve en silencio a favor de uno de los dos.

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
