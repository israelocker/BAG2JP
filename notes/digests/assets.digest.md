---
id: assets-digest
title: "Digest: assets y efectividad de herramientas"
tags: ["digest", "assets", "tools"]
summary: "Entrada compacta al inventario, pertinencia obligatoria e historiales por herramienta."
related: ["notes/assets.md"]
created: "2026-11-06"
updated: "2026-11-06"
doc_kind: digest
source: "notes/assets.md"
source_sha256: "95ec3960005ff6ce244a520b06799bb66d6a8ed63589dadaa6ebf5c045e2e098"
---

# Assets y herramientas — digest

- Identificar assets por disco/tabla/miembro/hash, no nombres de carpetas.
- Instalación aislada y versiones en la fuente; ayuda CLI o ventana vacía no
  prueban eficacia BAG2JP. asm-differ necesita configuración y objdump MIPS.
- AGENTS exige uso pertinente y registro posterior: consultar en la fuente la
  tabla de diez historiales bajo `notes/tool-evidence/`. dumpsxiso y mkpsxiso
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
- Primer ensayo jPSXdec sobre XA/STR con hash y contraste sigue pendiente;
  los antecedentes de instalación están etiquetados como históricos.
