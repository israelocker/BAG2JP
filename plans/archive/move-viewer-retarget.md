---
id: move-viewer-retarget
title: "Visor: copia de movimientos entre esqueletos distintos (Heat, Bi-O, Gas-O)"
status: done
created: 2026-11-21
---

# Objetivo
Permitir copiar movimientos de otro banco al slot de un personaje cuyo esqueleto
no coincide, sin romper el modelo, y validarlo con partida grabada en BAG2JP-exp-8mb.

# Evidencia actual (`_work/move-viewer/f3/cross_reasons.py`)
- Strike BAG1/BAG2: misma jerarquía → ya soportado.
- Heat BAG1/BAG2: 15 nodos con otro padre (primeros 11,12,13,25,26,27); mapa nodo→pista distinto en 12,13 (38 enlaces en ambos).
- Bi-O: 41 nodos frente a 42; el mapa no se puede derivar.
- Gas-O: no hay archivos BAG1 de origen; la copia solo puede venir de otro personaje.

# Fases
1. **Mapa de huesos por perfil** (host): tabla explícita origen→destino por personaje
   en el perfil, sin heurística oculta; huesos sin pareja quedan "unresolved" y bloquean.
2. **Retargeting por rotaciones locales** (host): copiar pistas por hueso mapeado;
   cuando cambia el padre, recomponer la rotación a espacio del nuevo padre usando la
   pose de reposo de ambos; huesos extra del destino conservan su pista original.
   Pruebas: identidad (Strike→Strike byte a byte), round-trip, rechazo si falta mapa.
3. **Vista previa en el visor** lado a lado origen/resultado antes de generar.
4. **Heat** primero (diferencia acotada), luego **Bi-O** (nodo extra), y Gas-O
   solo desde otro personaje compatible tras mapa explícito.
5. **Validación grabada** P1 y P2 por personaje: modelo íntegro, movimiento reconocible,
   resultado y vuelta al selector; conformidad del owner al final.

# Riesgos / límites
- Formato exacto de rotación/translación por pista aún no documentado para todas las
  pistas: la fase 2 empieza con un análisis Ghidra del decodificador de movimiento.
- Diferencias de proporciones pueden dar deslizamiento de pies; no se promete IK.
- Coste estimado: varias sesiones; Heat es el primer hito comprobable.

# Decisión pedida
Aprobar el plan (o recortar a solo Heat).


# Registro de ejecución (2026-11-21)
- Aprobado por el owner. Fase 1/2: `tools/move_viewer/retarget.py` (mapa de pistas explícito, escala de raíz, rechazo de pistas sin mapa o fusionadas). Las diferencias de nodos eran de nodos sin animar: el mapa de pistas resultó ser identidad en Heat y Bi-O, sin recomposición de rotaciones.
- Fase 3: no hay vista previa en la UI. Se sustituyó por una comparación objetiva (`_work/move-viewer/retarget/compare_*.py`): rotación mundial 0.0° y ratio de raíz igual a la escala.
- Heat: commit 775d7db; tomas rt-heat-p1/p2-20261121a aceptadas.
- Gas-O = variante BAG1 del personaje 9 (carpeta bi_o); no existe otra fuente. Commit c5c1084 (slot_map `sb`); tomas rt-bio-p1/p2-20261121a aceptadas.
- Pendiente: revisión fotograma a fotograma del movimiento copiado y conformidad del owner; vista previa lado a lado en la UI no implementada.
