---
id: reusable-import-process-audit
title: "Reusable BAG1 import process audit"
tags: ["bag1", "documentation", "audit", "plan"]
summary: "Owner-approved audit of reusable import processes, retained evidence and Ghidra connectivity; no runtime changes."
related: ["notes/documentation-audit.md", "CHARACTER_IMPORT.md"]
created: "2026-11-05"
updated: "2026-11-06"
doc_kind: plan
---

# Reusable BAG1 import process audit

Status: documentation verified; Ghidra validation blocked by unavailable backend.
Approved by owner («Si, procede»).
Owner request: auditoría exhaustiva y documentación de procesos realmente probados
para futuras importaciones de personajes, efectos, escenarios, canciones y endings;
comprobar Ghidra MCP al terminar la documentación.

## Objective and acceptance

Actualizar las fuentes canónicas con recetas trazables al código y evidencia
conservada. Cada proceso debe identificar inputs/región, herramientas y funciones,
comandos contrastados, outputs, dependencias, restauración, pruebas, límites y
condiciones de reutilización. No equiparar existencia, tests host o ejecución
histórica con aceptación visual/audio o compatibilidad entre personajes.

Cobertura exhaustiva significa contabilizar todos los procesos propios encontrados
en fuentes, scripts, perfiles, plugins y evidencias del port, con exclusiones
explícitas; no certificar cada archivo de terceros ni volver a jugar todas las
combinaciones. No declarar completo el inventario hasta contrastar ambos árboles.

## Baseline

- Canonical: `D:/Dev/Recomp/BAG2JP`; build tree y experimental según AGENTS.
- HEAD observado: `6dea3c1`; rama `main`, workflow local conservado.
- Cambios previos: conservar todos; baseline en el log de preflight.
- Preflight aprobado: `_work/workflow/20261106T030832757825Z-reusable-process-audit-plan/`.
- Drift observado: `mods-src/bag2jp.feature.netsync/src/bag2jp_netsync.c`.
  Diagnóstico, no permiso para sincronizarlo.
- Auditoría anterior: `notes/documentation-audit.md`, 2026-11-02;
  sus comprobaciones no recertifican cambios posteriores.
- Fecha local de la solicitud: 2026-11-05; timestamps UTC pueden ser 2026-11-06.

## Method

Clasificar cada afirmación como: probado en juego (alcance exacto), probado host,
evidencia histórica, experimental/rechazado, o sin evidencia suficiente.
Vincular hashes de inputs/runtime cuando existan; si faltan, declarar la limitación.
Registrar contradicciones sin elegir automáticamente la nota más reciente.
Leer archivos grandes por digest vigente o secciones necesarias. Los scripts de
`_work` ligados a hashes concretos no se convertirán en comandos genéricos.

## Phases

