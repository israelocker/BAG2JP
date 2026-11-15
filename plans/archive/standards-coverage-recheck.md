---
id: standards-coverage-recheck
title: "Reanálisis de cobertura del estándar BAG2JP"
tags: ["plan", "standards", "evidence"]
summary: "Contrastar casos ya observados con reglas y aceptación explícitas; solo documentación, sin nuevas capacidades runtime."
related: ["notes/gaso-import.md", "notes/character-pipeline.md", "notes/bag1-stage-song.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: plan
---

# Reanálisis de cobertura

Autorización: owner, «analiza todo el estandar que tenemos, y reanaliza si estas
considerando realmente todos los casos que vimos y agrega el detalle en caso sea
necesario o de un mejor resultado». Continúa la decisión previa «Normas ahora,
herramientas aparte». No reabre aceptación de juego ni elecciones ya aprobadas.

## Pasos

1. **Contraste de cobertura** (sin dependencias): tres análisis acotados de escenarios,
   personajes y desarrollo/pruebas contra los cinco informes retrospectivos existentes.
   Entrega: casos→evidencia→regla actual→hueco→destino canónico en
   `_work/retro/standards-recheck/`. No releer todo el ledger de Gas-O.
2. **Integración documental** (depende de1): confirmar hallazgos contra fuentes;
   completar únicamente la regla en su autoridad existente y enlazar desde índices.
   Prioridad: checklist de escenario (cámara estática/animada, entorno por puntaje,
   render y audio), sin perder identidad/HUD, lifecycle, regional y aceptación.
   Fuentes previstas: pipeline, pruebas, stage/song, entradas alternativas,
   runbook/coding/Goldfish solo si un hueco real lo justifica; digests asociados.
3. **Cierre** (depende de2): checker dirigido y hashes de todos los documentos
   modificados, enlaces y triaje de una revisión fría cuando la lista Goldfish lo
   exija; registrar resultado en Gas-O y preservar pendientes de implementación.
   Checkpoint local de archivos propios y next_action actualizado.

## Comprobación

- Cada caso revisado termina como cubierto, regla detallada, excepción acotada o
  pendiente explícito; no afirmar exhaustividad de toda la historia por una búsqueda.
- `py -3.13 tools/workflow/audit_docs.py check --output <fresh-json>` y comprobación
  dirigida con `inspect_document`: cero issues en el cambio, sin llamar verde la
  auditoría global. SHA de digest contra bytes actuales; `git diff --check` con
  `core.whitespace=cr-at-eol` solo para preservar finales históricos.
- No sustituir datos nativos con valores Gas-O ni convertir un candidato/histórico
  en aceptación actual. Las skills remiten a fuentes canónicas; sin guías paralelas.

## Límites y decisiones

- Solo normas: no herramientas, código, assets, build, deploy, instalaciones,
  partidas o saves. Automatización y deuda de tests siguen tareas separadas.
- Reutilizar evidencia vigente y consultas MCP previas con mismo binario/contexto;
  una cuestión nueva que lo requiera usa una lectura acotada, no análisis masivo.
- Cualquier decisión nueva de fidelidad o aceptación que no esté autorizada se
  registra como pendiente, no se inventa ni se pide al worker que la decida.

## Progreso

| Paso | Estado |
|---|---|
| Contraste | Tres informes terminados; revisión primaria de rutas/digests/skills |
| Integración | Casos detallados en sus fuentes; preservados pendientes y alcance aprobado |
| Verificación/cierre | Checker dirigido sin issues; 32tests del checker pasan. Dos Goldfish con correcciones aplicadas; última comprobación y checkpoint en la nota Gas-O |

## Registro de ejecución

- Matrices: `_work/retro/standards-recheck/{stages,characters,workflow,primary}.md`;
  disposiciones de57casos solapados en `coverage-triage.json`. No cobertura de toda
  la historia ni aceptación del juego.
- Autoridades existentes ampliadas; no guía normativa paralela. Reglas de cámara
  por fase, eventos/recursos, ownership/identidad, audio e integración regional.
- Goldfish: `_work/goldfish/standards-coverage-recheck-20261115/`; restauración con
  conflictos, tooling host y DBI sin prohibición ciega corregidos. Enlaces de alcance
  de cámara y región precisados. Veredicto no es aprobación ni permiso de despliegue.
- Sin código, assets, build, deploy, partidas ni protocolo nuevos. Estado de
  implementación/deuda y pendientes Bloque5/Robo-Z se conservan para continuar.
