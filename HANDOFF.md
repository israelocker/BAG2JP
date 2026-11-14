---
id: handoff-gaso-20261112
title: "Handoff: ataque del tanque Gas-O y reacción CAUGHT"
tags: ["handoff", "gaso", "bag1", "caught"]
summary: "Punto de entrada limpio para retomar la reconstrucción fiel del ataque del tanque de Gas-O. Incluye el hallazgo P0 sobre el binario desplegado, el contrato nativo confirmado y los pendientes con su criterio de aceptación."
related: ["AGENTS.md", "NOTES.md", "_work/current-state.json", "notes/gaso-import.md", "plans/gaso-attack-effect.md"]
created: "2026-11-12"
updated: "2026-11-12"
doc_kind: handoff
---

# HANDOFF — Gas-O: ataque del tanque y reacción CAUGHT

## 0. Cómo usar este documento

Orden de lectura de una sesión nueva:

1. `AGENTS.md` (reglas del proyecto, obligatorias).
2. `NOTES.md` (índice; no es un segundo estado).
3. `_work/current-state.json` → `active_task.next_action`.
4. **Este documento** (estado real y siguiente paso).
5. Solo la nota concreta del tema: `notes/gaso-import.md` (ledger canónico),
   `plans/gaso-attack-effect.md` (plan F1–F8 aprobado).

Este documento no sustituye a las notas: es el mapa de entrada. Si algo aquí
contradice la evidencia en disco, **manda la evidencia** y hay que corregir el
texto, no al revés.

---

## 1. Objetivo vigente

Reconstruir el **ataque especial BAG1 de Gas-O** en BAG2JP con fidelidad
completa: efecto visual, sonido, tamaño, altura de caída, lógica y **reacción
del rival (CAUGHT)**, sin inventar escalas, tiempos ni poses.

Petición literal del propietario (2026-11-10): «necesitamos la reconstrucción
100% fiel: el efecto, sonido, tamaño, todo». Aprobado el plan F1–F8
(`plans/gaso-attack-effect.md`).

Alcance: solo instalación experimental `BAG2JP-exp-8mb`. La instalación estable
`BAG2JP-win` no se toca. Fuera de alcance: puntuación BAG1, remasterizar,
rehacer música/escenario, cambios incidentales a otros personajes.

---

## 2. Resumen de 60 segundos

**Vigente (2026-11-12):** banco enlazado, captura/consumo observe-only y lookup
diagnóstico por receptor probados en exp-8mb `A9296DDB`: Heat BAG1 `ready`,
Heat BAG2 `rejected`, `a2 unchanged`, canción y regreso al selector.
El clip sigue sin publicarse; no es aceptación de la animación CAUGHT. Véanse
§8 y `notes/gaso-import.md` § `caught-observe-20261112` y
§ `caught-p2a-lookup-20261112`. Los builds y resultados
de la sesión anterior que siguen son históricos.

**Aceptado y preservado:** cartel GAS del escenario (defecto A), aceptado por el
propietario el 2026-11-10. Escala de Gas-O es candidato host (3132 Q12), no
aceptación visual.

**No aceptado:** el efecto del tanque. Hoy lo instalado es un candidato
aproximado; el port fiel (F2/F3/F4/F5) sigue abierto.

**Histórico cerrado (no re-verificar sin motivo, no confundir con aceptación):**

- Importación Gas-O USA: fases 0–5, P1/A, P1/B, P2/A, P2/B y canción completa con
  vuelta al selector (evidencia 2026-11-06). No demuestra escenario Gas-O ni
  variante JP aceptados.
- Escucha en combate de Chemical Love: ejecución real con audio SPU/FLAC completo
  (`_work/versus-runs/20261108T225855012145Z-gaso-listen-gameplay/`).
- Cartel GAS intro v2: sin solape en las capturas reales; aceptado 2026-11-10.
- Escala Gas-O 3132 Q12: candidato host probado (6/6), no aceptación visual.

**Completado en la sesión anterior (2026-11-11):**

