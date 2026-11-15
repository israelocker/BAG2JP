---
id: host-configuration-migration-plan-digest
title: "Configuración central: ampliación de auditoría y migración"
tags: ["digest", "plan", "config"]
summary: "Plan aprobado de migración host: S1 workflow/report entregado con guardas/overlay/equivalencia; auditoría semántica/checker y demás familias aún pendientes de ejecución."
related: ["plans/pending/host-configuration-migration.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "plans/pending/host-configuration-migration.md"
source_sha256: "0591fcc94ab11f436ae123d071b965026b1a1888916b21fb3611a4c986012217"
---

# Ampliación de configuración central

- Owner pidió abarcar todos los archivos de desarrollo y explicitar el estándar
  y significado de claves para reutilización. La regla documental aplica desde ahora.
- Plan ampliado aprobado con «Si continúa» el 2026-11-15; ejecución inline, sin
  cambios externos, builds, partidas o despliegues implícitos.
- Inventario por archivo/hash: 471 versionados; señales automáticas de rutas de
  máquina/relativas, entorno, defaults y constantes nativas. No equivale a revisión
  semántica ni a una lista de defectos confirmados. No rastreados se preservan.
- S1 entregado: work_root y guardas de logs/sheet/build; overlay absoluto al child,
  Python/probe opcionales según operación; script fijo inspeccionado sin ejecutarlo.
  101 pruebas dirigidas, 103 workflow discovery, 8 mutantes muertos y Goldfish aplicado.
  Prueba real workflow→report leyó logs existentes, no fue una nueva partida.
- S2: auditoría semántica por familia y checker con baseline/excepciones justificadas;
  ningún archivo sin disposición y regresión causal ante nuevos hardcodes.
  Ambos autorizados; S2b espera disposiciones semánticas de S2a, no otro gate humano.
- S2a en curso: primer mapa del harness encuentra tres lectores de producción que
  capturan/leen globals y dos módulos de tests; migrar la API coherentemente, no
  quitar globals sin trazar lectores. Faltan secciones de selección/finish y lectores.
- S3: versus y PowerShell; S4: captura/FFmpeg/referencias; S5: importadores/perfiles;
  S6: herramientas de paquetes/instalador; S7: bootstrap/externos y cierre.
- Lotes pequeños con tests/diccionario/operaciones/consumidores reales, Goldfish y
  checkpoint. No nuevo parser por lenguaje, duplicación de valores ni fallback oculto.
- No convertir hechos nativos o gates en ajustes; no reescribir historia/releases,
  terceros o settings. Externos requieren inventario propio y permiso adicional para
  cambios instalados; sin build/deploy/partida/publicación implícitos.
- Claves exactas y lectores pendientes se determinan antes de cada sub-lote;
  decisiones de autoridad/contrato/permisos no se resuelven silenciosamente.
