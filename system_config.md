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
| Harness/PowerShell/captura | Pendientes de análisis semántico y migración |
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