- Acceso a clip CAUGHT en arena propia `9f000000..9f100000` (Expansion1), con
  API legacy intacta y adaptador con región explícita.
- Banco de clips auténticos CAUGHT (host-only, **no enlazado al runtime**).
- Lector de contexto de llamada (host-only, **no enlazado**).
- Captura de origen en el *productor* de la petición 202 (host verificado).
- Wiring runtime: callback de entrada `0x8002d06c` + plugin de instrucción en
  `0x8009b5b4`.
- Build `gaso-caught-deploy-2jobs` (3/3 pasos, 25,5 s) y despliegue del
  ejecutable a `BAG2JP-exp-8mb`.

**No se jugó** tras ese despliegue. No hay ninguna aceptación nueva.

**Antes de cualquier partida:** leer la sección 3 (P0).

---

## 3. P0 — resuelto 2026-11-12 (corrección de la premisa más abajo)

**Estado (evidencia fresca 2026-11-12):** el despliegue `BDAF4B82` ya era inerte
en la práctica: el runtime fijado (`mod_packages.cpp:4150-4183`,
`mod_runtime.cpp:368-394`) solo activa hooks de los ids presentes en
`plan.plugins`, y el manifest desplegado `F76698BE` no declara
`bag1-gaso-caught`. El registro no filtra; la activación sí. Corrección posterior:
la ausencia de `0x8009b5b4` en `mod_instruction_sites` no impide la captura vía
intérprete dirty-RAM: se observó en diag2 al activar ambos ids. Esa lista es
necesaria para instrumentar ejecución nativa AOT. El defecto de código era real
y latente; quedó corregido (`GASO_CAUGHT_CLIP_PUBLISHED 0`, captura solo de
origen Gas-O BAG1 directo, consumo único, invalidación en cada publicación).
Tests host RED→GREEN, Goldfish CON HALLAZGOS aplicados, build `68E3AB2E…`
desplegado en `BAG2JP-exp-8mb` con hash verificado. Sin partida. Detalle en
`notes/gaso-import.md` § `caught-p0-inert-20261112`. El texto siguiente es el
diagnóstico histórico original.

Las notas describen el callback como «inerte/default-off». Eso es cierto solo
mientras `captured[]` esté vacío. En el binario actual, en cuanto se acepta una
captura, el callback cambia `a2=1` en **todas** las entradas posteriores a
`0x8002d06c`, sin consumir ni limpiar el registro.

Por qué importa:

- La captura acepta **cualquier** publicación de la petición 202 que pase las
  validaciones (tabla `0x80051458` por carácter de origen). Heat, Strike y Gas-O
  comparten la petición 202, así que un especial de Heat o de Strike también
  llena `captured[]`.
- Con `a2=1` se pide la ruta de slot1 (préstamo/owned), pero **no hay clip
  auténtico publicado** ni bytes copiados al guest: la reacción podría usar un
  slot1 ajeno, congelar o romper visualmente al rival.
- No hay evidencia en juego de este build; no se puede afirmar que sea inocuo.
- Tampoco está observado en juego que el plugin de instrucción se dispare en el
  overlay real; lo verificado es la cadena: callback enlazado en el ejecutable,
  registro sin filtro de feature y `a2` escrito cuando hay registro.

Evidencia concreta (verificada en esta sesión):

| Hecho | Dato |
|---|---|
| El ejecutable desplegado contiene los dos callbacks | cadenas `bag2jp.gaso_caught` y `bag2jp.gaso_caught_capture` presentes en `BAG2JP.exe` |
| El registro de plugins no consulta la feature/manifest | `psx_mod_register_function_entry_plugin` solo valida id/dirección/callback |
| El manifest desplegado no declara `bag1-gaso-caught` | `mods/bundled/.../manifest.toml`, 4587 B, SHA `F76698BE…` (manifest aceptado) |
| `captured[]` nunca se limpia | estático, solo escritura en `capture_producer_source()` |
| El callback escribe `gpr[6]=1` | `bag2jp_gaso_caught.c`, `gaso_caught_entry_cb()` |

