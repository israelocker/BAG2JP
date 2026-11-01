---
id: bag1-stage-song-clean
title: "BAG1 Stage Song: Heat - Clean Reference"
tags: ["bag1", "stage", "song", "heat", "reference"]
summary: "Esencia del port de stage y canción Heat BAG1 a BAG2JP: mapeo, chart, audio y destrucción. Sin detalles de test ni rutas personales."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-30"
updated: "2026-11-01"
---

# BAG1 Stage Song: Heat - Clean Reference

## Mapeo de Stages BAG1 → BAG2
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

## Estado de Importación Heat ✅
| Elemento | Estado | Notas |
|----------|--------|-------|
| Stage DBI | ✅ | Convertido y parcheado en 0x801DAF10 |
| 17 calls main exe | ✅ | Mapeados con trampolines |
| Stage struct | ✅ | Adaptado BAG1 0x100 → BAG2 0xB0 |
| Callbacks BAG2 | ✅ | 4 callbacks id-0 wireados |
| Canción "2Bad" | ✅ | Chart convertido, duración fijada a 129s |
| Audio plugin | ✅ | `bag2jp.bag1_stage` reemplaza XA ch0 |
| Fever voices | ✅ | Cues 0x1000/0x1001 muteados durante fever |
| Destrucción paneles | ✅ | Niveles 1 y 2 verificados |
| Selección stage | ✅ | Carousel con HEAT BAG2 → HEAT BAG1 |

## Canción y Audio
- **Canción BAG1**: "2Bad" (CD track 02), NO "Chemical Love"
- **Chart conversion**: `port_bag1_stage.bag1_chart()` convierte formato BAG1 → BAG2
- **Duración**: BAG1 123s → BAG2 slot 152s (25s silencio antes fever)
- **Fix aplicado**: `tools/bag1import/song_ending.py`, plugin set 0x800555A8[0] = 129
- **Audio**: Plugin `bag2jp.bag1_stage` reemplaza XA ch0 con archivos BAG1 FLAC

## Fever y Voces
- **Fever choreography**: Entradas 17-52 mapeadas (Heat usa folders 22/40)
- **Voice handling**: Cues 0x1000/0x1001 muteados durante fever
- **Anim remap**: `anim_remap.mute_voices()` puntos bank-1 cues a 0x1FFF

## Destrucción y Efectos
- **Paneles rotos**: Level 1 (32 panels) y Level 2 (64 panels) verificados
- **Fondo city**: Estable tras helper en SHIM+0x10
- **Flicker fix**: Delay-slot lui + black TILE en OT[0xFFF]

## Selección de Stage
- **Carousel**: HEAT BAG2 → HEAT BAG1 (thumbnails distinct)
- **Version routing**: `bag2jp_bag1_set_stage_version(-1/0/1)` para entry 200
- **Practice mode**: BAG1 Heat en BAG2 stage probado exitosamente

## Referencias Rápidas
- `tools/bag1import/port_bag1_stage.py` - Conversión principal
- `tools/bag1import/song_ending.py` - Fix duración canción
- `tools/bag1import/build_heat_stage_test.sh` - Test mod
- `tools/bag1import/fever_entries.py` - Mapeo fever entries
- `CHARACTER_IMPORT.md` - Reglas canonicales