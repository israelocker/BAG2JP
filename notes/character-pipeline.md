---
id: character-pipeline-shared
title: "Pipeline compartido de personajes"
tags: ["character", "pipeline", "workflow"]
summary: "Reglas por evidencia y límites de los helpers; perfiles de datos, no pipelines clonados."
related: ["CHARACTER_IMPORT.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md", "notes/strike-recovery.md"]
created: "2026-10-31"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: requirements
---

# Pipeline compartido

Estándar autorizado: mismo motor/orquestación; perfiles contienen IDs, paths,
capacidades y excepciones justificadas, no comandos ni forks del pipeline Heat.

## Gates

1. **Inventario:** disco/región/hashes, IDs reales, modelo, lista, esqueletos,
   miembros y lados/trajes. No asumir conteos/DBI de otro personaje.
2. **Contrato:** significado, beats, eventos requeridos y fuente/destino completos.
   Clasificar vacío/repetido/adaptado y mantener desconocidos sin resolver.
3. **Transiciones:** predecesores y continuidad nativa son chequeos distintos de
   igualdad de slots. Pose final parecida no prueba equivalencia musical.
4. **Candidato:** producir assets solo tras gates de perfil/contrato; no auto-deploy.
5. **Aceptación:** matriz por capacidades, cuatro lados/trajes, movimientos,
   audio, fever aplicable, canción y retorno con mods. Cache no es aceptación.

## Qué implementan realmente las herramientas

`tools/bag1import/character_workflow.py` expone `init-profile`, `validate-profile`,
`plan`, `prepare`, `status`, `acceptance-plan`, `cache-record`, `cache-check`, con
`--profile` requerido. Se contrastó el parser actual. Las recetas completas están
en CHARACTER_IMPORT, no duplicadas aquí.

`animation_policy.py` valida políticas; los remapeadores/auditor Heat y el
remapeador Strike contienen adaptación específica. No hay asignador semántico
universal ni optimizador de grafos aceptado con todos los personajes.
DFS/payload compartidos: [integración](character-alternate-entries.md), con sus
límites manuales. Harness: [pruebas](character-import-testing.md), catálogo limitado.

### Búsqueda auxiliar de funciones: funcmatch

Usar `tools/bag1import/funcmatch.py` para acotar equivalentes entre funciones de los
ejecutables principales BAG1/BAG2 antes de repetir búsquedas manuales. Ejecución
desde la raíz canónica: `py -3.13 tools/bag1import/funcmatch.py <BAG1-address-hex>`.
El script lee rutas fijas `_work/bag1/scus.bin` y `_work/mainexe/slpm.bin` y presupone
base `0x80010000`: comprobar región, hashes y layout de esos archivos primero.

**No está plenamente comprobado; necesita pruebas más profundas.** Enmascara
algunos operandos y devuelve candidatos (la CLI muestra como máximo cinco); puede
omitir equivalentes y producir coincidencias ambiguas. No busca overlays ni decide
equivalencia semántica. Confirmar instrucciones, llamadas y función real en Ghidra;
no aplicar parches ni declarar aceptación basándose únicamente en un match.

## Lecciones verificadas en Strike (2026-11-04): checklist para el siguiente personaje

Cada punto falló de verdad en Strike, se corrigió con evidencia y es reutilizable. Detalle,
hashes y rutas en [Strike](strike-recovery.md). Aplicar como comprobación, no por analogía.

1. **Carpeta = traje, sufijo = lado.** En BAG1 la pareja de carpetas (`PLAYER1/2` vs
   `PLAYER3/4`) elige el traje; el sufijo `A/B` del archivo elige el lado del jugador
   (SCUS `FUN_8003AE20`: lado×14 + traje×28 + personaje). Test: `test_strike_costume_assets.py`.
2. **Alineación DFS a 4 bytes.** El loader pasa miembro+20 a `LoadImage` y el DMA
   redondea hacia abajo (`& ~3u`): un TIM desalineado sube desplazado y produce parches
   blancos. `rebuild_dfs_members.py` ya alinea cada miembro; comprobar offsets mod 4.
3. **Copias de atlas `MoveImage` del DBI de BAG2.** El código del personaje en BAG2
   copia rectángulos de su propio atlas (Strike: DBI `0x2358/0x23D4`, 10×36 palabras).
   Sobre un atlas BAG1 destruyen texturas (emblema B, mancha del pecho A). Anularlas
   con el contrato reversible por hash/guard (`strike-texture-contract.json`,
   `dbi_word_contract.py`) en **todos** los trajes y lados, no solo donde se vio.
   Verificar con volcado de VRAM: atlas y CLUT idénticos al TIM BAG1 tras la carga.
4. **Esqueleto/manos por traje.** Comparar el grafo de huesos de cada traje BAG2 con
   BAG1; un traje puede tener otra topología e inicializador de manos (Strike B: 42 vs 44).
   Adaptar solo el inicializador demostrado (`strike-skeleton-contract.json`).
5. **Neutral nativo en slot 0** y política de 101 slots por rejilla `B2_ROWS/B2_ALT`,
   transiciones nativas y roles semánticos; nunca por cercanía de frames.
