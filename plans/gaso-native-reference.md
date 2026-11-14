---
id: gaso-native-reference-plan
title: "Plan: referencia visual nativa BAG1 de Gas-O (Dance View y combate) y pendientes"
tags: ["gaso", "bag1", "plan", "evidence"]
summary: "Grabar en BAG1 nativo todos los movimientos de Gas-O (Dance View) y un duelo Gas-O contra Gas-O (humo de entrada, ataque del tanque, fever), compararlos con BAG2 y cerrar las diferencias."
related: ["notes/gaso-import.md", "plans/gaso-attack-effect.md", "notes/bag1-character.md", "notes/bag1-stage-song.md"]
created: "2026-11-07"
updated: "2026-11-07"
doc_kind: plan
status: "approved"
approved: "owner 2026-11-07"
---

# Objetivo y aceptación

Petición del propietario (2026-11-07): ejecutar BAG1, cargar la tarjeta para desbloquear
Dance View, comparar visualmente todos los movimientos de Gas-O con sus equivalentes en BAG2
(dudas concretas sobre algunos fever time), jugar en BAG1 Gas-O contra Gas-O para ver qué
efectos faltan (humo al inicio, efectos del ataque especial) y grabarlo como evidencia. El
ataque de Gas-O no derriba: deja al rival congelado dentro de un tanque gigante, y eso debe
reproducirse igual contra todos los personajes en BAG2.

Aceptación del plan completo: existe una referencia nativa grabada (vídeo + capturas por
movimiento) y una tabla BAG1↔BAG2 revisada para cada movimiento de Gas-O; cada diferencia
queda corregida o registrada como decisión del propietario; humo de entrada y ataque con
tanque funcionan en BAG2 contra los 19 personajes (P1/P2) con canción, fever y vuelta al
selector, 21 saves restaurados y revisión del propietario.

# Fases

1. **Referencia Dance View BAG1 (sin cambios de código).** Runtime BAG1 USA PSXRecomp en
   copia aislada `D:/Dev/Scratch/bag1-native-reference` con tarjetas copiadas (método de
   Heat 2026-10-31 y Strike `_work/character_import/strike/native_combat_probe.py`):
   Options → Memory Card → Load Data → YES (`LOAD OK!`), Dance View, Gas-O A. Recorrer
   todas las opciones (pasos, especiales, poses, fever solo/dueto) con ~70 ms por tecla,
   3 capturas por opción + vídeo continuo (ffmpeg gdigrab). Índice/nombre de cada opción
   validado. Salida `_work/gaso/native-reference/danceview/`.
   **Resultado 2026-11-07 (Gas-O A):** 67 opciones (A–ZZZ, FINISH1-7, SOLO 4/8/16 A-C,
   WAIT, WALK, INDIVIDUAL, ATTACK1/2, DODGE, HIT1-3, TIRED, CAUGHT, DOWN1-3, WIN1-3,
   LOSE1/2, FEVER1/2, ---, NEUTRAL) en `danceview/gaso-a-catalog.json` (hashes de
   capturas), vídeos FEVER1/FEVER2. FEVER1 nativo empieza con break dance de cabeza y
   vuelve a pararse girando (ciclo ~16 s). gdigrab por título graba negro; se captura
   la región cliente del escritorio (`window_rect.ps1`). Traje B no recorrido.
2. **Referencia Dance View BAG2.** Misma lista con Gas-O BAG1 en la instalación
   experimental (`viewer_probe.py`) y, como control, Bi-O BAG2. Tabla lado a lado
   (hoja de contacto por movimiento) contra `contracts/gaso-animation-contract.json`:
   clip correcto, rol, duración en beats, transición. Señalar fever que no sean de Gas-O.
   **Resultado 2026-11-07:** barrido 88 índices, 85 capturados, saltados 78 (WIN4), 85/86 (FEVER4/5 vacíos).
   Se confirmó que Gas-O no tenía entrada 17 en payload y reproducía los fevers de Bi-O de stock.
   Con la corrección (fase 5), anim 82 (FEVER1) y anim 83 (FEVER2) quedaron mapeados e integrados.
3. **Duelo nativo BAG1 Gas-O contra Gas-O (grabado).** Partida completa con vídeo y
   capturas: humo de entrada, ataque especial (tanque, congelación, liberación, duración en
   beats, qué hace el rival al salir), defensa/esquiva si ocurren, fever solo y dueto,
   victoria. Además el ataque de Gas-O contra al menos un rival distinto (Heat) para ver
   si el tanque depende del rival. Salida `_work/gaso/native-reference/combat/`.
4. **Mismo duelo en BAG2 experimental** (grabado, `--audio-dump`) y lista de diferencias
   con evidencia: efectos ausentes, efecto de Bi-O heredado, reacción del rival.
5. **Corrección de movimientos/fever** si la fase 2 encuentra clips mal asignados:
   cambio en `gaso-animation-policy.json`/`anim_remap_gaso.py` (no en el código
   compartido salvo error demostrado), rebuild, payload, Dance View BAG2 otra vez.
   **Resultado 2026-11-07:** Implementado `build_fever()` en `anim_remap_gaso.py` con fuentes (82, 83, 82),
   cues rebasadas a 0x6900, y cola vacía. Integrada entrada 17 en `build_gaso_assets.py` y `make_fever_spec.py`.
   Verificado en Dance View controlado de BAG1 y BAG2: FEVER1 y FEVER2 de Gas-O coinciden exactamente
   en ciclos y poses (incluyendo floor freeze de anim 83). Solo fever resuelto y validado visualmente.
6. **Humo de entrada y ataque con tanque**: continúa `plans/gaso-attack-effect.md`
   (fases 2-4) con esta evidencia. Análisis en Ghidra (BAG2) y Capstone (BAG1, no está
   en el proyecto Ghidra) del DBI de Gas-O y de la reacción "congelado en tanque";
   implementación en `bag2jp.feature.bag1-content` con helpers compartidos; tests host
   RED→GREEN; aceptación contra los 19 personajes en P1 y P2.

# Decisiones del propietario

- Resuelta (2026-11-07): la reacción del rival es la BAG1 nativa (tanque, sin derribo),
  igual para todos los personajes BAG2.
- Pendiente tras la fase 2: qué hacer con cada fever/movimiento que no tenga equivalente
  BAG1 claro.
- Pendiente, fuera de este plan: retrato HD Gas-O↔Bi-O en el selector.

# Límites y riesgos

Solo instalación experimental y copia aislada de BAG1; instalaciones y tarjetas originales
intactas. Un juego a la vez y sin GPU local durante grabaciones. Si un personaje BAG2 no
tiene animación compatible con el tanque, se informa antes de adaptar. Herramientas usadas
se registran en `notes/tool-evidence/`.
