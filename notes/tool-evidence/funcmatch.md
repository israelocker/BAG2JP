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
