---
topic: song-start-sync
status: investigating (native reference measured; port comparison pending)
updated: 2026-11-17
---
# Song start sync (testers: "songs start slightly early")

## Native mechanism (Ghidra, SLPM_862.19 + overlay 005.dbi)
- `FUN_800358bc(song_idx)`: Mute, SetFilter(file1, idx&7), SetMode 0xC8, Setloc+ReadS (pos table 0x80089270), Demute; resets frame counter 0x800892EC.
- `FUN_80035b44` updates 0x800892E4 from GetlocL each frame.
- 005.dbi gate (80098730 / 8009909c / 8009d990): dance/chart start (0x8005D3DC=1) only when GetlocL position passes the saved start sector. Music and chart therefore start together, after the real CD seek.

## Native reference (DuckStation 0.1-12640, log `Seek time`, Heat song a0=0 at 08:16:32)
| run | mode | from | seek |
|---|---|---|---|
| demo | 0 | 02:24:17 | 366.7 ms |
| campaign Comet vs Heat (rival table 0x80051334 forced) | 1 | 01:50:63 | 374.8 ms |
| practice Heat | 3 | 01:48:46 | 372.1 ms |
| practice RETRY | 3 | 10:03:12 | 305.1 ms |
| demo Hiro vs Heat | 0 | 01:50:61 | 372.5 ms |
Same call site (ra=800986f4) in all modes. Seek is always a far "sled" seek: 305–375 ms.
VS (mode 2) not yet measured: the title "2player game" entry did not open with virtual pad 2 (unresolved).
Caveat: DuckStation's seek model is approximate vs real hardware.

## Port
`psxrecomp/runtime/src/cdrom.c` `start_read_stream`: `read_delay = initial_read_delay_cycles()` = one sector (~13 ms), no seek component even if `setloc_seek_far`. Expected: song + chart start ~290–360 ms earlier than native relative to the stage intro.
Pending: confirm in a recorded port run (`PSX_RB_CD_BISECT=1` logs ReadS arm), then a bounded fix (seek delay for far Setloc+ReadS) with recorded validation.

## Tools
`tools/test/duck_gdb.py` (GDB RSP logger, --bp/--read/--write); `_work/sync/vpad.py` (ViGEm pads; JP: Circle=B confirms, Cross=A cancels, title confirms with START); `_work/sync/dshot.py` (background capture).

## Port measurement 2026-11-17 (VS Heat vs Heat, exp-8mb, BAG2JP_AUDIO_DUMP)
- Song request (0x800892E8 0, 0x800892F0=0x081632) at gf 2738; dumped mix audio audible from +0-70 ms (rising RMS from +0 ms, strong at +500 ms). Native seek before audio: 305-375 ms (DuckStation). Port therefore starts audio ~300 ms earlier relative to the request frame.
- Anomalies to resolve: in port 0x800892E4 (GetlocL position) stays 0x1735 (not BCD start/progress) and 0x8005E2E4 stays 0, 0x8005D3DC unchanged; the 005.dbi gate path observed natively (ra 800986f4) not confirmed in port VS. Next: Ghidra/trace which caller starts VS song in port and why GetlocL returns 00:17:35; then test adding the far-seek delay in cdrom.c start_read_stream.
- Recording attempts: sync_vs1 accepted but started after song start; sync_vs2 raw.mkv empty (recorder attached during game restart). No valid video of song start yet.

## Experiment PSX_CD_XA_FAR_SEEK_MS (2026-11-17, WIP, not accepted)
- cdrom.c start_read_stream (build tree): if Setloc pending + setloc_seek_far + mode&0x40, add env PSX_CD_XA_FAR_SEEK_MS ms (default 0 = unchanged). Built (workflow tag xa-seek), deployed to exp-8mb exe sha256 700FB13196B7...; backup BAG2JP.exe.bak-xaseek.
- VS Heat, =360: audio onset rms>300 at +428 ms (baseline +69 ms), rms>3000 +872 ms (baseline ~+500 ms) -> shift ~360 ms as intended. Script _work/sync/onset.py.
- OPEN RISK: in port VS, 0x8005E2D4/0x8005E2E4 read 0 and 0x8005D3DC unchanged, so it is unproven that dance/chart wait with the audio; if not, the delay would desync chart vs music. Must verify chart-vs-music alignment (recorded video, baseline vs delay) before any acceptance.

