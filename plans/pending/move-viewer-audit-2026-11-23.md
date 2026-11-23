---
status: approved_in_progress (owner 2026-11-23: A-D, pausa antes de E)
source: notes/move-viewer.md "Auditoría completa del visor (2026-11-23)", "Revisión visual detallada", "Validación en el visor ejecutable"
evidence: _work/move-viewer/audit/ (audit.json, visual/, live/, rec/)
---
# Plan visor de movimientos tras auditoría 2026-11-23

Orden: estabilidad → geometría que falta → compañero → fidelidad → validación en juego.
Límite corregido tras indicación del owner: A–D autorizan implementación, Ghidra,
evidencia histórica y pruebas/grabaciones del visor, NO partidas nuevas. Toda captura
nativa nueva y comparación contra el juego pertenece a E y exige parar y pedir continuar.
Una dependencia de evidencia nativa no se resuelve lanzando el juego desde D2/C1.
Las pruebas adelantadas `viewer-d2-cal-d506` y `viewer-d2-cal-317e` fueron rechazadas;
no satisfacen aceptación. El observador experimental317E sigue desplegado, con respaldo
D506 en `_work/move-viewer/audit/d2-v2-stage/BAG2JP.before.exe`; estable intacto.

Estado real: A implementada; B1/B2 con pruebas, B3 parcial y B4 candidato explícito
de mallas hoja (cinco parejas, diez secuencias del visor, sin eventos/mapa nativos); C2 candidato
con grabación del visor; C1 aritmética A/B y estado por nodo explícito (checkpoint70afeac),
sin perfil completo del mismo draw; C3 candidato de preservación local explícita,
sin historial real de motion96. Suite218tests verde. D1 seam identificado, D2 sigue
sin historial/peso del mismo draw; D3 caché y grabación real del modelo primario
slot66 (264frames/88claves), no del dúo. No declarar A–D completas ni aceptar
geometría/iluminación/colocación nativas a partir de estos resultados de host.
Estimaciones en sesiones de trabajo (S ≈ una sesión del agente). Cada tarea termina con
test de host + grabación del visor (`record_live.py`) de los personajes afectados.

## Fase A — Estabilidad (host) · 2 S
| ID | Tarea | Depende | Aceptación |
|----|-------|---------|-----------|
| A1 | Stubs de 4 bytes: marcar "vacío" en la lista, no decodificar | — | test recorre 72 bancos sin excepción |
| A2 | Commit WIP de scene/frame_preparation/preparation_worker/companion_reference + tests | A1 | suite completa verde; commit local etiquetado WIP |
| A3 | `audit_all.py` → `tools/move_viewer/audit.py` + test de regresión | A2 | test falla si aparece prim no soportado, índice fuera de rango o excepción |

## Fase B — Geometría que falta (Ghidra + host) · 5 S
| ID | Tarea | Depende | Aceptación |
|----|-------|---------|-----------|
| B1 | Kind 0x35: leer su emisor en Ghidra (tabla FUN_800220b8) y decodificar | A3 | 0 unsupported en 72 variantes; Comet B con medias |
| B2 | Kinds 0x34/0x36/0x37/0x39: tamaño documentado, fail-closed | B1 | nota + test |
| B3 | Raíces 1–2: qué son y cuándo se dibujan (Ghidra) | A3 | función/condición documentada con dirección |
| B4 | Resolver selección de piezas con evidencia existente; no dibujar todas las raíces indiscriminadamente | B3 | pruebas de selección/imports; dudas nativas sobre Pander/Heat registradas para E |

## Fase D — Compañero y rendimiento (planes ya aprobados) · 4 S
| ID | Tarea | Depende | Aceptación |
|----|-------|---------|-----------|
| D1 | Chichi: seam de captura del historial antes del dibujo (Ghidra) | A2 | dirección del seam y estructura verificadas |
| D2 | Implementar colocación del compañero con contexto explícito e historial verificable existente | D1, B4 | pruebas y grabación del visor; verificación nativa nueva exclusivamente E |
| D3 | Presupuesto de caché de preparación (Chichi slot 66) | D2 | slot 66 prepara sin superar el límite configurado |

## Fase C — Fidelidad visual · 5 S
| ID | Tarea | Depende | Aceptación |
|----|-------|---------|-----------|
| C1 | Implementar cálculo GTE con estado explícito, usando código y capturas existentes | B4 | vectores deterministas y contraste histórico; ajuste/aceptación nativos nuevos en E |
| C2 | Semitransparencia abr 0–3 (Sushi primero, luego los 6 restantes) | B4 | 7 personajes grabados sin artefactos |
| C3 | Tsutomu: barras amarillas + pistas 15/18 de motion 96 | B4 | barras unidas al hueso correcto o explicadas |

## Fase E — Validación contra el juego (requiere owner) · 3 S
| ID | Tarea | Depende | Aceptación |
|----|-------|---------|-----------|
| E1 | Tras pausa y autorización: capturar historial/peso D2, estado GTE C1 y referencias Comet B/Sushi/Tsutomu/Chichi/Capoeira | implementación A–D + autorización owner | manifest `accepted: true`, restauración y verificación nativa de B4/C1/C3/D2/D3 |
| E2 | Comparación fotograma a fotograma visor vs juego | E1 | diferencias listadas; owner confirma conformidad |
| E3 | Commit final, snapshot del hito | E2 | snapshot verificado |

## Gantt por fases (sesiones de calendario; corregido 2026-11-23)
Las fases se solapan: las sesiones de calendario (15) son menos que la suma de esfuerzo.
```
Sesión              1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
FASE A Estabilidad  ━━━━━                                          ◆1 fin S2
  A1 stubs          ██
  A2 commit WIP        ██
  A3 audit test        ██
FASE B Geometría          ━━━━━━━━━━━                              ◆2 fin S6
  B1 kind 0x35            ██ ██
  B3 raíces Ghidra        ██ ██
  B2 kinds resto                ██
  B4 raíces dibujo                 ██
FASE D Compañero                ━━━━━━━━━━━━━                      ◆3 fin S9
  D1 seam Chichi                ██ ██
  D2 compañero                        ██ ██
  D3 caché                                  ██
FASE C Fidelidad                      ━━━━━━━━━━━━━                ◆4 fin S11
  C1 luz GTE                          ██ ██
  C2 semitransp.                            ██ ██
  C3 Tsutomu                                      ██
FASE E Juego (owner)                                 ━━━━━━━━━━━━  ◆5 fin S15
  E1 grabar juego                                    ██ ██  ← autorización owner
  E2 comparar                                              ██
  E3 cierre                                                   ██
```
Ruta crítica: A1 → A2 → A3 → B3 → B4 → C2 → C3 → E1 → E2 → E3.
Hitos: ◆1 visor estable y auditoría como test · ◆2 geometría completa · ◆3 18/18 personajes visibles
· ◆4 fidelidad visual · ◆5 validado contra el juego.

## Delegación
Según `docs/model-routing.md` § "Delegación por tipo de tarea": A1/B2 edición mecánica; A3 tests; resúmenes Ghidra B1/B3/C1/D1 local_llm; B4/C2/D3 implementación; B1/B3/C1/D1 RE difícil (gpt-6.2-sol + primario); revisión Goldfish de `tools/move_viewer/**`; aceptación y E siempre primario/owner.

## Riesgos
- Raíces 1–2 pueden depender de estado de juego no estático → B4 puede quedar parcial (fail-closed).
- La luz GTE puede romper el ajuste ya validado de Heat → comparar contra la referencia existente antes de aceptar.
- Fase E depende de disponibilidad del owner para autorizar partidas.
