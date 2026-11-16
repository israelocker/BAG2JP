---
id: host-configuration-migration
title: "Configuración central: auditoría completa y migración por consumidores"
tags: ["plan", "config", "standards", "migration"]
summary: "Migración por consumidores: inventario conciliado de 495 archivos y 21 grupos con evidencia; 9 alcances host históricos entregados. Avance ponderado/calendario pendientes de baseline, no inferidos de archivos cambiados."
related: ["system_config.md", "docs/coding-standards.md", "docs/data-dictionary.md", "AGENTS.md"]
created: "2026-11-15"
updated: "2026-11-16"
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
S1 workflow/report (`46d528c`) entrega rutas/pins/WSL, metadatos, guardas y compatibilidad del
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
- Preparación de esquema: siete campos observados de deadlines/input con tests de
  tipos/finite/política; el registro no significa consumo por el runner ni operación
  activa. Preservar las tres constantes de input observado como política bloqueada.
- S3a: `tools/test/versus_session.py`, pruebas de navegación; GAME/WINSHOT/CATALOG
  y defaults operativos sin cambiar RAM watches, allowlists ni aislamientos.
- S3b: `bag2_endings_view.ps1`, `bag2_endings_acceptance.ps1`,
  `capture_dance_view.ps1`: JSON/destinos efectivos; mantener parámetros existentes.
- Costura: tests de identidad/argv/destinos y JSON en PowerShell 7/5.1, nunca partida.
- Comando: desde `tools/test`, `py -3.13 -m unittest test_versus_navigation`;
  añadir tests de adapters al runner del lote. Uso real en juego queda pendiente.

### S4 — Captura y referencias (sub-lotes S/M)
- Blocked by: S3, S2a de esta familia.
- S4a: `tools/test/bag2_record.py` — ENTREGADO (commit 1ed6f81): grabador consume
  el resolver único, settings inmutables, operaciones condicionales, 73 recording OK.
- S4b: `tools/bag1native/run_match_and_attack.py` y lectores de referencia — ENTREGADO (commit 18d0c51): `run_match_and_attack.py` usa `tools.ffmpeg_native` desde el resolver (sin literal de ruta de máquina); `bag1_mem.py`/`attack_bot.py` conservan constantes de RAM nativa; tests de host pasan (81 OK, mocked, sin juego). Inventario bag1native b60449f (8 tests).
- Costura: resolución de FFmpeg/backends, overlays, metadatos y carpetas aisladas;
  conservar relojes/audio exacto, propiedad de PID/HWND y orden de cierre.
- Comando: `py -3.13 -m unittest tools.test.test_bag2_record tools.test.test_bag2_record_config tools.test.test_recording_window tools.test.test_audio_clock_probe tools.test.test_process_audio_capture tools.test.test_bag1_native_ffmpeg`.
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

