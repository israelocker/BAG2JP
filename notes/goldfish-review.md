---
id: goldfish-review
title: "Revisión Goldfish: crítica en frío antes de cerrar un cambio"
tags: ["workflow", "review", "evidence", "process"]
summary: "Procedimiento acotado para lanzar revisores sin contexto (efecto Goldfish): lista cerrada de rutas que lo disparan, registro durable en la nota del tema y veredicto que no es aprobación."
related: ["AGENTS.md", "notes/character-pipeline.md", "notes/gaso-import.md", "_work/current-state.json"]
created: "2026-11-10"
updated: "2026-11-15"
doc_kind: process
---

# Revisión Goldfish

Procedimiento propio de BAG2JP, pedido por el propietario el 2026-11-10
("que siempre aplique el goldfish si es que mejora el resultado"). No instala el
plugin Elephant-Goldfish Model ni importa su proceso de ramas/PR: solo reutiliza
la idea de **revisar en frío**, con cero historial de la sesión, antes de cerrar
un cambio.

## Qué es y qué no es

- **Es** una crítica previa al cierre: uno o varios subagentes nuevos que leen
  únicamente un spec corto y los archivos crudos indicados, sin el historial de
  la conversación.
- **No es una aprobación.** El veredicto es una hipótesis: cada hallazgo se
  comprueba contra el código, la evidencia o una ejecución real antes de
  aceptarlo. La aceptación sigue siendo del propietario y de la costura real
  (partida, Ghidra, tests).
- **No sustituye** la verificación en la costura, ni autoriza cambiar el
  criterio de aceptación (eso requiere aprobación del propietario, como cualquier
  decisión consecuente), ni crea un proceso de ramas/rebase/push/PR.

## Cuándo se aplica (lista cerrada)

Se aplica si y solo si `git diff --name-only` del cambio incluye al menos una de
estas rutas:

- `tools/**` (código ejecutable; los `.md` de `tools/` no cuentan)
- `mods-src/**`
- `patches/**`
- el generador de payload, un payload o su manifiesto, identificados por su función
  en el paquete y sus rutas declaradas, no solo por contener `payload`/`manifest`
  en el nombre
- `AGENTS.md`, `IMPORT_STANDARD.md`, `docs/coding-standards.md`

No se aplica si el diff completo cae en `notes/**`, `docs/**` (salvo las tres
rutas anteriores), `_work/**`, o si es solo typo, enlace o recuento.
Esa exclusión se refiere a documentación/evidencia: un payload o manifiesto real
no deja de activar revisión por estar en `_work/` o tener otro nombre. Un texto
que solo menciona un payload no es por ello un manifiesto.

Reglas adicionales:

- **Máximo una revisión por checkpoint.** Mismo diff sin cambios no se repite.
- Si no se aplica, se anota la omisión y su razón en la nota del tema, igual que
  se registra una herramienta bloqueada. Silenciar la omisión no vale.
- Conservar spec, respuestas y hashes/copia exacta de todos los archivos revisados,
  incluidas skills externas al repo si están en alcance. Un diff sin sus entradas
  no identifica lo que leyó el revisor. Documentar las correcciones posteriores.
- Una respuesta cortada por cuota o sin material es `REVISIÓN NO UTILIZABLE`,
  nunca «sin hallazgos». Si no quedan revisores, aplicar la omisión de abajo.
- Ante un cambio mixto (una ruta de la lista y otra fuera), se aplica y el spec
  declara qué queda fuera de revisión.

## Procedimiento

1. **Spec corto y autocontenido** en `_work/goldfish/spec-<tema>.md`: máximo una
   página con objetivo, alcance exacto, fuera de alcance, criterios numerados,
   evidencia disponible y 3-5 preguntas concretas. Nada de "revisa esto".
2. **Revisores en frío**: 2 o 3 subagentes `general` en paralelo, con el spec y
   la lista cerrada de archivos permitidos. Prompt explícito: solo lectura, sin
   escritura en Git, sin asumir historial, responder con problemas concretos,
   respuestas a las preguntas y veredicto.
3. **Triaje**: cada hallazgo se clasifica como confirmado, refutado o no
   verificable. Los confirmados se corrigen; los refutados se registran con la
   razón; los no verificables se declaran como límite, no se maquillan.