6. **Memoria.** Comparar tamaño de modelo+motions con el búfer stock del lado; si no
   cabe, usar la región de RAM ampliada 8 MB (`bag2jp_model_region.h`) en vez de
   recortar motions.
7. **Voces.** Rebasar el banco SEDT BAG1 a `0x6000 + id_BAG2*0x100` **y** los eventos de
   animación al mismo rango; conservar los cues del anunciador BAG2 del personaje
   (`preserve_announcer.py`, Strike `0x1107/0x1108`). Verificar en la tabla SPU
   `0x8007F180` en combate (`probe_cue_table.py`): sin el SEDT rebasado las voces callan.
   **Presupuesto SPU (Gas-O, 06-11):** un VS espejo carga dos bancos de voz; si el
   cuerpo VAB supera al stock, P2 falla en `SsVabOpenHead` (SystemError `'V'`,1,
   ra `8002E060`; ghidra-033). Limitar con `voice_bank.max_body_bytes` del perfil y
   `tools/bag1import/vab_budget.py` (`fit_voice_budget`: dedup sin pérdida, luego
   remuestreo con corrección de tono, ghidra-034; muestras stock byte a byte). El
   remuestreo tiene pérdida: requiere aprobación del propietario y escucha humana.
8. **Escala.** Comparar vértices/traslaciones BAG1 convertido frente a stock BAG2; el
   tamaño en pantalla sale de la escala del bailarín (tabla `0x80051904`). Si el ratio no
   es ~1 (Strike 0,837; Heat 0,98), fijar el factor por personaje/traje en
   `b1v_scale_q12` (`bag2jp_bag1_versions.c`) y verificar en combate espejo BAG1 vs BAG2.
9. **Rostro/iluminación.** Leer paquetes GPU antes de tocar materiales. La prueba
   facial de Strike aisló iluminación sustractiva; **el propietario descartó el
   override nativo del actor** por conflictos con escenarios BAG2 (05-11).
   `strike-lighting-profile.json` y el header son respaldo histórico, no una receta
   activa. Conservar la regresión que exige callback inactivo.
10. **Manifest.** `[[overlay]].sha256` identifica el payload;
    `expected_sha256` identifica los bytes **originales del disco** que se reemplazan,
    con esa longitud, no el payload. `[[target]].disc_sha256` identifica el disco
    y no cambia por regenerar el mod. Ver la receta de integración.
11. **Aceptación mínima reutilizable** (`_work/character_import/strike/`):
    `test_strike_full_match.py` (canción+fever+retorno, A y B), `probe_cue_table.py`,
    `test_strike_scale_mirror.py`, Dance View individual. Restaurar ajustes/tarjetas
    (lo hace `IsolatedFiles`; si un run se interrumpe, restaurar desde su `baseline/`).

## Lecciones de Gas-O incorporadas (2026-11-15)

