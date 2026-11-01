---
id: online-optimized
title: "Online Optimized"
tags: []
summary: "Auto-generated frontmatter - please review"
related: []
created: 2026-11-01
updated: 2026-11-01
---
# Online play, netsync, audio latency

## Estado actual de netplay ✅
- **Netplay activado** en BAG2JP (CMakeLists: PSX_NETPLAY ON)
- **Lobby**: ws://netplay.retcomm.net:8765
- **Mods desactivados** en modo netplay (JP title, sin HD intro)
- **Un solo PC probado**: Dos copias, LAN directo funciona (127.0.0.1:7777)
- **Sincronización**: Todos los bars idénticos en ambos PCs

## Step sync online ☑
- **Plugin**: `bag2jp.feature.netsync` (igual que StepMania)
- **Modelo**: Cada PC toca su propia música; solo los bar results viajan
- **MODS menu**: ONLINE = OFF/LOCAL NETWORK/INTERNET/DIRECT IP/TEST
- **LAN**: UDP broadcast 47300 con hash del room code
- **INTERNET**: MQTT 3.1.1, topic `bag2jp/v1/<room hash>`
- **DIRECT IP**: Host en UDP 47100, join = ip:port

## Focus pause ✅
- **Auto pause** si se pierde foco de ventana (alt-tab, minimize)
- **OSD message** muestra estado pause/resume
- **Timer SDL** mantiene link vivo durante pause
- **Test switch**: `BAG2JP_NETSYNC_FOCUS=always`
- **Verificado**: Pause al inicio, pause a mitad de danza, resume en ambos

## Latencia de audio 🔧
- **Buffer default**: 90 ms (en game.toml y exp install)
- **Probe**: `BAG2JP_AUDIO_PROBE=1` escribe logs `_work/np_logs/`
- **Resultados 1P focused**:
  - buffer 180 ms: fill avg 164 ms, sin underruns
  - buffer 90 ms: fill avg ~80 ms, un burst al song start
  - buffer 50 ms: fill avg 42 ms, burst al song start
- **Objetivo**: Remover song-start stall, luego buffer 50 (~75 ms total) seguro

## Versiones y releases 📦
- **Release v7**: Portable (457 MB) / Installer (451 MB)
- **Defaults**: ONLINE=INTERNET, room code 2GWE
- **Audio**: buffer_ms 90, canciones japonesas
- **Instalador**: NSIS 3.08, shortcuts en menú inicio

## Referencias rápidas
- `patches/BAG2JP-game.toml` - Config audio buffer_ms
- `mods-src/bag2jp.feature.netsync` - Plugin config
- `tools/test/bag2_report.py` - Reportes de test