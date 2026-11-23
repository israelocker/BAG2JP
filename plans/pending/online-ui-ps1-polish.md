---
id: online-ui-ps1-polish
title: "Plan de trabajo: Pulido PS1 nativo del Modo Online (Transiciones, SFX, Animaciones y Mando)"
tags: ["online", "ui", "ps1", "sfx", "transitions", "plan"]
status: pending
created: "2026-11-22"
updated: "2026-11-22"
related: ["plans/pending/online-native-lobby.md", "plans/pending/online-lobby-2instance-tests.md", "mods-src/bag2jp.feature.netsync/src/bag2jp_lobby_ui.c"]
---

# Plan de trabajo: Pulido PS1 nativo del Modo Online

## Objetivo
Hacer que el **Online Lobby** y la **Sala 1 vs 1** se sientan indistinguibles de un menú original de **Bust A Groove 2 (PS1)**: transiciones suaves a negro, efectos de sonido nativos del juego en cada acción, feedback visual de selección/error y soporte de mando/gamepad además de teclado.

---

## Opciones y fases propuestas

### Fase P1: Transiciones de difuminado a negro (Fade-out / Fade-in)
- **Qué hace**:
  - Máquina de estados de transición en `bag2jp_lobby_ui.c` (`FADE_NONE -> FADE_OUT -> SWITCH_SCREEN -> FADE_IN`, ~15 fotogramas salida + ~15 fotogramas entrada a 60 fps = ~0.5 s total, igual que los menús de `system/002.dbi`).
  - Aplica a todas las transiciones:
    1. `Menú Principal (online match)` -> `Online Lobby`
    2. `Online Lobby` -> `Sala 1 vs 1` (al crear `[C]` o unirse `[Enter]`)
    3. `Sala 1 vs 1` -> `Online Lobby` (al salir `[Esc]`)
    4. `Online Lobby` -> `Menú Principal` (`[Esc]`)
    5. `Sala 1 vs 1` -> `Partida Versus` (al aceptar `match_start`)
- **Prueba de aceptación (TP1)**:
  - Grabación oficial `bag2_record.py` (`manifest.json` `"accepted": true`) inspeccionando fotogramas intermedios (ej. 50 % negro y 100 % negro) entre Menú -> Lobby -> Sala 1 vs 1 sin cortes bruscos en 1 frame.

### Fase P2: Efectos de sonido (SFX) nativos de Bust A Groove 2
- **Enfoque técnico (a elegir / validar en Ghidra `SLPM_862.19`)**:
  - **Opción A (SPU nativa via hook MIPS)**: localizar en Ghidra la función de reproducción de SFX de menú en `system/002.dbi` / `SLPM_862.19` y disparar los mismos IDs de SFX del menú principal (mover cursor, confirmar, cancelar, error).
  - **Opción B (WAVs extraídos del juego en host)**: si la SPU está pausada o el módulo de menú cambia, reproducir vía SDL3/host los mismos SFX extraídos de los bancos `.vb/.vh` del juego.
- **Mapa de eventos sonoros**:
  - Mover selector de sala (`Arriba/Abajo/Izq/Der`) -> **SFX cursor**
  - Confirmar (`online match`, crear sala `[C]`, unirse `[Enter]`) -> **SFX confirmar**
  - Cancelar / volver (`[Esc]`) -> **SFX cancelar**
  - Cambiar retrato de personaje (`[P]` / `[F4]`) -> **SFX cursor / cambio de personaje**
  - Intentar `START [F6]` sin que el Guest esté `READY` -> **SFX error / bloqueo**
  - Invitado marca `READY!` (`[F5]`) -> **SFX confirmar agudo / listo**
  - Nuevo mensaje de chat entrante -> **SFX notificación suave**
- **Prueba de aceptación (TP2)**:
  - Grabación oficial `bag2_record.py` con `--audio-backend process` + análisis de picos de audio (`ffmpeg` / `audio_probe.py`) confirmando que cada acción dispara su SFX exacto y verificación auditiva humana del owner.

### Fase P3: Feedback visual estilo PS1 (animaciones y avisos)
- **Qué hace**:
  - **Parpadeo / pulso suave del selector `1P`** en la ficha seleccionada del Lobby (como en *Character Select*).
  - **Aviso visual temporal (banner rojo PS1 ~2 s)** cuando ocurre un error del servidor (ej. `"GUEST IS NOT READY!"` al pulsar `[F6]` sin Ready, `"ROOM IS FULL"`, `"DISCONNECTED"`).
  - **Indicador de sala creada/ocupada en vivo** con actualización automática cada 3 s en el Lobby (sin necesidad de pulsar `[R]` manualmente).
  - **Historial de 2–3 líneas de chat** visibles en la caja oscura (en lugar de solo el último mensaje).
- **Prueba de aceptación (TP3)**:
  - Fotogramas de grabación mostrando: (a) aviso rojo `"GUEST IS NOT READY!"` tras pulsar `[F6]` en T3, (b) 2 líneas simultáneas de chat (`[GUESTP2]: HOLA HOST` y `[HOSTP1]: LISTO PARA BAILAR`), y (c) auto-refresco de sala en Lobby.

### Fase P4: Soporte de Mando / Gamepad (D-Pad + X / O)
- **Qué hace**:
  - Permitir navegar el Lobby y la Sala 1 vs 1 también con el mando configurado en BAG2JP (D-Pad para elegir sala, `X`/Confirmar para unirse, `O`/Cancelar para volver, `L1/R1` para cambiar retrato, `Start` para `READY`/`START`), manteniendo teclado completo para el chat y nombre.
- **Prueba de aceptación (TP4)**:
  - Prueba funcional con mando (o inputs de pad mapeados) navegando Lobby -> Sala -> `READY` -> `START` sin tocar el teclado salvo para escribir en el chat.

### Fase P5: Regresión integral (T1–T6 con pulido completo)
- **Qué hace**:
  - Re-ejecutar la batería completa **T1–T6** (`online-lobby-2instance-tests.md`) verificando transiciones a negro, SFX en cada paso, aviso visual de bloqueo sin `READY`, chat multilínea, retratos oficiales y `manifest.json` `"accepted": true`.

---

## Resumen de pruebas

| Prueba | Fase | Qué valida |
|---|---|---|
| **TP1** | P1 | Fotogramas de fade-out / negro / fade-in en todas las transiciones de pantalla. |
| **TP2** | P2 | Audio grabado (`process`) con SFX reales en cursor, confirmar, cancelar, error sin Ready, `READY!` y chat. |
| **TP3** | P3 | Banner de error `"GUEST IS NOT READY!"`, chat multilínea (2–3 líneas) y auto-refresco del Lobby. |
| **TP4** | P4 | Navegación y acciones principales del Lobby/Sala funcionando con mando/pad. |
| **TP5** | P5 | Corrida integral T1–T6 final con `bag2_record.py` (`accepted: true`) + revisión del owner. |
