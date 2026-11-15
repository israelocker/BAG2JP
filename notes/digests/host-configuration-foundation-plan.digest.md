---
id: host-configuration-foundation-plan-digest
title: "Plan de configuración host: base y piloto"
tags: ["digest", "plan", "config"]
summary: "Cinco tareas de base/resolución/diccionario y checker de lectura; plan pendiente de aprobación y método, sin implementación."
related: ["plans/pending/host-configuration-foundation.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "plans/pending/host-configuration-foundation.md"
source_sha256: "59c2473f107aca80b7112a690c7187e31c6e1971f36b4e2376c0559e31cdb68e"
---

# Primera entrega host

- Especificación escrita aprobada; el owner debe revisar este plan y elegir
  ejecución antes de código. Plan canónico, interfaces y tests en la fuente.
- Tarea1: TOML común/local, esquema1/overlay por clave, resolver inmutable y
  validación tipada; jobs2/pins preservados, raíz independiente de CWD.
- Tarea2: rutas protegidas/aliases, JSON para PowerShell y conversión Windows→WSL;
  sin parser duplicado, ejecución de strings ni permiso implícito de acción.
- Tarea3: diccionario consistente con FIELDS, native facts por referencia, archivo
  local ignorado creado sin sobrescribir datos previos. Consumidores futuros
  marcados como tales; no schemas de perfil cambiados.
- Tarea4: piloto `check_payload_manifest.py`, CLI y OK/FAIL/exitcodes conservados;
  default deriva raíces y `--package` explícito no exige defaults sin usar.
- Tarea5: suites host/fixtures, checks documentales, Goldfish por checkpoint,
  registro y commit local. No build, partida, deploy, assets o saves modificados.
- Inventario textual48archivos/95matches no equivale a48consumidores activos.
  Workflow/harness/captura/importadores van en planes posteriores: Bash instalado
  tiene root/toolchain fijos; no fingir su migración con un cambio solo en Python.
- No se ejecutaron tests de componentes futuros: aquí solo se comprueba el plan.
