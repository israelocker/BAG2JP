---
id: bag1-character-heat-clean
title: "BAG1 Import: Heat Character - Clean Reference"
tags: ["bag1", "import", "heat", "character", "reference"]
summary: "Esencia de la importación de Heat BAG1 a BAG2JP: modelo, animaciones, fever, voces y adaptación. Sin detalles de test ni rutas personales."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-29"
updated: "2026-11-01"
---

# BAG1 Import: Heat Character - Clean Reference

## Resumen Ejecutivo
Importación de BAG1 Heat a BAG2JP. Estado: completado con adaptaciones documentadas. Este archivo contiene solo la información esencial para reusar el proceso en otro personaje.

## Log de Progreso
- **2026-10-29**: Modelo convertido, Heat renderiza y danza
- **2026-10-30**: Slots de animación mapeados, beanie parcheado, fever mapeado, sonidos remapeados
- **2026-10-31**: Anunciador de victoria, roles de animación auditados, aceptación de combate mixto verificada

## Estado Actual ✅
| Elemento | Estado | Notas |
|----------|--------|-------|
| Modelo | ✅ | 24 meshes + 14 type-4 nodes, convertido vía `model_bag1_to_bag2.py` |
| Animaciones | ✅ | 84 BAG1 → 101 slots BAG2, remapping completado |
| Fever | ✅ | Tipos solo y duet mapeados, cues muteados |
| Beanie/Cabeza flotante | ✅ | Patch DBI aplicado (`patch_heat_dbi.py`) |
| Sonidos | ✅ | Banco 1 swap (voces + SFX), banco 3 (announcer) se mantiene BAG2 |
| 2P Autoplay | ✅ | Verificado en modo 2 (sin ataques CPU) |
| Anunciador victoria | ✅ | Cue 0x1007 preservado vía `preserve_announcer.py` |
| Selector personaje | ✅ | Versión + costume por jugador, mirror rule implementada |
| Routing versiones | ✅ | RAM tables reescritas cada vblank |

## Adaptaciones Documentadas (Heat-specific, NO generalizar)
| BAG2 Rol | BAG1 Fuente | Evento Adaptado | Nota |
|----------|-------------|-----------------|------|
| TIRED | TIRED69 | - | Corrección exacta (no CAUGHT70) |
| GUARD | DODGE65 | (1,1,902) | Adaptación, no original BAG1 |
| REFLECT | ATTACK2 64 | (1,1,903) sin type16 | Adaptación |
| POSE1 | ATTACK2 postura final | - | Adaptación |
| POSE2 | WAIT60 hold | - | Adaptación |
| MISS1..6 | HIT1/HIT2/HIT3 x2 | - | Reemplaza 5 loops de tired |

**Regla crítica**: Números de request iguales ≠ roles semánticos iguales.

## Reglas Clave para Reusar en Otro Personaje
1. **Modelo**: BAG1 000+001 → BAG2 via converter. Nunca hacer file swap directo.
2. **Animaciones**: Request tables BAG1 FUN_80030090 vs BAG2 FUN_8002a090. Usar `reqmap.py`.
3. **Audio**: Solo banco 1 swap (BAG1 English 007). Banco 3 se mantiene BAG2.
4. **Costume B**: Colores BAG1 2P, requiere mapeo DBI específico.
5. **Versiones**: Routing por vblank, player-side entries siguen su versión.
6. **Online**: M_PICK (versión), M_CONTENT (hash alt-entry). No replay de popup entre PCs.

## Archivos de Herramienta
- `tools/bag1import/model_bag1_to_bag2.py` - Conversión modelo
- `tools/bag1import/anim_remap.py` - Remapping animaciones
- `tools/bag1import/patch_heat_dbi.py` - Patch beanie/huesos
- `tools/bag1import/reqmap.py` - Mapeo request→slot
- `tools/bag1import/build_heat_test.sh` - Build test mod
- `tools/bag1import/audit_animation_roles.py` - Auditoría roles animación

## Referencias Rápidas
- `CHARACTER_IMPORT.md` - Manual canónico completo
- `IMPORT_STANDARD.md` - Guía de tarea estándar
- `NOTES.md` - Índice actual
- `_work/current-state.json` - Estado compacto con `gaps`
