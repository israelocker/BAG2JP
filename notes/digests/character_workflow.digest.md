# character_workflow.py Digest

**Source:** `tools/bag1import/character_workflow.py` (358 lines, ~20 KB)

## Public Commands (CLI)

| Comando | Descripción | Argumentos requeridos |
|---------|-------------|----------------------|
| `init-profile` | Inicializar perfil de personaje | `--character`, `--source-archive`, `--source-list`, `--runtime` |
| `validate-profile` | Validar perfil existente | `--profile` |
| `plan` | Generar plan de importación | `--profile` |
| `status` | Ver estado actual | `--profile` |
| `acceptance-plan` | Ver casos de aceptación | `--profile` |
| `prepare` | Preparar workspace candidato | `--profile` |
| `cache-record` | Registrar cache de referencia | `--profile`, `--cache`, `--evidence` (multiple) |
| `cache-check` | Verificar cache | `--profile`, `--cache` |

## Funciones Principales (por rango de líneas)

| Función | Líneas | Propósito |
|---------|--------|-----------|
| `file_sha()` | 11-13 | SHA256 de archivo |
| `load_profile()` | 15-76 | Cargar y validar perfil (schema 1/2) |
| `motion_fingerprint()` | 78-111 | Hash de prefijos de movimiento (sin events) |
| `_atomic_write_json()` | 116-129 | Escritura atómica JSON |
| `_missing_schema2_gaps()` | 131-143 | Detectar gaps en schema 2 |
| `acceptance_cases()` | 145-169 | Generar matriz de aceptación |
| `character_plan()` | 171-182 | Plan completo con gaps/next_action |
| `write_state()` | 184-191 | Escribir `_work/character-import/.../state.json` |
| `prepare_workspace()` | 193-205 | Crear manifest candidato (no deploy) |
| `signature()` | 207-213 | Generar signature para cache |
| `record_cache()` | 215-250 | Registrar cache con evidencia |
| `check_cache()` | 252-263 | Verificar cache (hit/miss) |
| `init_profile()` | 265-312 | Inicializar perfil desde DFS archive |
| `main()` | 314-358 | CLI entry point |

## Reglas de Validación Críticas

### Profile Schema 1 (Inventario inicial)
- `character`: slug `[a-z0-9-]+`
- Campos requeridos: `source_animation_list`, `game_catalog`, `reference_runtime`
- `stage`: `inventory`, `contract`, `verified`

### Profile Schema 2 (Plan completo)
- Adicional: `display_name`, `capabilities`, `assets`, `target_character_id`
- `capabilities`: `costumes`, `versions`, `fever`, `stage`, `song`, `ending`, `shared_announcer_name`, `online_content`
- `assets`: dict con `file` y `sha256` (verificados contra disco)
- `stage`: `inventory`, `contract`, `candidate`, `verified`

### Excepciones
- `status`: `pending` o `verified`
- `verified` requiere `evidence: {file, sha256}`
- `pending` bloquea stage `verified`
- IDs únicos, scope al personaje

### Cache de Referencia
- Key: `signature()` = motion fingerprint + catalog/runtime/input SHA256
- Cache hit: todos inputs + evidencia sin cambios
- Cache miss: inputs cambiados, evidencia cambiada, o sin registro
- Atomic write con temp file

## Comportamiento de Estado

### write_state() genera:
```json
{
  "character": "...",
  "display_name": "...",
  "stage": "...",
  "status": "planned|candidate_created",
  "pending_exceptions": [...],
  "gaps": [...],
  "prepare_ready": bool,
  "next_action": "prepare|resolve_gaps",
  "acceptance_count": N,
  "updated_utc": "ISO8601"
}
```

### Gaps comunes detectados:
- `target_character_id` - target no asignado
- `contract_not_approved` - stage no en candidate/verified
- `exception_assessment` - assessment pendiente
- `pending_exceptions` - excepciones sin resolver
- `gameplay_evidence` - sin evidencia en verified
- `schema_2_required_for_plan` - schema 1 no tiene plan

## Matriz de Aceptación (capability-driven)

| Capability | Caso | Requerido |
|------------|------|-----------|
| - | inventory-validation | Siempre |
| - | model-sides-costumes | Siempre |
| - | game-flow | Siempre |
| - | song-end | Siempre |
| - | return-to-selection | Siempre |
| costumes | costume-selection | Sí |
| versions | mixed-version | Si online_content |
| fever | fever-solo | Siempre |
| fever | fever-duet | Si "duet" en fever |
| stage | stage-load | Sí |
| song | song-end | Sí |
| ending | ending-video-credits-return | Sí |
| shared_announcer_name | announcer-name | Sí |
| online_content | online-content-identity | Sí |

## Cache Behavior

1. **record_cache**: Escribe `{key: signature, evidence: [{file, sha256}]}` atómicamente
2. **check_cache**: 
   - `hit`: key coincide + evidencia intacta
   - `miss`: reason = `no_record` | `inputs_changed` | `evidence_changed`
3. **Protección**: No permite sobrescribir inputs, catalog, ROM, archivos JSON no-cache

## Uso Típico (Heat example)

```bash
# 1. Inicializar
py character_workflow.py init-profile \
  --profile _work/character-import/heat/profile.json \
  --character heat \
  --source-archive assets/archive/characters/heat/pack_a_p1.dfs \
  --source-list _work/bag1_assets/heat/anim_list.bin \
  --runtime _work/reference/runtime.bin \
  --catalog tools/bag1import/contracts/bag1-usa-bag2jp.roles.json

# 2. Validar
py character_workflow.py validate-profile --profile _work/character-import/heat/profile.json

# 3. Plan
py character_workflow.py plan --profile _work/character-import/heat/profile.json

# 4. Si no hay gaps -> prepare
py character_workflow.py prepare --profile _work/character-import/heat/profile.json

# 5. Cache para animaciones
py character_workflow.py cache-record \
  --profile _work/character-import/heat/profile.json \
  --cache _work/character-import/heat/cache.json \
  --evidence _work/evidence/heat_anim.mp4
```

## Archivos Generados

| Archivo | Propósito |
|---------|-----------|
| `_work/character-import/<char>/profile.json` | Perfil fuente |
| `_work/character-import/<char>/source_animation_list.bin` | Lista animaciones extraída |
| `_work/character-import/<char>/state.json` | Estado compacto (ver current-state.json) |
| `_work/character-import/<char>/candidate/manifest.json` | Manifest para deploy |
| `_work/character-import/<char>/cache.json` | Cache de referencia |

## Referencias Rápidas

- Ver también: `IMPORT_STANDARD.md` (guía de tarea)
- Ver también: `_work/current-state.json` (estado compacto global)
- Tests: `tools/test/test_character_workflow.py` (24 tests)