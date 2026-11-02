# BAG2JP — Documentación Maestra

Este archivo es el punto de entrada único para toda la documentación del proyecto.
**No leas todos los archivos**: usa este índice para ir directo a lo que necesitas.

---

## 📋 Inicio Rápido (leer primero)

| Archivo | Qué contiene | Cuándo leerlo |
|---------|-------------|---------------|
| `AGENTS.md` | Políticas y workflow del proyecto | Siempre, al iniciar un chat nuevo |
| `NOTES.md` | Índice de notas temáticas con summaries | Cuando necesites saber qué notas existen |
| `_work/current-state.json` | Estado compacto actual + `gaps` | Para saber qué necesita atención |
| `docs/guides/import-standard.md` | Guía paso a paso para importar personaje BAG1→BAG2 | Cuando vayas a importar un personaje |

---

## 📚 Documentación por Categoría

### 1. Proyecto y Configuración

| Documento | Descripción | Ruta |
|-----------|-------------|------|
| Project overview | Builds, carpetas, saves, resume | `notes/project.md` |
| Game configuration | Configuración del juego (video, audio, controller) | `patches/BAG2JP-game.toml` |
| User settings | Configuración de usuario (launcher, hotkeys, controller) | `installer/settings.toml` |
| Asset toolkit | Layout de archivos, extracción, verificación | `notes/assets.md` |

### 2. Importación de Personajes (BAG1 → BAG2)

| Documento | Descripción | Ruta |
|-----------|-------------|------|
| Canonical runbook | Reglas no negociables, orden de comandos, matriz de aceptación | `CHARACTER_IMPORT.md` |
| Import standard guide | Guía paso a paso lista para ejecutar | `docs/guides/import-standard.md` |
| Shared pipeline | Pipeline compartido, perfiles, contratos de animación | `notes/character-pipeline.md` |
| Heat: character | Modelo, animaciones, fever, voces, 2P autoplay | `notes/bag1-character.md` |
| Heat: stage & song | Port de escenario, chart de canción, audio | `notes/bag1-stage-song.md` |
| Heat: clean reference | Versión resumida sin ruido de test | `notes/bag1-character-clean.md` |
| Stage-song: clean reference | Versión resumida sin ruido de test | `notes/bag1-stage-song-clean.md` |

### 3. Características del Juego

| Documento | Descripción | Ruta |
|-----------|-------------|------|
| Online & NetSync | Configuración online, paso a paso, latencia de audio | `notes/online.md` |
| Online: clean reference | Versión resumida sin ruido de test | `notes/online-clean.md` |
| Ending View | Menú de endings, hooks JP, ledger de aceptación | `notes/endings-view.md` |
| Ending View: clean | Versión resumida sin ruido de test | `notes/endings-view-clean.md` |
| Regional content | Opciones regionales, canciones CD-quality, anunciador | `notes/regional.md` |
| Regional: clean | Versión resumida sin ruido de test | `notes/regional-clean.md` |
| UI Mods & HD Fonts | Fuentes HD, menú MODS, teclado | `notes/ui-mods.md` |

### 4. Pipeline Compartido

| Documento | Descripción | Ruta |
|-----------|-------------|------|
| Character pipeline | Pipeline compartido, perfiles, contratos | `notes/character-pipeline.md` |
| Character pipeline: clean | Versión resumida sin ruido | `notes/character-pipeline-clean.md` |
| Agent handoff | Guía para retomar trabajo entre agentes | `notes/agent-handoff.md` |

---

## 🔧 Scripts de Mantenimiento

| Script | Propósito | Comando |
|--------|-----------|---------|
| Validar frontmatter | Revisa y rellena frontmatter en notas | `py tools/workflow/validate_frontmatter.py --fix` |
| Generar digests | Crea/actualiza resúmenes de archivos grandes | `py tools/workflow/generate_digests.py --all` |
| Medir contexto | Mide tamaño de contexto de inicio | `py tools/workflow/measure_context.py --detailed` |
| Mantenimiento completo | Ejecuta todas las verificaciones | `py tools/workflow/maintenance_check.py` |
| Workflow helper | Preflight, build, test, report | `py tools/workflow/bag2_workflow.py <comando>` |

---

## 📁 Estructura de Carpetas

```
D:/Dev/Recomp/BAG2JP/
├── AGENTS.md                    # Políticas y workflow (leer primero)
├── CHARACTER_IMPORT.md          # Runbook canónico de importación
├── IMPORT_STANDARD.md           # Guía estándar de tarea
├── MAINTENANCE_GUIDE.md         # Checklist de mantenimiento
├── NOTES.md                     # Índice de notas temáticas
├── NOTES.idx                    # Índice semántico para búsquedas
├── _work/current-state.json     # Estado compacto actual
├── patches/                     # Parches del framework (game.toml, CMakeLists)
├── mods-src/                    # Código fuente de mods/features
├── tools/
│   ├── bag1import/              # Herramientas de importación BAG1
│   └── workflow/                # Scripts de mantenimiento y medición
├── notes/                       # Documentación temática
│   ├── *.md                     # Notas originales (conservadas)
│   ├── *-clean.md               # Versiones limpias sin ruido de test
│   ├── digests/                 # Resúmenes de archivos grandes
│   └── NOTES.idx                # Índice semántico
├── installer/                   # Instalador NSIS y configuración
└── _work/                       # Archivos de trabajo (no commitear)
    └── current-state.json       # Estado compacto generado
```

---

## 🎯 Protocolo de Inicio para Chat Nuevo

Lee solo lo necesario, en este orden:

1. **AGENTS.md** — Políticas y reglas del proyecto (≈6 KB)
2. **NOTES.md** — Índice para saber qué notas existen (≈2 KB)
3. **_work/current-state.json** — Estado actual y qué necesita atención (≈0.5 KB)
4. **Nota temática específica** — Solo la que necesitas para tu tarea (2-8 KB)

**No leas todas las notas.** Si el índice + estado + guía estándar responden tu pregunta, detente ahí.

---

## 📌 Reglas de Mantenimiento

- Toda nota nueva debe tener frontmatter: `id`, `title`, `tags`, `summary`, `related`, `created`, `updated`
- Cualquier cambio en una nota debe actualizar el campo `updated`
- Los digests se regeneran cuando el archivo fuente cambia
- `_work/current-state.json` debe tener el campo `gaps` actualizado
- Nunca eliminar notas; dividirlas o crear versiones limpias en su lugar
- Los archivos `*-clean.md` son versiones sin ruido de test ni rutas personales

---

*Última actualización: 2026-11-01*