Acción mínima antes de jugar (elegir una):

- **(a)** Volver a dejar el runtime realmente inerte: no escribir `a2` salvo que
  exista una captura **autenticada como Gas-O**, consumida una sola vez, y con
  clip verificado; o
- **(b)** desplegar la variante inerte de cuarentena (stub de 1085 B,
  `17CEB85D…`) y continuar la investigación sin exponer el juego.

Criterio de aceptación del P0: un test host que demuestre (1) que una petición
202 de Heat/Strike **no** produce cambio de `a2`, y (2) que tras una captura
válida el cambio ocurre una sola vez y solo con origen Gas-O acreditado. Después,
build y despliegue experimental verificados por hash.

---

## 4. Estado por capas

| Capa | Archivo(s) | Estado | Verificación |
|---|---|---|---|
| Política de préstamo | `bag2jp_caught_loan.h` | Host, commiteado | 6 tests binding/loan |
| Binding tupla slot1 | `bag2jp_caught_binding.h` | Host, `_in` con región owned | 10 tests owned clip |
| Adaptador + ciclo de vida | `bag2jp_caught_adapter.h` | Host: `b1ca_reset/save_state/load_state/state_size` (128 B) | 25 tests, escenarios 0–24 |
| Banco de clips auténticos | `bag2jp_caught_bank.{h,c}` + `_data.inc` | **Enlazado** (P1, 2026-11-12): lo prepara la activación de `bag2jp.gaso_caught`; nada lo consulta aún | `build_caught_bank.py --check`; 7 tests bank + escenarios 1/4/5/6 runtime |
| Lector de contexto | `bag2jp_caught_context.{h,c}` | Host, **no enlazado** | 111 escenarios |
| Captura de origen | `bag2jp_caught_source.{h,c}` | Host verificado | probe3: 124 llamadas, 100 aceptadas |
| Composición de entrada | `bag2jp_caught_entry.h` | Host, **no incluido** por el runtime | 5 tests / 60 ejecuciones |
| Callback runtime | `bag2jp_gaso_caught.c` | **Enlazado y desplegado**, inerte (`GASO_CAUGHT_CLIP_PUBLISHED 0`, feature apagada) | 9 tests, escenarios 0–6 × 2 builds |

Staging vigente (2026-11-12, P1): el build tree compila copias hash-idénticas
de las canónicas: `bag2jp_gaso_caught.c` `2020CF47…`, `bag2jp_caught_bank.c`
`6C3225FF…`, `.h` `FD9D107E…`, `_data.inc` `238AFCD5…`. El `CMakeLists.txt`
del build tree (no versionado) tiene en L75–78 `target_sources` para
`gaso_caught`, `caught_source`, `caught_context` y `caught_bank`; el repo
canónico no guarda ese cableado (hueco previo). Exe desplegado en exp-8mb:
`01C9BD93…`. El detalle de abajo es histórico (antes de P0/P1).

Detalle histórico de staging:

- El build compila `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP/src/bag2jp_gaso_caught.c`
  (SHA `B605A188…`), que es la versión **con captura** pero con literales en vez
  de constantes con nombre.
- La copia canónica `mods-src/.../bag2jp_gaso_caught.c` (SHA `A1CFEBEA…`, 8629 B)
  ya tiene las constantes con nombre; **no está staged** en el build tree.
- `src/mods-src/.../bag2jp_gaso_caught.c` es un stub inerte obsoleto de 1085 B
  (SHA `17CEB85D…`); no se compila, pero confunde. No lo tomes como estado real.
- El manifest canónico (`mods-src/.../1.0.0/manifest.toml`, 4974 B, SHA
  `6EAB9377…`) **sí** declara la feature `bag1-gaso-caught` (`default_enabled =
  false`); el desplegado en exp-8mb no (SHA `F76698BE…`).

---

## 5. Contrato nativo confirmado (no re-investigar sin motivo)

