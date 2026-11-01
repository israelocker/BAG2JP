# Regional Content & Launcher — Optimized Summary

## Opciones del Launcher (bag2jp.localization.regional) ✅
Instalado en BAG2JP-exp-8mb.

| Opción | Valores | Default | Estado |
|--------|---------|---------|--------|
| Región | japanese / international | international | Activo |
| Canciones | cd / game | cd | Activo |
| Announcer | japanese / international | international | Activo |
| Command buttons | international / jp | international | Hecho (2026-10-27) |
| VS Screen | international / jp | international | Hecho (2026-10-27) |

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
- tools/hq/render3.py (2026-10-29)
- 13 canciones renderizadas: BUST2_01 ch0-7, BUST2_02 ch0-3, BUST2_04 ch7
- Cobertura: 72-96% (BUST2_02 ch3 Acid Line = 72%)
- Runtime: framework hook `cdrom_set_xa_host_filter` + plugin `bag2jp.hq_songs`
- Copia spans de FLAC (sector k = frames k*2352)
- Log: `bag2jp_hq_songs.log`

### Announcer (opción añadida)
- Menu narrator: XA/BUST2_02.XA ch 4,5,6 (264s cada uno)
- Title voice: XA/BUST2_04.XA ch 6
- US audio en slots JP, resto ADPCM silencioso
- 20 disc_raw overlays de 2048 sectores (narrador), 1 overlay (title)

## Defaults Actualizados (2026-10-29)
- `songs` y `announcer` ahora default = "japanish" (antes "international")
- Cambiado en mods-src y en copias instaladas (exp install, netplay_peer2)
- state.toml con valor explícito mantiene su valor

## Comandos de Build
```
mods-src/bag2jp.localization.regional/tools/build_regional.py
tools/hq/render3.py <nombre-canción>
```

## Evidencia Verificada
- Both title/boot logo values: OK in game
- TV studio stage: loads clean
- Practice on Comet's stage: runs (audio by ear pending)
- Sushi Planet: shows US menu sign (stage_signs OK)
- Heat vs Strike: opens BUST2_01 ch1, match runs
- Full Comet song 1P: no seeks or slow reads