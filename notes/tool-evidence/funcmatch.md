---
id: tool-evidence-funcmatch
title: "Evidencias: funcmatch.py"
tags: ["tools", "evidence"]
summary: "Historial del matcher experimental de ejecutables principales; eficacia pendiente."
related: ["notes/assets.md", "notes/character-pipeline.md"]
created: "2026-11-06"
updated: "2026-11-10"
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

## 20261110-funcmatch-002 — 2026-11-10 UTC — emisores nativos para el defecto GAS
- Tipo: uso real acotado; matcher experimental sin modificar, SHA-256
  `f296ea81ad74cf3d38aa61cf18ed24db7f986d57ef098e8e839231b06a914a2e`.
- Comando: `py -3.13 _work/gaso/compare_sign_emitters.py`, desde la raíz canónica.
  El wrapper verifica cabeceras PS-X EXE, carga `0x80010000`, payload desde
  `0x800` y correspondencia de ambos ficheros hard-coded antes de usar `find`.
- Entradas: BAG1 USA `_work/bag1/scus.bin`, 333824 bytes, SHA-256
  `46cf25699eccd91057c61fe3c68ccd708e2c2c6ea348593e6c7b3ce3171b61c9`;
  BAG2 JP `_work/mainexe/slpm.bin`, 315392 bytes, SHA-256
  `143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b`.
  No overlays. Regiones contrastadas con SCUS_942.63 / SLPM_862.19.
- Resultado: candidatos únicos BAG1→BAG2 `8002E74C→80027FC8` (56 palabras),
  `8002EECC→80028748` (63), `8002F360→80028BDC` (55); los tres tramos son además
  idénticos byte a byte. Evidencia `_work/gaso/sign-emitter-comparison.json`, SHA-256
  `3c234e3b4a1e17f26fdbd2a7dba5ccbea4631a3e61742991405cabe79f9bb379`.
- Contraste: MCP leyó los tramos BAG2 (ghidra-043); instrucciones/rol de emisor y
  layout FT4 concuerdan con paquetes del snapshot. Callers y ejecución exacta de
  ambos juegos **no** confirmados; no se cargó BAG1 en Ghidra ni se parcheó código.
- Dictamen: **útil** para reducir esta comparación a tres candidatos; **inconcluso**
  como validación general del matcher o causa de A. Identidad de estos tramos no
  implica identidad de todo el renderer/estado de cámara. Ahorro, ejecución y
  revisión/retrabajo no medidos. Siguiente: conservar candidatos, no repetir sin
  cambios de inputs; completar evidencia del frame con oclusión antes de un parche.

## 2026-11-11 — native-timing-contract: puente JP→US para reloj
- `py -3.13 _work/gaso/match_native_clock.py`, usa sin modificar tools/bag1import/funcmatch.py SHAf296ea81ad74cf3d38aa61cf18ed24db7f986d57ef098e8e839231b06a914a2e. Verifica hardcoded scus.bin/slpm.bin contra payload PS-X EXE/base80010000 antes de buscar. US46cf25699eccd91057c61fe3c68ccd708e2c2c6ea348593e6c7b3ce3171b61c9; BAG2raw143b4bf866bf6e47876f54c9667aa476e178b3aaa1ecf4d8a9f022c7583cc00b; JP9676a28c589e20829e5b43874c8534e49393337f4f5238610598b14257a778ff.
- NativeJP8001f32c→US usa body/mask; cero candidatos US, no se ejecutó find US→BAG2. body alcanzó tope200words y ends_at_jr_ra=false. `_work/gaso/native-clock-match.json`,0.069s; preparación/revisión manual desconocida, ahorro no medido.
- Resultado Inconcluso; ningún candidato para confirmar en MCP; cero no prueba inexistencia ni eficacia general. Se siguió el índice BAG2 ya conocido, no matches inventados ni escaneo de overlays con funcmatch. Siguiente: reutilizar este resultado mientras inputs no cambien; contrastar datos/consumidor005 en Ghidra.