Todo lo siguiente está contrastado con Ghidra MCP (main JP SHA `ea5a1668…`,
raw `143b4bf8…`, base `0x80010000`) y/o probes host. Reutilizar mientras los
hashes no cambien.

**Entrada del controlador (hook aprobado)**

- `0x8002d06c` es un controlador: `a0` = puntero al controlador, el actor está
  en `word[a0]`. `a2` es el modo/slot de destino.
- La petición 202 **ya llegó como slot 89** antes de esta función; no comparar
  aquí contra 202.
- Hook en codegen: `patches/BAG2JP-game.toml` línea 36 →
  `mod_function_entry_funcs = ["0x8002D06C"]`; el generado
  `generated/SLPM_862.19_full_09.c` contiene
  `if (psx_mod_function_entry(cpu, 0x8002D06Cu)) return;` (L11308).

**Productor de la petición**

- `0x8009b5b4`: `sh v0,0x18(s5)` — palabra esperada `0xa6a20018`.
  Registros antes de ejecutar: `v0`=petición, `s2`=lado origen,
  `s4`=lado receptor, `s5`=dirección de pending del receptor, `sp`=pila.
- `0x8009b588` guarda el carácter de origen en `0x8005e728 + side*0x32 + 0x2f`.
- El selector borra activo/origen antes del consumidor: **no se puede recuperar
  la dirección con una lectura tardía**.
- Flag en `sp + 0x30 + receptor`: `1` = directo, `2` = reflejado (mismo lado).

**Tablas y estructuras**

| Símbolo | Dirección / regla |
|---|---|
| Lista principal de actores | `0x8005f808 + side*8` |
| Controlador main | `0x8005f820 + side*0x98`; companion en `+0x4c` |
| Actor: bytes | `0x155c` (carácter en `+4`, lado en `+5`) |
| Tabla carácter→petición | `0x80051458`, 18 filas, stride 2 |
| Pending global | `0x8005cf08 + side*0x24 + 0x18` |
| Puntero base de overlay | `word[0x80010ce0] == 0x8008f890` |
| Instrucciones a validar | `0x8009b5ac` = `0x90420000`, `0x8009b5b0` = `0x00000000` |
| Consumidor del dispatcher | `0x8009d06c..0x8009d0c8` |
| Dispatcher | `0x8002a090`; RA main `0x8002ae68`; RA exterior en `word[sp+0xd4]` |

**Traducción de peticiones observada:** 200→85, 201→87, 202→89, 203→91, 204→71;
al expirar el temporizador con current 89 se pide salida 90.

**Arena de memoria propia**

- `psx_mod_alloc_guest_memory(size, align)` → arena bump de 1 MiB en
  `PSX_MOD_MEMORY_BASE = 0x1F000000`, devuelve `0x9F000000 + offset`.
- Sin liberación, `memset` a 0, alineación potencia de 2 ≤ 4096.
- Asignar **una sola vez, tamaño fijo, en init del plugin**: el snapshot/layout
  cookie depende de `mod_memory_used`.
- `0x80400000` **no está reservado**. No escribir clips ahí.

**Clips auténticos CAUGHT (host verificado con el decoder original 70)**

| Rival | Bytes | Offset en el banco |
|---|---|---|
| Heat | 348 | 0 |
| Strike | 352 | 348 |
| Gas-O | 348 | 700 |
| Total | 1048 | — |

Generador: `tools/bag1import/build_caught_bank.py --check`, contrato
`tools/bag1import/contracts/caught-bank.json`. Fuente: miembro 1, slot 70 de los
DFS BAG1. El `.inc` determinista tiene SHA `238afcd5…`.

**Contrato estático BAG1 (para F2/F3, aún no equivalencia temporal probada)**

- `0x8001f32c` genera el flag `02` cada 4 pasos de tabla (fase retardada).
- `0x8001fc84` inicializa el ataque con contador 3; `0x8001ef9c` transfiere
  contador y carácter atacante al rival con flag `10`.
