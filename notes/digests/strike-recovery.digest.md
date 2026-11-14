---
id: strike-recovery-digest
title: "Strike recovery and current acceptance digest"
tags: ["digest", "strike", "recovery"]
summary: "Strike: disparo y matriz con evidencia histórica; iluminación descartada. Recetas vigentes separadas de la cronología; no aceptación global ni campaña."
related: ["notes/strike-recovery.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "notes/strike-recovery.md"
source_sha256: "6a5489f8ac3a4afbe41fcc58f15f4f0973914ce0b3a7c06ca584eb55d0057e1f"
---

# Strike: estado vigente

Auditoría 06-11: usar primero «Lectura vigente tras auditoría» en la fuente.
El disparo ya tiene aceptación visual registrada el 05-11; no implementar de nuevo
el próximo paso antiguo de proyección. Partidas posteriores cubren los cuatro
casos lado/traje. Voces/anunciador tienen evidencia SPU, no escucha subjetiva
universal. El override de iluminación fue descartado por el propietario: mantener
inactivo aunque el ensayo facial histórico de abajo fuera satisfactorio.
Stage/audio: `notes/bag1-stage-song.md`; media/selector/salida de endings:
`notes/endings-view.md`. Ending View no demuestra campaña final.
Inventario y metadatos de evidencia contrastados: `notes/documentation-audit.md`.

## Cronología anterior, no instrucciones actuales

Las prioridades, PIDs, restauraciones pendientes y «siguiente» de abajo describen
su fecha; no autorizan tocar sesiones actuales ni prevalecen sobre el estado
anterior. Se preservan para no perder hashes, diagnósticos y pruebas únicas.

- En curso 05-11: Efecto del disparo de Strike BAG1. Fase 1 y 2 completadas (referencia nativa en combate capturada con fogonazo, trazador de bala y partículas; bucle de dibujo 0x801DB940 y evento 16 aislados). Propietario eligió Opción A (plugin C nativo). Módulo `bag2jp_strike_shot.h` implementado y probado con tests host. Posición 3D del bailarín localizada en `dancer + 0x14B8` (P1 x=-775, y=0, z=-147; 0x14E4 era escala). Próximo paso: actualizar offsets de proyección en `bag2jp_strike_shot.h`, compilar y validar alineación del trazador en combate.
- Escala 04-11: Strike BAG1 es ~19,5 % mayor que BAG2 (vértices/traslaciones BAG2/BAG1 = 0,8371 A, 0,8384 B; Heat ≈0,98). Confirmado en espejo `versus-runs/20261104T213116596013Z-strike-scale-mirror-a-1793827876`. Corregido: escala del bailarín 98->82 solo en el lado Strike BAG1 (`b1v_dancer_scale`), exe `1b87a790…ddca`; espejo A/B y partida A verificados; P2 pendiente.
- Voces y anunciador integrados y verificados 04-11: banco de voces BAG1 rebasado de 0x1200 a 0x6100 (12 cues) y cues de anunciador 0x1107/0x1108 de BAG2 preservados en miembro SEDT de los 4 paquetes (73, 74, 145, 146). Payload `65bbe67e…9b37`, exe `0d38ab64…0674`. Tabla SPU en RAM (0x8007F180) confirma 12 cues 0x6100..0x610b (registros 43..54) y anunciador 0x1107/0x1108 (55..56) activos junto a Heat 0x10xx sin colisión (`cue-table-audit.json`). Combates enteros con audio activo en Traje A y Traje B pasaron (162.6s, retorno root 13). PASSED.
- Partida completa verificada 04-11 (Canción + Fever + Retorno): ejecutados dos combates Versus P1 Strike (BAG1) vs P2 Heat (BAG2) en Stage 200. Traje A (165.7s, retorno root 13, `versus-runs/...p1a...`) y Traje B (162.5s, retorno root 13, `versus-runs/...p1b...`) completaron canción entera, barra Fever y retorno automático a selección sin bloqueos. Ambos trajes sin mancha ni parches en gameplay. PASSED.
- Diagnóstico facial y prueba en vivo 04-11: inyectada iluminación nativa completa de Strike (`ST_STRI.DFS`) en sesión viva BAG2 PID39676. Piel circundante pasa de [0,0,0] a [255,173,31]; boca [0,0,0] recupera nitidez y definición exactas de BAG1. Evidencia `face_audit/face-full-native-centered.png`. Prueba Versus P1 Strike (BAG1/A) vs P2 Heat (BAG2/A) en Stage 200 (`_work/versus-runs/20261104T192150838807Z-strike-lighting-vs-heat-1793820110/`): Strike mantiene contraste facial y perilla en movimiento; Heat conserva su iluminación de escenario. Perfil respaldado en `tools/bag1import/profiles/strike-lighting-profile.json`. Modelos 109/110/181/182 idénticos a BAG1.
- PechoA corregido04-11 (P1/NEUTRAL): baseline `graphics-run/20261104T125757-candidate` reproduce copiaBAG2 ymancha; candidato `20261104T130315-candidate` sinmancha y3dumps conambos atlas/CLUT exactos aBAG1. Solo16bytes enalternativosA73/74;17entradas intactas,130tests ybuild OK. Exe `a5fa8cf1…804a`, payload `baa149bb…aea6`. Checkpoint WIP37a4b3d contrato/tests. **Preservar abiertas BAG1 PID17936 yBAG2 PID39676**, journal graphics-session.json;24saves originales intactos, restauración pendiente. Rostro/boca/iluminación sin cambios ni resolver;P2/flujos completos pendientes. Evidencia `chest_audit/verification.json` y `chest-before-after.png`.
- Diagnóstico histórico anterior al arregloA: `chest_audit/source-audit.json` encontró copiasBAG2 activas solo enA73/74; simulación semejante a la mancha. Confirmación ycorrección runtime ya registradas arriba. Boca/rostro siguen pendientes; no subir brillo global como supuesto arreglo.
- Entrega inicial04-11: BAG1 PID17936/BAG2 PID40012 enStrikeB. **BAG2 PID40012 fue cerrado/restaurado con permiso y sustituido porPID39676** (arriba). Journal vigente `strike/graphics-session.json`. BAG1 máximo4x, BAG2 9x/4K interno; objetivo144presents/s por interpolación, no medición sostenida. No nuevo packHD corporal.
- Prioridad vigente04-11: texturas/definición antes de Heat/VS. Comparación fresca `emblem_audit/filter-comparison-b.png` (xBR basal, bilinear/nearest por mod): bilinear difumina detalles, nearest escalona; no mejora clara ni cambio persistente. Ajustes/saves restaurados. Los overrides `texture_filtering` en settings son ignorados; primeras seis comparaciones inválidas. Falta localizar con propietario el defecto residual; no afirmar fidelidad ni detalle HD recuperado.
- 04-11 último: elegido ampliar memoria (8 MB). El vblank de `bag2jp_bag1_versions.c` + `bag2jp_model_region.h` mueve la base del modelo del lado BAG1 a `0x80200000`/`0x80300000` (solo con 8 MB y estados de carga seguros). Test RED→GREEN, suite128 OK, exe `8e8f6004…41be`. Dance View: A ya carga y se ve bien; B sin solapes. Pendiente: P2/VS, regresión de Heat BAG1, online.
- Histórico anterior a RAM alta: payload `336bc625` excedía la memoria stock de P1 (488092 B hasta P2 `0x801485EC`): A31024 B, B3192 B. El límite `001.bin`285556 B solo aplica al buffer stock; el propietario eligió RAM8MB, implementada arriba. Evidencia `motion_recovery/memory-budget.json`.
- 04-11 último: reconstruidos los99/101slots activos de Strike (`anim_remap_strike.py` + `strike-animation-policy.json`, `status=proposed`) con rejilla `B2_ROWS/B2_ALT`, transiciones nativas `0x80055854` y roles semánticos;0slots activos vacíos (solo1/97stock vacíos). `ATTACK` (`74`) desenfunda2pistolas y colapsa5 `type 16` en `(16,26,0)`, rebasando cues `0x1200->0x6100`. Suite127 OK; build `20261104T142916677989Z-strike-semantic-motions-aligned`, payload `336bc625…7a46` (5365760 B), exe `4180ef0d…1c6b`.
- Dance View P1/B `viewer-run/20261104T093044` (`clips-sheet.png`): `A` (slot2), `E` (slot6), `K` (slot12, paso1compás), `WAIT` (slot71) y `ATTACK` (slot74, pistolas duales) verificados sin hundimiento y con emblema/antebrazos/manos correctos; sesión cerrada y saves restaurados.
- 04-11 último: emblema recuperado en P1/B individual al omitir2copias de atlas
  BAG2 (DBI0x2358/0x23D4) solo en alternativosB145/146. Destino anterior(704,268)
  = origen(732,460),360palabras exactas. Contrato reversible por hash/guards,
  no cambia UV/CLUT/modelos/motions; conserva flags/delay slots/handlers de paleta.
  **Suprime efecto BAG2 incompatible, no implementa animación de textura BAG1.**
- Run `viewer-run/20261104T070206`: neutral0,11(K),21(U), emblema completo visible;
  volcados6000/7500/9000 tienen ambos atlas y CLUT enteros idénticos a TIM BAG1.
  Sesión cerrada/restaurada. Suite126 OK; build `20261104T120126197978Z-strike-emblem-copy-guard`.
  Payload `bf775fd2…d241`, exe `8d7af184…2541`,17entradas intactas, backups en
  `emblem_audit/candidate/`. Referencia nativaB capturada (neutral, K, U, ATTACK1, HIT1, FEVER1/2) y cerrada:
  emblema estático confirmado y DBI nativo (`0x801DA778`) sin copias `10×36` ni `0xC9/0xCA`.
  Causa de53slots vacíos aislada (`req==req` en vez de rejilla/roles). Siguiente: reconstruir53slots y probar en Dance View.
- 04-11 anterior: VRAM demuestra TIMs desplazados una palabra por DFS desalineado
  tras DBI. Rebuild ahora alinea4bytes (regresión RED→GREEN,125tests); candidato
  experimental payload `e9fcc65a…35cc`, exe `d7553505…8f57`, build
  `20261104T115144533310Z-strike-dma-alignment`. Solo4packs cambian padding/offsets;
  miembros y15entradas restantes intactos. Backups en `strike/dma_alignment/`.
- Dance View P1/B fresco `viewer-run/20261104T065228`: antebrazos sin blanco;
  neutral0 y clip11. Frame6000 CLUT14+10filas exactas y TIM2 exacto; TIM1 difiere
  en206palabras (x0..9/y19..47). Frame7500 cambia además CLUT8/9 tras mover.
  Emblema todavía incorrecto: localizar escritura/UV/tpage/CLUT, no aceptación global.
  Ambas sesiones cerradas con configuración y saves verificados; estable intacto.
- Referencia BAG1 terminada:90posiciones,66roles únicos,8muestras/rol;
  `a-moves/index.json` sin nombres desconocidos y `labels3.png` válido con escala
  real. TrajeA solamente; no ciclos/transiciones exhaustivos. Referencia cerrada.

- 04-11 anterior: neutral nativo restaurado (payload `7c7a001a…41cc`, exe `97d90967…`,
  experimental). Dance View individual BAG1/B: manos completas; clips 0/11/21
  completos, sin hundimiento dentro del clip. Pendientes: 53 slots vacíos (incl.
  paso A slot6), antebrazos/emblema (textura/CLUT), matriz VS, fever, audio.

- Reanudación autorizada04-11 tras comparación acotada Heat. Plan aprobado;
  preflight `20261104T083326224847Z-strike-skeleton-resume` pasado, sin nuevos
  cambios de código/assets Strike. Siguiente: contrastar inputs/hashes/índices
  de auditorías de manos/esqueleto con DBI/modelos nativos antes de adaptador.
  Continuación fresca en `_work/character_import/strike/resume-skeleton.md`.
- Continuación posterior solicitada en la misma sesión: auditoría nativa nueva
  `hand_contract/channel-binding-audit.json`; cuatro grafos BAG1 iguales y stores
  de canales idénticos a ramaA BAG2. RamaB cambia15 bytes de tabla. Candidato
  guardado/reversible anula dos ramas (canales0x1AE0 y manos0x28E4) solo en
  packs alternativos B145/146. Motor común+contrato declarativo; suite122 pasa.
  Payload experimental `4f6c9f67…a3ca9a3`,12 bytes cambiados,17 entradas intactas
  incluidas11Heat, backups exactos. Probe P1/B manos/transiciones en curso.
  Todavía sin aceptación visual, neutral, movimientos, fever, canción/retorno.

- Recuperación actual: `_work/character_import/strike/loading_recovery/20261103T054908Z/`.
  El rebuild ad-hoc confundió TIM con modelos de 16 huesos y packs con modelos;
  esas conclusiones y las canciones supuestamente completas quedan retractadas.
  Se recuperaron los ocho DFS preservados y once filas Heat por hash (19 total).
- Run fresco `20261103T055322770178Z-strike-loading-recovery-p1b` sí llega a
  gameplay con gate estricto, captura y motions cambiantes; no canción completa.
  Ajustes/21 saves preservados. 3 tests assets + 49 harness pasan. Voz VS sin verificar.
- Referencias nuevas del usuario: Heat blanco/rojo y rojo/blanco. Run de aislamiento
  `20261103T055715562472Z-heat-texture-isolation-stock-strike` conserva Heat rojo
  aun con Strike BAG2: revisar Heat traje/lado y materiales/CLUT, no culpar solo Strike.
- Corrección Heat posterior verificada en `notes/bag1-character.md`: modelos 96/167
  ahora siguen el traje, no el lado. Ambos diseños revisados en P1/P2 y run inverso
  completó canción/retorno. No cambia bytes Strike. Estado/hashes actuales en current-state.
- Política frame-nearest vuelve a proposed, no aceptada; no desplegada al recuperar.
  Manos/postura/emblema Strike siguen rechazados. Plan aprobado, no terminado.

- ID JP=1. Packs 73/74/145/146; modelos 109/110/181/182. Datos Strike, no plantilla.
- BAG1 A/B 44 huesos; BAG2 A 44, B 42. Compatibilidad histórica no probaba ambos
  trajes. Inicializador de manos stock usa índices distintos según traje.
- Modelo/lista convertidos y TIMs retargeteados integrados mediante payload alternativo.
- Bloqueo VS corregido: el script ad-hoc escribió offsets iguales por miembro.
  Sustituido por `rebuild_dfs_members.py`, sin truncar packs y conservando DBI/SEDT.
- Heat se recuperó de payload original verificado; conservar sus 11 filas al añadir
  ocho Strike. El baseline no es el candidato instalado actual.
- Causa demostrada: en BAG1 carpetas 1/2 son traje A y 3/4 traje B; sufijo de
  fichero A/B es lado P1/P2. Native FUN_8003AE20 y tablas confirman el contrato.
  El inventario viejo confundía ambos ejes y asignaba camisa a P2, no a traje B.
- Recuperación de carga anterior, 6/5 miembros P1/P2, sin TIM de retrato extra;
  payload `5398ea9efc8810df7e14ed7b7faae8d2142e1054ad38857b2fb7d5c2634c2a15`;
   exe `1d1ef29dd1c78f68e21b62001edcf8b50b1ea8b818c82df3a73742cbc79bb5a4`.
- Regresión observada RED→GREEN en A/P2 y B/P1 (modelo y atlas); suite host 112
  verde; build verde y calibración con cuatro capturas de aristas revisadas.
  P1/B `20261103T013200235135Z-strike-costume-role-p1b` falló retorno al selector;
  amarillo visible, emblema/antebrazos/manos incorrectos; ajustes y 21 saves restaurados.
- Lista instalada: 101 slots, 54 vacíos (neutral incluida); nativo vacíos 1/97.
   Política anterior tenía 20 targets sin mapear y fever en slots normales;
   su reemplazo por cercanía de frames tampoco acredita semántica. Perfil pending.
- Auditorías skeleton-contract, hand-initializer y animation-list bajo
  `_work/character_import/strike/texture_diagnosis/`. No prueba de causa única del
  hundimiento; falta medir raíz/soporte de pies y seam runtime.
- Plan `plans/strike-skeleton-motion-recovery.md`: preservar 44 huesos BAG1 y
  adaptar contratos runtime demostrados, reconstruir motions/transiciones.
   Aprobado por propietario; adaptación pendiente. Carga recuperada no es aceptación.
- Run anterior `20261102T122710391240Z-strike-7member-nameplate-p1a` completó
  canción/retorno y preservó ajustes/21 saves, pero revisión visual confirma
  parches blancos en antebrazos. No aceptación visual.
- Baseline pasó cuatro flujos con fuentes mal asignadas, no cuatro trajes correctos.
  Web y tablas nativas corroboran la referencia amarilla con F de BAG1.
- Atlas 004 contiene arnés/tatuajes/zapatos; 005 contiene UI/efectos. Modelo PLAYER4
  contiene torso amarillo, emblema CLUT 13 y cabeza sin coleta.
- Loader nativo 0x80031268 recorre descriptores y permite sobrescribir coordenadas.
  No está demostrado que TIMs añadidos al DFS se carguen; no repetir variantes a ciegas.
- Input audit en `_work/character_import/strike/texture_diagnosis/`: fuentes,
  palabras nativas y paquetes contrastados; payload cabe en DUMMY (27648000 bytes).
- Contraste directo USA/Japón: modelos A/B idénticos por lado; tres raíces 0/22/29,
  no dos trajes demostrados. Cambiar de región no resuelve los materiales de brazos.
- Descriptores runtime BAG2: CLUT corporal P1 (960,0), P2 (960,16), no el (0,480)
  del TIM. No inferir solapamiento runtime desde encabezados. TIM 000 es retrato.
- Referencias del propietario válidas; no volver a bloquear por su procedencia.
- Falta matriz runtime corregida, materiales/CLUT de brazos, animaciones, fever y audio;
  regresiones del generador previas pendientes. No aceptación final ni contenido propio.
- Validación del harness corregida: permitir Strike BAG1; rechazo no implementado
  se prueba con Comet. 49 pruebas navegación + 8 DFS, no cobertura universal.
