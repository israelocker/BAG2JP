---
id: contributing
title: "Desarrollo local de BAG2JP"
tags: ["development", "workflow"]
summary: "Entrada al workflow autorizado, estándares y evidencia sin duplicar recetas técnicas."
related: ["AGENTS.md", "NOTES.md", "docs/coding-standards.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: requirements
---

# Desarrollo

1. Aplicar `AGENTS.md`; consultar índice/estado y ejecutar preflight.
2. Investigar causa o contrato antes de modificar. Cambios acotados, nombres
   ingleses y comunicación española. No mezclar trabajo ajeno.
3. Aplicar [estándares](docs/coding-standards.md). Escribir regresión que falle
   antes del arreglo de comportamiento, luego verificar que pase.
4. Consultar [rutas](docs/paths.md) y [flujo](docs/workflows.md) de la fase.
   No asumir que el build sincroniza fuentes/recursos ni que una compilación
   acredita aceptación del juego.
5. Para runtime, verificar flujo real en experimental con ajustes/tarjetas
   preservados. Para documentación, aplicar [mantenimiento](MAINTENANCE_GUIDE.md).
6. Guardar decisiones/evidencia, commit local de archivos propios y snapshot
   verificado según AGENTS. El proyecto no tiene remoto: no hay clone/push/PR
   obligatorio ni procedimiento de publicación implícito.

La guía anterior está [archivada](docs/archive/CONTRIBUTING-before-audit.md);
sus ejemplos de API/configuración y promesas no son autoridad vigente.
