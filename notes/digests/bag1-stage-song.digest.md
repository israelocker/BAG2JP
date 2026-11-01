# bag1-stage-song.md Digest

**Source:** `notes/bag1-stage-song.md` (13 KB, 137 lines)

## Resumen
Port de stage BAG1 (ST_HEAT) y canción "2Bad" a BAG2JP. Incluye chart conversion, audio handling, cámara, efectos de destrucción, fever voices, y selección independiente de stage.

## Secciones Principales

| Sección | Fecha | Estado | Puntos Clave |
|---------|-------|--------|--------------|
| BAG1 stage import findings | 2026-10-30 | ✅ | Stage mapping, DBI relocation, 17 calls mapped |
| Independent Heat stage selection | 2026-10-30 | ✅ | Carousel con ambos Heat, thumbnails distinct |

## Hallazgos Críticos (para reusar)

### Stage Mapping
```
BAG1 id → BAG2 archive
0 → 200 (ST_HEAT - Heat)
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

### Stage DBI Conversion
- Loader FUN_8003398C: DFS entry 0=DBI, 1=SEDT, TIM slots
- BAG1 ST_HEAT: mismo orden (DBI, SEDT, 6 TIMs, model, 1 camera track)
- Modelo convierte con `model_bag1_to_bag2.py` (13 meshes + 1 type 3)
- `port_bag1_stage.py` relocates DBI (delta 0x801DAF10-0x801E17B0)
- 17 main-exe calls mapeados (lights setup/update 0x80023724/0x80022FF4)
- Stage struct adaptado: BAG1 0x100 → BAG2 0xB0 bone struct
- 4 callbacks BAG2 id-0 wireados con trampolines

### Song Chart
- **Canción BAG1**: "2Bad" (CD track 02), NO "Chemical Love"
- Chart en main exe table 0x800513DC[Heat id 0]
- `port_bag1_stage.bag1_chart()` convierte BAG1→BAG2 format
- BAG1: start, frames, beats, sections (mode<<8|beats), -1
- BAG2: start, frames, beats, intro beats, sections (mode 0=none, 1/2 solo, 3 both)
- Intro beats: 32 del pre-roll, start -5

### Audio Handling
- Plugin `bag2jp.bag1_stage` wraps XA host filter
- Reemplaza BUST2_01 ch0 con `<bag1_music>/heat_2bad_<cd|game>.flac`
- Option `bag1_song_audio` (default cd)
- CD re-aligned con hq tools (coverage 90%, score 0.74)

### Song Length Fix
- **Problema**: BAG1 2Bad ends 123s, BAG2 Heat slot 152s → 25s silence antes fever
- **Fix**: `tools/bag1import/song_ending.py` - CD render switches to game tail at cut
- Plugin sets `0x800555A8[0] = 129` while BAG1 stage loaded
- Verified: dance end f10635, song stop f10994, fever f11132 (was f12401)

### Stage Destruction
- BAG1 breaks window panels at level changes (1 at 15000, 2 at 45000 BAG1 points)
- Bug: plugin copied prev every vblank → update never saw change
- **Fix**: Helper at SHIM+0x10 calls BAG1 update then copies level→prev
- Thresholds usan BAG2 dance-level table (0x8005141C x play beats/256)
- Level 1 at 9300, Level 2 at 18900 (BAG2 match ends ~25-30k)

### Fever Voices
- BAG1 anims 82/83 (requests 160/161) fire Heat voice cue 0x1006 8x
- BAG2 fever has none
- `anim_remap.mute_voices()` points bank-1 cues at missing cue 0x1FFF

### Broken Window Flicker Fix
- Night-city backdrop used tpage 0x0FF3 on odd tiles
- Delay-slot lui never relocated (porter paired lui only along linear flow)
- **Fix**: `port()` carries delay-slot lui to branch target
- Tiles widened to -8..5 + black TILE at OT[0xFFF] (sky above city)

### Fever Choreography Entries
- BAG2 loads via table 0x8005510C[char id*2 + fever type-1]
- Heat (id 0) = entries 22/40 = folders "kelly/choreography_a|b"
- **Before fix**: BAG1 fever dances never used (Heat danced BAG2 fever)
- **After**: solo = BAG1 82/83/82 muted, duet = BAG2 duet muted 0x10xx

### Stage Camera
- Both games: blocks [size][flags 0x4000|keys][keys: pos xyz, target xyz], 0 terminator
- BAG1 ST_HEAT entry 9 = solo intro fly-in (180 keys)
- BAG2 ~28 tracks (0=intro, rest follow dancers)
- Ported: BAG1 track 0 + BAG2 tracks 1.. (same world units)

### Stage SEDT
- BAG1 ST_HEAT bank 0 = cue 0x4000 fire burst (voice slot 20)
- BAG2 has 14 slots, table 0x8006D9F0
- Port: bank 0 <- BAG1 bank 0, cue renumbered 0x5000
- Call site patched to BAG2 FUN_8002E478(0x5000,-1,-1,-1) (free slot)

## Independent Heat Stage Selection
- Carousel: HEAT BAG2 → HEAT BAG1 (thumbnails distinct)
- Characters/versions/costumes independent; story mode auto default
- `bag2jp_bag1_set_stage_version(-1/0/1)` selects auto/BAG2/BAG1 for entry 200
- Thumbnails: BAG1 DFS1/ST_SEL.BPE entry 23, BAG2 system/015.bpe entry 029
- Rebuild: `python tools/bag1import/build_stage_previews.py`

## Tests Verificados
- Practice: BAG1 Heat on BAG2 stage ✅
- 2P P1 BAG2 A + P2 BAG1 B on BAG1 stage: CD 2Bad, song 129s, fever/return ✅
- Same session, both BAG1 A/B on BAG2 stage: stock stage, CD BUST2_01, fever/return ✅

## Referencias Rápidas
- `tools/bag1import/port_bag1_stage.py` - conversión principal
- `tools/bag1import/song_ending.py` - fix duración canción
- `tools/bag1import/build_heat_stage_test.sh` - test mod
- `tools/bag1import/fever_entries.py` - mapeo fever entries