Sublote S5a Gas-O cerrado en host (`d1d7c11`, `b1b585c`, `1ca68e5`): extracción
USA/JP, perfil, stock, motions y salidas consumen configuración central; el perfil
conserva layout y región independiente del anunciador. V10: 12 lectores + 120
workflow + 7 HUD, 17 mutantes; Goldfish corregido sin segunda revisión. No demuestra
equivalencia de paquetes ni aceptación nativa. Heat queda cerrado en su costura host
(V6: 32 lectores + 120 workflow + 7 HUD, sintaxis Bash y 34 mutantes por aserción);
sin ejecución de adaptadores. S5b
perfiles/cache/init sigue pendiente. No repetir los lotes entregados.

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
| S2a auditoría semántica | Familia harness: fuentes/3 lectores/3 tests leídos y disposición por hash; nav parcial y global 471 aún pendientes; inventario bag1native b60449f (8 tests) |
| S3a harness versus | Entregado: driver/batch/wrapper consumen resolver; 108 tests harness + 113 workflow OK; 31 mutantes; Goldfish 0 BLOCKER (hallazgos MENOR corregidos/refutados) |
| S3b vistas PowerShell | Entregado host: endings/view/acceptance y Dance View consumen JSON; 19 tests PS7/5.1 + 113 workflow + 108 harness OK, 24 mutantes; Goldfish A/B CON HALLAZGOS corregidos por RED→GREEN (sin segunda revisión); sin juego/build/deploy |
| S3 preparación de esquema | 7 campos preparados (presupuestos ≤ 86400 s), consumidos por S3a; Goldfish 0 BLOCKER, 6 SHOULD-FIX corregidos/registrados |
| S4a preparación de esquema | Contrato preparado: 10 defaults host + 3 rutas sin operación activa; grabador intacto, S4a consumidor ENTREGADO (1ed6f81: 73 recording OK + 119 workflow + 108 harness OK; 28 mutantes; Goldfish CON HALLAZGOS corregidos sin segunda revisión; sin partida/build/deploy de runtime) |
| S4a consumidor | ENTREGADO (commit 1ed6f81): grabador consume resolver único, settings inmutables, operaciones condicionales y guardas; 73 recording OK + 119 workflow + 108 harness OK; 28 mutantes por aserción; Goldfish CON HALLAZGOS corregidos sin segunda revisión; sin grabación/partida ni build/deploy de runtime |
| S4b lectores nativos | ENTREGADO (commit 18d0c51): run_match_and_attack usa tools.ffmpeg_native desde el resolver (sin literal de ruta de máquina); bag1_mem.py/attack_bot.py conservan constantes de RAM nativa; 81 tests OK (mocked, sin juego); inventario bag1native b60449f (8 tests) |
| S2b y S3–S7 | Pendientes: S2b auditoría config, S5b perfiles/caché/init, S6 paquetes/instalador, S7 bootstrap/externos/cierre; bloqueados por sus dependencias (S2a, lotes previos) |
| S5a piloto workspace | Cerrado solo este piloto: plan/prepare/state configurados; 38 tests lectores (37 OK, 1 omitido por privilegio file-symlink), 120 workflow OK, 17 mutantes por aserción. Goldfish A/B CON HALLAZGOS corregidos sin segunda revisión; límites en system_config.md. Evidencia histórica del piloto; Gas-O/Heat tienen cierre separado abajo. S5b perfiles/caché/init pendiente; sin paquetes ni juego |
| S5a Gas-O builder | Cerrado en host (`d1d7c11`, `b1b585c`, `1ca68e5`): extracción regional y seis claves para perfil/stock/motions/salidas, guardas antes de mkdir; 51 campos en ese checkpoint. V10: 12 lectores + 120 workflow + 7 HUD fresh, 17 mutantes detectados; Goldfish A/B CON HALLAZGOS corregidos sin segunda revisión. Sin paquetes ni juego; Heat y S5b son lotes separados |
| S5a Heat scripts | Cerrado host: launcher con resolver único, cinco claves nuevas (56 campos), preparación/empaquetado separados, entradas directas y links/reparse comprobados antes del runner. V6: 32 lectores (20 Heat + 12 Gas-O), 120 workflow, 7 HUD y bash -n de ambos scripts OK; baseline verde, 34 mutantes por aserción sin ERROR, hashes iguales. Goldfish A/B CON HALLAZGOS: tres corregidos RED→GREEN, sin segunda revisión. V4 scoring inválido y V5 timeout/deriva conservados sin puntuar. Sin adaptadores/conversiones/paquetes/build/deploy/juego; siguiente S5b |

## Control conciliado por lote y archivo

Actualizado el 2026-11-16 a petición del owner, sobre `50d1f22`. Fuente única de
asignaciones: [inventario existente](host-configuration-migration.inventory.json),
`reconciliation.lots[].inventory_files`. Conserva las 471 filas originales con
sus hashes y añade 24 archivos versionados: **495 asignaciones únicas**, sin
contar dos veces archivos compartidos. `associated_lots` conserva asociaciones
adicionales. No rastreados e instalaciones externas no forman este denominador.

La columna de archivos muestra consumidores/rutas principales; la lista completa,
incluidos tests, esquema y documentación de soporte, está en el JSON. El número
es asignación administrativa, no archivos totalmente migrados. Los grupos
pendientes grandes se dividirán tras revisar sus lectores; no son lotes de ejecución
listos ni estimaciones de esfuerzo equivalentes.

