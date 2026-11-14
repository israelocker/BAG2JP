---
id: heat-attack-effect-plan
title: "Plan: portar el efecto de ataque nativo BAG1 de Heat"
tags: ["heat", "bag1", "plan"]
summary: "Sustituir el efecto de fuego BAG2 (roto con texturas BAG1) por el efecto nativo BAG1 de Heat, manteniendo la lógica de golpe/reacción BAG2."
related: ["notes/bag1-character.md", "plans/strike-shot-effect.md", "notes/character-pipeline.md"]
created: "2026-11-05"
updated: "2026-11-06"
doc_kind: plan
status: "accepted_by_owner_visual_review"
---

# Objetivo

## Revisión solicitada 2026-11-06: Heat, Heat, Strike, Strike

El propietario solicita PvP Heat BAG1/A contra Strike BAG1/A en escenario Strike
BAG1, dos ataques consecutivos de Heat y después dos de Strike, esperando su
aceptación. El fixture alternante anterior no cumple ese orden. Se añade el modo
debug opt-in `BAG2JP_TEST_ORDERED_DUEL=1`: cuatro entradas nativas `0x6E`, orden
P1/P1/P2/P2, separación mínima 480 vblanks y comprobación de ataques pendientes
en ambos lados. No modifica efectos, puntuación ni fuerza animaciones/golpes.

Pruebas: nuevo caso inicialmente RED (función ausente), después cuatro casos
del fixture y suite host completa **156/156** en verde. Build WSL dos jobs pasado
en `_work/workflow/20261106T043001811613Z-ordered-heat-strike-attacks/`.
Ejecutable experimental `0e6f892a66a22c2a55081e4b2ffa237c03f30544ce0dffb05a415c0f5fa7c85c`;
original retenido en `_work/character_import/heat/ordered-duel-build/BAG2JP.before.exe`.
Driver aislado `_work/character_import/heat/run_ordered_duel.py` mantiene la ventana
abierta para el propietario; restaura ajustes y tarjetas al cerrarla.

### Aceptación visual del propietario (2026-11-06)

El propietario revisó en vivo el duelo ordenado (`_work/versus-runs/20261106T043419201749Z-ordered-heat-heat-strike-strike`,
runtime `0e6f892a66a22c2a55081e4b2ffa237c03f30544ce0dffb05a415c0f5fa7c85c`) con las cuatro entradas
de ataque ejecutadas en orden (`P1, P1, P2, P2` en frames 8307, 8829, 11439, 11961) y declaró
explícitamente **aceptado** el efecto de ataque especial de llamas de Heat BAG1 («*queda aceptado el efecto de ataque especial de heat, actualizalo como aceptado*»).
El efecto queda cerrado y aceptado para la versión experimental. Quedan como gaps separados
la progresión de eventos del escenario con el puntaje y las verificaciones globales de campaña/audio.

El propietario eligió (2026-11-05) portar el efecto nativo BAG1 de Heat, como con Strike,
y que el fixture de prueba fuerce que la CPU del P2 no esquive ni bloquee en el compás del
ataque. Aceptación: en VS, Heat BAG1 muestra un ataque equivalente al de BAG1 nativo
(`_work/character_import/heat/native-combat-runs/20261105T022031/heat-native-attack-final.mp4`);
el efecto BAG2 roto (aro blanco, arco pixelado) desaparece; VRAM de Heat BAG1 intacta; el
rival recibe el golpe (req202); canción, fever y retorno al selector pasan.

# Hechos demostrados (fase 1, evidencia)

- Capturas BAG2: stock `_work/versus-runs/20261105T084044962366Z-heat-attack-bag2`,
  importado `_work/versus-runs/20261105T084321997619Z-heat-attack-bag1`.