- Salida visual: `0x801d6480` (estado 2 espera contador rival < 1),
  `0x801d60c4` (estado 0 con pulso `02`).
- BAG2 calcula duración como
  `T[barStart + 4*units + 3] - T[barStart + 3]` con `T = 0x8005e2f0`,
  `barStart = 0x8005e684`. La equivalencia con BAG1 **no está demostrada**.

---

## 6. Lo único medido en partida (2026-11-11, build diagnóstico)

Partida limpia `_work/versus-runs/20261111T163601126807Z-gaso-clean-tank-attack/`
Gas-O BAG1/A vs Heat BAG2/A, fixture artificial (sin escrituras de animación
rival). Resultado: **no se ve un tanque activo ni se prueba fidelidad**.

- P1 `110→74`: f7005/song695 y f7211/song901.
- P2 `202→89`: f7109/song799 y f7313/song1003 (dos peticiones, no una).
- P2 permanece en slot 89 hasta f7529/song1219 (420 frames muestreados).
- Slot 90 dura 92 frames; vuelve a slot 6 en f7621/song1311.
- P1 `123→78` desde f7415/song1105 (cansancio del atacante, no de la víctima).

Esto es routing observado, **no** un temporizador. No convertir 420/216 frames en
constantes ni equiparar song-frame BAG2 con el flag beat/bar BAG1.

---

## 7. Comandos reproducibles

```powershell
$PY='D:/Dev/Tools/ghidra-mcp-python/python.exe'
& $PY tools/workflow/bag2_workflow.py preflight --tag <tarea>
& $PY tools/workflow/bag2_workflow.py build   --tag <tarea>
```

Tests (Windows, `py -3.13`):

```powershell
py -3.13 -m unittest -v tools.test.test_caught_adapter tools.test.test_caught_source `
  tools.test.test_caught_context tools.test.test_caught_integration `
  tools.test.test_gaso_caught_runtime tools.test.test_caught_bank

py -3.13 -m unittest discover -v -s tools/test -p "test_*.py"
py -3.13 tools/bag1import/build_caught_bank.py --check
```

Baseline de la suite completa (no verde, preexistente): **306 tests, 1 fallo +
32 errores**, siempre los mismos nombres. El fallo es «Existing Heat entries must
all be preserved»; los errores son `KeyError` en `test_strike_costume_assets` /
`test_strike_texture_contract`. Comparar nombres, no solo el número.

Ghidra (obligatorio, lo abre el agente):

```
D:/Dev/Tools/ghidra_12.1.4_PUBLIC/ghidraRun.bat D:/Dev/Recomp/BAG2JP/ghidra/BAG2JP.gpr
```

Abrir `SLPM_862.19` en CodeBrowser y llamar `get_program_info` antes de cualquier
consulta. Un proceso Java vivo no prueba que MCP funcione.

Juego: `D:/Dev/Tools/winshot/bag2_run.ps1` y `tools/test/bag2_report.py`.
Instalación de pruebas: `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`.

---

## 8. Pendientes en orden

**P0 — Neutralizar el binario.** Cerrado 2026-11-12 (ver §3).

**P1 — Clips auténticos en guest.** Enlazar `bag2jp_caught_bank.c`, asignación
única al init, copia verificada de los 1048 B. Aceptación: lookup rechaza
corrupción sin reparar; decoder lee las poses correctas; arena intacta tras
reset/savestate.
Estado 2026-11-12: banco listo en `9f000000` y captura/consumo **observe-only
verificados en juego** con exe `97DE924A…`: dos impactos Gas-O BAG1 → Heat BAG2,
`sp=807fff28`, ambos consumidos por lado 2 con `a2 unchanged`. P2a (exe
`A9296DDB`) añade el lookup diagnóstico por personaje/versión del receptor:
Heat BAG1 `ready` y Heat BAG2 `rejected`, sin publicar. Ver
`notes/gaso-import.md` `caught-observe-20261112` y
`caught-p2a-lookup-20261112`. Esto no prueba la lectura de
poses por el decoder ni la arena tras reset/savestate, aún pendientes.
Activar la feature cambia el cookie de layout de savestate
(`mod_memory_used` +1048 B): los savestates hechos con la feature apagada se
rechazan con ella encendida y viceversa. Si la primera copia falla, el banco
queda no disponible para todo el proceso aunque un savestate restaure los bytes.

