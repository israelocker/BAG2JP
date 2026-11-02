---
id: regional-content-clean
title: "Regional Content & Launcher - Clean Reference"
tags: ["regional", "launcher", "localization", "songs", "reference"]
summary: "Esencia de opciones regionales, canciones CD-quality, anunciador y configuración del Launcher para BAG2JP. Sin detalles de test ni rutas personales."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-29"
updated: "2026-11-01"
---

# Regional Content & Launcher - Clean Reference

## Opciones del Launcher (bag2jp.localization.regional) ✅
Instalado en BAG2JP-exp-8mb.

| Opción | Valores | Default | Estado |
|--------|---------|---------|--------|
| Región | japanese / international | international | Activo |
| Canciones | cd / game | cd | Activo |
| Announcer | japanese / international | international | Activo |
| Command buttons | international / jp | international | Hecho |
| VS Screen | international / jp | international | Hecho |

## Contenido Regional por Categoría

### Title Screen & Boot Logos
- system/016 002,003,005,006 + 004 subtitle (hidden)
- system/012/004 ranking logo
- US TIMs re-headed a posiciones JP VRAM/CLUT

### Hiro Icon
- pack_a_p1/pack_b_p1 000.tim (18 caracteres)
- system/015.bpe 001, Hiro packs a/b 002/003 + p2 001/002

### Stage Signs
- Stages: 199/002, 201/004, 202/003/004/006/007, 203/007
- system/015.bpe 033

## Canciones y Audio

### CD Songs v3 (CD audio only) ✅
- **Herramienta**: tools/hq/render3.py
- **Canciones**: 13 canciones (BUST2_01 ch0-7, BUST2_02 ch0-3, BUST2_04 ch7)
- **Cobertura**: 72-96% (BUST2_02 ch3 Acid Line = 72%)
- **Runtime**: Framework hook `cdrom_set_xa_host_filter` + plugin `bag2jp.hq_songs`
- **Mecanismo**: Copia spans de FLAC (sector k = frames k*2352)
- **Log**: `bag2jp_hq_songs.log`

### Announcer (opción añadida)
- **Menu narrator**: XA/BUST2_02.XA ch 4,5,6 (264s cada uno)
- **Title voice**: XA/BUST2_04.XA ch 6
- **US audio**: En slots JP, resto ADPCM silencioso
- **Overlays**: 20 disc_raw de 2048 sectores (narrador), 1 overlay (title)
- **Herramienta**: tools/build_xa.py

## Defaults Actualizados (2026-10-29)
- `songs` y `announcer` ahora default = "japanish" (antes "international")
- Cambiado en mods-src y en copias instaladas (exp install, netplay_peer2)
- state.toml con valor explícito mantiene su valor

## Comandos de Build
```
mods-src/bag2jp.localization.regional/tools/build_regional.py
tools/hq/render3.py <nombre-canción>
tools/build_xa.py
```

## Referencias Rápidas
- `mods-src/bag2jp.localization.regional/` - Paquete completo
- `tools/hq/` - Herramientas de renderizado HQ
- `CHARACTER_IMPORT.md` - Reglas de audio para personajes