4. **Re-verificación**: lo corregido se comprueba en la misma costura que el
   cambio (test, ejecución, captura). Un hallazgo "confirmado" leyendo archivos
   no basta para cerrar.
5. **Registro durable**: bloque corto en la **nota canónica del tema**
   (versionada): fecha, commit o hash del estado revisado, número de revisores,
   veredicto, hallazgos aplicados y refutados. `_work/goldfish/<tema>-verdict.json`
   es solo evidencia cruda, no el registro. `NOTES.md` sigue siendo índice.
6. **Cierre**: si un hallazgo cambia el criterio de aceptación, no se aplica: se
   eleva al propietario y se espera su decisión. No se relanza todo por inercia.

## Veredicto (etiquetas no aprobatorias)

- `SIN HALLAZGOS BLOQUEANTES`
- `CON HALLAZGOS` (con lista; el decisor de aplicarlos es el agente del cambio)
- `REVISIÓN NO UTILIZABLE` (revisor sin material, respuestas vacías o fuera de
  alcance; se registra y no se cuenta como revisión)

Toda respuesta de revisor y todo registro debe llevar la línea fija:
`Veredicto de revisor: no es aprobación del propietario ni permiso de despliegue.`

Un hallazgo confirmado **no** bloquea ni autoriza por sí solo: decide el agente
del cambio qué aplica, y el propietario sigue siendo el único que acepta el
resultado. El despliegue mantiene sus propias reglas.

## Si no hay subagentes disponibles

Se registra la omisión con la razón y se sustituye por una auto-revisión
declarada como tal, nunca presentada como Goldfish. No se inventa un revisor.

## Límites conocidos

- El lanzamiento es manual: ningún comando garantiza que se ejecute.
- Un revisor sin contexto también se equivoca por falta de contexto; de ahí la
  re-verificación obligatoria.
- No mide tokens ni ahorro; no se declara "más rápido" sin medición.
- Los fixtures en `_work/` no están versionados: los tests que los leen son
  irreproducibles en otro checkout (límite del repositorio, no de la revisión).

## Caso de ejemplo: checkpoint del candidato V2 (2026-11-10)

Spec `_work/goldfish/spec-checkpoint-v2.md`, 3 revisores en frío, veredicto
`CON HALLAZGOS`. Hallazgos aplicados y cómo se comprobó cada uno:

1. El criterio de test del spec era falso: `tools/test/test_stage_port.py:17`
   define `load_tests`, que pytest ignora, y el runner WSL está en `:22-26`.
   *Verificado leyendo el archivo.* Runner real:
   `wsl -d Ubuntu --exec python3 -m unittest tools.test.test_stage_port tools.test.test_stage_geometry`.
2. `stage_geometry.py` importa `model_bag1_to_bag2`; se incluyó en el alcance.
   *Verificado con `git show --stat ae6a004` (8 archivos, incluido ese).*
3. Los tests leen fixtures de `_work/` (`test_stage_port.py:36,37,76,93,94`), no
   versionado: irreproducible en otro checkout. *Verificado leyendo el archivo;
   límite aceptado y declarado.*
4. Tests tautológicos que repiten constantes de la implementación. *Verificado
   leyendo `tools/test/test_stage_geometry.py`; queda como deuda, no se corrigió.*
5. Riesgo real: `git add -A` accidental más que `reset --hard`. Se usaron
   pathspecs explícitos y snapshot previo del árbol sucio. *Aplicado; snapshot en
   `_work/goldfish/pre-commit-dirty.patch`.*
6. Evidencia con afirmaciones desactualizadas (aceptación "pendiente" cuando ya
   estaba aceptada; recuento de frames). *Corregido en
   `_work/gaso/defect-a-v2-review.json` con `owner_acceptance` y `review_limits`.*

Resultado: commit `ae6a004`, 15 tests OK con el runner real (ejecutado, sin log
retenido), 80 entradas sucias ajenas intactas tras el commit, sin push y sin
tocar `BAG2JP-win`. El registro de este caso se añadió después en
`notes/gaso-import.md`; antes de esta corrección la nota exigía un
`-verdict.json` que no existía, y por eso el registro pasó a la nota del tema.