| ID | Archivos asignados | Consumidores o familia principal | Estado y evidencia de entrega |
|---|---:|---|---|
| F0 | 6 | `tools/workflow/project_config.py`, `tools/bag1import/check_payload_manifest.py` | Base/piloto host: `7fefc07`, `28fc1e9` |
| S1 | 5 | `tools/workflow/bag2_workflow.py`, `tools/test/bag2_report.py` | Rutas/pins/jobs/WSL: `46d528c`; valores numéricos legacy no cerrados |
| S3a | 10 | `tools/test/versus_session.py`, `strike_acceptance_batch.py`, `bag2_versus.ps1` | Harness host: `949fdb2`, `e9236e7`; límites de Goldfish históricos en nota canónica |
| S3b | 6 | `tools/test/view_config.py`, `view_config.ps1`, `bag2_endings_view.ps1`, `bag2_endings_acceptance.ps1`, `capture_dance_view.ps1` | Rutas/guardas host: `a0f3935`; tres wrappers siguen parciales por valores legacy |
| S4a | 7 | `tools/test/bag2_record.py`, `recording_config.py` | Grabador host: `1058670`, `1ed6f81`; sin grabación real |
| S4b | 6 | `tools/bag1native/run_match_and_attack.py` y revisión de familia | FFmpeg host: `18d0c51`, `b60449f`; RAM nativa no se migra a TOML |
| S5a-workspace | 3 | `tools/bag1import/character_workflow.py` | Solo workspace: `b1297cd`; archivo parcial por S5b |
| S5a-gaso | 3 | `tools/bag1import/build_gaso_assets.py` | Builder host: `d1d7c11`, `b1b585c`, `1ca68e5`; sin paquetes |
| S5a-heat | 14 | `tools/bag1import/heat_test_launch.py`, `build_heat_test.sh`, `build_heat_stage_test.sh` | Costura host/contratos estáticos: `50d1f22`; no adaptadores ejecutados |
| S2a-remainder | 60 | Otras fuentes host sin disposición explícita | Revisión pendiente; no inferir defectos ni exenciones del triaje |
| S2b | 0 | Crear `audit_config.py` en `tools/workflow/`; aún inexistente | Checker pendiente; cero archivos existentes no significa cero trabajo |
| S3-remainder | 3 | `tools/test/discover_strike_id.py`, `discover_strike_id_p1.py`, `versus_navigation.py` | Dos lectores pendientes de cambio y navigation parcial; asociación con wrappers legacy |
| S5b | 19 | `tools/bag1import/profiles/`, `cache/`, `contracts/` | Revisión/migración pendiente; `character_workflow.py` asociado, no contado otra vez |
| S6-localization | 24 | `mods-src/bag2jp.localization.regional/tools/` | Revisión pendiente, subdividir antes de ejecutar |
| S6-textures | 5 | `mods-src/bag2jp.hd-texture-pack/tools/` | Revisión pendiente, sin regenerar assets |
| S6-bag1-tools | 7 | `mods-src/bag2jp.feature.bag1-content/tools/` | Revisión pendiente, sin generar paquetes |
| S6-installer | 4 | `installer/` | Revisión/generadores pendientes, sin publicación |
| S7-bootstrap | 4 | `.opencode/`, `ghidra-scripts/`, `tools/workflow/generate_digests.py` | Contratos pendientes, sin instalar ni editar terceros |
| S7-native-boundary | 84 | Runtime, recursos, parches y configuración del título | Determinar fronteras/excepciones/generadores; no convertir constantes por categoría |
| S7-support | 225 | Documentos, pruebas y metadatos restantes | Separar fixtures/ejemplos/historia y dependencias reales; no implica 225 migraciones |
| S7-external | 0 | Build/scripts instalados fuera de Git | Inventario externo pendiente; cambios sujetos a permiso específico |

### Métricas, reutilización y calendario

- **9 alcances host históricos entregados**, 12 grupos restantes. 9/21 =42,86 %
  solo cuenta grupos, no esfuerzo ni avance global. No se da crédito dos veces por
  preparar esquema y migrar el mismo consumidor.
- En los 471 originales: 12 entregados en su costura, 5 parciales, 2 pendientes de
  cambio, 3 sin cambio host identificado históricamente, 19 de soporte registrado
  y 430 sin revisión consolidada. **22/471 =4,67 %** es cobertura de disposición
  acotada de consumidores, no cumplimiento del proyecto. Los 30 archivos con bytes
  cambiados no son un indicador de aceptación; 441 sin cambios no son 441 tareas.
