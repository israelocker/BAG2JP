---
id: gaso-attack-effect-plan
title: "Plan: portar el efecto de ataque nativo BAG1 de Gas-O y revisar la reacción del rival"
tags: ["gaso", "bag1", "plan"]
summary: "Plan F1–F8 aprobado 2026-11-10 para fidelidad completa del ataque BAG1: imagen, escala, lógica y sonido. F1 inventariado; F2/F3 en investigación; tanque instalado parcial y no aceptado."
related: ["notes/gaso-import.md", "plans/heat-attack-effect.md", "plans/strike-shot-effect.md", "notes/bag1-character.md"]
created: "2026-11-07"
updated: "2026-11-10"
doc_kind: plan
status: "in_progress"
approved: "owner 2026-11-10: Aprobar plan (question tool)"
---

# Objetivo y aceptación

Informe del propietario (2026-11-07): el ataque especial de Gas-O "aún no está del todo
implementado"; falta el efecto BAG1 y la reacción del rival está mal. Hoy Gas-O usa el
DBI/efecto heredado de Bi-O (no se ha portado nada del ataque).

Aceptación: en VS, Gas-O BAG1 (P1/P2 × A/B) muestra un ataque equivalente al BAG1 nativo;
sin restos del efecto de Bi-O ni texturas corruptas; el rival reacciona según la decisión
de la fase 2; canción, fever y vuelta al selector pasan; 21 saves restaurados; revisión
visual del propietario.

# Fases

1. **Evidencia (sin cambios de código).** Capturar el ataque en BAG1 nativo (mismo método que
   `_work/character_import/heat/native-combat-runs/`), BAG2 stock Bi-O y Gas-O importado;
   volcados VRAM antes/durante; anotar la animación/req del atacante y del rival
   (170 esquiva, 171 guardia, 202 golpe) frame a frame.
2. **Análisis estático.** DBI BAG1 de Gas-O (`P_GAS_A1.DFS`) y tablas de eventos del
   ejecutable BAG1 (índice `char*4 + side*0x38`, como Heat), con Ghidra; DBI de Bi-O en BAG2
   para ver qué dibuja con las texturas de Gas-O y si su efecto altera la reacción del rival
   (en Heat la decisión de golpe está en el ejecutable principal, `0x8005E74D`). Resultado:
   qué es "reacción mal" (efecto de Bi-O sobre el rival, animación de reacción o lógica).
3. **Implementación** en `bag2jp.feature.bag1-content` reutilizando los helpers compartidos
   de `bag2jp_strike_shot.h` (no clonar el pipeline de Heat): anular el efecto de Bi-O solo
   para Gas-O BAG1 y emitir el efecto BAG1; ajustar la reacción solo si la fase 2 lo demuestra.
   Tests host primero (RED→GREEN), build, despliegue experimental, recalibración.
4. **Aceptación** con el duelo ordenado `BAG2JP_TEST_ORDERED_DUEL=1` ampliado a Gas-O,
   comparación con el clip nativo, partida completa y revisión del propietario.

# Decisiones del propietario

- Reacción del rival: resuelta por el propietario (2026-11-07): portar la BAG1 nativa,
  rival congelado dentro de un tanque gigante, sin derribo, contra todos los personajes.
  La evidencia de la fase 1 la aporta `plans/gaso-native-reference.md`.

# Límites

Solo instalación experimental. No se porta la puntuación BAG1. Bi-O BAG2 queda intacto.