**P2 — Autorización y consumo.** El registro debe probar: Gas-O principal y
atacante, `bag2jp_bag1_has_version()` + selección real (no solo `get_version`),
generación/identidad de carga, origen no reflejado ajeno. `take` consume una
sola vez; `ABANDON` owned y retiro quiescente implementados en runtime.

**P3 — Ciclo de vida.** Conectar `b1ca_reset/save_state/load_state` al
reset/savestate reales del runtime (hoy solo probado en host).

**P4 — Equivalencia temporal.** Demostrar la alineación BAG1 flag02 ↔ tabla
BAG2 antes de fijar duración. No usar 420/216 frames como contrato.

**P5 — Fidelidad visual/sonora (F2/F3/F4/F5).** Partículas/gas, escala, altura
de caída, fade, y cues de audio `0x1806/0x180a` con PCM/onset verificado.
Estado actual: identificados, muestras desplegadas remuestreadas, falta
contraste.

**P6 — Aceptación (F7/F8).** P1/P2 × A/B, acierto/esquiva/defensa, liberación,
fin de canción, fever y retorno al selector; matriz de 19 personajes por tandas.

---

## 9. Prohibiciones y trampas conocidas

- No reservar ni escribir en `0x80400000`: **no es una reserva**.
- No escribir el pending del actor/controlador (`+0x18`) para forzar CAUGHT.
- No sustituir el slot 78 globalmente ni forzar frame 0 por tick.
- No usar HOLD65/FADE15 ni constantes del candidato aproximado como contrato.
- No regenerar ni sustituir el payload aceptado
  (`376287AB…`, stage `0A994860…`).
- No modificar la instalación estable `BAG2JP-win`, saves, tarjetas ni ajustes.
- No declarar aceptación por compilar, desplegar, pasar tests o aprobar un plan.
- No asumir que «petición 202 + Gas-O enfrente» identifica el ataque: hay 8 casos
  con 202 y Gas-O delante cuyo origen es Heat o Strike.
- No confundir «opponent es Gas-O» con «el ataque es de Gas-O» (caso espejo).
- No re-ejecutar la partida limpia ni los probes con inputs idénticos sin que
  cambie código o hipótesis.

---

## 10. Evidencia en disco

| Qué | Dónde |
|---|---|
| Estado de tarea | `_work/current-state.json` |
| Ledger Gas-O (histórico completo) | `notes/gaso-import.md` |
| Plan aprobado F1–F8 | `plans/gaso-attack-effect.md` |
| Decoder original (10 intentos, probe10 OK) | `_work/gaso/owned-decoder-probe10/trial.json` |
| Banco de clips | `_work/gaso/caught-clip-bank-report.json` |
| Lector de contexto (111 escenarios) | `_work/gaso/caught-context-reader-report.json` |
| Captura de origen (probe3) | `_work/gaso/source-capture-probe3/trial.json` |
| Procedencia del impacto (probe5) | `_work/gaso/hit-provenance-probe5/trial.json` |
| Contexto del dispatcher (probe3) | `_work/gaso/caught-dispatch-context-report.json` |
| Contrato de entrada | `_work/gaso/caught-entry-contract-report.json` |
| Build observe-only vigente | `_work/workflow/20261112T050545068145Z-gaso-caught-lookup-observe/` |
| Partida positiva P2a (receptor BAG1) | `_work/versus-runs/20261112T051100576135Z-gaso-p2a-lookup-heat-bag1/` |
| Partida negativa P2a (receptor BAG2) | `_work/versus-runs/20261112T051605884720Z-gaso-p2a-lookup-heat-bag2/` |
| Calibración del exe `A9296DDB` | `_work/versus-runs/20261112T050755645568Z-gaso-p2a-calibration/` |
| Partida observe-only histórica | `_work/versus-runs/20261112T042121831233Z-gaso-caught-observe-diag2/` |
| Revisión visual acotada | En esas partidas: hojas de contacto y capturas de retorno |
| Regresión de pila y suite | `_work/gaso/observe-stack-{red,green,full-suite}.log` |
| Suite P2a | `_work/gaso/p2a-{red,green,green2,full-suite}.log` |
| Suite de integración | `_work/gaso/caught-loan-gaso-caught-integration-final.json` |
| Revisiones Goldfish | `_work/goldfish/*.json` |

