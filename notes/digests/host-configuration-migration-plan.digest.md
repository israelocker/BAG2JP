---
id: host-configuration-migration-plan-digest
title: "Configuración central: ampliación de auditoría y migración"
tags: ["digest", "plan", "config"]
summary: "Plan propuesto de auditoría semántica y migración por consumidores; barrido automático de 471 archivos, lote workflow/report autorizado WIP, resto pendiente de aprobación."
related: ["plans/pending/host-configuration-migration.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "plans/pending/host-configuration-migration.md"
source_sha256: "794ecaef3bf44aa829aa465f2d790efd8aef76facd2ecc988b09326cc505d41b"
---

# Ampliación de configuración central

- Owner pidió abarcar todos los archivos de desarrollo y explicitar el estándar
  y significado de claves para reutilización. La regla documental aplica desde ahora.
- Migración ampliada propuesta, no aprobada aún. Workflow/report sí autorizado,
  con 83 tests dirigidos verdes en WIP; no cerrado ni certificado por esa cifra.
- Inventario por archivo/hash: 471 versionados; señales automáticas de rutas de
  máquina/relativas, entorno, defaults y constantes nativas. No equivale a revisión
  semántica ni a una lista de defectos confirmados. No rastreados se preservan.
- S1: cerrar workflow/report (guardas/work_root, overlay, audio opcional, build fijo,
  métricas y equivalencia). Bash instalado fija árbol/toolchain: no fingir migración.
- S2: auditoría semántica por familia y checker con baseline/excepciones justificadas;
  ningún archivo sin disposición y regresión causal ante nuevos hardcodes.
  S2a (análisis) puede continuar sin otra aprobación; S2b (código) espera el plan.
- S3: versus y PowerShell; S4: captura/FFmpeg/referencias; S5: importadores/perfiles;
  S6: herramientas de paquetes/instalador; S7: bootstrap/externos y cierre.
- Lotes pequeños con tests/diccionario/operaciones/consumidores reales, Goldfish y
  checkpoint. No nuevo parser por lenguaje, duplicación de valores ni fallback oculto.
- No convertir hechos nativos o gates en ajustes; no reescribir historia/releases,
  terceros o settings. Externos requieren inventario propio y permiso adicional para
  cambios instalados; sin build/deploy/partida/publicación implícitos.
- Claves exactas y lectores pendientes se determinan antes de cada sub-lote;
  decisiones de autoridad/contrato/permisos no se resuelven silenciosamente.
