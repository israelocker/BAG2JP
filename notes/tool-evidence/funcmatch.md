---
id: tool-evidence-funcmatch
title: "Evidencias: funcmatch.py"
tags: ["tools", "evidence"]
summary: "Historial del matcher experimental de ejecutables principales; eficacia pendiente."
related: ["notes/assets.md", "notes/character-pipeline.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: evidence
---

# funcmatch.py — historial

Aplicar [criterios y plantilla](../assets.md#clasificación-y-medición-obligatorias).

## 20261106-funcmatch-001 — antecedente de inspección, no ejecución
- Tipo: inspección histórica del script, transcrita el 2026-11-06.
- Fuente: `tools/bag1import/funcmatch.py`; no se fijó hash en este antecedente,
  por lo que no certifica una revisión futura ni resultados anteriores.
- Entradas/comando: ninguno. No se buscaban equivalentes de funciones en la
  auditoría documental; no corresponde ejecutar el matcher para llenar un log.
- Observado: utiliza rutas fijas y base `0x80010000`, enmascara instrucciones
  y presenta hasta cinco coincidencias. No es matcher genérico de overlays.
- Evidencia: sección Function matching aid en AGENTS y receta en
  `notes/character-pipeline.md`. No hay conjunto de aciertos/falsos positivos.
- Dictamen: **no ejecutado**; eficacia práctica desconocida, requiere validación
  profunda. Inspección de código no es evidencia de buen matching.
- Medición: tiempos y ahorro no medidos.
- Siguiente: cuando se busque un equivalente, registrar hashes de script/binarios,
  ejecutar desde la raíz verificada y contrastar candidatos/callers/rol en Ghidra.

## 2026-11-11 — native-timing-contract: puente JP→US para reloj
- `py -3.13 _work/gaso/match_native_clock.py`, usa sin modificar tools/bag1import/funcmatch.py SHAf296ea81ad74cf3d38aa61cf18ed24db7f986d57ef098e8e839231b06a914a2e. Verifica hardcoded scus.bin/slpm.bin contra payload PS-X EXE/base80010000 antes de buscar. US46cf25699eccd91057c61fe3c68ccd708e2c2c6ea348593e6c7b3ce3171b61c9; BAG2raw143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b; JP9676a28c589e20829e5b43874c8534e49393337f4f5238610598b14257a778ff.
- NativeJP8001f32c→US usa body/mask; cero candidatos US, no se ejecutó find US→BAG2. body alcanzó tope200words y ends_at_jr_ra=false. `_work/gaso/native-clock-match.json`,0.069s; preparación/revisión manual desconocida, ahorro no medido.
- Resultado Inconcluso; ningún candidato para confirmar en MCP; cero no prueba inexistencia ni eficacia general. Se siguió el índice BAG2 ya conocido, no matches inventados ni escaneo de overlays con funcmatch. Siguiente: reutilizar este resultado mientras inputs no cambien; contrastar datos/consumidor005 en Ghidra.
