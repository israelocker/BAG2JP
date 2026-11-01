# online.md Digest

**Source:** `notes/online.md` (12 KB, 144 lines)

## Resumen
Configuración de netplay, step sync online, latencia de audio, release v7 portable e installer para BAG2JP.

## Secciones Principales

| Sección | Estado | Puntos Clave |
|---------|--------|--------------|
| Online play (generic netplay) | ✅ | PSX_NETPLAY ON, lobby ws://netplay.retcomm.net:8765 |
| Online step sync (netsync) | ✅ | Plugin bag2jp.feature.netsync, modelo StepMania |
| Auto pause focus loss | ✅ | M_FOCUS msg, SDL timer keepalive, OSD countdown |
| Audio latency | 🔧 | buffer_ms 90 (exp), objetivo 50 ms |
| Release v7 portable | ✅ | 457 MB zip, defaults ONLINE=INTERNET |
| Windows installer | ✅ | 451 MB NSIS, per-user install |

## Configuración Netplay

### Generic Netplay
- CMakeLists: `PSX_NETPLAY ON` + `ENABLE_NETPLAY_IF_PRESENT`
- Lobby: `ws://netplay.retcomm.net:8765`
- Launcher: NETPLAY button (LAN / Direct IP / Online Netplay)
- LAN mantiene vanilla content (mods off en match)
- Ambos jugadores necesitan mismo .cue/.bin (disc fingerprint en game.toml)
- Tested 1 PC, 2 copias: Direct 127.0.0.1:7777 works

### Step Sync (bag2jp.feature.netsync)
- Plugin: `src/bag2jp_netsync.c` (copy + manifest)
- Modelo: Cada PC toca su propia música; solo bar results viajan
- MODS menu: ONLINE = OFF / LOCAL NETWORK / INTERNET / DIRECT IP / TEST (MIRROR)
- Room code: 4 letters/digits, pad editor (Circle edit, Up/Down letter)
- LAN: UDP broadcast 47300 con room code hash, P1 = higher random id
- INTERNET: MQTT 3.1.1 QoS 0, topic `bag2jp/v1/<room hash>`
  - Servers: HiveMQ, EMQX, Mosquitto (bag2jp_online_servers.txt)
  - STUN: Google, Cloudflare
  - UDP hole punch 10s, luego relay via broker
  - Switch `BAG2JP_NETSYNC_RELAY_ONLY=1`
- DIRECT IP: Host escucha UDP 47100, join = "ip:port", port forwarded

### Sync Logic (BAG2 JP)
- En system/005.dbi (base 0x8008F890), FUN_80099e90
- Per-bar 2-player loop ~0x8009B000
- CPU path cuando mode 0x8005D2C4 == 0 or (==1 and player != human 0x8005E6C8)
- Result code: 0x8005CF1C + p*0x24 (0x6e attack, 0xaa dodge)
- Timing: 0x8005CF14 + p*0x24
- Per-player block: 0x8005E728 + p*0x32

### Focus Pause
- Durante online dance: si SDL_GetKeyboardFocus() == NULL → BOTH PCs pause
- `psx_host_pause_push("online")`: guest + audio frozen, last frame on screen
- Message `M_FOCUS` (9): u8 focused, u8 paused, u16 match, u32 dance frame
- OSD: "ONLINE PAUSED - come back..." / "resuming in 3..."
- SDL timer (16 ms) keeps link alive (net poll, pings, focus)
- `s_mu` (SDL mutex) serializes timer with vblank plugin + 3 instruction hooks

### Bar Handling
- Gate 0x8009ABC4 closes local bar (FUN_800120F8) y envía
- Wait max 180 frames for other result
- NEW: 0x8009A0C0 holds beat until waiting bar resolved
- Out-of-sync: STEP carries COOL/right-bar counts (0x8005E798/0x8005E7A8)
- Start barrier (READY) + ping/pong RTT on status line ("slow" > 250 ms)

## Audio Latency
- Output buffer (DRC ring): target `buffer_ms` (default 180, allowed 30..500)
- SDL device buffer: 1024 samples = 23 ms @ 44.1 kHz
- Game judge runs on own clock → music heard lags game by fill + 23ms + OS

### Probe: `BAG2JP_AUDIO_PROBE=1`
- Writes `bag2jp_audio_probe.log` next to exe
- Once/sec: fill/target/underruns + frame gap > 40ms ("stall")
- Logs: `_work/np_logs/audio_probe_*.log`

### Resultados 1P Autoplay, Window Focused
| buffer_ms | fill while dancing | underruns while dancing |
|-----------|-------------------|------------------------|
| 180 | avg 164 ms (124..174) | none |
| 90 | avg ~80 ms | one burst at song start (~6s) |
| 50 | avg 42 ms (26..92) | one burst at song start |

### Song-Start Stall
- ~50 ms con HD texture pack OFF
- ~220 ms con HD texture pack ON (pack holds HD system font, 31 images, preloaded at boot 119ms)
- Not PNG decode; likely first upload/composition when text appears
- FLAC open = 0.2 ms
- 180 ms hid it; con menos buffer = short audio gap at song start
- **Set to 90** in exp install y patches/BAG2JP-game.toml
- **Next**: Remove song-start stall → then 50 (~75ms total) safe

## Release v7: Online Portable
- `releases/v7-online-portable/BAG2JP-online(.zip, 457 MB, 537 MB unpacked)`
- Exe + configs + mods (CD songs included)
- No personal paths (game.toml disc line removed, settings.toml [disc] empty, no disc.cfg)
- No logs/saves/test files
- Defaults: ONLINE=INTERNET, room code 2GWE, autoplay off, songs/announcer Japanese, buffer_ms 90
- LEEME.txt (Spanish how-to)
- First run no disc: launcher shows "No disc selected" → Browse → PLAY saves path

## Windows Installer
- NSIS 3.08 (Ubuntu debs extracted, no root)
- Sources: `installer/bag2jp_online.nsi`, `settings.toml`, `LEEME.txt`, `build.sh`
- Pages (Spanish): welcome → folder (%LOCALAPPDATA%\Programs\Bust A Move 2 Online, per-user) → game disc (.cue + .bin) → install → finish
- Checks: files exist, .cue single FILE line, .bin >= 100 MB
- Install: FLAC/MPG stored, rest zlib, .bin copied to disc_image\
- game.cue written from user's .cue, disc.cfg + settings.toml point to disc_image/game.cue
- Shortcuts: desktop + start menu (exe --no-launcher, launcher, instructions, uninstall)
- HKCU uninstall entry, uninstaller asks delete saves
- Tested end-to-end with real clicks (bag2_setup_test.ps1, etc)
- Bug fixed: `${GetSize}` is for folders; .bin size now via FileSeek END
- **Save card**: installer writes card1.mcd (DexDrive save) with SetOverwrite off
- Correction: save IS fully unlocked (hidden chars = real icons, DANCE VIEW appears)

## Referencias Rápidas
- `patches/BAG2JP-game.toml` - audio buffer_ms config
- `mods-src/bag2jp.feature.netsync` - plugin config
- `tools/test/bag2_report.py` - test reporting
- `installer/bag2jp_online.nsi` - NSIS script
- `_work/np_logs/` - audio probe logs