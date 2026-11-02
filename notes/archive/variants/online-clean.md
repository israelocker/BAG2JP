---
id: online-play-clean
title: "Online Play & NetSync - Clean Reference"
tags: ["online", "netplay", "netsync", "latency", "reference"]
summary: "Esencia de configuración online, netstep sync y latencia de audio para BAG2JP. Sin detalles de test de red ni rutas personales."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-29"
updated: "2026-11-01"
---

# Online Play & NetSync - Clean Reference

## Estado Actual de Netplay ✅
| Elemento | Estado | Notas |
|----------|--------|-------|
| Netplay activado | ✅ | CMakeLists: PSX_NETPLAY ON |
| Lobby | ✅ | ws://netplay.retcomm.net:8765 |
| Mods en netplay | ✅ | Desactivados (JP title, sin HD intro) |
| Modos de transporte | ✅ | OFF / LOCAL NETWORK / INTERNET / DIRECT IP / TEST |

## Step Sync Online (bag2jp.feature.netsync)
| Aspecto | Configuración |
|---------|---------------|
| Modelo | Cada PC toca su propia música; solo bar results viajan |
| LAN | UDP broadcast 47300 con room code hash |
| INTERNET | MQTT 3.1.1 QoS 0, topic `bag2jp/v1/<room hash>` |
| DIRECT IP | Host UDP 47100, join = ip:port |
| Servidores | HiveMQ, EMQX, Mosquitto |
| STUN | Google, Cloudflare |
| Hole punch | UDP 10s, luego relay via broker |

## Focus Pause (Auto Pause)
- **Trigger**: SDL_GetKeyboardFocus() == NULL (alt-tab, minimize)
- **Efecto**: BOTH PCs pause con `psx_host_pause_push("online")`
- **Mensaje M_FOCUS** (9): u8 focused, u8 paused, u16 match, u32 dance frame
- **OSD**: "ONLINE PAUSED - come back..." / "...the other player left..."
- **Resume**: Cuenta regresiva "resuming in 3..." en ambos PCs
- **Keepalive**: SDL timer 16ms durante pause (net poll, pings, focus)
- **Mutex**: `s_mu` serializa timer con vblank plugin y instruction hooks

## Latencia de Audio 🔧
- **Buffer default**: 90 ms (en game.toml y exp install)
- **Output buffer**: DRC ring, target `buffer_ms`, range 30-500 ms
- **SDL device buffer**: 1024 samples = 23 ms @ 44.1 kHz
- **Lag total**: fill + 23 ms + OS overhead

### Resultados de Medición (1P, window focused)
| buffer_ms | Fill promedio | Underruns |
|-----------|---------------|-----------|
| 180 ms | avg 164 ms (124-174) | Ninguno |
| 90 ms | avg ~80 ms | Un burst al song start |
| 50 ms | avg 42 ms (26-92) | Un burst al song start |

**Objetivo**: Remover song-start stall, luego buffer 50 (~75ms total) seguro.

## Versiones y Releases 📦
- **Release v7 Portable**: 457 MB zip (exe + configs + mods + CD songs)
- **Release v7 Installer**: 451 MB NSIS
- **Defaults**: ONLINE=INTERNET, room code 2GWE, buffer_ms 90, canciones JP

## Referencias Rápidas
- `patches/BAG2JP-game.toml` - Config audio buffer_ms
- `mods-src/bag2jp.feature.netsync` - Plugin config
- `CHARACTER_IMPORT.md` - Character select popup online (M_PICK, M_CONTENT)
