---
id: documentation-evidence-audit
title: "Auditoría documental por evidencia y contexto mínimo"
tags: ["plan", "documentation", "audit", "workflow"]
summary: "Propuesta pendiente de aprobación: auditar Markdown propio, contrastar afirmaciones/comandos, consolidar duplicados y verificar integridad y consumo de contexto sin modificar gameplay."
related: ["AGENTS.md", "NOTES.md", "docs/coding-standards.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
---

# Auditoría documental: propuesta

Estado: **pendiente de aprobación del propietario**. La solicitud autoriza
investigar; esta propuesta fija alcance y criterios antes de la depuración amplia.
No se ha ejecutado la consolidación.

## Alcance y evidencia inicial

Inventario preliminar: 63 Markdown versionados, 367064 bytes, 13 superiores a
10000 bytes. Incluye raíz, docs, notes/digests, agent-skills locales, README de
mods y planes. Se inventariarán también Markdown propios no versionados/ignorados;
los generados se clasificarán, no se cargarán ni editarán indiscriminadamente.
Terceros, snapshots y copias de build no son fuentes canónicas.

Hallazgos iniciales, todavía no auditoría completa:
- Familias original/clean/optimized para varios temas: requieren comparación de
  contenido y referencias antes de consolidar; no hay archivos byte-idénticos.
- `ARCHITECTURE.md` referencia `tools/test/bag2_run.ps1`, ausente en ese destino;
  existe helper externo registrado. Debe verificarse el destino correcto.
- `docs/index.md` referencia `docs/guides/import-standard.md`, ausente.
- `MAINTENANCE_GUIDE.md` prescribe pruebas de runtime para cambios de notas y
  tamaños de contexto aproximados que deben sustituirse por medición actual.
- Existen código/candidatos previos sin commit; no pertenecen a la limpieza.

## Estándar propuesto

1. **Hecho verificado:** alcance/versiones/inputs y evidencia o seam concreto.
   Diferenciar lectura de código, tests host y aceptación real en juego.
2. **Requisito del propietario:** norma de trabajo, no funcionalidad ya implementada.
3. **Propuesta o hipótesis:** fuera de las instrucciones operativas; explícitamente
   no verificada. Si no aporta valor, retirar tras revisar referencias.
4. **Histórico:** fechado y fuera de la ruta activa; conserva evidencia única y
   decisiones rechazadas sin presentarlas como procedimiento vigente.

Una fuente canónica por tema, índices que enlazan sin duplicar y digests con
procedencia/fecha. Elegir solo uno entre resumen dentro de nota y digest cuando
ambos repitan el mismo contenido sin justificar su coste.
No usar «funciona» por existir un comando o un archivo. No exigir una captura
de juego para probar un enlace Markdown; cada afirmación tiene su seam adecuado.
No prometer ahorro de tokens a partir de bytes sin indicar método/limitaciones.

## Fases

### 1. Inventario verificable (Size: S)
- Aceptación: cobertura de documentos propios y exclusiones explícitas;
  grupos de duplicación/canonicidad; baseline de contexto de arranque e importación.
- Archivos: informe completo en `_work/docs-audit/`, registro compacto en
  `notes/documentation-audit.md`; helper propuesto `tools/workflow/audit_docs.py`.
- Verificación: `py -3.13 tools/workflow/audit_docs.py inventory` (por implementar).
- Seam: rutas reales, Git, hashes, tamaños, referencias entrantes.
- Blocked by: aprobación del plan.

### 2. Contraste de afirmaciones (batches Size: S/M)
- Batches: raíz/estándares; build/entorno; imports; UI/online; planes/skills locales.
- Aceptación: cada documento revisado tiene resultado; contradicciones con fuente
  citada; declaraciones sin evidencia se corrigen o se etiquetan, nunca se inventa prueba.
- Archivos: Markdown de cada batch y registro de hallazgos; no runtime/plugins.
- Verificación: paths, parsers CLI, fuentes/pins, resultados existentes con hashes;
  ejecutar solo probes read-only seguros cuando sean necesarios.
- Seam: afirmación → evidencia y alcance. Fallo de evidencia queda pendiente.
- Blocked by: fase 1; batches se completan secuencialmente con checkpoints.

### 3. Consolidación (batches Size: S/M)
- Aceptación: una autoridad activa por tema; información única preservada;
  referencias migradas sin perder las reglas del propietario.
- Archivos: `NOTES.md`, `docs/index.md`, runbooks/estándares, `notes/` y digests,
  planes obsoletos tras demostrar estado. Archivar copias útiles o dejar redirect
  corto; borrar solo redundancia demostrada y sin referencias necesarias.
- Verificación: `py -3.13 tools/workflow/audit_docs.py check` (por implementar).
- Seam: enlaces, frontmatter según clase documental, rutas CLI, estado/digest.
- Blocked by: fase 2 del mismo batch.

### 4. Validación repetible (Size: M)
- Aceptación: checker stdlib con tests para enlaces, exclusiones, archivos ausentes
  y falsos positivos de ejemplos/globs; medición antes/después con método idéntico;
  cada corrección trazable a hallazgo, sin tests de juego innecesarios.
- Archivos: helper de auditoría y `tools/workflow/test_audit_docs.py`, informe.
- Verificación: `py -3.13 tools/workflow/test_audit_docs.py`,
  `py -3.13 tools/workflow/audit_docs.py check`, `git diff --check` limitado al task.
- Seam: casos sintéticos del checker + repositorio real. Tokens exactos solo si
  hay tokenizer correspondiente; de otro modo bytes y estimación etiquetada.
- Blocked by: fases 1 y 3.

### 5. Conservación (Size: S)
- Aceptación: checkpoint local de cambios propios; snapshot verificado con backup;
  índice y estado reflejan auditoría terminada o pendientes, sin importar Strike aceptado.
- Archivos: nota de auditoría, plan a archive, documentos canónicos en build para snapshot.
- Verificación: diff staged por ruta, hash de archivos en snapshot, exclusión de build dirs.
- Blocked by: fase 4.

## Decisiones y supuestos para aprobación

| Decisión | Propuesta | Motivo |
|---|---|---|
| Ámbito | Markdown propio del repositorio, incluidos skills locales | Evitar instrucciones contradictorias |
| Historia | Preservar información única; sacar duplicados de ruta activa | Reducir contexto sin destruir evidencia |
| Políticas | Mantener AGENTS; señalar contradicciones, no cambiar preferencias | Workflow aprobado por propietario |
| Automatización | Un checker local pequeño y probado | Evitar otra limpieza manual repetida |
| Evidencia | Código/tests/ejecución según tipo de afirmación | No confundir especificación y aceptación |

## Siempre / Nunca

- Siempre: conservar saves, settings, sesiones, cambios previos y estable; usar
  Git local secuencial. Revisar documentos de terceros solo si hace falta referencia.
- Nunca: reescribir políticas globales de agentes fuera del repo, modificar
  gameplay/conversores para hacer cierta una nota, instalar dependencias,
  publicar/push/PR, borrar histórico único o ejecutar comandos peligrosos de ejemplos.
- Medición no significa promesa: registrar reducción real del conjunto mínimo
  para tareas representativas, no un porcentaje universal de ahorro.

## Progreso

| Fase | Estado |
|---|---|
| 1 | Inventario preliminar; esperando aprobación |
| 2–5 | No iniciadas |
