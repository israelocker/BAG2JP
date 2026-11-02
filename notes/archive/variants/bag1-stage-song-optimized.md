---
id: bag1-stage-song-optimized
title: "Bag1 Stage Song Optimized"
tags: []
summary: "Auto-generated frontmatter - please review"
related: []
created: 2026-11-01
updated: 2026-11-01
---
# BAG1 import: stage port, song chart and audio

## Visión general
Port de stages BAG1 a BAG2JP. Heat stage id 0 (ST_HEAT) importado y verificado.

## Mapeo de stages BAG1 → BAG2
```
BAG1 id → BAG2 archive
0 → 200 (ST_HEAT)
1 → 209
2 → 199
3 → 210
4 → 202
5 → 208
6 → 204/205/206
7 → 203
8 → 201
9 → 198
10 → 197
11 → 207
12 → 211
```

## Estado de importación Heat ✅
- **Stage DBI**: Convertido y parcheado en `0x801DAF10`
- **17 calls al main exe**: Mapeados y trampolines puestos
- **Estructura stage struct**: Adaptada (0x100 → 0xB0 bone struct)
- **Callbacks BAG2**: 4 callbacks id-0 wireados

## Canción y audio ✅
- **Canción BAG1**: "2Bad" (no "Chemical Love")
- **Chart conversion**: `port_bag1_stage.bag1_chart()` 
- **Duración**: BAG1 123s → BAG2 152s (25s silencio antes fever)
- **Fix aplicado**: `tools/bag1import/song_ending.py` set 0x800555A8[0] = 129
- **Audio plugin**: `bag2jp.bag1_stage` reemplaza XA ch0 con archivos BAG1

## Fever y voices ✅
- **Fever choreography**: Entradas 17-52 mapeadas (Heat usa folders 22/40)
- **Voice handling**: Cues 0x1000/0x1001 muteados durante fever
- **Anim remap**: `anim_remap.mute_voices()` pointing at 0x1FFF

## Destrucción y efectos ✅
- **Paneles rotos**: Niveles 1 (32 panels) y 2 (64 panels) verificados
- **Fondo city**: Funciona estable tras helper en SHIM+0x10
- **Flicker fix**: Carry delay-slot lui + black TILE en OT[0xFFF]

## Selección de stage ✅
- **Carousel**: HEAT BAG2 → HEAT BAG1 (thumbnails distinct)
- **Version routing**: `bag2jp_bag1_set_stage_version(-1/0/1)`
- **Practice mode**: BAG1 Heat en BAG2 stage probado exitosamente

## Referencias
- `tools/bag1import/port_bag1_stage.py` - Conversión principal
- `tools/bag1import/build_heat_stage_test.sh` - Test mod
- `tools/bag1import/song_ending.py` - Fix duración canción
- `CHARACTER_IMPORT.md` - Reglas canonicales