| Step | Size | Scope and likely files | Acceptance / verification | Blocked by |
|---|---|---|---|---|
| 1 | M | Inventario de procesos propios: `tools/bag1import`, `tools/test`, `tools/re`, `mods-src`, `patches`, perfiles y evidencia pertinente de `_work`; lectura del build tree. Salida `_work/process-audit/coverage.json` | Inventario determinista con categorías, exclusiones, rutas y estado de revisión; cotejo de archivos y Git sin alterar fuentes | Approval |
| 2 | M | Personajes/modelos/texturas/animaciones/DFS/payload: `CHARACTER_IMPORT.md`, `notes/character-pipeline.md`, `notes/character-alternate-entries.md`, `notes/strike-recovery.md`, `notes/bag1-character.md` | Matriz de procesos y evidencia; separar Heat/Strike, P1/P2 y trajes, adaptadores y fallos; contrastar funciones y tests de cada receta | 1 |
| 3 | S | Efectos/DBI/VRAM/callbacks: secciones correspondientes de `notes/bag1-character.md`, `notes/strike-recovery.md`, `notes/bag1-stage-song.md` | Identificar guardas, región, direcciones originales, recursos compartidos, evidencia nativa y aceptación pendiente; no promover el efecto Heat sin revisión visual | 1 |
| 4 | M | Escenarios/cámaras/luces: `notes/bag1-stage-song.md`, perfiles de stages y porter (solo lectura de código) | Recetas Heat y Strike contrastadas; distinguir porter compartido de adaptaciones; preservar límites de región y pruebas reales | 1 |
| 5 | S | Canciones/charts/XA/FLAC/voces/SFX: `notes/bag1-stage-song.md`, notas de personajes | Documentar extracción, sincronía y cues con región/hash; escucha subjetiva no inferida de logs o SPU | 4 |
| 6 | S | Endings/créditos/selector/campaña: `notes/endings-view.md`, notas de personajes | Separar media, selección, créditos y campaña real; verificar qué recorridos tienen evidencia conservada y cuáles no | 1 |
| 7 | M | Build/staging/pruebas/recuperación: `notes/project.md`, `notes/character-import-testing.md`, `notes/documentation-audit.md`, índices/digests afectados | Comandos contrastados sin deploy; enlaces, hashes y regresiones documentales/host no invasivas. `py -3.13 tools/workflow/test_audit_docs.py`; `py -3.13 tools/workflow/audit_docs.py check --output D:/Dev/Recomp/BAG2JP/_work/process-audit/docs-check.json`; host discovery solo tras inspeccionar side effects | 2,3,5,6 |
| 8 | S | Ghidra MCP y cierre: ledger `notes/documentation-audit.md`, `_work/process-audit/`, punteros de estado pertinentes | Tras documentar, invocar `get_program_info` como primera llamada Ghidra, confirmar binario abierto y una consulta de lectura. Registrar error si no responde; comprobar o iniciar servidor existente con procedimiento local contrastado, sin cerrar sesiones ni instalar/actualizar herramientas | 7 |

Cada categoría tendrá cobertura explícita de procesos aceptados, fallidos y pendientes.
No ejecutar scripts de importación/deploy como si fueran probes de lectura.
Documentar solo opciones CLI confirmadas en el parser o mediante ayuda segura.

## Decisions and assumptions for approval

- Auditoría documental/técnica con evidencia existente y comprobaciones host seguras;
  no nueva campaña de pruebas del juego. Las lagunas quedan visibles, no resueltas
  cambiando código o inventando aceptación.
- Mantener una autoridad por tema; ampliar las notas existentes y su ledger, no
  generar un segundo manual que compita con ellas. Índices solo enlazan.
- Usar scripts deterministas para inventario/hashes. Modelos locales solo si hay
  trabajo mecánico acotado que lo justifique; una GPU y sin competir con el juego.
- No adoptar una nueva rama, rebase, remote, tickets ni publicación.
- Si Ghidra requiere instalar componentes, actualizar o modificar configuración
  externa no cubierta por el procedimiento existente, registrar el bloqueo y pedir
  autorización antes de esa ampliación.

## Always / Never

- Always: conservar cambios, partidas, settings, sesiones activas y originales;
  distinguir evidencia fresca, histórica y ausencia de evidencia.
- Never: cambiar comportamiento del juego, regenerar payloads, desplegar, modificar
  estable, reparar drift ajeno, certificar visual/audio por tests host o generalizar
  adaptadores sin prueba de otro perfil.

## Progress

| Phase | Status |
|---|---|
| Research / baseline / plan | Baseline leído, preflight pasado y aprobación explícita recibida |
| 1 inventory | Both trees inventoried and compared; local scripts explicitly historical, exclusions recorded |
| 2–6 processes | Canonical recipes corrected; evidence metadata contrasted; missing campaign/subjective acceptance explicit |
| 7 verification | Passed: 155 host tests, 9 Ending View C cases, 32 checker tests; 113 documents, 0 errors, 9 historical warnings; digest hashes and focused review passed |
| 8 Ghidra and close | Probed after documentation: BACKEND_UNAVAILABLE at localhost:8080, no Java/Ghidra process. Read query blocked until owner opens project/plugin; no configuration changes |

## Resume point

Documentary results and limits: `notes/documentation-audit.md`. Do not repeat
unchanged host tests. When Ghidra is open with its MCP backend, call
`get_program_info` first, verify the intended program/region and perform one bounded
read query. Only then close/archive this plan. Actual campaign completion, human
listening and remaining visual acceptance are separate gameplay work, not claims
made by this audit.
