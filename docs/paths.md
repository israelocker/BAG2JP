# BAG2JP — Rutas Centralizadas del Proyecto

Este archivo documenta todas las rutas importantes del proyecto para evitar rutas personales o dispersas en la documentación.

## Rutas del Proyecto (Canonical)

| Propósito | Ruta | Notas |
|-----------|------|-------|
| Repositorio principal | `D:/Dev/Recomp/BAG2JP` | Canonical project |
| Build tree (Codex) | `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP` | Entorno de compilación |
| Stable install (NO tocar) | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-win` | Requiere permiso explícito del owner |
| Experimental install (default) | `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb` | Target por defecto para deploy/test |
| Disc image (BAG2 JP) | `D:/Games/Bust A Groove 2 (Japan)/ISO/...cue` | SLPM-86219 |
| Disc image (BAG1 USA) | `D:/Games/Bust A Groove (USA)/ISO/...cue` | SCUS-94263 |

## Herramientas

| Herramienta | Ruta | Propósito |
|-------------|------|-----------|
| Game runner | `D:/Dev/Tools/winshot/bag2_run.ps1` | Ejecutar el juego con configuración |
| Test reporter | `tools/test/bag2_report.py` | Generar reportes de pruebas |
| Audio probe | `D:/Dev/Tools/audio-probe` | Análisis de audio |
| Ghidra scripts | `D:/Dev/Tools/ghidra-scripts/run_headless.ps1` | Decompilación headless |

## Archivos de Configuración

| Archivo | Ruta | Propósito |
|---------|------|-----------|
| Game config | `patches/BAG2JP-game.toml` | Video, audio, controller, netplay |
| User settings | `installer/settings.toml` | Launcher, hotkeys, window, localization |
| CMakeLists patch | `patches/BAG2JP-CMakeLists.txt` | Configuración de compilación |
| Installer NSIS | `installer/bag2jp_online.nsi` | Script del instalador Windows |

## Directorios de Trabajo (_work)

| Propósito | Ruta | Commitear |
|-----------|------|-----------|
| Estado compacto | `_work/current-state.json` | ❌ (generado) |
| Character imports | `_work/character-import/<slug>/` | ❌ |
| Evidence | `_work/evidence/` | ❌ |
| Logs | `_work/logs/` | ❌ |
| Workflow | `_work/workflow/` | ❌ |
| Temp/scratch | `_work/scratch/` | ❌ |

## Herramientas de Importación BAG1

| Script | Ruta | Propósito |
|--------|------|-----------|
| Model converter | `tools/bag1import/model_bag1_to_bag2.py` | Convertir modelo BAG1→BAG2 |
| Animation remap | `tools/bag1import/anim_remap.py` | Remapear slots de animación |
| DBI patch | `tools/bag1import/patch_heat_dbi.py` | Parche de beanie/huesos |
| Request map | `tools/bag1import/reqmap.py` | Mapeo request→slot |
| Build heat test | `tools/bag1import/build_heat_test.sh` | Build del test mod |
| Build heat stage | `tools/bag1import/build_heat_stage_test.sh` | Build del test de stage |
| Song ending fix | `tools/bag1import/song_ending.py` | Fix de duración de canción |
| Fever entries | `tools/bag1import/fever_entries.py` | Mapeo de entradas de fever |
| Stage port | `tools/bag1import/port_bag1_stage.py` | Conversión de stage |
| Alt entries | `tools/bag1import/make_alt_entries.py` | Tabla de entradas alternativas |
| Announcer preserve | `tools/bag1import/preserve_announcer.py` | Fusionar nombre de announcer |
| Restore winner | `tools/bag1import/restore_heat_winner.py` | Restaurar voice packs |
| Audit roles | `tools/bag1import/audit_animation_roles.py` | Auditoría de roles de animación |

## Scripts de Mantenimiento

| Script | Ruta | Propósito |
|--------|------|-----------|
| Validate frontmatter | `tools/workflow/validate_frontmatter.py` | Validar/rellenar frontmatter |
| Generate digests | `tools/workflow/generate_digests.py` | Generar/actualizar digests |
| Measure context | `tools/workflow/measure_context.py` | Medir tamaño de contexto |
| Maintenance check | `tools/workflow/maintenance_check.py` | Ejecutar todas las verificaciones |
| Workflow helper | `tools/workflow/bag2_workflow.py` | Preflight, build, test, report |

## Directorios de Mods

| Mod | Ruta | Feature |
|-----|------|---------|
| BAG1 Content | `mods-src/bag2jp.feature.bag1-content/` | bag1-heat, bag1-stage, select-popup |
| HD Intro | `mods-src/bag2jp.enhancement.hd-intro/` | hd-intro |
| Autoplay | `mods-src/bag2jp.feature.autoplay/` | autoplay |
| NetSync | `mods-src/bag2jp.feature.netsync/` | netsync |
| Regional | `mods-src/bag2jp.localization.regional/` | regional |
| Mods Menu | `mods-src/bag2jp.feature.mods-menu/` | mods-menu |
| Endings View | `mods-src/bag2jp.feature.endings-view/` | endings-view |
| Anim Trace | `mods-src/bag2jp.debug.anim-trace/` | anim-trace |
| Expanded RAM | `mods-src/bag2jp.experimental.expanded-ram/` | expanded-ram |

## Documentación

| Documento | Ruta | Propósito |
|-----------|------|-----------|
| Project policies | `AGENTS.md` | Políticas y workflow |
| Import runbook | `CHARACTER_IMPORT.md` | Manual canónico de importación |
| Import guide | `IMPORT_STANDARD.md` | Guía estándar de tarea |
| Maintenance guide | `MAINTENANCE_GUIDE.md` | Checklist de mantenimiento |
| Notes index | `NOTES.md` | Índice de notas temáticas |
| Semantic index | `NOTES.idx` | Índice para búsquedas rápidas |
| Docs master | `docs/index.md` | Índice maestro de documentación |
| Note template | `docs/templates/note-template.md` | Plantilla para nuevas notas |

## Pruebas

| Test | Ruta | Propósito |
|------|------|-----------|
| Character workflow | `tools/test/test_character_workflow.py` | Validación de workflow |
| HD menu assets | `tools/test/test_hd_menu_assets.py` | Validación de assets HD |
| Endings view | `tools/test/test_endings_view.py` | Validación de endings view |

---

*Este archivo debe actualizarse cuando se añadan nuevas rutas al proyecto.*
*Última actualización: 2026-11-01*