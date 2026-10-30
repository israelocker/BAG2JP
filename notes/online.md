# Online play, netsync, audio latency, v7 release and installer

## Online play (generic PSXRecomp netplay vs BAG1-style step sync)
- Generic netplay enabled in BAG2JP (CMakeLists: PSX_NETPLAY ON + ENABLE_NETPLAY_IF_PRESENT, lobby
  ws://netplay.retcomm.net:8765). Launcher gets a NETPLAY button: LAN / Direct IP (no account) or
  Online Netplay (Discord sign-in, lobby server). LAN keeps vanilla content: our mods are off in the
  match (JP title, no HD intro / international VS). Both players need the same .cue/.bin (disc
  fingerprint in game.toml [netplay]).
- Tested on one PC with two copies (second copy: _work/netplay_peer2): Join Direct 127.0.0.1:7777 works
  (joining from the LAN list did not on one PC). CLI test: --no-launcher --netplay --net-slot 0|1
  --net-bind --net-peer (delay-sync). 2P VS: character select, stage select and the dance stayed in
  sync, host and guest inputs both applied, no desync lines (PSX_RB_PAD_TRACE=1 logs to stderr).
- Test helpers in D:\Dev\Tools\winshot: winshot.ps1 (PrintWindow capture of covered windows),
  postkey.ps1 (posts key messages to a window; works when another app holds the foreground),
  sendkey.ps1, focus.ps1, np_cli.ps1 (starts the two CLI peers), dbg.ps1.
- BAG1 step sync (bag.netsync, colleague's port, source not public): BAG1 FUN_800207bc(player) is the
  per-player bar update; CPU player = bits 2-3 of 0x80068704; CPU decision FUN_80020e10 returns the
  bar result (0x46/0x3c/0x32 judged, -1 miss, 0x6e attack, 0xaa dodge); human FUN_80020a7c; apply
  FUN_80022884 (CPU) / FUN_80022130 (human). The plugin replaces the CPU decision with results that
  arrive from the other PC. Decompile: _work/bag1/bag1_decomp.txt.
- BAG2 JP: the same logic is inlined in the game module system/005.dbi (base 0x8008F890), giant
  FUN_80099e90; per-bar 2-player loop around 0x8009B000: CPU path when mode 0x8005D2C4 == 0 or
  (== 1 and player != human 0x8005E6C8); result code at 0x8005CF1C + p*0x24 (0x6e attack, 0xaa
  dodge), timing at 0x8005CF14 + p*0x24, per-player block 0x8005E728 + p*0x32. Decompile:
  _work/game/jp005_decomp.txt.
- Current BAG2JP CMakeLists.txt (with netplay on) copied to patches/BAG2JP-CMakeLists.txt.

## Online step sync (bag2jp.feature.netsync)
- Plugin src/bag2jp_netsync.c (copy + manifest + default server list in mods-src/bag2jp.feature.netsync).
  Same model as StepMania/SMOnline: each PC plays against its own music; only bar results travel.
- MODS menu: ONLINE = OFF / LOCAL NETWORK / INTERNET / DIRECT IP / TEST (MIRROR) (option transport,
  next start) and ROOM CODE (4 letters/digits, pad editor: Circle edit, Up/Down letter, Left/Right move,
  Circle/Cross save; stored in line 1 of bag2jp_online.txt; re-read live while not linked).
- LAN: UDP broadcast on 47300 with the room code hash. P1 = higher random id.
- INTERNET: MQTT 3.1.1 (QoS 0, plain TCP 1883) meeting point, topic bag2jp/v1/<room hash>; servers in
  bag2jp_online_servers.txt (written with defaults on first run: HiveMQ, EMQX, Mosquitto; STUN Google,
  Cloudflare), tried in order on a worker thread. HELLO carries the STUN public address and the LAN
  address; both sides punch UDP holes for 10 s; until a UDP packet arrives everything goes through the
  broker (relay). Test switch BAG2JP_NETSYNC_RELAY_ONLY=1.
- DIRECT IP: host (line 2 of bag2jp_online.txt empty) listens on UDP 47100 and shows its public address;
  join = line 2 "ip:port". Host is P1. Needs the port forwarded on the host's router.
- Menus routed as before (port 2 = controller source + transform; MODS screen still works through the
  netsync transform via bag2jp_mods_menu_pad_filter / _reattach).
- Character select popup (BAG1/BAG2 version + costume) online: messages M_PICK / M_CONTENT, see
  notes/bag1-character.md (Character select popup).
- Per bar: gate 0x8009ABC4 closes the local bar (FUN_800120F8) and sends it; the bar waits (max 180
  frames) for the other result. NEW: 0x8009A0C0 (bnez v0, beat advance) holds the beat that starts the
  next bar until the waiting bar is resolved (before this, a late result dropped the bar on one PC).
  Hold even when the result arrives that frame (the advance runs before the resolve).
- Out-of-sync check: STEP carries COOL/right-bar counts (0x8005E798 / 0x8005E7A8, P1/P2) at the close;
  a difference shows a toast. (Scores 0x8005E6F8 count up over time, so they differ by timing: log only.)
- Start barrier (READY) when the match module loads; ping/pong RTT on the status line ("slow" > 250 ms).
- Tests on one PC with two copies (keep both windows in the background: the copy behind the foreground
  game window was throttled to ~35 fps): LAN, internet with direct path (HiveMQ meeting, STUN, punch),
  internet relay-only (~400 ms RTT through HiveMQ from Lima): 40 bars, all identical on both PCs, waits up
  to 34 frames held correctly. Direct IP link OK (127.0.0.1:47100).
- Not tested yet: two real PCs on different networks (hole punching through real NATs), rematch/results.
- Tools: D:\Dev\Tools\winshot (bag2_two.ps1 [-RelayOnly] [-BArgs], bag2_vs_flow.ps1 [-FromTitle],
  winshot.ps1 [-Screen], postkey.ps1, focus.ps1).

### Auto pause when a window loses focus (online dance)
- During an online dance (after the start barrier), if either PC's game window loses keyboard focus
  (`SDL_GetKeyboardFocus() == NULL`: alt-tab, minimize, another app), BOTH PCs pause with the runtime
  host pause (`psx_host_pause_push("online")`: guest and audio frozen, last frame kept on screen).
- Message `M_FOCUS` (9): u8 focused, u8 paused, u16 match, u32 dance frame of the pause. Sent on every
  focus change and every 20 frames with the ping.
- OSD: "ONLINE  PAUSED - come back to the game window to continue" (this PC) or "... - the other player
  left the game window"; when both are back, "ONLINE  resuming in 3..." and both resume. The PC whose own
  window came back waits half a ping more so both resume together; leftover drift (half a ping) is
  absorbed by the bar hold.
- The vblank plugin does not run during a host pause, so an SDL timer (16 ms) keeps the link alive
  (net poll, pings, focus) and pops the pause. `s_mu` (SDL mutex) serializes the timer with the vblank
  plugin and the three instruction hooks. If the link drops or the dance ends, the pause is released.
- A first version compensated the "dance frames ahead" between PCs; removed: hold frames make that
  count run ahead without the song being ahead (it made one PC wait 2 s more).
- No-step-in-time on a bar where this PC has no steps either (result 0xFFFF) now writes "no bar" for
  the rival instead of a miss (result 0).
- Test switch `BAG2JP_NETSYNC_FOCUS=always` (this PC counts as always focused);
  `bag2_two.ps1 -BFocusAlways` sets it for copy B. `focus.ps1` now attaches to the foreground thread and
  falls back to minimize/restore (Windows foreground lock). New `keys_shot.ps1 -Ids "a,b" -Keys ... -Wait`.
- Tested on one PC (LAN): pause at dance start, mid-dance pause from either side, countdown in step on
  both, bar results identical through two pauses. Same-PC caveat: the background copy runs ~35-45 fps,
  so long songs pile up bar holds and the faster copy can leave the bar section before the slow one.

## Audio latency (game.toml [audio] buffer_ms)
- The runtime keeps an output buffer (DRC ring, target `buffer_ms`, default 180, allowed 30..500)
  plus the SDL device buffer (1024 samples = 23 ms at 44.1 kHz) plus Windows. The game's judge runs
  on its own clock, so the music heard lags the game by roughly fill + 23 ms + the OS.
- Probe: `BAG2JP_AUDIO_PROBE=1` (in bag2jp_netsync.c) writes bag2jp_audio_probe.log next to the exe:
  once a second fill/target/underruns, plus every frame gap > 40 ms ("stall"). `bag2_1p.ps1 -SetEnv`.
  Logs: _work/np_logs/audio_probe_*.log.
- Results, 1P autoplay, window focused:
  | buffer_ms | fill while dancing | underruns while dancing |
  | 180 | avg 164 ms (124..174) | none |
  | 90  | avg ~80 ms | one burst at song start (~6 s into the stage) |
  | 50  | avg 42 ms (26..92) | one burst at song start |
- The burst comes from a frame stall at song start: ~50 ms with the HD texture pack off, ~220 ms with
  it on (the pack holds only the HD system font, 31 images, preloaded at boot in 119 ms, so the stall
  is not PNG decode; likely the first upload/composition when that text appears). FLAC open is 0.2 ms.
  180 ms hid it; with less buffer it is a short audio gap at the start of each song.
- Set to 90 in the exp install and in the project game.toml (patches/BAG2JP-game.toml). Next: find
  and remove the song-start stall; then 50 (about 75 ms total) should be safe.

## Release v7: online portable (2026-10-29)
- releases/v7-online-portable/BAG2JP-online(.zip, 457 MB, 537 MB unpacked): exe + configs + mods
  (CD songs included), no personal paths (game.toml disc line removed, settings.toml [disc] empty,
  no disc.cfg), no logs/saves/test files. Defaults: ONLINE = INTERNET, room code 2GWE, autoplay off,
  songs/announcer Japanese, [audio] buffer_ms 90, player_name "Player". LEEME.txt (Spanish how-to).
- First run with no disc: the launcher shows "No disc selected"; PLAY answers "Select a valid Disc
  first"; "Browse For Disc / SBI" opens the file dialog, then "Disc verified" and PLAY saves the
  path to settings.toml and disc.cfg (not asked again).
- Tested from the extracted zip (_work/portable_test): launcher > Browse > PLAY, joined room 2GWE
  on broker.hivemq.com, linked with netplay_peer2 (direct after the broker), both into 2PLAYER GAME,
  match start barrier and the focus pause on both PCs.
- New tools: winshot\realclick.ps1 (real mouse click at window fractions), typetext.ps1 (SendKeys),
  postclick.ps1 (posted click; does not work on the launcher), bag2_vs_flow.ps1 -AD/-BD.

## Windows installer (2026-10-29): releases/v7-online-portable/BAG2JP-Online-Setup.exe (451 MB)
- NSIS 3.08 (Ubuntu debs extracted into ~/tools/nsis, no root; added to Tools/vm-setup/setup_vm.sh).
  Sources: installer/bag2jp_online.nsi, settings.toml (disc path "disc_image/game.cue"), LEEME.txt
  (installed-game version), build.sh (payload = the portable zip extracted to ~/work/installer).
- Pages (Spanish): welcome (what you need) -> folder (default %LOCALAPPDATA%\Programs\Bust A Move 2
  Online, per-user, no admin) + "desktop shortcut" checkbox -> game disc (.cue + .bin; picking the
  .cue fills the .bin if it sits next to it; checks: files exist, .cue, single FILE line, .bin >= 100
  MB) -> install -> finish ("Abrir el juego ahora", optional LEEME).
- Install: game files (FLAC/MPG stored, rest zlib), .bin copied to disc_image\, game.cue written from
  the user's .cue with its FILE line pointing at the copied .bin, disc.cfg + settings.toml point at
  disc_image/game.cue (relative, resolved against the exe folder). Shortcuts: desktop + start menu
  "Bust A Move 2 Online" (BAG2JP.exe --no-launcher), "BAG2JP - Configuracion" (launcher),
  "Instrucciones", "Desinstalar"; HKCU uninstall entry. Uninstaller asks whether to delete saves.
- Tested end to end with real clicks (winshot\bag2_setup_test.ps1, bag2_uninstall_test.ps1,
  check_shortcuts.ps1): install into _work\installer_test, game opened from the finish page straight
  into the intro (disc found), joined room 2GWE; uninstall removed folder, shortcuts and entry.
- Bug found and fixed in testing: ${GetSize} is for folders; .bin size now via FileSeek END.
- 2026-10-29 (later): the zip and the installer now carry the user's memory card (saves\card1.mcd,
  the DexDrive save). The installer writes it with SetOverwrite off (a reinstall never replaces a
  player's card). LEEME: if the game does not pick it up, OPTIONS > MEMORY CARD > LOAD DATA > YES
  (tested: "LOAD OK").
- Correction (user): the save IS fully unlocked. The "?" cells are the real icons of the hidden
  characters; on an empty card those cells and DANCE VIEW do not appear at all. All my char-select
  tests had card1.mcd in place (copied before the first test), and the game loads the card at boot
  by itself. So shipping the card = everything unlocked, and both online players get the same grid.
  The CodeBreaker plugin attempt was therefore not needed; source kept in _work/bag2jp_unlock_all_wip.c
  (untested on an empty card). LEEME now says the save comes fully unlocked and loads by itself.
