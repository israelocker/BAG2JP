---
id: online-lobby-2instance-tests
title: "Plan de Pruebas del Lobby 1 vs 1 (2 sesiones locales de BAG2JP.exe)"
tags: ["online", "lobby", "testing", "2-instance", "plan"]
status: pending
created: "2026-11-22"
updated: "2026-11-22"
related: ["plans/pending/online-native-lobby.md", "notes/online.md", "tools/online/lobby_server.py"]
---

# Plan de Pruebas del Lobby 1 vs 1 en la misma PC (2 sesiones reales)

## Objetivo
Validar de extremo a extremo, con **dos instancias reales de `BAG2JP.exe --no-launcher`** corriendo en la misma PC (`BAG2JP-exp-8mb`) contra `tools/online/lobby_server.py` (`127.0.0.1:47400`), todo el ciclo de sala 1 vs 1: creación, unión, **bloqueo de inicio sin `READY`**, chat bidireccional e inicio de partida sincronizado.

## Precondiciones
- Binario desplegado: `D:\Games\Bust A Groove 2 (Japan)\BAG2JP-exp-8mb\BAG2JP.exe`.
- Servidor limpio en puerto `47400`: `py -3.13 tools/online/lobby_server.py` (sin instancias previas colgadas).
- Dos perfiles/nombres diferenciados por entorno:
  - **Sesión A (Host)**: `BAG2JP_PLAYER_NAME=HostP1`
  - **Sesión B (Guest)**: `BAG2JP_PLAYER_NAME=GuestP2`
- Ambas ventanas lanzadas en `WinSta0\Default` vía `D:\Dev\interactive-launcher\Invoke-Interactive.ps1` (y sin taparse) para grabación y verificación visual.

---

## Matriz de casos de prueba

| ID | Caso de prueba | Pasos | Resultado esperado (Criterio de aceptación) |
|---|---|---|---|
| **T1** | Arranque dual y conexión al Lobby | Lanzar `lobby_server.py`, Sesión A (`HostP1`) y Sesión B (`GuestP2`). Navegar en ambas a `online match` en el menú principal. | Ambas sesiones muestran el **Online Lobby PS1** conectadas (`NO ROOMS YET` inicialmente) sin error de socket ni crash. |
| **T2** | Crear sala (Host) y unirse (Guest) | En Sesión A pulsar `[C]` (crear sala). En Sesión B pulsar `[R]` (refrescar), verificar la ficha `#1` (`WAIT 1/2`) y pulsar `[Enter]` (unirse). | Ambas sesiones entran a **ROOM 1V1**: Host en lado izquierdo (`1P`, amarillo mostaza) y Guest en lado derecho (`2P`, celeste) con sus nombres y retratos oficiales. |
| **T3** | **Bloqueo de `START` sin `READY` del invitado** *(prueba negativa)* | Con `GuestP2` dentro de la sala pero **sin** haber pulsado `[F5]`, pulsar `[F6]` (`START`) en Sesión A (Host). | El botón del Host sigue en gris (`WAIT READY`), el servidor rechaza `start_match` (`not_ready`), la sala **no se cierra** y la partida **no inicia**. |
| **T4** | Chat bidireccional en sala | En Sesión B escribir `hola host` + `Enter`. En Sesión A escribir `listo para bailar` + `Enter`. | Ambos mensajes aparecen en tiempo real en la caja de chat oscura de **ambas** sesiones con su remitente (`[GuestP2]: ...` y `[HostP1]: ...`). |
| **T5** | `READY!` del invitado + `START [F6]` del Host | En Sesión B pulsar `[F5]` (`READY`). Verificar cambio visual en ambas sesiones. Luego en Sesión A pulsar `[F6]` (`START`). | Al pulsar `[F5]`, aparece el sello verde **`READY!`** sobre el Guest y el botón del Host pasa a verde **`START [F6]`**. Al pulsar `[F6]`, el servidor emite `match_start` con `room_code` a ambas sesiones, ambas invocan `bag2jp_netsync_apply_lobby_match(room_code)` y salen de la sala hacia el modo Versus. |
| **T6** | Cierre limpio y evidencia | Detener grabación oficial, revisar fotogramas de T2, T3, T4 y T5, y revisar log del servidor (`lobby_server.py`). | Grabación aceptada + fotogramas verificados de los 4 hitos (unión, bloqueo sin Ready, chat, Ready+Start) + log sin errores inesperados. |

---

## Orden de ejecución
1. **Preparación**: script automatizado `_work/recordings/run_online_2instance_test.ps1` que lanza `lobby_server.py` (con log detallado de eventos), Sesión A (`HostP1`), Sesión B (`GuestP2`) y grabación en `WinSta0\Default`.
2. **Ejecución secuencial T1 -> T2 -> T3 -> T4 -> T5**:
   - Alternar foco de ventana entre Sesión A y Sesión B antes de cada entrada de teclado (`C`, `R`, `Enter`, `F6` bloqueado, chat Guest, chat Host, `F5` Ready, `F6` Start).
3. **Inspección de evidencia (T6)**:
   - Extraer y revisar fotogramas de cada hito con `read_file`.
   - Confirmar en el log del servidor: `create_room` -> `join_room` -> `start_match` rechazado (`not_ready`) -> 2× `chat_msg` -> `set_ready(true)` -> `start_match` aceptado (`match_start`).
4. **Entrega al owner**: video, fotogramas por caso (T2–T5), log del servidor y dictamen por cada criterio.

## Alcance y límites declarados
- Esta batería valida el **100 % de la lógica de Lobby, Sala, Chat, bloqueo `READY`, perfiles/retratos y arranque dual** entre dos procesos reales de `BAG2JP.exe` en la misma PC (`127.0.0.1`).
- No sustituye la validación final de **Fase 6 en 2 PCs físicos / redes distintas** (`notes/online.md`), que sigue pendiente para probar NAT/latencia real por Internet.