- VRAM f6700 stock vs importado: difiere x704-895 y256-511 (además de CLUTs x958-1010 y
  x832-896 y0-251). En el importado esa zona contiene texturas BAG1 de Heat; el efecto del
  DBI BAG2 (`FUN_801cf89c`/`FUN_801ce628`) dibuja con UV de esa zona: aro blanco y arco
  pixelado. Herramientas: `_work/heatdbi/vramdiff.py`, `vrambox.py`, `vram2png.py`.
- Sin daño en el importado: la CPU del P2 esquivó (req170/anim75) y bloqueó (req171/anim76);
  en stock recibió el golpe (req202/anim89). No es fallo de la importación. Los códigos
  están en `notes/archive/bag1-character-before-audit.md` (170 dodge, 171 guard, 202 struck).

# Análisis estático del DBI BAG1 (fase 2, en curso)

- `_work/heatdbi/bag1_heat.bin` (003.dbi de P_HEATA1.DFS sin cabecera, 8896 B) se carga en
  **`0x801DA778`** (igual que Strike). La base `0x801DB1D4` era errónea: con ella los
  punteros de las tablas caían a mitad de función. Decompilado:
  `_work/heatdbi/bag1_heat_decomp.txt` (Ghidra, `-Funcs '801dc29c,801dc6a8,801dc7ec'`).
- Tablas estáticas del ejecutable BAG1 (`_work/bag1/scus.bin`, base `0x80010000`),
  índice `char*4 + side*0x38`, Heat P1:
  - tipo 16 `0x80059424` → `0x801DC6A8` → `FUN_801daa10(dancer, value)`: ocupa una de
    3 ranuras de 0x44 B en `0x801DCA48`; origen = posición del atacante
    (`dancer+0x36F4/36F8/36FC`), destino = rival; 500/600 de vida/alcance; cue `0x1005`.
  - por fotograma `0x80055924` → `0x801DC7EC`: `FUN_801dc6c8` (→ `FUN_801dc29c`,
    `MoveImage` `0x8004D044`) y `FUN_801dac24` (matriz cámara `0x800613B8`; dibuja ranuras
    con `FUN_801dad98`, sprites `FUN_801db6b0` en `0x801DD778` ×3 de 0x3C, partículas
    `FUN_801dbd28` en `0x801DCB18` ×0x48 de 0x2C).
  - tipo 1 `0x800593B4` → `0x801DC29C` (animación de textura con `MoveImage`; candidata a
    las llamas del cuerpo). En BAG2 el tipo 1 hace el cambio de malla (`FUN_801cefa4`).
- Llamadas externas BAG1: `0x800350E4` (cue), `0x8004AFFC/0x8004B08C` (matriz),
  `0x8004B47C` (RotTransPers), `0x8004B56C`, `0x80049E1C/0x80049EEC`, `0x8004FA0C/FA3C/FB0C`
  (prims), `0x800500FC` (rand), `0x8004D044` (MoveImage). Mapa BAG1→BAG2 parcial en
  `tools/bag1import/port_bag1_stage.py` (`FUNCS`, `GLOBALS`).

## Resultado fase 2 (estático, 2026-11-05)

- Vida del efecto = fotogramas restantes de la animación al disparar el evento tipo 16
  (`FUN_800318d0` pasa `param_1[7]`); con el evento en f1 ≈ duración completa.
- Ranura de llama (`FUN_801dad98`): billboard POLY_FT4 code 0x2e, tpage `desc+0x46&0xff9f|0x20`
  (abr1 aditivo), clut `desc+0x44`, gris `min(bright>>12,0xff)`. UV: tabla `0x801DCA18`,
  14 fotogramas de 32 px (fila v=0: u 0..0xE0; fila v=0x78: u 0..0xA0), alto v 0x72 (0x3f
  con flag7). Semiancho `((w<<10)/5)/otz`, alto `h*0x1cc/otz`; OT `otz-0x60`.
  Estados: 0 aparece (vida/4) → 1 sostiene (vida·3/8) → 2 se apaga (vida/16) → 3 llamarada
  invertida que sube (w 1500→300, h 100→700, y+1000, +300/dt, vida/8) → 4 cae sobre el rival
  desde `y+vida/8·400` a −200/dt → al tocar: anillo + 24 partículas, llama corta → 5 se apaga.
