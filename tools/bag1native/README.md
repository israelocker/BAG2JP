---
id: bag1native-reference-tools
title: "Native BAG1 reference tools"
tags: ["bag1", "reference", "tools"]
summary: "External RAM and input helpers for the SCUS_942.63 reference runtime; writes require isolated sessions and restored controls."
related: ["notes/strike-recovery.md", "notes/character-import-testing.md"]
created: "2026-11-05"
updated: "2026-11-06"
doc_kind: reference
---

# Native BAG1 reference tools

External helpers for the native BAG1 runtime (`BustAGroove_Recompiled.exe`, reference install
`D:/Dev/Scratch/bag1-native-reference`). The BAG1 exe has no plugin source, so these tools read and
write PSX RAM from outside the process.

## bag1_mem.py
Finds `static uint8_t ram[]` (psxrecomp `memory.c`) inside the exe image by matching three
`SCUS_942.63` text probes, then reads/writes PSX addresses.

    py -3.13 tools/bag1native/bag1_mem.py base
    py -3.13 tools/bag1native/bag1_mem.py read 80068766 1 h

Heap copies of RAM (rewind/savestates) also match the probes; only the image copy is live.

## attack_bot.py
Presses a button on the rising edge of the bar boundary (`0x80068704 & 0x10`) so the human
command path (`FUN_80021c6c` -> `FUN_80022130`) accepts a Jammer attack. Verified 2026-11-05:
P1 Strike vs P2 Heat, 2/2 attacks accepted (`0x80068766` 2 -> 1 -> 0, flags `0x808`).

    py -3.13 tools/bag1native/attack_bot.py --player 1 --seconds 40 --log <run>/attack.json

Requires the temporary keybinds from `_work/character_import/strike/native_combat_probe.py boot`
(P1 Triangle = `A`, P2 Triangle = `V` -> `--player 2 --vk 0x56`) and the game window in the foreground.

## RAM map (SCUS_942.63, per player p, stride 0x14 unless noted)
| Address | Meaning |
|---|---|
| `0x80068704` | bar state: `0x01` beat tick, `0x80` pre-boundary, `0x10` bar boundary, `0x02` bar evaluation |
| `0x80068440` (low 16) | beat counter |
| `0x800686e8` (s16) | beats remaining; attack backfires when `< 5` |
| `0x8006875e` | player flags: `0x10` incoming attack, `0x08`/`0x04` attack accepted, `0x900` backfire, `0x80` hit |
| `0x80068766` (s16) | remaining attacks (2 per round) |
| `0x800687e8 + p*0x4b0` | input history, 150 entries x 8 bytes, index `0x80069148` |

Recording: `ffmpeg -filter_complex ddagrab=...` (see `notes/strike-recovery.md`); `gdigrab` gives black frames.
