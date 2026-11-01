# bag1-character.md Digest

**Source:** `notes/bag1-character.md` (31 KB, 227 lines)

## Resumen
Documentación completa de la importación de Heat (personaje BAG1) a BAG2JP. Cubre modelo, animaciones, fever, voces, 2P autoplay, character select popup, versiones side-by-side, victoria announcer, y combat acceptance.

## Secciones Principales

| Sección | Fecha | Estado | Puntos Clave |
|---------|-------|--------|--------------|
| BAG1 Heat: model format solved | 2026-10-29 | ✅ | Modelo convertido, 24 meshes + 14 type-4, crash resuelto |
| BAG1 Heat: animation slots, beanie, fever | 2026-10-30 | ✅ | 84→101 slots, beanie patch, fever mapping, sound remap |
| Two-player autoplay | 2026-10-30 | ✅ | Mode 2 CPU timing, no attacks, verificado |
| Character select popup | 2026-10-30 | ✅ | Version + costume per player, mirror rule |
| BAG1 and BAG2 versions side by side | 2026-10-30 | ✅ | Alt entries, version routing, sound rebase |
| Heat victory announcer | 2026-10-31 | ✅ | Cue 0x1007 preserved, preserve_announcer.py |
| BAG1 native Dance View reference | 2026-10-31 | ✅ | Audit roles: TIRED→CAUGHT, GUARD→HIT1, etc |
| Complete Heat animation comparison | 2026-10-31 | ✅ | 84 sources, 404 checks, 25 direct equivalents |
| Heat animation-role experiment | 2026-10-31 | ⚠️ | Adaptations: GUARD=DODGE, REFLECT=ATTACK2, etc |
| Local mixed-version combat acceptance | 2026-10-31 | ✅ | Owner approved, 8 inputs, 9 outcomes |

## Hallazgos Críticos (para reusar)

### Modelo
- BAG1 000+001 → BAG2 via `model_bag1_to_bag2.py`
- Converter probado: stock BAG2 Heat + Strike + BAG1 Heat = exact end
- Texturas: BAG1 pack 004/005/006 → BAG2 slots 002/003/004

### Animaciones
- Request tables: BAG2 FUN_8002a090 / BAG1 FUN_80030090
- `tools/bag1import/reqmap.py` prints request→slot for both
- Fever type 0x8005E6C0 (1 solo, 2 duet)
- Remapping: `anim_remap.py` 101 slots BAG2 order

### Beanie/Floating Head
- BAG1: head 12 + beanie 13
- BAG2: extra chest bone 12, head 13
- Patch: `patch_heat_dbi.py` `sb v0,0xd(t8)` → `sb v0,0xc(t8)`

### Sonidos
- BAG1 bank 1 (005/007 cues 0x1000+) → voices + SE
- BAG2 bank 3 (006, p2 005: 0x3000 name call) → announcer
- Solo bank 1 swapped (BAG1 English 007)
- Cue IDs kept; hand-swap effects 1-6 work (same hand bones)

### 2P Autoplay
- p1_2p / p2_2p options (default off; exp install: p2_2p on)
- Mode 2 uses register hooks, no CPU attacks
- Verified: BAG1 Heat vs BAG1 Heat full match

### Character Select Popup
- Circle = costume A, Triangle/Circle = costume B
- Version select: Circle/Triangle on selectable char
- Mirror: same char+costume → later pick gets costume ^ 1

### Version Routing
- `bag2jp.bag1_versions` rewrites RAM tables every vblank
- Heat = char id 0: packs 59/60/131/132, models 95/96/167/168
- Online: M_PICK (version), M_CONTENT (alt-entry hash)
- Verified 2-PC same session

### Victory Announcer
- JP table 0x80051424, Heat cue 0x1007
- `preserve_announcer.py` merges stock name into VAB
- Opt-in for Heat in build_heat_test.sh

### Dance View Audit
- BAG1 VIEW.DBI: TIRED index54=req124=anim69
- BAG2 system/008.dbi: TIRED index71=req123=slot78
- **Request numbers ≠ semantic roles** (critical finding)

## Adaptaciones Experimentales (2026-10-31)

| BAG2 Role | BAG1 Source | Event Adaptado | Nota |
|-----------|-------------|----------------|------|
| TIRED | TIRED69 (no CAUGHT70) | - | Exact correction |
| GUARD | DODGE65 | (1,1,902) | Adaptation |
| REFLECT | ATTACK2 64 | (1,1,903) no type16 | Adaptation |
| POSE1 | ATTACK2 held posture | - | Adaptation |
| POSE2 | WAIT60 hold | - | Adaptation |
| MISS1..6 | HIT1/HIT2/HIT3 x2 | - | Replacing tired loops |

## Próximos Pendientes (de owner 2026-10-31)
1. **Deferido**: 3 nonadjacent dance-grid edges (no missing/broken)
2. **Pendiente**: Actual guard/reflect vs attacks interactions
3. **Pendiente**: Subjective review documented adaptations
4. **Pendiente**: Fresh online/mixed-version regression

## Referencias Rápidas
- Tools: `tools/bag1import/` (model_bag1_to_bag2.py, anim_remap.py, patch_heat_dbi.py, build_heat_test.sh, etc)
- Evidence: `_work/animation-policy/`, `_work/bag1_heat_test_*.png`
- IMPORT_STANDARD.md para guía de tarea estandarizada