- Cada archivo registra `status`, `review_scope`, `delivered_scopes`, `remaining`,
  `evidence` y hash actual. Cada lote registra commits, archivos, aceptación,
  dependencias y vigencia de evidencia. Historial entregado no se borra por deriva.
- Antes de repetir una validación: documentar qué consumidor/dependencia cambió,
  contradicción o requisito nuevo y costura afectada. La conciliación encontró
  deriva compartida en varios manifiestos; exige análisis de impacto, no reruns
  globales. Heat V6 conserva 169 hashes. F0/S1/workspace solo se compararon contra
  commit; no se presenta como verificación completa de sus inputs de test.
- Fecha límite confirmada por el propietario: **martes 17-11-2026 a las 12:00 del
  mediodía, America/Lima (UTC−5)**, equivalente a `2026-11-17T17:00:00Z`.
  Trabajo del lunes 16 hasta las **22:00**; martes **09:00–12:00 (3 horas)**, sin suponer
  jornada nocturna ni garantizar todo el alcance sin estimarlo. Sin baseline de esfuerzo,
  porcentaje global ponderado y pronóstico siguen **desconocidos**, no ~60 %.
  Para contrastar el plazo: revisar y estimar cada sublote dentro de la ventana confirmada
  en intervalo, registrar tiempo real y retrabajo, y actualizar previsión al cerrar.
  Alcanzar presupuesto sin cerrar obliga a informar riesgo y recortar alcance
  opcional explícitamente, nunca a extenderlo o reducir aceptación en silencio.
- Próxima frontera: revisión acotada de S5b y candidatos host de S2a. Elegir alcance,
  presupuesto y aceptación antes de implementar; no se ejecutan en esta conciliación.

