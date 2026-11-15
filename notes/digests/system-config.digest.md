---
id: system-config-digest
title: "Configuración host: autoridades y estado"
tags: ["digest", "config", "migration"]
summary: "Base/piloto y S1 workflow/report entregados; plan ampliado aprobado, auditoría semántica y demás lotes pendientes. No certifica migración global ni aceptación del juego."
related: ["system_config.md", "docs/data-dictionary.md", "plans/pending/host-configuration-migration.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "system_config.md"
source_sha256: "42032018c11cf00cb4567755c34381c945dd521dcc5c80036e6a5bd474025e42"
---

# Configuración: estado mínimo

- Autoridad: resolutor único `tools/workflow/project_config.py`, TOML común con
  defaults/política, local ignorado para ubicaciones verificadas, diccionario con
  significado/tipo/unidad/origen/validación/permisos/operaciones/consumidores.
- Base/piloto: `7fefc07` y `28fc1e9`; checker de manifiestos configurado, 4 copias.
- S1 (`46d528c`): workflow/report migran rutas/pins/WSL y contrastan jobs. Usan work_root y
  guardas de escritura para logs, sheets y destino build. Overlay absoluto al child,
  valores/orígenes/hashes en métricas; Python/probe opcionales según operación real.
- Bash instalado sigue fijo. Adaptador estricto de seis líneas, paths literales,
  árbol/jobs comprobados antes de lanzar build; no se ha modificado ni ejecutado.
- Verificación: 101 pruebas dirigidas, 103 workflow discovery, 8 mutantes en copias;
  ruta real workflow→report con logs existentes. No nueva evidencia de partida.
- Goldfish S1 encontró build sin guarda, sintaxis Bash no literal y carrera del WAV;
  corregidos RED→GREEN y tests antes enmascarados corregidos. Source tiene hashes,
  consultas y evidencias. Veredicto no es permiso de despliegue ni aceptación humana.
- 471 archivos versionados inventariados automáticamente, con hashes/procedencia.
  No equivalen a análisis semántico ni ausencia de hardcodes. S2 y demás familias
  pendientes; plan ampliado aprobado. Defaults numéricos legacy siguen candidatos.
- S2a parcial: GAME/WINSHOT/CATALOG del harness trazados; tres lectores de producción
  y dos tests dependen de exports actuales. No retirar globals rompiendo lectores;
  wrappers legacy no se borran por referencias obsoletas. No se ha ejecutado harness.
- Nuevo/modificado host sigue el estándar central; runtime, hechos PSX y guards
  conservan su autoridad. No tocar historia, releases, settings, saves o terceros.
- Límites: config no demuestra identidad de estable; TOCTOU no garantizado,
  POSIX no probado, locals alternativos no ignorados automáticamente.