## Recorded takes 2026-11-17 (accepted manifests)
- sync_rec_base3 (exe 700fb131…, PSX_CD_XA_FAR_SEEK_MS unset) and sync_rec_seek3 (=360): both ACCEPTED (wgc + process audio). Driver: _work/sync/rec_take.ps1 (recorder starts after window resize settles; earlier takes failed with 'capture window resized' -> raw.mkv 0 bytes).
- Audio onset vs song request: base 29/69/513 ms (rms>40/300/3000); seek 388/428/872 ms. Shift of +359 ms reproduced.
- FINDING: the bag2_run.ps1 flow ends in Dance View (ROUTE/SPEED/CAMERA HUD), not a scored VS match, so there is no chart to compare. The HUD appears ~+62..74 frames after the request in both takes: it does NOT move with the delay. Heat's idle bounce could not be resolved at 4 fps. Not proven: whether chart/dance timing in a scored match follows audio.
- Next: a scored-match take (practice or 1P) in the port, frame-level comparison of first chart arrow vs audio onset, with and without the delay; same in DuckStation.

## Practice-mode takes 2026-11-17 (scored flow, accepted manifests)
- bag2_run.ps1 / bag2_2p_pick.ps1 got -Downs (default 3 = Dance View, unchanged); 1 = 2player (P2 pick not automated), 2 = practice.
- In practice the native gate RUNS in the port: 8005E2E4 := start sector, 800892E4 advances via GetlocL, 8005D3DC 0->1 (dance start).
- sync_pr_base4: request f3071, gate f3073 (+2 frames); audio onset 14/54/493 ms.
- sync_pr_seek4 (PSX_CD_XA_FAR_SEEK_MS=360): request f3080, gate f3103 (+23 frames = 383 ms); audio 388/428/872 ms.
- Conclusion: the dance/chart start follows the CD read, as in the original, so the delay moves music AND dance together (+21 frames vs +359 ms audio). Port today starts both ~300-375 ms earlier than native relative to the intro.
- Dance View has no gate (HUD on a fixed frame), which is why the earlier takes did not move.
- Pending: decide the default (fixed ms vs seek model by LBA distance), make it the default for far XA ReadS, full song + return-to-select validation, owner listening.

## Seek model as default (2026-11-17, WIP experimental, owner conformity pending)
- cdrom.c: `xa_seek_model_cycles(from,to)` = DuckStation GetTicksForSeek (2N <7200 LBA: 50/100 ms; sled: 0.05+0.85*(0.4*ln d/ln 324000+0.6*d/324000) s), applied in start_read_stream when Setloc pending + far + mode&0x40. `s_setloc_from_lba` stored at Setloc. PSX_CD_XA_FAR_SEEK_MS: unset = model (default), 0 = off, N = fixed ms (clamped 0..2000).
- FMV/STR path unaffected: SeekL/SeekP completion clears setloc_seek_far and setloc_pending (cdrom.c ~2657) before their ReadS (mode 0xC0); read_continues_current_stream (~1661) only when no seek is needed.
- sync_pr_model5 (exe 815217F1…): request f3076, gate f3100 (+24 f); audio 398/438/797 ms (native DuckStation seek 372 ms). sync_pr_full5: full song, RESULT screen (RETRY/QUIT) reached. Both ACCEPTED. Not exercised: QUIT/return to select, VS, campaign, BAG1 songs, FMV/XA dialogue playback.
- Clamp rebuild (workflow tag xa-seek-clamp) deployed to exp-8mb, exe B4F503DFD2C8A036…; changes only the fixed-N debug path, so default behaviour equals the tested 815217F1 build (not re-run).
- Patch: patches/psxrecomp-xa-song-seek-time.patch (`git apply --check --reverse --recount` OK on build tree).
- Goldfish (spec _work/goldfish/spec-xa-song-seek.md): CON HALLAZGOS, non-blocking. Fixed: int overflow for large N (clamp). Open: model omits motor spin-up/short seek; FMV/voice XA after far Setloc untested in game; getenv read once.
- Next: owner listening of _work/recordings/sync_pr_full5/owner.mp4 and tester feedback; then QUIT/return-to-select and a VS/campaign take before acceptance.
- 2026-11-17 owner: conforme con el arranque en sync_pr_full5 (escucha).
- sync_pr_quit6 (ACCEPTED): RESULT -> K,S selects RETRY (cursor is horizontal); song restarts with music, no hang. sync_pr_quit7 (ACCEPTED, exe B4F503DF, model default): RESULT -> Right,S = QUIT -> title menu (1player/2player/practice...) reached and stable for 12 s. _work/sync/rec_take.ps1 gained -PostKeys/-PostWait.
- VS/campaign not recorded in the port: 2P pick and 1P campaign are not automated in the harness. Native evidence: all modes (demo, campaign, practice, RETRY) start the song from the same call site (ra 800986f4) with the same far seek, so the same port path applies; unverified in game.
- 2026-11-17 VS and campaign automated (D:/Dev/Tools/winshot/bag2_2p_pick.ps1: -Downs 1 adds 3 x P2 circle M = pick, popup, difficulty; -Downs 0 = 1player campaign). exe B4F503DF, model default, all ACCEPTED:
  - sync_vs_try10 (2player, Heat vs Heat, Heat stage): request f3763, gate f3785 (+22 f); audio rms>300 at 413 ms, rms>3000 852 ms. Match in progress.
  - sync_camp11 (1player campaign, Heat vs Strike, song idx 1, stage 1): request f2701, gate f2725 (+24 f); audio 388/508 ms. Match in progress, scoring works.
  - Native DuckStation references: campaign 374.8 ms, practice 372.1 ms. Port now within ~15-40 ms of native in practice, VS and campaign.