La comprobación de esta actualización valida conservación de las filas originales,
asignaciones/conteos, commits/evidencia y documentación; no reejecuta consumidores.
Resultado: `_work/configuration/progress-reconciliation/verification.json`.
Procedimiento detallado de control en [system_config.md](../../system_config.md#control-de-avance-de-la-migración-2026-11-16).

### S5b: revisión acotada de fuentes y siguiente sublote

Revisión de los 19 JSON asignados a S5b y de sus lectores localizados, sin editar
perfiles, cachés ni consumidores. El inventario conserva por archivo el hash leído,
la clasificación y el trabajo restante en `progress.scope_review`; no cambia su
estado a entregado ni convierte esta lectura parcial en auditoría completa.

- Tres perfiles de personajes contienen `reference_runtime`. Su lector es
  `character_workflow.py`; existe ya `inputs.bag1_reference_runtime`, por lo que no
  se propone otra autoridad ni otra clave para esta ubicación host.
- Catálogo, contratos, políticas y evidencias tienen referencias enlazadas a hashes.
  Cambiar el texto sin seguir al lector puede invalidar cachés o elegir otros bytes.
  Rutas internas, IDs, escalas, cues y mapas nativos no se sustituyen como rutas host.
- La caché Heat no tiene el contrato `key/evidence` del lector actual y contiene
  hashes vacíos de contenido; queda registrada como legacy incompatible, **no** como
  evidencia válida. Strike conserva evidencias por hash: no se recapturan ni se
  actualizan hashes para hacer pasar una comprobación.
- `profiles/stages/heat.json` no presenta rutas host en el contenido leído. Los
  perfiles de etapa Gas-O/Strike y `regional_variants.json` tienen lectores de
  paquetes: se tratan por separado, sin ejecutar conversiones ni generar paquetes.

**Sublote S5b1 — autoridad del runtime de referencia (implementado host 2026-11-16):**

- Alcance: `character_workflow.py` y pruebas host de lectura/firma de perfiles;
  reutilizar `inputs.bag1_reference_runtime`, pasar un único snapshot resuelto y
  distinguir explícitamente el campo histórico del perfil de la ubicación operativa.
  Determinar los llamadores afectados antes de editar; no declarar migrados otros lectores.
- Aceptación: Heat/Strike/Gas-O en fixtures reubicados seleccionan el runtime de
  config, mantienen hashes/identidad/región y fallan sin fallback ante config ausente;
  caché detecta cambio real de bytes, no un simple cambio de ubicación equivalente.
- Exclusiones: catálogo/assets, políticas y contratos nativos, cachés existentes,
  init-profile y lectores de paquetes; necesitan sus propios sublotes. Ninguna prueba
  en juego, build, deploy o cambio de herramientas instaladas.
- Previsión inicial **90–150 minutos**, hipótesis de planificación, no tiempo medido
  ni compromiso global; incluye regresiones host, Goldfish aplicable y cierre.
  Control a los **90 minutos**: si no está cerrado, informar pendiente y previsión
  revisada antes de ampliar trabajo. Registrar duración real y causas de retrabajo.
  Esta estimación no cubre los otros grupos ni demuestra viabilidad del plazo total.

Resultado acotado: `character_workflow.py` recibe config central en load_profile,
signature/record_cache/check_cache/character_plan/prepare y todos los lectores CLI;
un snapshot por invocación, runtime real protegido y validado antes de outputs.
El campo histórico reference_runtime no es requerido ni operativo en estos lectores;
init-profile sigue usando su argumento explícito. No se editó ningún perfil/cache.
Fixtures reubicados Heat/Strike/Gas-O, identidad/región preservadas, mismo contenido
conserva cache y distintos bytes invalidan. Host: 68 tests, 67 PASS/1 skip de symlink,
3 mutantes causales (AssertionError, 0 errores). Evidencia y comando exacto en
`_work/configuration/s5b1/verification.json`; revisión en `_work/goldfish/s5b1/`.
Límite: dos revisores locales read-only, pero B fue resumen no utilizable y A
parafraseó línea fija; no declarar dos Goldfish conformes. No se relanzó revisión.
Auto-revisión suplementaria, no sustituto de ese límite. Registro canónico:
[system_config.md](../../system_config.md#presupuesto-y-deadlines).
S5b entero continúa pendiente: siguiente revisión catálogo/assets del lector;
otros lectores, políticas, destinos cache, init y paquetes requieren sus sublotes.

**Sublote S5b2 — autoridad de catálogo/assets declarados (implementado host 2026-11-16):**

- Decisión: las rutas declaradas en perfiles y catálogo cuyo primer componente es
  `_work` se resuelven contra la clave ya registrada `paths.work_root`; el resto sigue
  relativo al proyecto. No se añadió clave ni se duplicó valor alguno, y con
  `work_root=_work` la resolución es byte-idéntica a la anterior.
- Alcance: sólo las resoluciones declaradas de `character_workflow.py`
  (`load_profile`, `_workspace_inputs`, `_profile_signature` y la acción CLI
  `validate-profile`). `init_profile`, los perfiles, contratos, políticas, cachés,
  datos nativos y los lectores de paquete etapa/regional quedan fuera.
- Guardas: se rechazan rutas absolutas/ancladas, componentes con `..` o alias de
  puntos/espacios finales, y toda ruta cuya resolución física (symlink/junction) salga
  del proyecto o de la raíz de trabajo configurada.
- Aceptación: con la raíz reubicada, perfil, catálogo, assets, evidencia de excepción
  y `validation_evidence` se leen de la ubicación configurada, mantienen sus hashes y
  disparan las mismas guardas al alterarse; la costura real de Gas-O devuelve
  `catalog_sha256 0d616c8b…`, `runtime_sha256 e7ed906a…` y 84 animaciones, iguales a
  la caché Strike existente.
- Host: 13 pruebas nuevas en `tools/test/test_character_asset_config.py`; suite
  acotada 81 tests, 80 PASS y 1 skip (workspace con privilegio de symlink).
  5 mutantes causales (`work_root_ignored`, `work_root_case_sensitive`,
  `absolute_allowed`, `traversal_alias_allowed`, `physical_containment_removed`).
  Evidencia: `_work/configuration/s5b2/{verification.json,mutants.json,green.log}`.
- Goldfish: dos revisiones frías read-only con línea fija literal → revisión
  utilizable, `CON HALLAZGOS`. Confirmados y corregidos: CLI sin resolver, ausencia de
  contención física, comparación de `_work` sensible a mayúsculas en Windows y
  `KeyError` por evidencia no validada en etapas distintas de `verified`. Añadida la
  prueba de identidad que faltaba. `..`/puntos finales queda como endurecimiento
  conservador no verificable en el entorno. Sin segunda ronda.
- Límites: Heat y Strike fallan aún en las guardas por deriva de hashes **previa** a
  este cambio (`patch_heat_dbi.py`, `001_strike_converted.bin`), no por la resolución.
  Sin validación nativa ni en juego. Siguiente frontera: políticas y contratos con
  lector propio, destinos de caché, `init-profile` y lectores de paquete.

No se repitieron suites para esta revisión de fuentes. Evidencia:
`_work/configuration/s5b-scope-review/extracted.json`; la extracción de cadenas
sirve de ayuda, no demuestra por sí sola que cada cadena sea una ruta operativa.

### S5b cerrado — alcance host acotado (implementado host 2026-11-16)

S5b se cierra como alcance host acotado, no como cierre del proyecto ni aceptación
nativa. Todos los lectores de la familia fueron migrados y verificados en host:

- **S5b1 — runtime de referencia:** `character_workflow.py` lee el runtime solo de
  `inputs.bag1_reference_runtime` (snapshot por invocación, sin fallback al perfil).
  El campo histórico `reference_runtime` del perfil queda no operativo para estos
  lectores. `init_profile` conserva su `--runtime` explícito (sublote separado).
- **S5b2 — entradas declaradas de catálogo/assets:** `resolve_declared_input` resuelve
  rutas declaradas con primer componente `_work` contra `paths.work_root`; el resto
  sigue project-relative. Guardas de absoluta/anclada, `..`, alias de puntos/espacios
  y contención física (symlink/junction). Aplicado en `load_profile`,
  `_workspace_inputs`, `_profile_signature` y CLI `validate-profile`.
- **S5b3 — política de animación:** `animation_policy.load_policy(path, project,
  config)` resuelve `input_evidence.file` mediante `resolve_declared_input` y compara
  `file_sha`; sin fail-open; `config` sin proyecto o `project=None` con evidencia
  lanza error. Roles, `native_variant` y `adapt_events` intactos.
- **S5b4 — init-profile y destinos de caché:** `init_profile` acepta `config`, valida
  `config.repo_root == project.resolve()`, resuelve archive/source/runtime/catalog
  mediante `_operator_input` (ruta absoluta verbatim si es absoluta fuera del repo).
  `record_cache` rechaza sobrescribir JSON legacy no caché y protege inputs reales.
- **S5b5 — lector de paquete de etapa:** `build_stage_package.package_paths` /
  `main_exe_path` resuelven `source`/`common`/`exe`/`stock` y `_work/mainexe/slpm.bin`;
  `build_from_project` carga config una vez, valida `config.repo_root`, CLI con
  `--project`/`--local-config`.
- **S5b6 — regional y caught:** `build_regional_variants` valida segmentos de ruta
  con `_trusted_segment` (rechaza absoluto/ancla/vacío/`.`/`..`/alias puntos-espacios)
  antes de construir; `build_caught_bank` ya usaba `resolve_declared_input`.

**Evidencia y verificación:** suite S5b conjunta 133 tests, 132 PASS, 1 skip (OK);
mutantes causales detectados y bytes restaurados (`_work/configuration/s5b{2..6}/`).
Costura real Gas-O: `catalog_sha256 0d616c8b…`, `runtime_sha256 e7ed906a…`, 84
animaciones, idénticos a la caché Strike existente.

**Límites:** cachés NO migradas (`heat.cache.json` legacy sin contrato key/evidence;
`strike.cache.json` evidencias absolutas por hash) preservadas sin editar; perfiles y
hashes no editados; Heat y Strike detenidos por deriva de hashes **previa** al lote;
sin paquetes, juego, runtime build/deploy, settings/saves, overlay local, herramientas
instaladas, push, snapshot ni worktree. Goldfish S5b2/S5b3/S5b5/S5b6: revisión
utilizable con línea fija literal, `CON HALLAZGOS`, correcciones RED→GREEN verificadas,
sin segunda ronda. S5b1 Goldfish declarado no utilizable (revisores no conformes),
con auto-revisión suplementaria registrada.

Plazo global: martes 17-11-2026 12:00 mediodía Lima (UTC−5 = 17:00Z); lunes hasta
22:00, martes 09:00–12:00. Viabilidad global no demostrada.
