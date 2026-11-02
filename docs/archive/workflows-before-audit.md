# BAG2JP — Flujos de Trabajo Consolidados

Este documento resume los pasos para cada tipo de tarea común en el proyecto.
Lee solo el flujo correspondiente a tu tarea actual.

---

## 📋 Flujo 1: Importar Personaje BAG1 → BAG2

**Tiempo estimado:** 30-45 minutos
**Archivos clave:** `CHARACTER_IMPORT.md`, `IMPORT_STANDARD.md`, `_work/current-state.json`

### Paso 1: Preparación
```
1. Leer AGENTS.md (políticas)
2. Leer NOTES.md (índice actual)
3. Leer _work/current-state.json (estado y gaps)
4. Verificar que el personaje no esté ya importado
```

### Paso 2: Inicializar Profile
```powershell
py -3.13 tools/bag1import/character_workflow.py init-profile `
  --character <slug> `
  --profile tools/bag1import/profiles/<slug>.json `
  --source-archive <unpacked-model.dfs> `
  --source-list _work/character_inventory/<slug>/001.bin `
  --runtime <native-reference.exe> `
  --catalog tools/bag1import/contracts/bag1-usa-bag2jp.roles.json
```

### Paso 3: Validar y Planificar
```powershell
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile <profile.json>
py -3.13 tools/bag1import/character_workflow.py plan --profile <profile.json>
py -3.13 tools/bag1import/character_workflow.py acceptance-plan --profile <profile.json>
```

**Regla crítica:** Si `gaps` no está vacío, NO continuar con `prepare`.

### Paso 4: Preparar Candidato
```powershell
py -3.13 tools/bag1import/character_workflow.py prepare --profile <profile.json>
```
*Esto crea un candidato, NO despliega.*

### Paso 5: Registrar Evidencia
```powershell
py -3.13 tools/bag1import/character_workflow.py cache-record `
  --profile <profile.json> `
  --cache <cache.json> `
  --evidence <video.mp4> `
  --evidence <timeline.json>
```

### Paso 6: Verificar Evidencia
```powershell
py -3.13 tools/bag1import/character_workflow.py cache-check `
  --profile <profile.json> `
  --cache <cache.json>
```

### Paso 7: Testing In-Game
- Ejecutar en `BAG2JP-exp-8mb` (instalación experimental)
- Verificar: modelo, animaciones, fever, 2P autoplay, announcer, selector
- Capturar evidencia (screenshots, video, audio)

### Paso 8: Actualizar Estado
- Actualizar `_work/current-state.json` con `gaps`, `next_action`, `acceptance_count`
- Crear nota en `notes/` con frontmatter si es nuevo personaje
- Actualizar `NOTES.md` si es necesario

### Paso 9: Commit y Snapshot
- Commit local con solo archivos de la tarea
- Refrescar `BAG2JP-project-snapshot.tar.gz`

---

## 📋 Flujo 2: Agregar Nueva Nota al Proyecto

### Paso 1: Crear con Plantilla
Copiar `docs/templates/note-template.md` a `notes/<nombre>.md`

### Paso 2: Rellenar Frontmatter
```yaml
---
id: <identificador-unico>
title: "<Título>"
tags: ["tag1", "tag2"]
summary: "<Resumen de 1-2 líneas>"
related: ["ARCHIVO_RELACIONADO.md"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

### Paso 3: Actualizar Índices
- Añadir entrada a `NOTES.md`
- Añadir palabras clave a `NOTES.idx`

### Paso 4: Validar
```powershell
py tools/workflow/validate_frontmatter.py --fix
```

---

## 📋 Flujo 3: Mantenimiento Periódico

Ejecutar al final de cada sesión de trabajo:

```powershell
# 1. Validar frontmatter en todas las notas
py tools/workflow/validate_frontmatter.py --fix

# 2. Verificar digests actualizados
py tools/workflow/generate_digests.py --check-only

# 3. Medir contexto de inicio
py tools/workflow/measure_context.py

# 4. Ejecutar todos los tests
py -3.13 tools/test/test_character_workflow.py
py -3.13 tools/test/test_hd_menu_assets.py
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py

# 5. Commit si hay cambios
git add <archivos-cambiados>
git commit -m "<descripción>"
```

---

## 📋 Flujo 4: Nuevo Chat (Inicio Rápido)

### Paso 1: Leer Archivos Esenciales (≈8 KB)
```
1. AGENTS.md
2. NOTES.md
3. _work/current-state.json
```

### Paso 2: Identificar Qué Hacer
- Revisar `gaps` en `_work/current-state.json`
- Revisar `next_action` en el mismo archivo

### Paso 3: Leer Nota Relevante (solo si es necesario)
- `notes/bag1-character-clean.md` - Para trabajo con Heat
- `notes/bag1-stage-song-clean.md` - Para trabajo con stage/canción
- `notes/online-clean.md` - Para trabajo con online/netplay
- `notes/endings-view-clean.md` - Para trabajo con endings view
- `notes/regional-clean.md` - Para trabajo con regional content
- `notes/character-pipeline-clean.md` - Para trabajo con pipeline compartido

### Paso 4: Ejecutar Tarea
Seguir el flujo correspondiente (Flujo 1, 2, 3, etc.)

---

## 📋 Flujo 5: Crear Digest de Archivo Grande

Cuando un archivo fuente supera los 10 KB:

```powershell
# Generar digest
py tools/workflow/generate_digests.py --file <archivo-fuente>

# Verificar que está actualizado
py tools/workflow/generate_digests.py --check-only
```

---

## 🚫 Qué NO Hacer

| Acción | Razónde por qué |
|--------|-----------------|
| Tocar `BAG2JP-win` sin permiso | Es la instalación estable; cambios requieren aprobación del owner |
| Leer todas las notas al inicio | Desperdicia tokens; usa el índice y el estado compacto |
| Copiar pipeline de Heat a otro carácter | Cada carácter necesita su propia validación |
| Reclamar importación solo por existir profile | Requiere aceptación completa en juego |
| Auto-deployar candidatos | `prepare` nunca despliega |
| Ignorar `gaps` en current-state | Los gaps bloquean el progreso |

---

## 📊 Matriz de Decisión Rápida

| ¿Qué necesitas? | Lee esto primero |
|-----------------|------------------|
| ¿Qué debo hacer ahora? | `_work/current-state.json` (campo `next_action`) |
| ¿Qué notas existen? | `NOTES.md` |
| ¿Cómo importo un personaje? | `IMPORT_STANDARD.md` |
| ¿Cuáles son las reglas? | `AGENTS.md` + `CHARACTER_IMPORT.md` |
| ¿Cómo mantengo las notas? | `MAINTENANCE_GUIDE.md` |
| ¿Dónde está X archivo? | `docs/paths.md` |
| ¿Qué tests ejecutar? | `tools/test/` |

---

*Última actualización: 2026-11-01*
