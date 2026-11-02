---
id: character-pipeline-clean
title: "Shared BAG1 → BAG2JP Character Pipeline - Clean Reference"
tags: ["workflow", "character", "pipeline", "shared", "reference"]
summary: "Esencia del pipeline compartido de importación BAG1 a BAG2JP: etapas, reglas y comandos. Sin detalles de test ni referencias a entornos de desarrollo anteriores."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-31"
updated: "2026-11-01"
---

# Shared BAG1 → BAG2JP Character Pipeline - Clean Reference

## Estándar del Owner (2026-10-31)
Un proceso compartido, perfiles basados en datos, excepciones justificadas estrechamente. Sin forks por carácter.

## 5 Etapas del Pipeline

| Etapa | Propósito | Autoriza aceptación de gameplay |
|-------|-----------|--------------------------------|
| 1. Inventory | Verificar sources, extraer modelo/animación/eventos, validar profile | ❌ No |
| 2. Contract | Asignar roles por significado y duración musical | ❌ No |
| 3. Sequence audit | Validar variantes dependientes de predecessor, continuidad | ❌ No |
| 4. Experiment | Regenerar assets cambiados, actualizar online identity | ❌ No |
| 5. Acceptance | Verificar poses/steps/attacks, flujo completo de juego | ✅ Sí |

**Regla crítica**: Inventory y contract no autorizan aceptar gameplay. Profile en stage verified requiere evidencia de gameplay con hash y sin excepciones pendientes.

## Hechos Compartidos vs Datos por Carácter

| Tipo | Ubicación | Contenido |
|------|-----------|-----------|
| Compartido | `tools/bag1import/contracts/bag1-usa-bag2jp.roles.json` | Dispatch base facts, game/version-specific |
| Por carácter | `tools/bag1import/profiles/<slug>.json` | IDs, source paths, capabilities, exceptions |

**Regla crítica**: ID/request ≠ rol semántico. Algunos labels, duración y orden difieren entre juegos. Unknown roles permanecen unresolved.

**Announcer**: Capability de carácter presente en ambos juegos. Imports sin esta capability mantienen announcer genérico.

## Reglas de Contrato de Animación

Grupar requests en: normal dance, special (por beat length), pose, intro, attack, defense, reaction, tired, fall/recovery, win/loss, fever.

**Prioridad**: Identidad semántica > duración musical > eventos necesarios > similitud de pose.

**Normalizar antes de medir**: Skeleton, scale, root direction, beat phase.

**Reportar siempre**: Todas las entradas source y target, duplicados, motions sin uso, contrapartes faltantes, entradas vacías, repeticiones deliberadas.

## Perfiles de Carácter

**Regla**: Perfiles son datos únicamente (sin código ejecutable ni instrucciones de deploy).

**Campos requeridos**: schema, character, display_name, source_character_id, target_character_id, stage, exception_assessment, source_animation_list, game_catalog, reference_runtime, capabilities, exceptions, assets, validation_evidence.

**Capabilities determinan acceptance matrix**: Usar solo capabilities verificadas. No copiar el set de Heat a otro carácter.

## Excepciones

- Requieren: character scope, rationale, status
- Status válidos: pending, verified
- Verified exceptions requieren: evidencia con hash inalterado
- IDs únicos, scope al carácter
- Nunca generalizar silenciosamente: beanie/skeleton patch, special attack handler

## Comandos Útiles

```powershell
# Inicializar profile (cambiar solo argumentos de datos)
py -3.13 tools/bag1import/character_workflow.py init-profile `
  --character <slug> `
  --profile tools/bag1import/profiles/<slug>.json `
  --source-archive <unpacked-model.dfs> `
  --source-list _work/character_inventory/<slug>/001.bin `
  --runtime <native-reference.exe> `
  --catalog tools/bag1import/contracts/bag1-usa-bag2jp.roles.json

# Validar profile existente
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile <profile.json>

# Generar plan de importación
py -3.13 tools/bag1import/character_workflow.py plan --profile <profile.json>

# Generar matriz de aceptación
py -3.13 tools/bag1import/character_workflow.py acceptance-plan --profile <profile.json>

# Verificar cache de referencia
py -3.13 tools/bag1import/character_workflow.py cache-check --profile <profile.json> --cache <cache.json>

# Registrar cache de referencia
py -3.13 tools/bag1import/character_workflow.py cache-record --profile <profile.json> --cache <cache.json> --evidence <video.mp4> --evidence <timeline.json>
```

## Estado por Carácter (Referencia)

| Carácter | Etapa | Target ID | Validado en gameplay |
|----------|-------|-----------|---------------------|
| Heat | Candidate | Resuelto | Sí |
| Strike | Inventory | No resuelto | No |

**Regla**: Nunca reclamar un carácter como importado solo porque existe un profile.

## Herramientas de Recursos

- Extracción y hashes: scripts determinísticos locales vía MCP
- MIPS listing: Capstone instalado
- Decompilación masiva: Ghidra headless (proyecto read-only separado)
- Video/capture: FFmpeg/ffprobe + test harness
- Anotación masiva: local-vibes/local-llm (un modelo RTX 3090 a la vez)

## Limitaciones Conocidas

- Graph optimizer automático: no implementado aún
- General assignment generation: no implementado aún
- Heat adapters son legacy especializados, NO generalizables a otros caracteres
- Second character conversion y gameplay aún no verificados
