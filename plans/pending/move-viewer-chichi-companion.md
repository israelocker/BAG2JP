# F1 Chichi/Sally: acompañante y procedencia P2

Status: proposed_pending_scope_decision

## Objetivo
Mostrar los dos modelos en la previsualización de movimientos aislados cuando su
correspondencia y colocación estén comprobadas, sin presentar una simulación
inventada del estado de una partida como reproducción fiel.

## Evidencia y decisión pendiente
- Resuelto en8db3098: P2 usa su tabla/base nativas;108 tests, dos Goldfish sin
  bloqueantes. No es por sí solo una corrección visual de Chichi.
- Modelo000 principal y002 acompañante comparten banco001.003 es efecto.
- Nativo8002a090 remapea e intercambia slots/estado y condiciona posiciones por
  historial, flags y contexto; un offset fijo universal sería incorrecto.
- Se propone mantener el visor de movimientos aislados: mostrar acompañante solo
  con una correspondencia verificada y etiquetar/bloquear la reproducción conjunta
  que dependa de contexto no disponible. No añadir un simulador de partidas.
- La aprobación de esa política de casos no resueltos es la decisión pendiente;
  no se ha implementado una escena parcial ni cambiado el criterio de aceptación.

## Pasos
### 1. Correspondencias verificadas (S)
- Archivos: un módulo de escena compartido bajo tools/move_viewer y sus tests.
- Criterios: cargar000/002 con banco001; resolver explícitamente pares comprobados;
  rechazar caminos de banco ausente o estado desconocido sin inventar un slot.
- Verificación: prueba roja de omisión del segundo actor y tests de límites;
  `py -3.13 -m unittest discover -s tools/move_viewer/tests`.
- Blocked by: aprobación de política anterior.

### 2. Previsualización conjunta (M)
- Archivos: render_offline.py, anim_view.py, tests de render/comparación.
- Criterios: escena comparte cámara/z-buffer; informa de los casos no verificados;
  mantiene origen/resultado y personajes simples sin regresión.
- Verificación: suite anterior y renders A/B P1/P2 de pares comprobados con
  inspección visual; no se aceptan dos renderizados independientes como escena.
- Blocked by:1.

### 3. Evidencia y empaquetado (M)
- Archivos: nota canónica y evidencias; artefacto PyInstaller existente.
- Criterios: contrastar posiciones/parejas con flujo grabado experimental,
  preservar/restaurar ajustes y guardados; ejecutable smoke y revisión Goldfish.
- Verificación: captura con manifest accepted=true, revisión de frames/eventos
  relevantes según bag2-game-recording; `MoveViewer.exe --smoke` y suite host.
- Blocked by:2; configuración de captura según perfil vigente, no adivinar CLI.

## Always / Never
- Always: flujo compartido, nombres ingleses, estado no verificado explícito,
  originales intactos y evidencia nativa distinguida de hipótesis.
- Never: F4, simulador completo de partida, BAG2JP-win, más limpieza de evidencia,
  publicación ni aceptación universal de todos los movimientos.

## Progress
| Paso | Estado |
|---|---|
| Procedencia P2 | Verificada,8db3098 |
| Decisión de política | Pendiente del owner |
|1–3|No iniciados|
