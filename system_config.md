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
y el [plan de base/piloto](plans/pending/host-configuration-foundation.md), y pidió
ejecutarlo directamente aquí.

Estado real (15-11): `config/project.toml` y `config/project.local.example.toml`
existen; `tools/workflow/project_config.py` resuelve y valida configuración, con
41 pruebas host en verde y guardas de escritura probadas por mutación. El archivo
local real, el diccionario de datos y la migración del checker de manifiestos aún
**no** existen. Ningún consumidor de juego/build fue migrado: workflow, harness,
captura, importadores y perfiles siguen en el roadmap. El script Bash instalado
tiene root y toolchain fijos y requiere su lote explícito.

No confundir esta base con settings vivos ni con datos nativos de perfiles.
`repo_root` no se configura; el `.gitignore` solo cubre el local por defecto, no
un `--local-config` alternativo. La configuración no demuestra la identidad de la
instalación estable ni autoriza operaciones, despliegues o partidas.

Goldfish de este checkpoint (`_work/goldfish/host-config-foundation/`, 2 revisores
en frío, veredicto **CON HALLAZGOS**): guardas de estable/prefijo/destino vacío
sin ejercitar y `_is_within` roto con raíz de unidad. Corregidos con casos nuevos y
cuatro mutantes muertos; `wsl.distribution` sin charset (refutado: rechazaría
nombres válidos), identidad de la instalación estable y symlink roto como límites
declarados. Revisor: no es aprobación del propietario ni permiso de despliegue.


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
