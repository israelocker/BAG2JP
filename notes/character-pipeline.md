---
id: character-pipeline-shared
title: "Pipeline compartido de personajes"
tags: ["character", "pipeline", "workflow"]
summary: "Reglas por evidencia y límites de los helpers; perfiles de datos, no pipelines clonados."
related: ["CHARACTER_IMPORT.md", "notes/character-alternate-entries.md", "notes/character-import-testing.md", "notes/strike-recovery.md"]
created: "2026-10-31"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: requirements
---

# Pipeline compartido

Estándar autorizado: mismo motor/orquestación; perfiles contienen IDs, paths,
capacidades y excepciones justificadas, no comandos ni forks del pipeline Heat.

## Gates

1. **Inventario:** disco/región/hashes, IDs reales, modelo, lista, esqueletos,
   miembros y lados/trajes. No asumir conteos/DBI de otro personaje.
2. **Contrato:** significado, beats, eventos requeridos y fuente/destino completos.
   Clasificar vacío/repetido/adaptado y mantener desconocidos sin resolver.
3. **Transiciones:** predecesores y continuidad nativa son chequeos distintos de
   igualdad de slots. Pose final parecida no prueba equivalencia musical.
4. **Candidato:** producir assets solo tras gates de perfil/contrato; no auto-deploy.
5. **Aceptación:** matriz por capacidades, cuatro lados/trajes, movimientos,
   audio, fever aplicable, canción y retorno con mods. Cache no es aceptación.

## Qué implementan realmente las herramientas

`tools/bag1import/character_workflow.py` expone `init-profile`, `validate-profile`,
`plan`, `prepare`, `status`, `acceptance-plan`, `cache-record`, `cache-check`, con
`--profile` requerido. Se contrastó el parser actual. Las recetas completas están
en CHARACTER_IMPORT, no duplicadas aquí.

`animation_policy.py` valida políticas; los remapeadores/auditor Heat y el
remapeador Strike contienen adaptación específica. No hay asignador semántico
universal ni optimizador de grafos aceptado con todos los personajes.
DFS/payload compartidos: [integración](character-alternate-entries.md), con sus
límites manuales. Harness: [pruebas](character-import-testing.md), catálogo limitado.

## Referencia cacheada

Reutilizar capturas solo con coincidencia de hashes de motions, perfil, catálogo,
runtime y evidencia. Revisar alcance de `cache-check`: un hit no cubre sonido ni
un paquete modificado. Captura nativa con ajustes/tarjetas aislados y proceso propio.
No competir con la GPU del juego; scripts para hashes/conteos antes que modelos.

## Estado respaldado, no promesas

Strike JP ID=1; integración y dos partidas completas P1/A y P2/B están en
[su ledger](strike-recovery.md), con fidelidad/matriz/fever pendientes.
Heat tiene adaptadores y evidencia histórica; no generalizar aceptación.
El [documento anterior](archive/character-pipeline-before-audit.md) conserva
decisiones y mediciones antiguas. Existencia de Context7 o Ghidra instalado no
demuestra conexión/servicio disponible en la sesión actual.
