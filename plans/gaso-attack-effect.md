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
| F2 | En curso: CAUGHT70/TIRED78, loop, escala R12 y argumentos de carga identificados; ajuste host y referencia1514→trabajo14e4 localizados; faltan contraste dinámico, selección por rival y partículas |
| F3 | En curso: cues 0x1806/0x180a y muestras originales identificados; desplegadas resampleadas; falta PCM/onset |
| Nueva implementación/captura | No iniciada; `d9ce984` sigue WIP |
| Entrada limpia 2026-11-12 | P0/P1 cerrados como checkpoints experimentales; `ab5480e` prueba captura/consumo observe-only, no publicación ni fidelidad. P2a añade lookup diagnóstico por receptor (positivo BAG1, negativo BAG2), sin publicar. Ver `notes/gaso-import.md#caught-observe-20261112` y `#caught-p2a-lookup-20261112`. |

### Desglose CAUGHT P2/P3 (2026-11-12, P2a completado; P2b/P3 en investigación)

Este desglose no modifica la aceptación F7/F8 ni autoriza publicar el clip. La
primera entrega fue **P2a**, selección diagnóstica sin escrituras, autorizada por
«Continua» tras la pregunta explícita de ejecutar únicamente P2a y completada el
mismo 2026-11-12. P2b/P3 siguen en investigación; no se implementará un
contrato de lifetime supuesto.

| Paso / tamaño | Archivos y alcance | Aceptación / verificación | Blocked by |
| --- | --- | --- | --- |
| P2a / S | `bag2jp_gaso_caught.c`, harness y driver existentes: consultar `b1cc_lookup` usando personaje y versión del **receptor**, nunca la versión BAG1 del atacante; registrar elegible/no soportado sin publicar | RED→GREEN: Heat/Strike/Gas-O BAG1 en ambos lados; BAG2, personaje sin clip y banco corrupto rechazados. CPU/RAM sin cambios en callbacks y sin nuevas asignaciones. `py -3.13 -m unittest tools.test.test_gaso_caught_runtime tools.test.test_caught_bank`; suite completa comparada con baseline; Goldfish antes de cierre. | Completado 2026-11-12: 20/20 host, suite sin nombres nuevos de fallo, dos Goldfish sin hallazgos bloqueantes. Ver `notes/gaso-import.md` §`caught-p2a-lookup-20261112`. |
| P2a runtime / S | Staging del único fuente cambiado, build y exp-8mb; nota canónica | `bag2_workflow.py build --tag gaso-caught-lookup-observe` con Python registrado; backups/hashes, calibración por nuevo exe; duelo receptor BAG1 positivo y BAG2 negativo con bridge existente. Mantener `GASO_CAUGHT_CLIP_PUBLISHED=0`, `a2 unchanged`, canción/selector y restauración. No prueba de decoder ni aceptación visual del clip. | Completado 2026-11-12: exe `A9296DDB`, calibración aceptada, Heat BAG1 `ready` y Heat BAG2 `rejected` en juego, restauración verificada. Sin publicar ni aceptar el clip. |
| P2b / investigación S | Lectura de cargador, identidad de tablas y generación; nota canónica | Identificar productor y consumidor de cada identidad y el evento de recarga aunque se reutilicen direcciones. Campos constantes `generation=1/tick=0`, hashes estáticos o actor igual no sirven. Fijar seam/test y contrato antes de proponer escrituras. | Completado 2026-11-12 (investigacion): evento de recarga = ciclo de fases DAT_8005d3dc 0->1->2->3->0; fase 3 reinicializa las cuatro parejas y pone +0x18=-1. Los buffers de actor son RAM fija (0x800ddb18/0x80154db4), por lo que la identidad del puntero no es generacion. Contrato de invalidacion de captured[] documentado en notes/gaso-import.md caught-p2b-generation-20261112; sin escrituras ni publicacion. P3 sigue pendiente. |
| P3 / investigación S | Ciclo de vida, binding/adapter y callbacks reales, preservando cambios previos | Completado 2026-11-12 (investigacion): session_reset y savestate registrados para bag2jp.gaso_caught; ambos invalidan captured[] sin escrituras guest ni asignaciones. Prueba host escenario 10 OK (21/21). Falta: publica/restore quiescente con guard y aprobacion del propietario. CLIP_PUBLISHED=0. | P2b; publica y restore quiescente pendientes |

Hechos que condicionan el desglose:

- `b1cc_lookup` acepta únicamente versión 1 y personajes 0/1/9. El banco es de
  1048 bytes originales; no existe un clip BAG2 autenticado en él. P2a confirmó
  en juego que un receptor Heat BAG2 se rechaza (`version=0`, clip 0), aunque
  capture/take funcionen.
- `psx_mod_register_session_reset_plugin` es limpieza host antes de activar
  planes, incluso si omiten el plugin; no puede restaurar tablas guest.
  `psx_mod_register_savestate_plugin` se invoca tras una restauración válida y
  antes de reanudar PC; no serializa automáticamente `captured[]` o el adapter.
- La compatibilidad de los 19 rivales permanece abierta. No reinterpretar BAG2
  como BAG1, no inventar equivalencia ni reducir F8 a los tres clips existentes.

Siempre: procedencia del receptor, rechazo conservador, instalación experimental,
preservar trabajo previo y evidencia histórica. Nunca en P2a: publicar slot 1,
cambiar `a2`, pending del actor, payload, pins o instalación estable. P2a quedó
cerrada como diagnóstico observe-only; publicación y diseño P2b/P3 siguen
bloqueados.
