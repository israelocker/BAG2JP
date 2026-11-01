---
id: character-pipeline-optimized
title: "Character Pipeline Optimized"
tags: []
summary: "Auto-generated frontmatter - please review"
related: []
created: 2026-11-01
updated: 2026-11-01
---
# Shared BAG1 → BAG2JP Character Pipeline — Optimized Summary

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

## Hechos Compartidos vs Datos por Carácter

- **Compartidos**: `tools/bag1import/contracts/bag1-usa-bag2jp.roles.json` (dispatch base, game-specific)
- **Por carácter**: `tools/bag1import/profiles/<slug>.json` (IDs, paths, capabilities, exceptions)
- **Regla**: ID/request ≠ rol semántico. Algunos labels/duración/orden difieren entre juegos.
- **Announcer**: Capability de carácter presente en ambos juegos. Sin ella → announcer genérico.

## Reglas de Contrato de Animación

Grupar requests en: normal dance, special (por beat length), pose, intro, attack, defense, reaction, tired, fall/recovery, win/loss, fever.

Preferir: identidad semántica, duración musical, eventos necesarios > similitud de pose.

Normalizar antes de medir: skeleton, scale, root direction, beat phase.

## Comandos Útiles

```powershell
# Inicializar profile (todos los caracteres, cambiar solo datos)
py -3.13 tools/bag1import/character_workflow.py init-profile `
  --character <slug> `
  --profile tools/bag1import/profiles/<slug>.json `
  --source-archive <unpacked-model.dfs> `
  --source-list _work/character_inventory/<slug>/001.bin `
  --runtime <native-reference.exe>

# Validar profile
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile <profile.json>

# Plan de importación
py -3.13 tools/bag1import/character_workflow.py plan --profile <profile.json>

# Plan de aceptación
py -3.13 tools/bag1import/character_workflow.py acceptance-plan --profile <profile.json>

# Cache check
py -3.13 tools/bag1import/character_workflow.py cache-check --profile <profile.json> --cache <cache.json>

# Cache record
py -3.13 tools/bag1import/character_workflow.py cache-record --profile <profile.json> --cache <cache.json> --evidence <video.mp4> --evidence <timeline.json>
```

## Estado por Carácter

| Carácter | Estado | Target ID | Validado en gameplay |
|----------|--------|-----------|---------------------|
| Heat | Candidate | Resuelto | Sí |
| Strike | Inventory | No resuelto | No |

## Herramientas de Recursos

- Extracción/hashes: scripts determinísticos locales vía MCP
- MIPS listing: Capstone instalado
- Decompilación masiva: Ghidra headless (proyecto read-only separado)
- Video/capture: FFmpeg/ffprobe + test harness
- Anotación masiva: local-vibes/local-llm (un modelo RTX 3090 a la vez)
- Docs externas: Context7 (solo referencia, no autoridad local)

## Notas Importantes

- No clonar el pipeline de Heat para otro carácter
- No generalizar patches específicos de Heat (beanie, skeleton, special attacks)
- Excepciones: requieren scope de carácter, razón y status
- Verified exceptions requieren evidencia con hash inalterado
- Un cache hit es evidencia visual, NO aceptación de gameplay
- No reusar pilot fallido como evidencia
- Restaurar byte-exact baseline después de tests