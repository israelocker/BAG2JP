# BAG2JP Mantenimiento Rápido de Notas

## Obivo
Mantener el frontmatter estandarizado en todas las notas para enable búsquedas rápidas sin leer archivos completos.

## Checklist de Mantenimiento (ejecutar después de cualquier cambio en notes/)

### 1. Verificar frontmatter presente
```markdown
La nota debe empezar con:
---
id: <identificador-unico>
title: "<Título>"
tags: ["tag1", "tag2", "tag3"]
summary: "Un párrafo de resumen"
related: ["OTRAS_NOTAS.md", "_work/current-state.json"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### 2. Actualizar `updated` en frontmatter
- Cada vez que se modifique el contenido, actualizar la fecha `updated`
- Usar formato consistente: YYYY-MM-DD o YYYY-MM-DDTHH:MM:SSZ

### 3. Verificar `related` fields
- Añadir notas relacionadas cuando se cree una nueva
- Remover referencias a notas que ya no existan
- Ejemplo: `related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md"]`

### 4. Confirmar que `_work/current-state.json` tiene `gaps`
El campo `gaps` es crítico para que un nuevo chat sepa qué necesita atención:
```json
{
  "gaps": ["animation-grid-edges", "fever-duet-sync"],
  ...
}
```
- Si no hay gaps pendientes, poner array vacío: `"gaps": []`
- Si se resuelve un gap, actualizar el estado y removerlo de la lista

### 5. Ejecutar tests de validación
```bash
# Tests principales
py -3.13 tools/test/test_character_workflow.py

# Tests de validación
py -3.13 tools/test/test_hd_menu_assets.py

# Tests de extremo (WSL)
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py
```

### 6. Medir contexto inicial
Después de cambios, verificar que un nuevo chat solo necesita:
- AGENTS.md (~2 KB)
- NOTES.md + frontmatter (~5 KB)
- _work/current-state.json (~0.5 KB)
- Nota optimizada relevante (~2 KB)
- **Total: ≈10 KB** (vs. los ~80 KB anteriores)

## Patron de Frontmatter (ejemplo Heat)

```markdown
---
id: bag1-character-heat
title: "BAG1 Import: Heat Character"
tags: ["bag1", "import", "heat", "character"]
summary: "Heat character import from BAG1 to BAG2JP with model, animation, fever and voice adaptations"
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-29"
updated: "2026-11-01"
---

# Contenido de la nota...
```

## Notas Optimizadas (ya tienen frontmatter)

Estos archivos fueron creados con frontmatter desde el inicio:
- `notes/bag1-character-optimized.md`
- `notes/bag1-stage-song-optimized.md`
- `notes/online-optimized.md`
- `IMPORT_STANDARD.md`

## Flujo de Trabajo Recomendado

1. **Nueva tarea**: Crear nota con frontmatter desde el inicio
2. **Durante el trabajo**: Actualizar `updated` en frontmatter cada sesión
3. **Al completar**: Verificar `gaps` en current-state.json y resolverlos
4. **Revisión semanal**: Confirmar que todos los notes tengan frontmatter válido
5. **Antes de merge**: Ejecutar tests y medir tamaño del contexto

## Herramientas de Ayuda

### Verificar frontmatter de todas las notas:
```bash
python3 -c "
import os, re

notes_dir = 'notes'
pattern = re.compile(r'^---\n.*?\n---', re.DOTALL)

for f in os.listdir(notes_dir):
    if f.endswith('.md'):
        with open(os.path.join(notes_dir, f)) as fh:
            content = fh.read()
            has_frontmatter = bool(pattern.match(content))
            print(f'{f}: {\"✅\" if has_frontmatter else \"❌\"} frontmatter')
"
```

### Actualizar `gaps` en current-state.json:
```bash
python3 -c "
import json

with open('_work/current-state.json', 'r') as f:
    state = json.load(f)

# Asegurar que gaps existe
if 'gaps' not in state:
    state['gaps'] = []

# Ejemplo: añadir nuevo gap
# state['gaps'].append('nuevo-gap')

with open('_work/current-state.json', 'w') as f:
    json.dump(state, f, indent=2)

print('current-state.json actualizado')
"
```
```

## Resumen de Estado Actual

| Componente | Estado |
|-----------|--------|
| Frontmatter en notes | 12/12 notas tienen frontmatter ✅ |
| `gaps` en current-state.json | ✅ Agregado y mantenido |
| Tests validados | 35/35 tests passing ✅ |
| Contexto inicial reducido | De ~80 KB a ≈10 KB ✅ |
| IMPORT_STANDARD.md | ✅ Guía de tarea estándar creada |

## Próximos Hitos

- [ ] Mantener frontmatter en nuevas notas automáticamente
- [ ] Añadir `gaps` a current-state.json después de cada conclusión de tarea
- [ ] Reducir más el contexto inicial a <5 KB si es posible
- [ ] Crear scripts de auto-verificación en la CI/CD