Owner aprobó incorporar las normas y dejar las mejoras ejecutables para otra
tarea. Evidencia y estado: [retrospectiva Gas-O](gaso-import.md#retrospectiva-incorporada-al-estándar-2026-11-15).
Estas reglas no certifican cobertura actual ni un conversor universal.

### Reutilizar el proceso, parametrizar el personaje

1. **Inventario por variante.** Registrar región/hash, ID, lado/traje, grafo,
   bindings, cola del miembro y slots vacíos/reutilizados. Un miembro puede tener
   bytes válidos tras el modelo; no truncarlos. No hay slot vacío común a todas
   las librerías BAG2 (Pander usa 1; Hiro usa 97). Un hueco no prueba ausencia de
   consumidores. Auditar dispatcher, llamadas directas y overlays antes de reservar.
2. **DBI.** Comparar el código del anfitrión con el modelo importado; no conservarlo
   ni reemplazarlo a ciegas. Adaptar solo stores/copias/inicializadores demostrados,
   con contrato de palabras originales, hashes y restauración por variante. Los
   21/30 bindings y cinco copias de Bi-O son evidencia de Gas-O, no una plantilla.
3. **SPU y cues.** Aplicar el presupuesto `voice_bank.max_body_bytes` ya descrito
   arriba, medido en el anfitrión real, antes de importar. Probar VS espejo (dos
   bancos) y verificar RAM completa cuando los actores exceden 2 MiB. El límite
   64032 B de Bi-O no es universal. Confirmar significado de cues por tabla nativa
   y escucha/transcripción antes de remapear; nombres, frases y efectos son distintos.
   Validar tono objetivamente frente al control nativo además de la escucha humana.
4. **Escala y fidelidad.** Medir primero modelo, motions y captura nativa del mismo
   personaje/región. Distinguir unidades de modelo, escala efectiva y cámara; buscar
   escritores también en el mod host. Registrar valores y procedencia por variante
   (incluida escala sin resolver); no suplirlos con porcentajes elegidos ni declarar
   «exacto» a partir de un build o una escucha. Cambios con pérdida requieren su gate.
5. **CAUGHT, requisito del owner.** Validar la pose en todos los importados BAG1 y
   nativos BAG2, P1/P2, variantes y cada compañero de parejas. Los 28 clips BAG1
   comparados tienen postura común salvo pista 5 de Kitty-N/Strike; difieren en la
   raíz. Conservar esas variantes y resolver colocación por modelo. La regla de raíz
   sigue sin resolver; Pander 13/14 es un candidato sin validación visual. Ni formato
   de 19 pistas ni similitud estadística prueban retarget correcto. Registrar cada
   celda pendiente: el banco actual solo cubre Heat/Strike/Gas-O BAG1.
6. **Hold y versión.** Para una reacción que deba mantenerse, verificar en el
   controlador real loop/clamp, traslación y salida. El clamp metadata+5=1 corrigió
   CAUGHT; no aplicarlo a todos los clips. Seleccionar la versión del receptor por
   su lado al consumirla, no por la versión del atacante. Comprobar re-hit y parejas.
7. **Escenarios.** Identificar ojo y objetivo de cámara antes de escalar distancia;
   tomar el aspecto de la presentación viva, no solo de settings. Comparar el mismo
   recorrido/frames nativos completos: una mejora local no prueba el resto del intro.
   Mantener los eventos por puntaje exigidos en la receta de escenarios.
8. **Motor común.** Un cambio compartido obliga a comprobar los imports afectados:
   regenerar el mapping anterior byte a byte cuando se espera estabilidad y auditar
   diferencias regionales miembro a miembro. No exigir igualdad entre regiones donde
   las fuentes difieren. Matriz y pruebas: [harness](character-import-testing.md).

### RE: demostrar la costura antes de construir sobre ella

- Confirmar región, hash, base, layout y módulo cargado. Buscar también en
  `system/*.dbi` y código host; el main no contiene todos los consumidores.
- Ghidra MCP sigue siendo obligatorio. Si no hay función definida, leer el rango
  con MCP y desensamblar con Capstone (`skipdata=True`); los huecos/datos no son
  instrucciones. Confirmar candidatos, callers y rol en Ghidra, no por byte sweep.
  `FUNCTION_NOT_FOUND` no significa función ausente del juego. Ante backend caído,
  seguir la recuperación registrada en `notes/tool-evidence/ghidra-psx-psyq.md`.
- Separar punteros de instrucciones y offsets de disco/archivo/RAM; comprobar
  JAL+8 y delay slot. No usar direcciones de docstrings de otro build como prueba.
- Demostrar request→slot y orden de eventos en el intérprete PSXRecomp con entradas
  nativas acotadas antes de desarrollar el adaptador. Enganchar antes del consumidor;
  probar también ramas negativas/reflejo. Un fixture artificial se etiqueta como tal.
- Memoria, lifecycle, guards y generación AOT: [estándar de código](../docs/coding-standards.md#regresiones-aprendidas-en-gas-o).

### Exclusivo de Gas-O: no convertir en regla global

Tanque/criogenia, humo, dimensiones/tiempos, voces de Gas-O sobre Bi-O, parche DBI
concreto, selector BI-O/GAS-O y cam95 quedan en su nota/perfil/adaptador.
La colocación del tanque es propia; el deber de validar al receptor CAUGHT es común.
No clonar esos valores para el siguiente personaje ni añadir campos de perfil que
el generador aún no implementa. Requisitos documentados no equivalen a validadores.

**Distancia: implementación común, no excepción Gas-O.** Los hooks de home,
leash y centrado en `bag2jp_bag1_versions.c` seleccionan bailarines BAG1 por lado,
no solo el mapa Gas-O. `bag2jp_bag1_home.h` usa ±870×zoom/256 en escenarios normales
admitidos por su tabla/layout, con exclusiones para especiales y parejas; BAG2
nativo conserva su inicio. Este valor se calibró en el trabajo Gas-O, no es un
campo de perfil ni una garantía de separación visual en todos los escenarios.
Inventariar esas excepciones y validar el escenario real, no copiar una distancia
en píxeles. Ver «Retrospectiva incorporada» de Gas-O para evidencia y límites.

## Referencia cacheada

Reutilizar capturas solo con coincidencia de hashes de motions, perfil, catálogo,
runtime y evidencia. Revisar alcance de `cache-check`: un hit no cubre sonido ni
un paquete modificado. Captura nativa con ajustes/tarjetas aislados y proceso propio.
No competir con la GPU del juego; scripts para hashes/conteos antes que modelos.

## Estado respaldado, no promesas

Strike JP ID=1. [Su ledger](strike-recovery.md) y el plan de disparo conservan
partidas posteriores de los cuatro casos P1/P2 × A/B; los dos casos diagonales
anteriores no son el límite actual ni aceptación global. Separar revisión visual,
fever observado y campaña pendiente. Escenario/audio: [receta propia](bag1-stage-song.md) (requiere obligatoriamente importar eventos/interacciones del entorno según el puntaje, no solo geometría y audio).
Heat tiene adaptadores y evidencia histórica; no generalizar aceptación.
El [documento anterior](archive/character-pipeline-before-audit.md) conserva
decisiones y mediciones antiguas. Existencia de Context7 o Ghidra instalado no
demuestra conexión/servicio disponible en la sesión actual.
