---
id: host-configuration-migration-plan-digest
title: "Configuración central: ampliación de auditoría y migración"
tags: ["digest", "plan", "config"]
summary: "S1/S3a/S3b entregados host; S4a consumidor en cierre host, después S4b/S5–S7/S2b. Sin build/deploy del runtime, captura ni partida."
related: ["plans/pending/host-configuration-migration.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "plans/pending/host-configuration-migration.md"
source_sha256: "aa3bd012ef9afdff927dd031227dca2975000d36c398358d5a0efdb983b93ddb"
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
- S2a familia harness auditada por hash (nav parcial, global 471 pendiente); migrar
  la API coherentemente con ajustes por ejecución, no quitar globals sin sus lectores.
- Preparación S3: siete `harness.*` (deadlines 25/35/40/420 s, tope 86400;
  hold/gap/fade 100 ms/350 ms/1.3 s observados y bloqueados, sin override local).
   Consumidos por S3a (108 harness + 113 workflow OK, 31 mutantes listados).
   Goldfish no es aceptación ni permiso de despliegue; ver límites en system_config.
- S3b: tres vistas PS usan JSON del resolver con destinos guardados, identidad/PID
   y parámetros conservados; helpers explícitos preceden al TOML, padre/hijo fijan
   inputs/archivos/destinos. Goldfish A/B con hallazgos corregidos; pruebas y mutantes
   posteriores: 19 vistas + 113 workflow + 108 harness OK, 24 mutantes en copias;
   sin aceptación en juego ni segunda revisión. Siguiente S4a (solo host).
- S4a-prep separa contrato (10 defaults + 3 rutas, sin operación activa) del consumidor
  aún intacto. 119 workflow + 55 recording OK, 37 mutantes; Goldfish A/B con hallazgos
  corregidos por pruebas, sin segunda revisión.
  Consumidor S4a posterior: settings por ejecución y operaciones condicionales,
  CLI/entorno con provenance y guardas de salidas/aliases; 73 recording + 119 workflow
  + 108 harness OK, 28 mutantes en copias. Goldfish/estado final en fuente canónica;
  no avanzar a S4b antes de cerrar esta verificación host.
- S3: versus y PowerShell; S4: captura/FFmpeg/referencias; S5: importadores/perfiles;
  S6: herramientas de paquetes/instalador; S7: bootstrap/externos y cierre.
- Lotes pequeños con tests/diccionario/operaciones/consumidores reales, Goldfish y
  checkpoint. No nuevo parser por lenguaje, duplicación de valores ni fallback oculto.
- No convertir hechos nativos o gates en ajustes; no reescribir historia/releases,
  terceros o settings. Externos requieren inventario propio y permiso adicional para
  cambios instalados; sin build/deploy/partida/publicación implícitos.
- Claves exactas y lectores pendientes se determinan antes de cada sub-lote;
  decisiones de autoridad/contrato/permisos no se resuelven silenciosamente.
