---
id: host-configuration-foundation-plan-digest
title: "Plan de configuración host: base y piloto"
tags: ["digest", "plan", "config"]
summary: "Cinco tareas entregadas: configuración común/local, resolutor con guardas, diccionario, archivo local verificado y checker de manifiestos migrado (62 pruebas host en verde)."
related: ["plans/archive/host-configuration-foundation.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "plans/archive/host-configuration-foundation.md"
source_sha256: "29e870dd6ad0c5a75dd250ccbce04117d62d3e8d0e71429102280e0c44122b2d"
---

# Primera entrega host

- Especificación y plan aprobados por el owner con ejecución directa. Las cinco
  tareas están cerradas en dos checkpoints locales (`7fefc07` y el de cierre).
- Tarea1: TOML común/local, esquema1/overlay por clave, resolver inmutable y
  validación tipada; jobs2/pins preservados, raíz independiente de CWD.
- Tarea2: rutas protegidas/aliases, JSON para PowerShell y conversión Windows→WSL;
  sin parser duplicado, ejecución de strings ni permiso implícito de acción.
- Tarea3: diccionario consistente con FIELDS (incluida columna de operaciones),
  native facts por referencia y archivo local ignorado con 13 valores verificados,
  creado sin sobrescribir datos previos.
- Tarea4: piloto `check_payload_manifest.py`; CLI, OK/FAIL y exit 0/1/2 conservados,
  default derivado de las raíces configuradas (4/4 OK reales) y `--package`
  explícito sin cargar configuración.
- Tarea5: 62 pruebas host en verde, mutantes muertos, Goldfish de dos rondas
  aplicado, checks documentales limpios y commit local. No se tocaron build,
  partidas, deploy, assets ni saves.
- El inventario textual 48 archivos/95 coincidencias no equivale a 48 consumidores
  activos. Workflow/harness/captura/importadores van en planes posteriores: el
  Bash instalado tiene root/toolchain fijos y no se finge su migración con un
  cambio solo en Python.
- Límites declarados: identidad de la instalación estable, symlink roto en el
  local por defecto, `--local-config` alternativo no ignorado, CLI de pruebas que
  lee el TOML real a propósito y `wsl.distribution` sin charset (refutado).