- Not verified: BAG1 songs, FMV/XA dialogue in game (code path analysis only), song end/return in VS/campaign.
- 2026-11-17 more takes (exe B4F503DF, model default, ACCEPTED):
  - sync_vs_full12: VS Heat vs Heat full song (f3765..f14410, 177 s), back to Character Select; audio 413/852 ms (same as try10).
  - sync_vs_bag1_14: VS stage HEAT BAG1 (stage select is horizontal; bag2_2p_pick/bag2_run/rec_take got -StageDowns n = Right presses). Log 'entry 200 -> BAG1 JP', content log heat_2bad_japanese.flac. Request f3875, gate f3897 (+22 f), audio rms>300 at 363 ms: the BAG1 song follows the same delayed start.
- Still not verified in game: FMV / XA dialogue (code path only), BAG1 song end in VS with this exe.
- 2026-11-17 sync_vs_bag1_full15 (ACCEPTED, exe B4F503DF): VS HEAT BAG1 stage (entry 200) full song f3916..f13159, audio start 363 ms, ends and returns to Character Select. Installer note (owner, next generation): release2 payload carries test junk (nested duplicate bag1-content ~170 MB, overlay_captures.json.d, exe backups, _to_delete, dumps, 71 test memory cards, mods/installed bag2jp.test.*); clean before next installer.
- 2026-11-17 other songs (exe 56142B56 = B4F503DF + env-gated PSX_CD_XA_SEEK_LOG stderr line, deployed exp-8mb; installer still B4F503DF). All ACCEPTED:
  - sync_prac_c2 (practice Comet), sync_vs_comet16, sync_vs_stage2 (song idx 2), sync_vs_stage4 (song idx 1): every song request uses the same XA start LBA 37082 (F0 81632); songs differ by idx/channel, not by disc position. Only the head's previous position varies: from 1127/8166/17808 -> delay 401/384/358 ms. stage4 audio rms>300 at 368 ms.
  - Conclusion: per-song distance does not vary in BAG2 songs; the model delay range seen is 358-459 ms, consistent with native 305-375 ms (+ up to ~60 ms). onset.py fails when song idx is 2 (only accepts 0/1).
- 2026-11-17 boot/intro take sync_fmv18 (ACCEPTED, exe 56142B56, idle from boot 130 s: intro, title, demo). Intro is the hd-intro mod (host MPG audio); bag2jp_hd_intro.log reads disc STR lba 214715..224035 and stops at 847: no xa-seek line for the STR stream (FMV path not delayed, as expected from code). Seeks logged: from 879 to 110586 = 547 ms (after intro, before title; title music is presumably at 110586, not confirmed), then from 8166 to 37082 = 384 ms (demo song). Native head after a full disc FMV would be near 224035; the model gives ~537 ms for that distance, ~10 ms from the port value. Not measured in DuckStation. Disc FMV audio itself (without hd-intro) and XA dialogue in story scenes still untested.
- 2026-11-17 drift check (gameplay songs): audio_sync.log over full songs sync_vs_full12 (f3785..f14400) and sync_vs_bag1_full15 (f3938..f13150): 734.996 samples/frame (44100 Hz), every 30 s window 734.91-735.02 -> audio and game frames stay locked, no accumulated drift (<0.02 %, < ~4 ms over 3 min). Beat-phase fold (beatdrift.py) too noisy (SFX, +-250 ms jitter): not usable as evidence. Remaining residual is only the start offset (gate vs audible start: VS +46 ms, campaign -12 ms, BAG1 -4 ms, crude RMS threshold). Not done: same-song native drift measurement (recorder cannot capture DuckStation).
