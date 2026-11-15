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

## Configuración host: base y piloto en curso

El owner eligió «Host primero», aprobó el diseño común/local + cargador +
diccionario, la [especificación escrita](docs/superpowers/specs/2026-11-15-host-configuration-design.md)
y el [plan de base/piloto](plans/archive/host-configuration-foundation.md), y pidió
ejecutarlo directamente aquí.

Estado real (15-11): existen `config/project.toml`, `config/project.local.example.toml`
y el local ignorado con 13 valores verificados; `tools/workflow/project_config.py`
resuelve y valida la configuración, y `docs/data-dictionary.md` documenta cada campo
con su consumidor real. `tools/bag1import/check_payload_manifest.py` ya deriva sus
cuatro copias de la configuración (4/4 OK, exit 0 en esta máquina) sin perder
`--package` explícito ni los códigos 0/1/2. Suites: 62 pruebas host en verde.
Workflow, harness, captura, importadores y perfiles **siguen sin migrar**: son
lotes posteriores del roadmap, no consecuencia de crear TOML. El script Bash
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
