---
id: move-viewer-retarget
title: "Visor: copia de movimientos entre esqueletos distintos (Heat, Bi-O, Gas-O)"
status: technical_validation_complete_pending_owner
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
- Cierre técnico posterior (2026-11-22): implementados perfiles, generación, comparación con modelo fuente original y ejecutable; revisión densa de slot0 en Heat/Bi-O P1/P2, además de secuencias conjuntas diagnósticas Heat A/B y Bi-O A/B con fixture realmente ejercitado. Bi-O `rt-bio-duet-residual24-20261122a` accepted=true, modelos íntegros y vuelta al selector revisados. Restaurado exe experimental1518964F verificado; diagnóstico no añadido al allowlist. Detalles/hashes, pruebas host y Goldfish en `notes/move-viewer.md` y logs de herramientas. Estas evidencias cierran el candidato acotado, no fidelidad exacta/universal ni conformidad del owner, aún pendiente.
- Corrección posterior al cierre: la validación del movimiento reconocible sigue abierta. Las capturas son aceptadas por el grabador, no una prueba del slot0 copiado: req106 corresponde a slot71. Revisión correctiva en `notes/move-viewer.md`; no se atribuye conformidad al owner. Este archivo permanece en su ubicación histórica para conservar las referencias, pero su estado ya no es «done».
- Aprobado por el owner. Fase 1/2: `tools/move_viewer/retarget.py` (mapa de pistas explícito, escala de raíz, rechazo de pistas sin mapa o fusionadas). Las diferencias de nodos eran de nodos sin animar: el mapa de pistas resultó ser identidad en Heat y Bi-O, sin recomposición de rotaciones.
- Fase 3 pendiente: no hay vista previa en la UI. La comparación objetiva (`_work/move-viewer/retarget/compare_*.py`: rotación mundial 0.0° y ratio de raíz igual a la escala) es evidencia adicional, no sustituye la vista lado a lado aprobada. No cerrar el plan mientras falte esa funcionalidad.
- Heat: commit 775d7db; tomas rt-heat-p1/p2-20261121a aceptadas.
- Gas-O = variante BAG1 del personaje 9 (carpeta bi_o); no existe otra fuente. Commit c5c1084 (slot_map `sb`); tomas rt-bio-p1/p2-20261121a aceptadas.
- Pendiente: revisión fotograma a fotograma del movimiento copiado y conformidad del owner; vista previa lado a lado en la UI no implementada.
- Avance correctivo posterior: revisadas 12 páginas densas de las cuatro tomas correctivas P1/P2 (460 posiciones solicitadas, no necesariamente fotogramas físicos únicos). Actores correctos e íntegros durante slot0 y su transición; sin afirmación de alineación exacta con frames locales ni dueto completo. Evidencia y límites en la nota canónica.
- Fase 3 implementada en candidato posterior a `8ddcf72`: vista lado a lado con modelo/texturas/mapa originales del banco BAG1 y resultado exacto sobre BAG2, reloj compartido. Probe Qt real revisado para Heat y Gas-O/Bi-O; 102 pruebas host verdes. Goldfish y ejecutable actualizado en curso; estas líneas sustituyen el estado de implementación pendiente anterior, no otorgan aceptación final.
- Verificación posterior del candidato: 106 pruebas host verdes; dos revisiones Goldfish `openai/gpt-6.1-sol` con correcciones aplicadas (límites DFS/modelo, ciclos, fallos de renderizado y cierre de temporizadores). Ejecutable PyInstaller reconstruido y smoke de 18 personajes correcto. Sigue pendiente completar la evidencia fever y la conformidad del owner; detalle y veredictos en la nota canónica.
- Cierre técnico posterior (2026-11-22), sin aceptación universal: 107 pruebas host, comparación fuente/resultado con modelos originales, ejecutable actualizado y smoke18; reubicación109 BAG2/110 BAG1 en runtime1518964F comprobada en toma b (la toma a no ejercitaba banco reubicado). Heat A/B: fixture score y RNG realmente ejercitados, secuencia conjunta inspeccionada y vuelta al selector. Gas-O/Bi-O: slot0 P1/P2 íntegro y reconocible; fever visible parcial, no prueba completa de coreografía/dueto. Conformidad del propietario todavía pendiente. No se amplía esto a todos los movimientos/personajes, ni se convierte la captura accepted=true en aceptación visual universal.
