---
id: tool-evidence-jpsxdec
title: "Evidencias: jPSXdec"
tags: ["tools", "evidence"]
summary: "Historial de jPSXdec; XA regional Gas-O decodificado y contrastado estructuralmente, escucha/asignación pendientes."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# jPSXdec — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-jpsxdec-001 — antecedente de instalación
- Tipo: arranque histórico; transcrito el 2026-11-06, no reejecutado.
- Versión: v2.1, distribución beta, Java 21; comando exacto en
  `D:/Dev/Tools/ps1-community/smoke-results.json`, objeto `jpsxdec`.
- Entradas: sin XA/STR; no aplica región/módulo. Archivo JAR/procedencia en
  `D:/Dev/Tools/ps1-community/installation-manifest.json`.
- Observado: ayuda `-?`, salida 0. No decodificación ni contraste independiente.
- Evidencia: manifiesto y reporte anteriores; `_work/tool-install/jpsxdec-help.log`.
- Dictamen: **inconcluso** para utilidad BAG2JP; solo acredita ayuda CLI.
- Medición: tiempos y ahorro no medidos; no hay referencia comparable.
- Siguiente: contrastar copias con hash de XA/STR, canales, duración y contenido.

## 20261106-jpsxdec-002 — DANCEXA2 USA/JP, canal candidato Gas-O

- Propósito: extraer audio real y comprobar si las regiones pueden compartirlo.
- Versión: jPSXdec2.1-beta, Java21.0.12.1+1. Comando base PowerShell:
  `& D:/Dev/Tools/jdk-21.0.12.1+1/bin/java.exe -jar D:/Dev/Tools/ps1-community/jpsxdec-2.1/jpsxdec_v2.1-beta/jpsxdec.jar`.
  Sufijos ejecutados para cada región: `-f <source> -x <index>`,
  `-x <index> -i 1 -dir <output>`; ayuda de ítem JP `-x <index> -i 1 -help`.
  Fuentes `_work/bag1jp_disc_full/XA/DANCEXA2.XA` y
  `_work/bag1_disc_full/XA/DANCEXA2.XA`; índices `_work/gaso/dancexa2-{jp,usa}.index`;
  salida `_work/gaso/audio-{jp,usa}/DANCEXA2.XA[1].wav`. Sin alterar originales.
- Hashes fuente JP `81ecaa875e0d3c62bc9c1e0b2193d9ba2db0a2f739bac76cb8f9fda1f9b74b78`,
  USA `e80ce5626f284260963263f646a8ed7fe8348302b6d9f076ffeed9616ecbc52a`.
- Evidencia: `_work/gaso/dancexa2-*-index.log`, `*-decode.log`, `*-item-help.log`;
  `_work/gaso/audio-region-audit.json` y script `audit_audio_resume.py`.
  Exit0 en índices/decodificaciones. Ambas: file1/channel1, sectores1..22929
  stride8, estéreo37800Hz4bit,152.9066667s,5779872frames. PCM JP
  `8832b9624d3ce75b80e2395d0f8e8c941395d0137f23bedd285056d061c99b82`, USA
  `d8a58f14e34f23e6480daa8500c6c2af5b5ab34985a8ace38480a7755bf802b6`.
- Contraste independiente: subheaders duplicados de cada sector2336bytes,
  selector canal1/audio, coding1,2867sectores×2016frames; WAV coincide en
  parámetros y número de muestras. ADPCM regional también difiere. No segundo
  decodificador ni escucha humana; asignación nativa Gas-O aún pendiente.
- Intento contraproducente registrado: `py -3.13 _work/stage_import/strike/scripts/xa_channels.py`
  sobre XA JP asumía2352bytes y offset16; produjo falsos canales/4468líneas.
  Se descarta su conclusión, no se modificó el script. Salida completa retenida
  en `C:/Users/israe/.local/share/opencode/shell/4ba40e57ef1a3c1bfb94ef1ebe3a673329380f1c/sh_1b178ce0d001XXM9rbuIqSo3hq.out`.
  El auditor corregido usa2336bytes/offset0 y valida cabeceras antes de contar.
- Dictamen: **útil** para extracción/contraste estructural regional; no aceptar
  identificación ni calidad subjetiva. Decode JP informó0.83s; total, ahorro y
  retrabajo no medidos. Siguiente: confirmar mapping nativo, escucha y conversión
  separada por región antes de integrar; no deduplicar estos PCM.

## 2026-11-06 — 003: Heat/Strike regional extraction and CD-source contrast

- Purpose: owner requested missing Heat/Strike variants now. Same installed
  jPSXdec2.1-beta/JDK21.0.12.1+1 as002, no installation/config changes.
- Commands: Java/jar as002, `-f _work/{bag1jp_disc_full,bag1_disc_full}/XA/DANCEXA1.XA
  -x _work/gaso/dancexa1-{jp,usa}.index`, then `-x <index> -i 0|1
  -dir _work/gaso/{heat,strike}-audio-{jp,usa}`; absolute paths in invocation.
  Both indexes and all four decodes exit0; logs in `_work/gaso/` with
  `dancexa1-*-index.log`, `heat-*-decode.log`, `strike-*-decode.log`.
- Independent audit: `py -3.13 _work/gaso/audit_shared_music.py`, NumPy2.3.5,
  validates2336-byte duplicate subheaders, coding1, stride8, ADPCM hashes and
  WAV stereo37800Hz samples=sectors×2016. Complete source/PCM/CD hashes and
  windows: `shared-music-audit.json` then corrected `shared-music-audit-v2.json`.
  Existing matcher reused from regional/tools/hq/match.py; no model/GPU used.