## Hallazgos de la ingeniería inversa BAG1 nativa (2026-11-09)
- Clip nativo de referencia: _work/gaso_native_attack_exact.mp4 (8.0s), hoja de contactos _work/gaso_native_attack_exact_tiles.png.
- Hipótesis históricas: estos números y descripciones NO son un contrato exacto verificado; contrastar con código, datos y trazas nativas:
  1. Caída vertical acelerada (frames 25..34): El tanque cae desde una altura de +1200 unidades sobre el rival hacia el suelo con aceleración cuadrática (10 frames).
  2. Confinamiento criogénico (frames 35..85): Tanque cilíndrico de 16 segmentos, con doble anillo cromado y emisión continua de niebla/gas criogénico blanco/celeste con dispersión radial y velocidad vertical. El rival permanece de pie temblando (standing stunned, slot 78) sin knockdown.
   3. Desvanecimiento y ruptura (frames 86..100): El tanque se desvanece gradualmente (fade out de alpha/brillo) en lugar de cortarse bruscamente.

## Revisión de alcance propuesta (2026-11-10)

Petición literal: «okay necesitamos la reconstrucción 100% fiel el efecto, sonido, tamaño, todo».
Se refiere al ataque del tanque, no a rehacer toda la importación o el escenario.
Sustituye la meta de aproximación visual. El candidato `d9ce984` usa malla original,
render/lógica nuevos, escalas 35/22 %, tiempos propios y congelación no continua;
no satisface este requisito. Revisión F1–F8 aprobada explícitamente por el propietario
el 2026-11-10 mediante «Aprobar plan»; ejecución iniciada por F1, sin aceptación del efecto.

### Contrato de fidelidad

- **Fuentes:** identificar región, ejecutable, módulo DBI, miembros DFS y hashes de
  cada recurso/consumidor BAG1. Reutilizar datos originales; no inventar texturas
  si el original usa polígonos sin textura. Auditar las regiones configurables sin mezclarlas.
- **Imagen:** geometría, proporción respecto del bailarín, transforms, trayectoria,
  materiales, colores, sombreado, mezcla PSX, orden/oclusión, sprites y partículas
  demostrados por la fuente. Sin ajustes arbitrarios para que «se parezca».
- **Lógica:** activación, acierto/esquiva/defensa, captura, pose/movimiento del rival,
  duración y liberación originales. Medir eventos en frames/tiempo del juego, no
  vídeo interpolado. El slot 78 de BAG2 no demuestra equivalencia por sí solo.
- **Audio:** muestras/banco/cues originales del ataque; disparo, tono/fine,
  envolvente, volumen relativo, panorama, duración y sincronía correctos. No
  sustituir el efecto por audio de vídeo con música ni asumir que ya está validado.
- **Prueba:** igualdad de datos/tablas, equivalencia de estados/eventos y paquetes
  bajo entradas comparables, comparación visual y audio aislado documentados.
  Cámara/escenario BAG2 no exigen igualdad de toda la pantalla, pero no justifican
  deformar el efecto. Toda diferencia sin resolver/medir queda abierta: no se
  rebaja el criterio ni se declara «100 %».

### Pasos y verificación

