# BAG1 import: Heat character (model, anims, dance grid, fever, voices)

## Resumen rápido
Importación BAG1 Heat a BAG2JP. Estado: completado con adaptaciones documentadas.

## Log de progreso
- **2026-10-29**: Formato de modelo resuelto, Heat renderiza y danza
- **2026-10-30**: Slots de animación, beanie, fever
- **2026-10-31**: Anunciador de victoria y feedback de popup

## Estado actual ✅
- Modelo: Conviertido vía `tools/bag1import/model_bag1_to_bag2.py`
- Animaciones: 84 BAG1 → 101 slots BAG2 (remapping completado)
- Fever: Tipos solo y duet mapeados
- Beanie: Parche DBI aplicado (`patch_heat_dbi.py`)
- Sonidos: Bancos remapeados (0x1006 → voz japonesa)
- 2P Autoplay: Verificado (combos, especiales, poses)

## Adaptaciones documentadas
- **BAG1 cue 0x1006** (step sound) → BAG2 voz japonesa
- **BANCO 1** (cues 0x1000+) → voces + SFX fired por anim events
- **BAG2 banco 3** (006, p2 005) → announcer para stage intro
- **Costume B**: Colores BAG1 2P, mapeo DBI necesario
- **Fever types**: Type 0x8005E6C0 (1 solo, 2 duet)

## Própendientes
- Grid de danza: 3 edges no optimizados (deferido por owner 2026-10-31)
- Animaciones roles: Algunas adaptaciones documentadas pero no reclamadas como originales BAG1

## Referencias rápidas
- `CHARACTER_IMPORT.md` - Manual canonical
- `NOTES.md` - Índice actual
- `_work/current-state.json` - Estado compacto
- `IMPORT_STANDARD.md` - Guía de tarea estándar