- Results: Heat JP/USA138.026667s, Strike JP132.053333s/USA137.013333s; both
  have differing regional ADPCM and PCM. Do not infer identical content from
  similar sound or apply JP129s battle length to USA without native evidence.
- Failed hypothesis retained: first CD probe used03Transform for Strike and
  found zero PCM windows>=0.6; corrected to12Power,5per region. Heat02/2Bad
  has9per region. ChemicalLove06 high envelope correlation but PCM<0.6;
  threshold is not listening acceptance. Reused unchanged Heat/Gas-O results
  in v2 rather than repeating their probes. No CD render generated.
- Downstream conversion: `py -3.13 _work/gaso/prepare_regional_flac.py`, calls
  installed `D:/ffmpeg/bin/ffmpeg.exe -hide_banner -loglevel error -n -i <wav>
  -ar 44100 -ac 2 -c:a flac <new-candidate>` for six regional variants, then
  ffprobe checks codec/rate/channels and duration. Six exit0 and metadata
  assertions pass. Output/hash/source provenance in
  `_work/gaso/regional-music-candidate/report.json`; not staged/deployed,
  no truncation/fade, XA-derived not CD quality. Existing Heat files preserved.
- Outcome: useful structural/regional preparation; no second decoder, no
  subjective listening or in-game acceptance. Total/manual rework/savings
  unmeasured. Next: native USA timing, CD edits, existing songs-option wiring,
   full experimental song/return test. Model/stage mod granularity still a gate.

## 20261106-jpsxdec-004 — CD-only edits downstream of 003

- Type: real postprocessing of retained jPSXdec output; jPSXdec was NOT rerun.
  The later owner approval fixes visual choices globally with Japanese defaults;
  the gate mentioned in003 is historical, not still open.
- Environment: Windows Python3.13/NumPy2.3.5; existing regional HQ matcher;
  `D:/ffmpeg/bin/ffmpeg.exe` build2024-09-19-git-0d5b68c27c-full_build-www.gyan.dev.
  No overlays/game process/GPU involved. Earlier Ghidra main-program evidence
  remains unchanged; this trial edits assets, not game code.
- Commands, canonical root: `py -3.13 _work/gaso/probe_cd_edits.py`, then
  `refine_cd_cuts.py`, `render_cd_edits.py`, `verify_cd_edits.py` with same prefix.
  All exit0. Dense3s windows each second plus local0.5s refinements retained in
  `cd-dense-alignment.json` / `cd-cut-refinement.json`; original files read-only.
- Inputs: JP WAV references and original CD tracks from003, not XA upsampling.
  Power CD12 SHA256284b83899967effbdbc46b78f31329b3d2cb7ac3db18eeda7a3e149b361401d7;
  ChemicalLove CD06 SHA256a3b982a6abce37a1e6cbdf184c6d5865d9db4e87df4f2bdc8c6f1ee225b94e09.
  All reference WAV paths/hashes in `cd-edits-candidate/report.json`.
- Output: `_work/gaso/cd-edits-candidate/strike_cd.flac`,129s,
  SHA2564dd30687ec749208ed05b40bc5ecd5bbbeba32c382070224e22f98f6afc9482f;
  `gaso_cd.flac`,150s,
  SHA256df3ff38319ccb60706c35bfa3165977a4181ad36ada6eea004deb9cd24ce67c6.
  Both stereo44100Hz/16bit FLAC. Gas provisional splices18.85/92.37s,25ms blends;
  robust affine timing per section, static body gain and reference edge attenuation.
  Zero XA PCM in output: the game reference supplies timing/level evidence only.
- Negative/ambiguous evidence: Strike intro0–16s and ending120–129s have no
  reliable CD match; extrapolated body timing does not recreate game-exclusive
  material. Gas repeated chorus120–127s causes misleading global alternative
  matches; bounded comparison supports keeping the continuous final section,
  not following every maximum through unrelated repeats. First Gas splice has
  only modest envelope-cost improvement; neither splice is listening-accepted.
- Independent verification: separate script uses ffprobe metadata, full ffmpeg
  s16 decode, exact frame counts5688900/6615000, source/output hashes unchanged,
  no saturated output samples and near-zero final sample. Same-timeline envelope
  comparison has9/12strong anchors, each within20ms; `verification.json` retains
  every window. This does not establish subjective sound quality or game sync.
- Outcome: useful candidate generation and objective structural checks;
  faithful Strike edges and subjective audio acceptance remain inconclusive.
  No original overwritten, no build staging/deployment/game run.
- Measurement: renderer4.712s (`perf_counter`, includes rendering and its checks);
  total preparation, listening/manual rework, baseline and savings unmeasured.
  Next: owner listening of Strike edges/Gas splices, revise if needed, then
  experimental full-song/fever/return validation with the existing songs mod.

## 20261106-jpsxdec-005 — not applicable to Gas-O SPU voice budget

- Type: applicability decision; jPSXdec was NOT run.
- Purpose: reduce Gas-O voice VAB body to the stock Bi-O 64032-byte SPU budget
  (owner-approved dedup + resample; diagnosis ghidra-033/034).
- Reason: jPSXdec decodes XA/STR streams; it does not encode SPU VAG ADPCM nor
  rewrite VAB headers/tone pitch. No installed tool in `notes/assets.md` covers
  that; installing psxavenc would need permission.
- Substitute: local shared encoder `tools/bag1import/vab_budget.py`, host tests
  `tools/test/test_vab_budget.py` (11 OK). Result recorded in `notes/gaso-import.md`.
- Outcome: irrelevant for this task (no utility claimed or refuted).
  Measurement: none. Next: none for jPSXdec on this step.
