---
id: assets-digest
title: "Digest: assets y efectividad de herramientas"
tags: ["digest", "assets", "tools"]
summary: "Entrada compacta al inventario, pertinencia obligatoria e historiales por herramienta."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-15"
doc_kind: digest
source: "notes/assets.md"
source_sha256: "45ce0a9961328afa62cc2b7bfe4389656b6a3eacfbec462be37a2056673265a9"
---

# Assets y herramientas — digest

- Identificar assets por disco/tabla/miembro/hash, no nombres de carpetas.
- Instalación aislada y versiones en la fuente; ayuda CLI o ventana vacía no
  prueban eficacia BAG2JP. asm-differ necesita configuración y objdump MIPS.
- AGENTS exige uso pertinente y registro posterior: consultar en la fuente la
  tabla de historiales bajo `notes/tool-evidence/`. dumpsxiso y mkpsxiso
  tienen registros separados; también Ghidra/PsyQ, PCSX-Redux y funcmatch.
- Añadir una entrada por ensayo, incluidos fallos y omisiones justificadas:
  pregunta, versión/comando, hashes/región/módulo, evidencia, contraste,
  dictamen, tiempos/retrabajo, referencia y siguiente decisión.
- Dictámenes: útil/buenos resultados, irrelevante, contraproducente,
  inconcluso o no ejecutado/bloqueado. No inventar tiempos ni ahorro.
- Historial acumulativo: corregir mediante nueva entrada enlazada. No ejecutar
  todas las herramientas ni repetir evidencia intacta para llenar registros.
- Copias/salidas nuevas; preservar sesiones y partidas. Ghidra MCP obligatorio,
  PSXRecomp nativo y aceptación real/escucha humana siguen siendo necesarios.
- La instalación06-11 y su primer ensayo pendiente son históricos: consultar
  ensayos posteriores en el log pertinente. Un uso XA no valida STR ni otros inputs.
- FFmpeg operativo `.agents/skills/ffmpeg-skill`; copia vieja `tools/ffmpeg-skill`
  conservada, sin borrado autorizado por esta revisión. Inventario/doctor no prueban
  fidelidad; no modificar audio/velocidad de evidencia original sin autorización.
