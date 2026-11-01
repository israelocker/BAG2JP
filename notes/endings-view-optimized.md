---
id: endings-view-optimized
title: "Endings View Optimized"
tags: []
summary: "Auto-generated frontmatter - please review"
related: []
created: 2026-11-01
updated: 2026-11-01
---
# Ending View — Optimized Summary

## Visión general
Implementación y aceptación de Ending View para BAG2JP. Estado: HD menu implementado, black video de Heat BAG1 fixado, aceptación parcial pendiente.

## Estado Actual ✅ / ⚠️

| Elemento | Estado | Notas |
|----------|--------|-------|
| HD menu (six rows) | ✅ | Implementado, assets listos, 2/2 tests pasan |
| Black video Heat BAG1 | ✅ | Root cause identificado y fixado en host movie |
| Aceptación final Heat | ⚠️ | Build pasó, no hay commit ni snapshot todavía |
| GAME/COSTUME popup | ✅ | Heat debe tener ambos; otros solo COSTUME |
| Stock sound/fade | ⚠️ | Confirm corregido, live sound pendiente de verificación |

## Flujo Aprobado ✅
main menu > DANCE VIEW > ENDING VIEW > OPTIONS (en ese orden)

## Archivos y Rutas Clave
- `mods-src/bag2jp.feature.endings-view/1.0.0/menu_hd` - Assets HD menu
- `_work/endings-view/` - Evidencia de pruebas
- `patches/psxrecomp-disabled-display-hud-present.patch` - Fix black frame
- `mods-src/bag2jp.enhancement.hd-intro/bag2jp_hd_intro.c` - Source sincronizado

## Tests
- Unit seam: 9/9 pasados (HD menu packet, confirmation/fade)
- Build `heat-ending-final-present` - pasó
- SHA256 desplegado: `49ECD14403FFB481E79EBF56499516DEA2EC94F379F9869AE0CE336F5EBDFB9C`
- Build `endings-view-movie-probe` - compilado, NO desplegado

## Pendientes
- Commit local y snapshot refresh (close-out de tarea pendiente)
- Live sound verification pendiente de confirmación del owner
- Native lettering experiment vs HD image (HD supersede)

## Comandos Útiles
```
wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/tools/test/test_endings_view.py
```