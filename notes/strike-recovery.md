---
id: strike-import-recovery
title: "Strike: evidencia vigente y pendientes"
tags: ["strike", "bag1", "acceptance"]
summary: "Integrado con mods; cuatro combinaciones lado/traje completaron canción y retorno. Fidelidad, fever propio y aceptación visual pendientes."
related: ["notes/character-alternate-entries.md", "notes/character-import-testing.md", "notes/character-pipeline.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Estado vigente de Strike

## Identidad y contenido

- ID JP=1. Packs 73/74/145/146; modelos 109/110/181/182.
- Inventario: `_work/character_inventory/strike/bag2jp-native-entries.json` y
  `structure-comparison.json`. Enlaces de 44 huesos coincidentes; conservar DBI
  stock. El parche por analogía Heat fue rechazado, no desplegarlo.
- Spec usado: `_work/character_import/strike/containers_spec.json`. Es datos
  locales para ocho contenedores, no un motor nuevo ni profile universal.
- Payload combinado: once filas Heat preservadas + ocho Strike, 3889152 bytes,
  SHA-256 `f267f1bba4bdf8a6e71b7bc583dcf60b2f75bfb49587ee136f4e4c3dde85deec`.
- Exe probado: `d22b3e4e8d80bb0b1e3c7bf3170c97c45cbf2b2ff7c162fc0434d328f14f3ab4`.
- Manifest `disc_user` offset 458823680; hash esperado de originales reemplazados:
  `688d86e8703cb952ce7bdf212e26e2e87ac8e7bd1efa98f0e507b93dab0bebe3`.

## Evidencia del 2026-11-02

Runs bajo `_work/versus-runs/`, con `result.json`, logs y capturas:

| Run | Caso | Resultado automático |
|---|---|---|
| `20261102T102131125467Z-strike-bag1-full-a` | Strike BAG1 P1/A vs Heat BAG2 P2/A | Canción y retorno en 161,2 s desde gameplay |
| `20261102T112902135591Z-strike-p1-b` | Strike BAG1 P1/B vs Heat BAG2 P2/A | Canción y retorno en 161,0 s |
| `20261102T102625676713Z-strike-bag1-full-p2-b` | Heat BAG2 P1/A vs Strike BAG1 P2/B | Canción y retorno en 162,2 s |
| `20261102T113407353131Z-strike-p2-a` | Heat BAG2 P1/A vs Strike BAG1 P2/A | Canción y retorno en 163,4 s |

Todos los cuatro casos P1/P2 × A/B pasaron canción y retorno.
P2/B gameplay mostró posible artefacto del pecho; revisar capturas de los cuatro casos.
No aceptación visual final.
Escenario/canción usados: Heat BAG2; no acreditan contenido propio Strike BAG1.
Logs fever1/fever2 no prueban fidelidad de solo/dueto BAG1.

## Causas demostradas y descartes

- Fuentes viejas en build: la compilación no sincronizaba mods-src. Corregido
  con staging explícito; versión visible en log, exe nuevo por hash.
- Packs truncados: ajuste innecesario, porque el plugin escribe `alt_size`.
  Quitar truncado por sí solo **no** resolvió VS.
- Defecto determinante de VS: script ad-hoc escribía todos los offsets DFS
  iguales. `rebuild_dfs_members.py` usa longitud real y verifica lectura posterior;
  después el mismo candidato pasó a gameplay y completó canción/retorno.
- Heat recompuesto erróneamente desde stock: restaurado de payload aceptado
  `9629d66cc72d2f7f2329069f4be3da59a26265d4c86fa087d49a0f800bc8ecad`
  e índice `096533d`, no de las entradas BAG2 del disco.
- Regresión del test: exigir rechazo Strike BAG1 deshabilitó el candidato.
  Se restauró soporte y el rechazo no implementado se prueba con Comet BAG1.

Las recetas reutilizables están enlazadas arriba. No reutilizar scripts
ad-hoc `_work/versus-navigation/` como pipeline. El [registro anterior](archive/strike-recovery-before-audit.md)
conserva toda la secuencia e inventarios, sin autoridad sobre el estado actual.

## Falta para aceptar

Comparación nativa de UV/CLUT/traje B y animaciones, fever aplicable y audio
por escucha; capacidades adicionales según alcance. Las cuatro combinaciones
lado/traje ya completaron flujo completo, pero no se aceptan visualmente ni
certifican fidelidad BAG1.
Perfil/cache pueden contener estado anterior: contrastar evidencia, no subirlos
a verified para ocultar gaps. Código/payload previos siguen sin checkpoint final
de importación; los commits documentales no sustituyen su aceptación.