| ID / tamaño | Trabajo y archivos probables | Aceptación y comprobación | Blocked by |
| --- | --- | --- | --- |
| F1 / S | Inventario; `notes/gaso-import.md`, evidencias `_work/gaso/`, perfiles existentes leídos | Tabla de fuentes/hashes/regiones y carencias; comprobar identidad de capturas antes de reutilizar. Ghidra MCP `get_program_info` y consulta relevante del binario/módulo correcto. Capturar solo para una carencia concreta. | Aprobación |
| F2 / M | Controlador visual/estados BAG1; nota y reportes | Constantes, matrices, materiales, eventos y reacción rastreados a datos/instrucciones. `funcmatch.py` solo para main, candidatos confirmados en Ghidra; no para overlays. Incertidumbres registradas, no inventadas. | F1 |
| F3 / S | Cues/VAB y eventos del ataque; nota y reportes | Muestra, registro y frame identificados; PCM aislado y parámetros reproducibles, o carencia explícita. Escucha histórica general no valida este ataque. | F1 |
| F4 / M | Port visual; `bag2jp_gaso_tank.h`, helpers solo si procede, `gaso_tank_harness.c`, `test_gaso_tank.py` | RED→GREEN de paquetes/estados derivados de F2, no de constantes elegidas por el candidato. `py -3.13 -m unittest -v tools.test.test_gaso_tank tools.test.test_bag1_dancer_scale`; ampliar seam real según contrato. Sin forzar slots no equivalentes. | F2 |
| F5 / S | Sonido con convertidor/perfil/routing existentes y sus tests | RED→GREEN de cue/parámetros/frame y bytes/banco, preservando otras voces. Fijar comando de regresión tras identificar consumidor F3 y antes de editar; no hay comparación de audio del ataque ya validada. | F3, F4 |
| F6 / S | Candidato experimental protegido | Goldfish según cambios; suite completa con fallos enumerados; `bag2_workflow.py build --tag gaso-native-fidelity` con Python registrado. Staging, capacidad payload si cambia, backups/hashes y nueva calibración antes de jugar. | F4, F5 |
| F7 / M | Comparativa de ataque/audio; evidencia y nota | P1/P2 × A/B, acierto/esquiva/defensa y liberación conforme a BAG1; escucha del propietario. Paquetes/estados sincronizados al guest frame, no inferidos del PrintWindow con heartbeat cada seis frames. | F6 |
| F8 / M | Compatibilidad/cierre; evidencia y nota | Contra los 19 personajes en ambos lados; variantes/regiones aplicables, fin de canción, fever y selector; originales restaurados y aceptación visual/auditiva del propietario. Dividir matriz en tandas reutilizando evidencia válida. | F7 |

Dividir pasos M en pruebas/cambios acotados por consumidor; no un cambio multisistema
de una vez. F2/F3 son investigación independiente, sin obligación de delegar. No usar
GPU local durante juegos ni implementar un consumidor cuyo contrato siga incierto.

### Decisiones, límites y pendientes

| Decisión | Criterio |
| --- | --- |
| Original antes que aproximación | Traducir/relocar código solo donde BAG2 lo requiera, conservando semántica demostrada. |
| Referencia BAG1 PSXRecomp aislada | Método del proyecto, sin DuckStation, instalaciones nuevas ni cambio de pins. |
| Preservar lo aceptado | Cartel GAS/defecto A, otras importaciones, preferencias, tarjetas y estable intactos. Si una fuente demuestra conflicto con algo aceptado, presentarlo antes de modificarlo. |
| Cierre condicionado | Build, tests actuales, Goldfish o aprobación del plan no sustituyen aceptación del ataque. |

Siempre en alcance: tanque completo, animación/eventos asociados, sonido, rival y
aislamiento. Fuera de alcance: puntuación BAG1, nuevas funciones, remasterización,
rehacer música/escenario/entrada o cambios incidentales a otros personajes. Preservar
experimentos/trabajo previo; checkpoints locales pequeños, sin publicar.

Pendientes técnicos por evidencia: controlador/módulo BAG1, transforms/ciclo exactos,
mezcla/orden, sonido y equivalencia de pose para cada rival BAG2. No son decisiones
que deba adivinar el propietario. Si aparece una incompatibilidad fundamental que
exija cambiar alcance o herramientas, se informa antes de adoptar una aproximación.

| Progreso | Estado |
| --- | --- |
| Requisito de fidelidad completa | Confirmado por petición del propietario 2026-11-10 |
| Revisión F1–F8 | Aprobada explícitamente 2026-11-10 |
| F1 | Inventario cerrado con carencias explícitas: report/accessory/audio-deployed; fuentes y vídeo auditados |
| F2 | En curso: controlador, matriz, 44 primitivas, blend y evento16/20/1 JP rastreados; faltan estado rival, partículas y dimensiones equivalentes |
| F3 | En curso: cues 0x1806/0x180a y muestras originales identificados; desplegadas resampleadas; falta PCM/onset |
| Nueva implementación/captura | No iniciada; `d9ce984` sigue WIP |
