---
id: host-configuration-migration
title: "Configuración central: auditoría completa y migración por consumidores"
tags: ["plan", "config", "standards", "migration"]
summary: "Ampliación aprobada: inventariar todos los archivos de desarrollo, distinguir configuración de datos nativos y migrar consumidores con diccionario y pruebas de equivalencia; workflow/report en ejecución."
related: ["system_config.md", "docs/coding-standards.md", "docs/data-dictionary.md", "AGENTS.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: plan
---

# Configuración central del desarrollo

## Estado y autorización

El owner pidió analizar todos los archivos de desarrollo, eliminar rutas/valores
operativos en duro de sus consumidores y hacer explícito el estándar y el
significado de cada clave para reutilización futura. La regla documental se
aplica desde ahora. El owner aprobó la ampliación con **«Si continúa»** el
2026-11-15, tras la pregunta explícita sobre ejecutar este plan por lotes sin
instalaciones externas, partidas ni despliegues. Workflow/report ya estaba
autorizado anteriormente con «si procede». Ejecución inline y secuencial.

La base y el piloto de manifiestos están entregados (`7fefc07`, `28fc1e9`).
S1 workflow/report entrega rutas/pins/WSL, metadatos, guardas y compatibilidad del
script fijo: 101 pruebas dirigidas, 103 en discovery de workflow y Goldfish aplicado.
No se certifican defaults numéricos legacy, otros consumidores, integración POSIX
ni build/juego con esas cifras; permanecen en los lotes y evidencias correspondientes.

## Alcance del inventario inicial

`host-configuration-migration.inventory.json` conserva clasificación y líneas
candidatas de los **471 archivos versionados existentes** examinados al inicio.
La evidencia completa está en `_work/configuration/development-audit.json`;
el inventario versionado no incluye textos de rutas personales ni sus valores.

| Grupo | Archivos |
|---|---:|
| Herramientas host generales | 82 |
| Herramientas host dentro de paquetes | 36 |
| Pruebas/harnesses (según clasificación inicial) | 94 |
| Perfiles, contratos y caches | 19 |
| C/H/INC de runtime en mods-src | 50 |
| Recursos/manifiestos/datos de paquetes | 28 |
| Parches/config del título | 6 |
| Instalador | 4 |
| Scripts Ghidra | 2 |
| Config del harness | 1 |
| Autoridad config común/plantilla | 2 |
| Markdown | 144 |
| Otros metadatos/activos | 3 |

Señales en 51 archivos de rutas de máquina, 127 de ubicaciones relativas, 10 de
entradas de entorno, 42 de defaults CLI y 87 de constantes nativas; los grupos se
solapan. Los números son **triaje automático, no defectos confirmados ni revisión
semántica completa**. Incluyen patrones, comentarios y fixtures legítimos. Los
valores numéricos de Python también se inventariaron para revisión contextual.

No rastreados (`.agents/`, `tools/ffmpeg-skill/`, logs y tests WIP) se enumeran
separadamente y se preservan; no son automáticamente código propio que editar.
Árbol de build/instalaciones son externos: no se presume auditado su contenido
por haber recorrido Git. Releases y evidencia histórica no se reescriben.

## Contrato de migración

- Una autoridad de esquema/resolución: `project_config.py`; valores portables en
  el TOML común, rutas de máquina en local ignorado y significado en el diccionario.
  Reutilizar claves por significado, no solo por tipo. Cada lote actualiza también
  operaciones, consumidores y estado real; claves no usadas siguen sin exigirse.
- Eliminar fallback operativo antiguo, conservando CLI/entorno documentados y
  registrando valores efectivos/procedencia. PowerShell/Bash usan datos del mismo
  resolutor; no otro parser ni `eval` de texto generado. La config no es permiso.
- Configuración host no convierte direcciones/opcodes, IDs de personaje, formatos,
  hashes, guards ni gates de aceptación en opciones arbitrarias. Clasificar y
  documentar la excepción y su autoridad. Defaults operativos configurables sí
  requieren claves, incluso si son numéricos o rutas relativas.
- Antes de efectos: validar tipo/requisitos/override y destino efectivo protegido;
  probar raíz reubicada, CWD distinto, override válido/erróneo, claves faltantes,
  alias y no escritura en estable. Preservar saves/settings/sesiones y pins/jobs2.
- El script instalado `build_bag2jp.sh` sigue fijando árbol/toolchain (6 líneas
  verificadas). Nunca atribuirle reubicación por cambiar Python. Hasta migrarlo,
  bloquear builds cuyo destino efectivo no coincida; preflight debe declarar el
  límite. No ejecutar builds para demostrar únicamente la lectura de configuración.

## Pasos y verificación

Los grupos amplios de auditoría no son commits monolíticos. Por cada familia se
completa primero el listado de lectores/candidatos/autoridades; se migran después
sub-lotes de hasta 3 consumidores junto a sus tests/diccionario. No modificar
consumidores aún no leídos ni resolver divergencias en silencio.

### S1 — Cerrar workflow/report (M; ya autorizado)
- Blocked by: ninguno; base entregada.
- Archivos: `tools/workflow/bag2_workflow.py`, `tools/test/bag2_report.py`, tests
  respectivos, registro/diccionario/config según claves realmente consumidas.
- Aceptación: work_root respetado y protegido; overlay propagado al subprocess;
  audio_probe requerido solo para búsqueda de audio; invariantes del Bash fijo
  declaradas/verificadas antes de build y valores efectivos/hashes en métricas.
- Costura: fixtures aislados, argv de subprocess, escritura de sheet y preflight
  real de solo lectura. Preservar resúmenes/códigos/salidas existentes.
- Comando: `py -3.13 -m unittest tools.workflow.test_project_config tools.workflow.test_data_dictionary tools.workflow.test_bag2_workflow tools.test.test_payload_manifest_config tools.test.test_bag2_report_config`.
- A continuación Goldfish y checkpoint; no declarar WSL/Linux verificado por mocks.

### S2 — Completar auditoría semántica e instrumentar guardia (M, dividido)
- S2a Blocked by: ninguno; es análisis interno ya autorizado por el owner.
- S2b Blocked by: disposiciones semánticas de S2a; aprobación del plan obtenida.
- S2a: revisar asignaciones, defaults, entorno y lectores de cada archivo host,
  tests y generadores de la lista; registrar clave destino o excepción justificada.
- S2b: crear `audit_config.py` y `test_audit_config.py` en `tools/workflow/`,
  convirtiendo el inventario en comprobador reproducible, después de fijar con
  casos reales qué patrones son defectos. Baseline explícita de deuda y excepciones
  revisables; no usar un regex que obligue a mover todos los números.
- Aceptación: ningún archivo del alcance sin disposición; deuda/excepciones con
  motivo, autoridad y consumidor; prueba que un nuevo hardcode no aprobado falla.
- Comando: `py -3.13 -m unittest tools.workflow.test_audit_config` (a crear en S2b).
- Archivos: inventario, checker/tests; no arreglos masivos en la fase de análisis.

### S3 — Harness versus y PowerShell (sub-lotes S/M)
- Blocked by: S1, S2a de esta familia.
- S3a: `tools/test/versus_session.py`, pruebas de navegación; GAME/WINSHOT/CATALOG
  y defaults operativos sin cambiar RAM watches, allowlists ni aislamientos.
- S3b: `bag2_endings_view.ps1`, `bag2_endings_acceptance.ps1`,
  `capture_dance_view.ps1`: JSON/destinos efectivos; mantener parámetros existentes.
- Costura: tests de identidad/argv/destinos y JSON en PowerShell 7/5.1, nunca partida.
- Comando: desde `tools/test`, `py -3.13 -m unittest test_versus_navigation`;
  añadir tests de adapters al runner del lote. Uso real en juego queda pendiente.

### S4 — Captura y referencias (sub-lotes S/M)
- Blocked by: S3, S2a de esta familia.
- S4a: `tools/test/bag2_record.py`; S4b:
  `tools/bag1native/run_match_and_attack.py` y lectores de referencia.
- Costura: resolución de FFmpeg/backends, overlays, metadatos y carpetas aisladas;
  conservar relojes/audio exacto, propiedad de PID/HWND y orden de cierre.
- Comando: `py -3.13 -m unittest tools.test.test_bag2_record tools.test.test_recording_window tools.test.test_audio_clock_probe tools.test.test_process_audio_capture`.
- Sin nueva grabación del juego ni gates relajados; registrar límites de evidencia.

### S5 — Importadores y perfiles (sub-lotes S/M)
- Blocked by: S2a de esta familia; no heredar valores de Gas-O para otros perfiles.
- S5a: lectores en `character_workflow.py`, `build_gaso_assets.py` y scripts
  `build_heat_test.sh`/`build_heat_stage_test.sh` (separar el build externo).
- S5b: `tools/bag1import/profiles/*.json` y referencias de caches: migración
  compatible de ubicaciones host, sin alterar identidad, región, entradas ni hashes.
- Contrato: después de migrar un lector, su ubicación operativa viene de config;
  campos históricos conservados se etiquetan como evidencia/no operativos. Un
  consumidor legado pendiente no se declara migrado. Divergencia se diagnostica.
- Costura: perfiles de Heat/Strike/Gas-O, ambas regiones, temporal/reubicado,
  mismo hash de assets de entrada y misma selección; no generar/deployar paquetes.
- Comando base: `py -3.13 -m unittest discover -s tools/bag1import -p test_*.py`;
  fijar las pruebas específicas de lectores antes de editar cada sub-lote y comparar
  fallos de baseline por nombre, no asumir verde toda la suite.

### S6 — Herramientas de paquetes e instalador (sub-lotes S/M)
- Blocked by: S2a de esta familia.
- Auditar todos los 36 scripts host de `mods-src/**/tools/**`. Primeros candidatos:
  localization `build_announcer.py`, `build_buttons.py`, `build_xa.py`, `diff_members.py`,
  `groups.py`, `map_entries.py`, `hq/render*.py`; texturas `esr_each.ps1`,
  `font_hd.py`, `gen_charsel_pack.py`; bag1-content `hq_bag1/render2.py`.
- Separar `installer/build.sh` y templates NSIS/settings: derivar en el generador
  solo ubicaciones de desarrollo; no poner dependencia del TOML host en el juego
  distribuido ni modificar releases existentes.
- Costura: argv y salidas temporales byte-equivalentes; antes de cada cambio,
  añadir su test específico al comando base `py -3.13 -m unittest discover -s tools/workflow -p test_*.py`.
- Cierre documental no equivale a construir/publicar instaladores o regenerar assets.

### S7 — Bootstrap, externos y cierre (sub-lotes S/M)
- Blocked by: S2a de cada familia y lotes previos pertinentes.
- Revisar `.opencode/opencode.json`, `ghidra-scripts/*`,
  `tools/workflow/generate_digests.py` y dependencias reales de tests. Distinguir
  patrones de búsqueda/documentación de valores operativos.
- El harness tiene esquema propio: usar referencias relativas admitidas o registrar
  excepción de bootstrap; no introducir claves desconocidas ni reiniciar/configurar
  MCP o instalar componentes. Consultar documentación oficial antes de editarlo.
- Script instalado y árbol build: inventario read-only propio, después adaptador
  reproducible versionado para destinos/toolchain/jobs, pruebas argv y comparación
  con instalación. No cambiar instalaciones externas en este plan sin autorización
  específica adicional; registrar lo pendiente, no fingir cobertura global.
- Cierre: `audit_config.py` (S2b) + tests por lotes + `audit_docs.inspect_document`
  en cada Markdown tocado. Goldfish/checkpoint por lote, cobertura por consumidor,
  plan archivado solo si todos los entregables autorizados pasan o el owner acepta
  explícitamente una entrega parcial.

## Decisiones y límites

| Decisión propuesta | Motivo |
|---|---|
| Migración host y generadores; runtime sin nuevo parser TOML | Preservar contratos nativos y despliegue |
| Auditoría por archivo con excepciones justificadas | Cero coincidencias no demuestra ausencia de valores en duro |
| No terceros/no rastreados/historia sin autorización específica | Pueden ser herramientas externas o trabajo del owner |
| No builds, deploy, partida, instalación ni publicación implícitos | La autorización de refactor host no los autoriza |

No especificado aún: nombres exactos de nuevas claves de cada familia y lectores
no examinados semánticamente. Son salida de S2a; no se inventan valores ni se
ejecuta su migración antes de clasificarlos. Una decisión que cambie autoridad,
contrato o permisos vuelve al owner; no se resuelve con otro fallback.

## Progreso

| Paso | Estado |
|---|---|
| Estándar explícito | Documentado; Goldfish de 2 revisores CON HALLAZGOS aplicado; no aprobación de la migración |
| Inventario inicial | 471 versionados clasificados automáticamente; revisión semántica pendiente |
| S1 workflow/report | Entregado: 101 pruebas dirigidas, 103 workflow discovery, 8 mutantes; Goldfish aplicado y prueba real de logs existentes |
| S2a auditoría semántica | Autorizada; triaje inicial disponible, revisión contextual pendiente |
| S2b y S3–S7 | Aprobados; pendientes de sus dependencias y ejecución |
