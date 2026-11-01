---
id: game-controls-menu
title: "BAG2JP Controls and Main Menu"
tags: ["controls", "menu", "reference"]
summary: "Controles reales y harness versus por nombre con estados observados, revisión visual y restauración; catálogo limitado a Heat, Comet y Strike."
related: ["NOTES.md", "AGENTS.md"]
created: "2026-11-01"
updated: "2026-11-01"
edited: "2026-11-01"
---

# BAG2JP — Controles y Menú Principal

## Menú principal (6 opciones)

1. 1 player game — modo campaña
2. 2 player game — versus P1 vs P2
3. practice — modo práctica
4. dance view — pruebas de movimientos de baile
5. ending view — visualizar endings de todos los personajes
6. options — opciones del juego

## Keyboard bindings — Player 1

| Acción | Tecla | Acción | Tecla |
|--------|-------|--------|-------|
| Up | Up | Circle | S |
| Down | Down / K | Square | Z |
| Left | Left | Triangle | A |
| Right | Right | Start | Return |
| Cross | X | Select | Right Shift |
| L1 | Q | L3 | T |
| L2 | E | R3 | Y |
| R1 | W | | |
| R2 | R | | |

## Fuente de configuración y controles de P2

Consultar `keybinds.ini` y `settings.toml` de la instalación experimental antes de enviar entradas. Los comentarios de scripts antiguos no son la fuente de verdad.

La configuración original observada usa teclado en ambos puertos. P2 tiene J/L para izquierda/derecha y K para abajo; arriba, botones frontales y Start están sin asignar. K también está ligado a abajo de P1: no es una entrada independiente.

El harness solo cambia temporalmente las acciones que necesita:

| Acción | P1 temporal | P2 temporal |
| --- | --- | --- |
| Arriba / abajo | Up / Down | I / K |
| Izquierda / derecha | Left / Right | J / L |
| Círculo / cruz | S / X | M / N |
| Triángulo / Start | A / Return | V / P |

No es una nueva preferencia permanente. Se rechazan teclas que accionen otro botón del mismo jugador o del otro puerto. Las tarjetas se copian a un directorio aislado y los ajustes originales se restauran después de cerrar únicamente la instancia propia.

## Navegación por estado observado

1. Esperar la apertura observada (estado raíz 5); saltarla con un único Start. No enviar Start durante la transición 6: puede confirmar campaña cuando aparece el menú.
2. Esperar menú raíz 7 y verificar cursor 1, correspondiente a `2 player game`, antes de confirmar con círculo.
3. Comprobar modo nativo 2 y firmas del overlay JP. El selector se inicializa en 12 y está activo en 13.
4. Leer ambos cursores, mover solo el jugador solicitado y verificar destino e inmovilidad del otro cursor. Inicialmente P1 está en Heat y P2 en Comet.
5. Abrir y revisar el popup; confirmar personaje, versión y traje con su log actual. Confirmar después NORMAL de forma independiente para cada jugador.
6. Verificar escenario y entrada en gameplay (raíz hexadecimal 13, es decir decimal 19). Comprobar identidades y trajes reales; no basta con texto VS, dos bailarines o campos P1/P2.

Un timeout o una observación ambigua detiene la secuencia y conserva evidencia. No se reinicia automáticamente ni se prueban offsets distintos a ciegas. Una fase estable no demuestra bloqueo ni un defecto de fever.

## Harness por nombre

Para consultar el código sin cargar archivos grandes: `notes/digests/versus-navigation.digest.md`, `notes/digests/versus-session.digest.md` y `notes/digests/test-versus-navigation.digest.md`.

```powershell
& tools/test/bag2_versus.ps1 -Action run -Tag heat-mixed `
  -P1Character Heat -P1Version BAG1 `
  -P2Character Heat -P2Version BAG2 -TemporaryControls

& tools/test/bag2_versus.ps1 -Action run -Tag comet-strike `
  -P1Character Comet -P1Version BAG2 `
  -P2Character Strike -P2Version BAG2 -TemporaryControls
```

- Parámetros de traje: `-P1Costume A|B`, `-P2Costume A|B`; escenario predeterminado `HeatBAG2`. Las pruebas de aceptación de esta iteración usan traje A y ese escenario; no certifican las alternativas no ejercitadas.
- Primera calibración, o tras cambiar el ejecutable: `-Action probe -TemporaryControls`. El catálogo local se guarda en `_work/versus-navigation/catalog.json`. Solo puede usarse después de revisar sus capturas y registrar aprobación con hashes de imágenes y digest del catálogo; crear imágenes no equivale a revisarlas.
- Catálogo inicial: Heat, Comet y Strike. BAG1 solo está admitido para Heat. Las demás identidades y rutas permanecen sin soporte hasta inventariarlas y verificarlas; no se afirma compatibilidad con todo el plantel.
- `-Action inspect -GameId <pid>` inspecciona identidad y controles sin iniciar/cerrar procesos ni confirmar una partida.
- La herramienta rechaza sesiones de juego activas. No usar los scripts de prueba anteriores con supuestos de tiempo ni interpretar `-P2Left` como una selección por personaje.

## Evidencia compacta y alcance de aceptación

Cada ejecución conserva `result.json`, logs, backups y capturas bajo `_work/versus-runs/`. La hoja `review-sheet.png` reúne los puntos críticos para una sola revisión visual. El estado automático distingue comprobación de máquina y revisión visual pendiente; una revisión explícita queda en `visual-review.json`, sin falsificar el resultado automático original.

Registro de aceptación y medición: `_work/versus-navigation/acceptance.json`. Se verificaron selección e inicio de Heat BAG1 contra Heat BAG2 y Comet BAG2 contra Strike BAG2, con restauración de configuración y originales preservados. No acredita canción completa, fever, audio ni importación terminada.

Para futuras sesiones, leer este resumen y el resultado de la ejecución pertinente; abrir logs completos solo ante un desacuerdo. Se miden tiempo, entradas y capturas. Sin datos de uso del harness no se afirma un número de tokens ni un ahorro porcentual.

### Baseline inicial (2026-11-01)

| Selección verificada | Tiempo del harness | Entradas | Capturas originales |
| --- | --- | --- | --- |
| Heat BAG1 / Heat BAG2 | 117,091 s | 12 | 9 |
| Comet BAG2 / Strike BAG2 | 120,094 s | 13 | 9 |

Estos tiempos incluyen arranque, captura, cierre y restauración; no miden una partida completa ni demuestran una mejora respecto del proceso anterior. Cada hoja compacta contiene seis puntos de revisión. El contador de llamadas a helpers se añadió después de estas mediciones y se registrará en ejecuciones posteriores; no confundirlo con llamadas al modelo o tokens de nube.

Pruebas host: `py -3.13 -m unittest discover -s tools/test -p 'test_*.py'`: 94 pruebas aprobadas, incluidas 46 del nuevo harness. La revisión independiente detectó y se corrigieron cuatro casos de error: watch detenido con heartbeat vivo, interrupción durante preparación, fallo de hoja de capturas y aprobación no vinculada al grafo. Los casos tienen regresiones; el parser final también se reprodujo contra los logs reales conservados.
