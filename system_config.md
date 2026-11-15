---
id: system-config
title: "Configuración: fuentes de verdad"
tags: ["config", "reference"]
summary: "Distingue configuración del título, plantilla y ajustes efectivos sin copiar defaults personales."
related: ["docs/paths.md", "notes/project.md", "notes/game-controls.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Configuración

## Configuración host: base y piloto entregados

El owner eligió «Host primero», aprobó el diseño común/local + cargador +
diccionario, la [especificación escrita](docs/superpowers/specs/2026-11-15-host-configuration-design.md)
y el [plan de base/piloto](plans/archive/host-configuration-foundation.md), y pidió
ejecutarlo directamente aquí.

Entrega de base (15-11): existen `config/project.toml`, `config/project.local.example.toml`
y el local ignorado, creado con 13 valores verificados; `tools/workflow/project_config.py`
resuelve y valida la configuración, y `docs/data-dictionary.md` documenta cada campo
con su consumidor real. `tools/bag1import/check_payload_manifest.py` ya deriva sus
cuatro copias de la configuración (4/4 OK, exit 0 en esta máquina) sin perder
`--package` explícito ni los códigos 0/1/2. Suites: 62 pruebas host en verde.
La entrega de base no migró workflow, harness, captura, importadores ni perfiles.
El estado posterior por consumidor figura abajo; crear TOML no los migra. El script Bash
instalado tiene root y toolchain fijos y requiere su propio lote.

No confundir esta base con settings vivos ni con datos nativos de perfiles.
`repo_root` no se configura; el `.gitignore` solo cubre el local por defecto, no
un `--local-config` alternativo. La configuración no demuestra la identidad de la
instalación estable ni autoriza operaciones, despliegues o partidas. `inspect` no
exige discos ni herramientas; cada operación futura exigirá solo sus claves.

Goldfish de dos rondas, ambas **CON HALLAZGOS** y aplicadas:

1. Tareas 1-2 (`_work/goldfish/host-config-foundation/`): guardas de
   estable/prefijo/destino vacío sin ejercitar, `_is_within` roto con raíz de
   unidad y exportación sin el archivo usado. Corregidos con casos nuevos y
   cuatro mutantes muertos.
2. Tareas 3-5 (`_work/goldfish/host-config-pilot/`): el diccionario declaraba
   «pendiente» un consumidor ya migrado y su propio test lo exigía; `check()`
   abortaba toda la ejecución con un manifiesto TOML inválido; faltaba columna de
   operaciones, comparación exacta de unidades y controles de rutas de máquina en
   el TOML común y la plantilla. Corregidos con tres mutantes muertos más.

Límites declarados: identidad de la instalación estable, symlink roto en el local
por defecto, `--local-config` alternativo no cubierto por `.gitignore`, el CLI de
pruebas lee el TOML real del repo a propósito y `wsl.distribution` sin charset
(refutado). Revisor: no es aprobación del propietario ni permiso de despliegue.

## Ampliación del estándar y auditoría de desarrollo (2026-11-15)

Petición del owner: analizar todos los archivos de desarrollo y hacer obligatorio
que rutas/valores operativos configurables se obtengan de config, con significado
documentado para poder reutilizarlos. Regla canónica:
[Configuración central obligatoria para desarrollo](docs/coding-standards.md#configuración-central-obligatoria-para-desarrollo),
enlazada desde AGENTS. [Diccionario](docs/data-dictionary.md) = significado y
consumidores; esta nota = estado/evidencia. No implica convertir datos nativos,
fixtures sintéticos o gates de aceptación en ajustes libres.

Barrido inicial: **471 archivos versionados existentes**, cada uno clasificado y
ligado a su hash en el [inventario](plans/pending/host-configuration-migration.inventory.json).
Hay señales en 51 archivos de rutas de máquina, 127 de ubicaciones relativas,
10 de entradas de entorno y 42 de defaults CLI; se solapan. Es triaje automático,
**no** 51 defectos ni análisis semántico terminado. El informe completo y las
líneas numéricas de Python están en `_work/configuration/development-audit.json`.
No rastreados/herramientas ajenas se preservan. Build/instalaciones externas no
quedan cubiertos por recorrer Git. Plan, orden, tests y permisos:
[migración por consumidores](plans/pending/host-configuration-migration.md).
El inventario identifica fecha UTC, comando/hash del extractor local y hash del
informe completo; su commit es solo la base del árbol sucio, no los bytes exactos
revisados (para eso sirve el hash individual). El extractor de investigación aún
no es una herramienta versionada de cumplimiento. Una disposición semántica se
revisa si cambia el consumidor, la autoridad de configuración o sus dependencias;
este barrido no concede por sí solo ninguna disposición semántica.

| Consumidor/familia | Estado real |
|---|---|
| Resolutor y checker de manifiestos | Entregados en `7fefc07` / `28fc1e9` |
| Workflow/report | S1 entregado en `46d528c`: rutas/pins/WSL/jobs y guardas; 101 pruebas dirigidas OK, Goldfish aplicado |
| Audio probe | Clave `tools.audio_probe` y ruta local verificada; requisito solo al buscar audio existente |
| Harness/PowerShell/captura | S3a (`e9236e7`) y S3b entregados solo host; S4 pendiente. S3b: 19 vistas PS7/5.1 + 113 workflow + 108 harness, 24 mutantes; sin aceptación en juego |
| Importadores/perfiles/herramientas de paquetes/instalador | Pendientes por lotes |
| Bash instalado fijo / bootstrap del harness | Exigen contrato y verificación propios; no migrados |

S1 prueba work_root/destinos protegidos, overlay absoluto en subprocess, dependencia
opcional de audio_probe/python_report y coherencia del build fijo. Ocho mutantes
en copias temporales murieron por aserción con baseline verde; fuentes canónicas
no modificadas por las mutaciones. Log final: `_work/configuration/lot1-mutations-goldfish/`;
la primera matriz de cinco se conserva en `lot1-mutations/` de la misma carpeta.
Suite dirigida: 101 OK; discovery de `tools/workflow`: 103 OK. No se presenta como
suite global del juego ni se ejecuta discovery de tests con efectos no examinados.

Preflight real: `_work/workflow/20261115T135004565296Z-config-lot1-proof/metrics.json`,
0.395 s, contrato legacy compatible con árbol real/jobs2; conserva el drift conocido
de `bag2jp_gaso_caught.c` (diagnóstico, no staging ni build). Ruta completa
workflow→reporte con overlay relativo y el Python configurado, tras corregir Goldfish:
`_work/workflow/20261115T140149654970Z-config-lot1-final-readonly/metrics.json` pasó
leyendo logs ya existentes; no es evidencia nueva de una partida ni grabación.
No se ejecutó partida, deploy, build ni cambio de settings.

Límite S1: migra rutas/pins/distribución y contrasta jobs; defaults numéricos de
espera/layout del reporte siguen en el inventario semántico, no certificados como
configurados. Bash instalado no se ha migrado: el adaptador reconoce solo su forma
literal de seis líneas, expone hash/toolchain/árbol/jobs y bloquea build si formato,
árbol o jobs divergen. Preflight informa la incompatibilidad sin fingir reubicación.
Las rutas de reporte son nativas según config, sin adivinar montajes; integración
POSIX no probada. Guardas de rutas no prometen protección TOCTOU ni identidad de
una instalación mal identificada en la config local.

Goldfish S1 (2026-11-15): dos revisores, ambos **CON HALLAZGOS**; copias/spec y
respuestas en `_work/goldfish/config-lot1/`. SHA-256 del manifiesto revisado:
`d407276e11145c57368694168c3f3e3bcbc9da4451de02a9fc3d47afd3ad2b2f`.
Confirmados y corregidos con RED→GREEN: build sin guarda de su destino estable,
redirección Bash aceptada como path literal, WAV aparecido durante la espera y
directorio confundido con WAV. Se eliminaron causas alternativas en los tests
de jobs/texto shell y mayúsculas de estable. La selección opcional se resuelve
después de esperar y antes de stdout/escrituras; el build valida raíz y carpeta
efectiva con rol build antes de lanzar Bash. Sin hallazgos refutados. No se relanzó
la revisión; las correcciones están ligadas a tests/mutantes y hashes posteriores.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Herramientas consideradas: Git + Python stdlib para extracción determinista y
hashes; MCP Ghidra obligatorio confirmó SLPM JP y byte nativo (log individual).
FFmpeg/grabador/Redux/funcmatch no son pertinentes a documentación y clasificación
de configuración; no hubo captura ni búsqueda de equivalentes MIPS. No se lanzó
modelo local para clasificar patrones deterministas: el resultado verificable sale
del script; ahorro no medido. La revisión semántica no se sustituye por ese script.

Goldfish documental de esta unidad (2026-11-15): dos revisores en frío, ambos
**CON HALLAZGOS**, sobre copias/hashes de `_work/goldfish/config-standard/`.
SHA-256 del manifiesto del estado revisado:
`b97d7f91e783718d53a128f6e3d89ea50df542146ddb3d9deef3969df4ad3db9`.
Confirmados y corregidos: ámbito host/generadores frente a runtime, tabla de
settings ilustrativa separada del esquema host, permiso de análisis S2a separado
del gate de implementación S2b, fecha del índice y procedencia/invalidez del
inventario. Sin hallazgos refutados; límites: el barrido no es análisis semántico,
los reviewers no ejecutaron código ni certificaron tests. Triaje/respuestas y
correcciones posteriores se conservan junto al spec. Checks documentales e
integridad del inventario acreditan esta unidad, no el código workflow/report WIP.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.
El owner aprobó ejecutar el plan ampliado con «Si continúa» el 2026-11-15.
Análisis/migración host siguen por lotes; no autoriza partidas ni cambios externos.

### S2a: disposición contextual de la familia del harness

Se trazaron GAME→`paths.experimental_install`, WINSHOT→`tools.winshot_root`,
CATALOG y carpetas de runs→`paths.work_root`; repo_root sigue derivado. Además de
`versus_session.py`, hay tres lectores de producción: `discover_strike_id.py`,
`discover_strike_id_p1.py` y `strike_acceptance_batch.py`, más dos módulos de tests.
Algunos capturan las rutas al importar: retirar globals sin migrar lectores rompería
esa API. Los wrappers discover también citan SELECT_ROOTS, ausente del módulo
actual; es indicio de API legacy, no prueba de desuso ni permiso para borrarlos.

El primer mapa quedó en `2b25d3f`; después se completó la lectura del runner,
sus tres lectores y tres módulos de pruebas. Disposiciones versionadas por hash,
con candidatos y excepciones: [auditoría de esta familia](plans/pending/host-configuration-harness-audit.json).
`versus_navigation.py` sigue revisado parcialmente como dependencia de guards,
no se declara toda su implementación auditada. La auditoría global de 471 archivos
continúa incompleta. No se ejecutó ni modificó el código del harness.

Sus direcciones/capacidad de watches/allowlist y gates de revisión no se vuelven
knobs libres. El catálogo vigente comprueba runtime/grafo/imágenes/evidencia; no
se inventa un gate automático de hashes de scripts donde hoy solo se reportan como
procedencia. Las rutas de helpers son relativas a su raíz configurada; los nombres
de archivos de protocolo no necesitan una clave distinta por cada filename.

Omisión Goldfish de esta continuación S2a: solo análisis/evidencia y nota/digests,
sin código ejecutable versionado ni política de la lista cerrada; auto-revisión
documental declarada, no presentada como otra revisión en frío.

### Preparación numérica S3: esquema, no activación del consumidor

Se registraron siete `harness.*` en el TOML común/diccionario, pasando de 24 a
31 campos: cuatro deadlines (25/35/40/420 segundos, tope 86400) y hold/gap/fade observados y bloqueados
(100 ms / 350 ms / 1.3 s). Se preservan valores observados en fuentes; ninguno
se conecta aún a `versus_session.py` ni tiene operación activa asignada.
Los presupuestos admiten números finitos positivos (no bool/texto, NaN/inf ni
enteros que desborden la representación flotante). Los tres valores de input son
política bloqueada: valor común exacto y sin override local. Un valor válido por
esquema no demuestra por sí solo soporte del timeout por una API de plataforma.

Pruebas: siete RED antes del registro → siete GREEN; suite host dirigida 108 OK,
discovery de workflow 110 OK y cuatro mutantes muertos por aserción en copias.
El baseline del harness es 63 tests, todos con fixtures/mocks, sin proceso del juego.
Primer intento de agruparlos desde `tools/test` dio un fallo de importación
(`tools` fuera de sys.path): se conservó el log y se corrigió solo el comando,
con `PYTHONPATH` apuntando al repo; no se relajó ni modificó un test para hacerlo pasar.
Logs en `_work/configuration/harness-*.log` y `harness-config-mutations/`.

Próximo: migrar la lectura por ejecución y sus consumidores de forma coherente,
sin global mutable para seleccionar overlay. Los scripts discovery no se usan como
base del engine: `SELECT_ROOTS` falta y sus flujos no tienen el aislamiento ni la
grabación de la vía vigente. Conservarlos como legacy hasta tratar sus límites,
sin borrado, lanzamiento, ampliación de allowlist o aceptación visual implícita.
Otros budgets/layouts/capturas quedan nombrados como candidatos en la auditoría,
no registrados ni certificados por haber preparado estos siete.

Goldfish del esquema numérico/auditoría (2026-11-15): dos revisores en frío sobre
15 entradas congeladas por hash; 0 BLOCKER, 6 SHOULD-FIX, varios NIT. Corregidos:
tope de 86400 s para presupuestos (antes 1e300 pasaba), aserciones por causa
exacta, variantes de tipo en la política bloqueada, test unresolved≠missing,
«calibrado» → «observado y bloqueado» (no hay registro de calibración de hold/gap),
cobertura indirecta del batch y precedencia CLI `--finish-timeout` > TOML.
Registrado como riesgo legacy, sin corregir aquí: `run_case` sustituye el
`subprocess.Popen` global e inyecta fixtures fuera del allowlist; su corrección
pertenece a S3a. RED 44 subpruebas → GREEN; 3 mutantes nuevos muertos por aserción.
Registro: `_work/goldfish/harness-config-prep/` (`reviewers.md`, `triage.md`,
`corrections.sha256.json`). Veredicto de revisor: no es aprobación del
propietario ni permiso de despliegue.

### S3a: versus session consume la configuración host (entregado)

Driver, batch y wrapper toman rutas y presupuestos del resolver único, por run e
inmutables. `HarnessSettings` resuelto por `versus-inspect`/`versus-session`;
juego rol `experimental`, catálogo/runs rol `work`; guardas antes de efectos.
`Session(run, settings, *, fixtures=...)` con `DECLARED_FIXTURE_ALLOWLIST` y
`fixtures` de solo lectura; el batch declara fixture y calendario VRAM por sesión,
sin sustituir `subprocess.Popen`; el entorno heredado sigue filtrado. `--finish-timeout`
explícito gana al TOML; default del parser = valor resuelto; el wrapper lo reenvía
solo si está enlazado. `assert_process_safe` se retiró (solo legacy lo usaba).

Evidencia: harness 108 tests OK (antes 97); workflow dirigido 113 OK; discovery de
workflow 113 OK. Mutantes en copias: 31/31 muertos por aserción (reporte en
`_work/configuration/versus-session-mutations/`, incluye `provenance.json` con HEAD
y hashes). `versus_session.py` pasó de CRLF a LF a propósito. Sin partida ni deploy.

Goldfish S3a (2026-11-15): dos revisores en frío sobre 20 entradas congeladas por
hash; 0 BLOCKER. Hallazgos MENOR corregidos: exit 2 en rechazo de guarda (A1),
test del sink de presupuesto (A2), reenvío condicionado del wrapper (A3), registro
de `debug_fixtures` (A4), atribución de consumidores en el diccionario (A5),
reasignación de `Session.fixtures` (B1), mezcla de evidencia entre sesiones (B2),
registro de fixture/VRAM armado (B3), mutantes que sobrevivían (B4), `KeyError` por
`[controller]` ausente y negativa por sesión activa fuera del `try` (B5). DUDAS
refutadas y documentadas: `versus-inspect` exige el deadline del helper (A6) y el
guard experimental en la inspección de solo lectura es intencional (B6); nota de
locale de `[double]` en PowerShell y guard no race-safe (B7). Triaje/respuestas y
hashes posteriores: `_work/goldfish/versus-session-s3a/`. Veredicto de revisor:
no es aprobación del propietario ni permiso de despliegue.


### S3b: wrappers de endings y Dance View (entregado host)

`view_config.py` adapta el único resolver y exporta JSON con destinos efectivos;
`view_config.ps1` solo invoca Python 3.13 y consume ese JSON. Reutiliza cinco claves
existentes, sin nuevos campos ni defaults en TOML. `endings-view` y
`endings-acceptance` guardan experimental/work y protegen estable antes de mkdir,
backups, helpers o lanzamiento. `dance-capture` conserva la identidad explícita
`ExpectedExe` (incluida referencia nativa), protege el Output bajo work y conserva
overrides de helpers; solo exige winshot_root si falta alguno. El proceso por PID
sigue verificado antes de efectos. Destino existente Dance View se preserva.

El padre endings reenvía destino absoluto, overlay efectivo, hashes e identidad de
archivos/destinos al hijo; una divergencia bloquea al hijo antes de actuar. Acceptance
exige una salida nueva y no reutiliza backups preexistentes. Lecturas, hashes,
copias y escrituras usan rutas literales, sin expandir corchetes. Los overrides
relativos conservan su texto de ejecución. No hay global
mutable de overlays. Direcciones, estados, índices, teclas y tiempos observados no
se convierten en knobs. `ObserveSeconds` conserva parámetro y default 42; las
esperas legacy siguen como candidatos de auditoría semántica, no como configuración
ya migrada. Las guardas de filesystem no son race-safe.

Inventario y decisiones: `_work/configuration/s3b-view-inventory.json`. Host final:
19 tests de vistas PS7/5.1, 113 workflow y 108 harness OK; 24/24 mutantes
assertion-killed en copias. Reportes: `_work/configuration/s3b-final-tests/` y
`_work/configuration/s3b-view-post-review-mutations/`. Baseline de 19 reutilizado
tras comprobar hashes de ocho inputs sin cambios; ronda anterior 12 tests/14
mutantes preservada. Preflight pasó (solo drift conocido `bag2jp_gaso_caught.c`):
`_work/workflow/20261115T155630190723Z-s3b-view-config/`.

Herramientas: Ghidra MCP verificó identidad y lectura acotada (log de herramienta
20261115-ghidra-s3b-view-config). PowerShell 7 y 5.1 ejecutan los wrappers con
dobles de proceso, teclas, capturas y escrituras en árboles temporales; no es prueba
en juego. FFmpeg, grabador y runner real no se usan: no hay media nueva y la partida
no está autorizada. Extracción/hashes/mutaciones son deterministas; un modelo local
no aporta validación independiente a esos cálculos, por lo que no se usa aquí.
Sin build, deploy, cambios instalados, settings personales ni tarjetas.

Comando del lote, desde la raíz: `py -3.13 -m unittest tools.test.test_view_config`.
La suite conserva wrappers y resolver reales; procesos/inputs/capturas/escrituras
son dobles salvo el caso de proveedor literal, que copia y lee solo archivos
temporales con un hermano señuelo. Un hook rechaza helpers externos al fixture
antes de invocarlos (launcher Python seleccionado permitido); no es un sandbox
contra código host malicioso. Registra también Set-Content y prueba padre/hijo
reales. Validación de IndexAddress precede ahora a mkdir.

Goldfish S3b, 2026-11-15: dos revisores fríos (A configuración/guardas, B costuras y
pruebas), ambos CON HALLAZGOS sobre snapshot inmutable de 17 archivos. Copia,
manifiesto original y respuestas literales: `_work/goldfish/view-config-s3b/`.
SHA-256 del manifiesto del estado revisado:
`b86ad5fc657de8f49198c8826306f0c9913741f2da9933d7e73218e7f30fca58`.
A1–A5/B1–B4 confirmados (A5 duplica B3/B4); corregidos por RED→GREEN y mutantes
en copias, sin segunda revisión. A2 endurece el contrato de selección/destino,
no demuestra divergencia espontánea del padre anterior. La equivalencia íntegra
con el baseline y el comportamiento de helpers reales no fueron certificados por
los revisores. Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Siguiente sublote aprobado: S4a `bag2_record.py` (host) y después S4b lectores de
referencias/`run_match_and_attack.py`. No implica autorizar una grabación en juego.

Corrección documental de la evidencia S3a anterior: los inputs Goldfish se
regeneraron después de corregir; sus hashes actuales no identifican exactamente
los bytes originales vistos por los revisores. `reviewers.md`/`triage.md` son
síntesis, no respuestas literales, y no hubo segunda revisión. El reporte 31/31
corresponde a los mutantes listados, no a alternativas sustituidas tras dar ERROR.
`copy_current` cubre cuatro logs del driver y las copias del batch; otras copias de
audio/RAM/SPU conservan sus controles legacy. Calendario VRAM registrado significa
programado, no necesariamente observado en juego. Estos límites no son aceptación.

### S4a-prep: contrato host del grabador (checkpoint histórico `1058670`)

Estado en ese checkpoint: se separa la preparación de S4a; el grabador combina captura, clocks,
audio y cierre; registrar primero el contrato permite revisar el esquema compartido
sin mezclarlo con esa reescritura. No cambia autoridad ni permisos. **S4a no está
entregado**: `bag2_record.py` conserva los bytes de `a0f3935` (SHA-256
`88f7d437aa081c6072c6663ccfe6ca4b076449e5bb8be5f9113b882a2c4bf594`).

Se preparan diez `recording.*` (FPS/duración y presupuestos host) y tres rutas:
`tools.ffprobe_review`, `tools.ffmpeg_look`, `tools.recording_font`. Los defaults
viven en TOML y se contrastan con el inventario del grabador. Las rutas no tienen
valor común; ninguna operación activa exige estas claves. El futuro consumidor
deberá preservar CLI explícita y `BAG2JP_FFMPEG_WGC` con provenance, sin fallback
oculto. PID/HWND, audio, gates, máscaras, formatos y orden de cierre quedan fuera.
240 FPS y un día son techos de cordura del esquema, no calibración ni gates.
No se modificó el overlay local ignorado.

Evidencia: `_work/configuration/s4a-recording-inventory.json` (40 entradas,
extracción acotada, no exhaustiva) y `s4a-recording-inventory-addendum.json`
(dos literales inline de window poll/process audio con fuente/hash).
`_work/configuration/s4a-prep-final-tests-v2/`: 119 workflow, incluidos 6 tests
nuevos; 55 recording OK reutilizados tras comparar ocho fuentes/tests sin cambios
con `a0f3935`. `_work/configuration/s4a-prep-final-mutations/`: baseline verde y
37/37 assertion-killed en copias; inputs canónicos sin cambios. Ronda original
28/28 preservada, sin pretender cobertura integral.
Comando nuevo desde la raíz: `py -3.13 -m unittest tools.workflow.test_recording_config`.
Suites e invocaciones exactas quedan en el reporte. El preflight pasó:
`_work/workflow/20261115T163501481593Z-s4a-recorder-config/`, solo drift conocido.

Herramientas: Ghidra MCP verificó binario y lectura acotada del entrypoint; utilidad
limitada a identidad, no prueba de configuración. Las pruebas host usan medios
sintéticos/fixtures y procesos propios; no son una nueva toma del juego. No se
ejecuta runner ni captura de partida; no hay material nuevo que inspeccionar con
ffmpeg-skill. Inventario/hashes/mutación son deterministas, sin modelo local.
Sin build/deploy de runtime, settings, tarjetas ni herramientas instaladas editadas.
La suite host compila un fixture C aislado en WSL; no construye el runtime.

Goldfish S4a-prep, 2026-11-15: dos revisores fríos A/B CON HALLAZGOS. Snapshot
original de 16 archivos y respuestas literales en `_work/goldfish/recording-config-prep/`;
SHA-256 del manifiesto revisado:
`894194d0587fae5fc7991806c0e18022e77e953d7c487f0b7e71104f1edccec9`.
A1/B1/B2 confirmados: expectativas enteras independientes, valores/orígenes de
todos los campos en overlays y ausencia de las tres rutas en el TOML distribuido.
Alternativas incorrectas pasaban las seis pruebas originales; ahora fallan por
aserción en copias. NIT de inventario corregido con addendum, sin sobrescribir
el original. Se añaden mutantes de rama numérica. Un ensayo intermedio tuvo
34 kills y un mutante con FAIL+ERROR (no puntuado): se reforzó el contrato de error
ConfigError y se repitieron los mismos 37 mutantes, no se sustituyó ese mutante.
Las pruebas UNC originales quedan preservadas; la ronda final usa rutas relativas
para no necesitar resolver shares. Un verificador asumió un módulo inexistente y
no ejecutó pruebas; su fallo se conserva, la evidencia válida es v2.
Sin segunda revisión; los revisores no certificaron ejecución, hashes, baseline
histórico íntegro ni disponibilidad de herramientas. Opcional inválido sí bloquea
la carga global; opcional ausente no activa ni se exige por una operación.
Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.

Siguiente: S4a consumo real del resolver por `bag2_record.py`, pruebas de
precedencia, operaciones y guardas antes de efectos, conservando backend/audio/
clocks/metadata/cierre; después S4b. No autoriza grabación ni partida.

### S4a: consumidor del grabador (verificación host)

`bag2_record.py` consume el resolver mediante `RecordingSettings` inmutable y las
operaciones `recording-record`, `recording-finalize`, `recording-frames`. Se usan
las diez claves host preparadas, sin campos nuevos. `--local-config` elige overlay;
CLI explícita gana al TOML, y `BAG2JP_FFMPEG_WGC` mantiene su precedencia documentada
con origen registrado. Su valor vacío/inexistente desactiva ese candidato: auto
solo puede pasar al gdigrab configurado, no a una ruta de máquina ni a PATH.
Entorno y archivos se resuelven por ejecución, no mediante global mutable.

Decisiones acotadas: `--game-dir` explícito conserva su identidad de fuente de
solo lectura fuera del experimental por defecto; no escribe allí. Una API Python
con argumentos explícitos los valida y vincula a la provenance de esa ejecución.
Las herramientas se requieren condicionalmente, con existencia de archivo, antes
de efectos; WGC no necesita gdigrab y review no procesa un override WGC ajeno.
Las escrituras quedan bajo work/recordings con guardas para aliases de directorio
y artefactos; no se promete seguridad frente a carreras. La fuente seleccionada
se copia como `clock-font.ttf`: el filtro no interpola una ruta host arbitraria.
`session.json` y `manifest.json` guardan configuración/orígenes/hashes efectivos.

Preservados PID/HWND, backends, clocks, audio, codecs, overlays y cierre: audio
arranca antes del vídeo y se detiene después. Los tests legacy conservan sus
aserciones de rechazo/aceptación; solo se adaptan al objeto settings explícito.
Inventario AST `_work/configuration/s4a-consumer-inventory.json`: 11 funciones
cambiadas, 26 funciones/clases y constantes nativas retenidas idénticas al baseline.
No equivale a prueba de equivalencia íntegra. Estilo de labels, span/step y
truncación diagnóstica siguen candidatos documentados; `look.py` instalado elige
sus propias dependencias PATH, frontera externa pendiente de S7, sin editarlo aquí.

Evidencia: `_work/configuration/s4a-consumer-final-tests/` y los ensayos retenidos
`s4a-consumer-mutations/`, `s4a-consumer-video-margin/` (28 mutantes en copias,
baseline verde, kills por aserción sin ERROR; inputs canónicos sin cambios).
Comando nuevo: `py -3.13 -m unittest tools.test.test_bag2_record_config` desde raíz.
El primer ensayo persistido falló por un fixture que sustituía recordings fuera
del contrato real; se corrigió el fixture, no se relajó la guarda. Sus hashes se
tomaron después de los tests mientras se editaba: no identifican esa ejecución.
La ronda v2 y la final separada preservan los resultados posteriores; el reporte
final distingue pruebas nuevas de workflow/harness reutilizados por hash.
Resultado: 73 recording OK (18 nuevos + 55 legacy), 119 workflow y 108 harness
OK reutilizados tras comparación de inputs. El verificador final salió 1 al
previsualizar Unicode en consola cp1252, después de guardar exit 0/log/hash del
test; validación separada de esos resultados e inputs en `runner-status.json`.
No se presenta ese fallo de consola como ejecución exitosa del verificador.

Preflight: `_work/workflow/20261115T165909846253Z-s4a-recorder-consumer/`, drift
conocido solamente. Ghidra MCP verificó identidad y entrypoint, no configuración
ni captura. FFmpeg se usa en tests con medios sintéticos; no hay toma del juego
que revisar con ffmpeg-skill ni permiso para runner/recording real. Inventario,
hashes y mutación son deterministas; no requieren modelo local. No se editan
settings, tarjetas, overlay ignorado ni herramientas instaladas; no build/deploy
del runtime. La compilación C aislada de la suite host no construye el juego.
Documentación FFmpeg consultada: escaping de filtros en `ffmpeg-all.html`, §32.2;
la copia con basename fijo evita introducir niveles de escaping host.

Goldfish: revisión fría pendiente sobre snapshot separado e inmutable. No es
aceptación de captura ni permiso de partida. Después de cerrar S4a, continúa S4b.

### S4b: lectores de referencia y run_match_and_attack.py (verificación host)

`run_match_and_attack.py` migra al resolver central: la ruta FFmpeg de captura nativa
BAG1 antes hardcodeada (`D:\ffmpeg\bin\ffmpeg.exe`) ahora se resuelve desde la clave
`tools.ffmpeg_native` del registro FIELDS, sin valor de máquina en el TOML común.
La clave está documentada en `docs/data-dictionary.md` con operación `native-capture`
y consumidor `bag1native/run_match_and_attack.py` marcado `(pendiente)` porque su
ejecución requiere el juego real (no autorizado). `bag1_mem.py` y `attack_bot.py`
conservan sus constantes de RAM nativa; ninguna ruta de máquina se agregó al TOML.

Pruebas de host: `tools/test/test_bag1_native_ffmpeg.py` verifica que `ffmpeg_native()`
resuelve desde el config, rechaza configuración faltante antes de cualquier efecto,
y que no queda ningún literal de ruta de máquina en el fuente. 81 pruebas de grabación
y native OK (18.445s). Preflight S4b-reference-readers pasó sin drift.

No hay cambios de juego, captura, build, deploy, settings, saves, overlay local ni
herramientas instaladas. `tools.ffmpeg_native` queda `unresolved` hasta que el owner
configure la ubicación verificada en `config/project.local.toml`.

## Fuentes vigentes

- `patches/BAG2JP-game.toml`: configuración reproducible del título, no todos los
  ajustes del usuario. Comparar con `game.toml` del árbol de build efectivo.
- `installer/settings.toml`: plantilla del instalador, no estado vivo del usuario.
- `settings.toml`, `keybinds.ini`, `mods/state.toml` de la instalación que se prueba:
  ajustes efectivos; guardarlos/restaurarlos byte a byte al probar.
- Ver `tools/test/versus_navigation.py` (`IsolatedFiles`) y
  `tools/test/versus_session.py` para aislamiento del harness local.

No copiar una configuración de ejemplo encima de tarjetas/opciones personales.
No asumir que un valor como `buffer_ms=90` sigue activo porque apareció en una nota.
Validar nombres/rangos contra el parser del framework fijado cuando se cambien.

La [copia anterior](docs/archive/system_config-before-audit.md) incluía una ruta
de sesión obsoleta y defaults particulares; queda solo como histórico.