Ejecutable desplegado en exp-8mb: `BAG2JP.exe`, SHA
`A9296DDBF5A9DE268C297D52F19E7654D95F73C71DD6FED42D9FB58B203D4F57`
(igual al del build tree). Backups `BAG2JP.exe.bak-97DE924A-pre-lookup` y
`BAG2JP.exe.bak-AE55F0C2-pre-stack`.
Feature habilitada solo en experimental; `GASO_CAUGHT_CLIP_PUBLISHED=0`.

---

## 11. Git y checkpoints

- Rama `fix/gaso-tank-anchor`. 2026-11-12: `7122b89` (P0 inerte), `f1355e1`
  (P1 banco enlazado) y `ab5480e` (captura/consumo observe-only con RAM viva).
  Este último checkpoint local WIP contiene runtime, harness, driver y solo el
  bloque CAUGHT del manifest; excluye los cambios previos de hashes del payload.
- Inventario histórico de la sesión anterior: 98 entradas sucias en `git status`;
  no es el recuento actual. Trabajo previo de otros temas preservado.
- Sin commit, push, worktree ni snapshot en la sesión anterior.
- Inventario histórico entonces sin commitear: `bag2jp_caught_source.{h,c}`,
  `bag2jp_gaso_caught.c`, harnesses y tests asociados.
- Commits locales de esta línea de trabajo: `2726fe4` (composición de entrada),
  `bf01979` (banco de clips), `28aaeee` (lector de contexto).
- El repositorio no tiene remoto: un commit es solo un checkpoint local.

---

## 12. Siguiente acción exacta

P0 cerrado; banco, captura/consumo observe-only y lookup diagnóstico P2a
probados el 2026-11-12. No repetir partidas con inputs iguales. Siguiente:

1. P2b completado (investigacion, 2026-11-12): evento de recarga = ciclo de
   fases `DAT_8005d3dc` 0->1->2->3->0; fase 3 reinicializa las cuatro parejas
   controlador/actor y pone `+0x18=-1`; los buffers de actor son RAM fija
   (`0x800ddb18`/`0x80154db4`), por lo que la identidad del puntero no es
   generacion. Regla de invalidacion de `captured[]` documentada en
   `notes/gaso-import.md#caught-p2b-generation-20261112`. Sin escrituras ni
   publicacion; `GASO_CAUGHT_CLIP_PUBLISHED=0`.
2. P3 completado (investigacion, 2026-11-12, commit ee2640a): session_reset y
   savestate registrados para bag2jp.gaso_caught; ambos invalidan captured[]
   sin escrituras guest ni asignaciones (escenario 10 del harness, 21/21 host
   OK). Falta: publica/restore quiescente con guard y aprobacion del
   propietario. CLIP_PUBLISHED=0, sin escribir guest, sin game run.
3. Ambos ids ya estan declarados. Correccion al requisito historico: el hook
   `0x8009b5b4` si dispara via interprete dirty-RAM sin
   `mod_instruction_sites`; instrumentarlo sigue siendo necesario si se cambia
   a ejecucion nativa AOT.
4. `bag2jp_bag1_versions.c` sigue con drift canonico->build tree (guarda
   `active/force_stock`, afecta a todos los personajes): re-stage como tarea
   propia con su prueba.