- Anillo (`FUN_801db64c/6b0`): 8 quads entre radio interior `r*4+200` (y=0) y exterior
  creciente, UV u 0xC0..0xD7 v 0x78.., clut `desc+0x44+0x40`; r = rival `+0x43BC`.
- Partículas (`FUN_801dbc34/dbd28`): 0x48 × 0x2C, gravedad −0x1000/dt (+y arriba), al suelo
  encogen v y se desvanecen; mismos UV de llama.
- Tipo 1 en BAG1 = cambio de malla + parpadeo de ojos (`MoveImage`), igual que BAG2: no hay
  lógica de llamas de cuerpo allí. Las llamas del cuerpo nativas son las fases 0-2 del slot.
- VRAM: tpage 4bpp x768 y256 (base u/v 0,0) contiene en el importado la tira de llamas BAG1
  coincidente con la tabla UV y el anillo en u0xC0 v0x78. Aparecen rectángulos negros sobre
  fotogramas 0-1 (zona de ojos BAG2, u0..0x5f v0..0x88): pendiente confirmar si el parpadeo
  del DBI BAG2 los escribe (comparar dumps 6700..7120). Herramienta `_work/heatdbi/vram4bpp.py`.
- Resuelto: los rectángulos negros los escribe la animación de cara del DBI BAG2
  (`FUN_801cefa4`/`FUN_801cf8c4`, `MoveImage` `0x80046c7c` en 6 sitios
  `0x801cf374,43c,4b8,584,604,688`). Parche 3 `nop_face_move_image` en
  `tools/bag1import/patch_heat_dbi.py`; aplicado al payload con
  `tools/bag1import/patch_heat_face_payload.py` (entradas 59, 60, 131, 132; copia previa en
  `_work/heatdbi/payload-backup-20261105-face/`). Test `tools/test/test_heat_dbi_face_patch.py`
  en verde. Pendiente comprobar en juego que la tira queda intacta.
- Golpe BAG2: `FUN_801cc3cc` solo lee el resultado del rival (`0x8005E74D + side*0x32`:
  1 golpe, 2 bloqueo/reflejo) y reacciona con efectos/cues; la decisión está en el ejecutable
  principal. Por tanto anular el render (`FUN_801ce628`) no cambia el golpe.

# Fases pendientes

1. ~~Cerrar fase 2~~ (hecho, ver arriba).
2. ~~Fixture P2 sin esquivar/bloquear~~ (host verde, falta verificar en juego):
   `bag2_heat_defense_fixture_tick` borra el comando 0xAA/0x6E de `0x8005CF40` en el sitio
   `0x8009B084` si el byte `sp+side+0x30` (bajo ataque) está activo; decisión CPU en
   `0x8009AF00` (`_work/game/dis_9ae00.txt`). Test `test_p2_defense_cleared_only_under_attack`.
3. Implementación en `bag2jp.feature.bag1-content` (como `bag2jp_strike_shot.h`): anular el
   efecto BAG2 de Heat BAG1, emitir el efecto BAG1. Tests host, build, despliegue
   experimental, recalibración.
4. Aceptación: captura vs nativo, VRAM, partida completa con retorno.

# Límites

Solo experimental. No se porta la lógica de ataque/puntuación BAG1. La reacción del rival
sigue siendo la de BAG2.

## Resultado fases 3-4 (2026-11-05)

Implementado y verificado en experimental (exe a7f056a4, payload 7fd23c00). Evidencia, gaps y detalle en `notes/bag1-character.md` (sección Ataque BAG1). Pendiente: revisión visual del propietario; el anillo de explosión se ve naranja/en bloques frente al destello blanco nativo.
