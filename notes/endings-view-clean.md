---
id: endings-view-clean
title: "Ending View - Clean Reference"
tags: ["endings", "acceptance", "ledger", "reference"]
summary: "Esencia del estado actual, alcance y evidencia verificada para Ending View de BAG2JP. Sin detalles de test específicos ni rutas personales."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-11-01"
updated: "2026-11-01"
---

# Ending View - Clean Reference

## Estado Actual ✅ / ⚠️
| Elemento | Estado | Notas |
|----------|--------|-------|
| HD menu (six rows) | ✅ | Implementado, assets listos, 2/2 tests pasan |
| Black video Heat BAG1 | ✅ | Root cause identificado y fixado en host movie |
| Aceptación final Heat | ⚠️ | Build pasó, pendiente commit y snapshot |
| GAME/COSTUME popup | ✅ | Heat debe tener ambos; otros solo COSTUME |
| Stock sound/fade | ⚠️ | Confirm corregido, live sound pendiente de verificación |

## Flujo Aprobado ✅
main menu > DANCE VIEW > ENDING VIEW > OPTIONS (en ese orden)

ENDING VIEW abre el selector stock de personaje/costume (sin difficulty) y lanza el ending de la selección directamente. Los modos normales se mantienen sin cambios.

## Archivos y Rutas Clave
| Archivo | Propósito |
|---------|-----------|
| `mods-src/bag2jp.feature.endings-view/1.0.0/menu_hd` | Assets HD menu (2 files, ready.txt) |
| `patches/psxrecomp-disabled-display-hud-present.patch` | Fix black frame en host movie |
| `mods-src/bag2jp.enhancement.hd-intro/bag2jp_hd_intro.c` | Source sincronizado |
| `_work/endings-view/` | Evidencia de pruebas |

## Tests Verificados
| Test | Resultado |
|------|-----------|
| Unit seam (HD menu packet) | 9/9 passed |
| Unit seam (confirmation/fade) | 8/8 passed |
| Build `heat-ending-final-present` | Passed |
| Build `endings-view-movie-probe` | Compiled, NOT deployed |

**SHA256 desplegado**: `49ECD14403FFB481E79EBF56499516DEA2EC94F379F9869AE0CE336F5EBDFB9C`

## Pendientes
- Commit local y snapshot refresh (close-out de tarea pendiente)
- Live sound verification pendiente de confirmación del owner
- Native lettering experiment vs HD image (HD image supersede)

## Comandos Útiles
```
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py
& D:/Dev/Recomp/BAG2JP/tools/test/bag2_endings_view.ps1 -GameId <PID> -Action options|selector|cancel|accept
```