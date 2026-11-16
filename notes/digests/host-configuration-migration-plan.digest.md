---
id: host-configuration-migration-plan-digest
title: "Configuración central: ampliación de auditoría y migración"
tags: ["digest", "plan", "config"]
summary: "Inventario conciliado: 495 archivos, 21 grupos con archivos/alcances/evidencia; 9 entregas host históricas, no porcentaje de esfuerzo. Calendario pendiente de baseline y capacidad."
related: ["plans/pending/host-configuration-migration.md", "system_config.md"]
created: "2026-11-15"
updated: "2026-11-16"
doc_kind: digest
source: "plans/pending/host-configuration-migration.md"
source_sha256: "6e1793654b02f3151a20cb44cc86f3c75e728d7b6e63c7cff6dd810c6a72443e"
---

# Ampliación de configuración central

- Control conciliado en el mismo inventario: 471 originales conservados +24 nuevos,
  495 asignaciones únicas; 9 alcances host entregados y 12 grupos restantes.
  `files[].progress`, `added_files[].progress`, `reconciliation.lots` contienen
  archivos/estado/parciales/commit/evidencia/deriva. No reiniciar lotes cerrados.
- 22/471 consumidores con disposición acotada =4,67 %, no avance global;
  19 soporte y 430 sin revisión consolidada. 30 archivos cambiados no miden cierre.
  9/21=42,86 % tampoco pondera esfuerzo. ~60 % retirado. Fecha límite confirmada:
  17-11-2026 a las 12:00 del mediodía, America/Lima (UTC−5); lunes hasta las 22:00.
  Martes 09:00–12:00 (3 horas). Faltan estimaciones por sublote para contrastar
  viabilidad. Datos desconocidos quedan nulos; no se garantiza todo el alcance.
- Deriva de dependencias exige análisis antes de elegir un check, no repetición
  automática. Conciliación documental sin suites nuevas ni implementación S5b.
- Sublote Gas-O builder cerrado en b1b585c/1ca68e5: extracción/config/perfil/stock/
  motions/salidas, anunciador independiente y snapshot compartido. V10 histórico:
  12 lectores +120 workflow +7 HUD, 17 mutantes; Goldfish sin segunda revisión.

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
   sin aceptación en juego ni segunda revisión. S4a se entregó después, solo host.
- S4a-prep separa contrato (10 defaults + 3 rutas, sin operación activa) del consumidor
  aún intacto. 119 workflow + 55 recording OK, 37 mutantes; Goldfish A/B con hallazgos
  corregidos por pruebas, sin segunda revisión.
  Consumidor S4a posterior: settings por ejecución y operaciones condicionales,
  CLI/entorno con provenance y guardas de salidas/aliases; 73 recording + 119 workflow
  + 108 harness OK, 28 mutantes en copias. Goldfish/estado final en fuente canónica;
   checkpoint consumidor posterior `1ed6f81`; S4b nativo `18d0c51` y auditoría
   bag1native `b60449f`, sin afirmar migración de todos los lectores pendientes.
- S5a workspace: plan/prepare/state, 38 readers (37 OK, 1 omitido por
   privilegio file-symlink), 120 workflow y 17 mutantes por aserción. Reutiliza tres
   claves; preserva inputs/hashes nativos. Goldfish A/B CON HALLAZGOS corregidos,
     sin segunda revisión; evidencia histórica del piloto. Heat cerrado host con
     enlaces/inputs directos y scoring estricto tras Goldfish: V6 32 lectores,
     120 workflow, 7 HUD, sintaxis Bash OK y 34 mutantes por aserción sin ERROR;
     hashes iguales, sin segunda revisión. Rutas de perfil/cache/init de S5b siguen
     pendientes. No adaptadores ni paquetes ejecutados.
- S3: versus y PowerShell; S4: captura/FFmpeg/referencias; S5: importadores/perfiles;
  S6: herramientas de paquetes/instalador; S7: bootstrap/externos y cierre.
- Lotes pequeños con tests/diccionario/operaciones/consumidores reales, Goldfish y
  checkpoint. No nuevo parser por lenguaje, duplicación de valores ni fallback oculto.
- No convertir hechos nativos o gates en ajustes; no reescribir historia/releases,
  terceros o settings. Externos requieren inventario propio y permiso adicional para
  cambios instalados; sin build/deploy/partida/publicación implícitos.
- Claves exactas y lectores pendientes se determinan antes de cada sub-lote;
  decisiones de autoridad/contrato/permisos no se resuelven silenciosamente.
