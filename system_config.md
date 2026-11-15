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
| Workflow/report | Lote autorizado, código WIP y 83 pruebas dirigidas OK; cierre pendiente |
| Audio probe | Clave `tools.audio_probe` y ruta local añadidas en el WIP, no cierre del lote |
| Harness/PowerShell/captura | Pendientes de análisis semántico y migración |
| Importadores/perfiles/herramientas de paquetes/instalador | Pendientes por lotes |
| Bash instalado fijo / bootstrap del harness | Exigen contrato y verificación propios; no migrados |

El lote workflow/report aún debe probar work_root y destinos protegidos, overlay
en subprocess, dependencia opcional de audio_probe y coherencia del build fijo.
El preflight real `_work/workflow/20261115T131557487604Z-config-wide-audit/metrics.json`
pasó en 0.371 s; conserva el drift conocido de `bag2jp_gaso_caught.c` (diagnóstico,
no staging ni build). No se ejecutó partida, deploy, build ni cambio de settings.

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
La ampliación de migración espera la aprobación del plan; análisis y documentación
continúan bajo la autorización existente.


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
