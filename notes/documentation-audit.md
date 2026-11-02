---
id: documentation-audit
title: "Auditoría documental: evidencia y mantenimiento"
tags: ["documentation", "audit", "workflow"]
summary: "Auditoría ejecutada: procedimientos contrastados, histórico separado, fuentes únicas y checker probado; no revalida gameplay ni todas las afirmaciones históricas."
related: ["plans/archive/documentation-evidence-audit.md", "NOTES.md", "docs/coding-standards.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Auditoría documental

Plan aprobado y ejecutado el 2026-11-02. Alcance: Markdown propio del repositorio,
skills locales y mapa auxiliar NOTES.idx; sin cambiar juego ni preferencias.

## Alcance y decisiones

- Ruling: se conserva el Git local secuencial y el directorio canónico según
  AGENTS; no se crea rama/worktree por instrucciones genéricas. Coste si fuera
  incorrecto: menor aislamiento; staging explícito y snapshot preservan el task.
- Ruling: no se cambia código de importación para hacer cierta una nota. Las
  limitaciones del payload y aceptación de Strike siguen pendientes.
- Una comprobación documental verde acredita estructura, no verdad de todas
  las afirmaciones. Cada afirmación operacional necesita evidencia apropiada.
- El histórico se conserva separado; consolidación no equivale a borrar pruebas.

## Cobertura y resultado

Inventario inicial completo: 65 Markdown propios (63 versionados originales más
plan y ledger nuevos), incluyendo directorios propios ocultos. Se excluyen datos
generados, assets, submódulos/terceros y build. No se afirma auditar cada Markdown
de una instalación externa o snapshot binario.

| Grupo | Tratamiento y evidencia |
|---|---|
| AGENTS y tres skills de reglas | Revisados como política/requisito; AGENTS sin cambios |
| Raíz, docs, mantenimiento | Recetas/rutas contra helper y parsers; índices duplicados compactados |
| Perfil/cache/contratos | CLI contrastado; init schema1 y gates schema2/prepare documentados sin simular evidencia |
| Integración/Strike | Exe, manifest, capacidad real DUMMY y hashes por fila contrastados; runs conservados coinciden con runtime |
| UI/regional/online/Heat/stage/ending | Fuente de código identificada; pruebas antiguas separadas y no recertificadas como estado vivo |
| Clean/optimized y resúmenes antiguos | Originales íntegros en archive, redirects/único resumen vigente |
| Digests activos | Procedencia/hash explícitos, sin números de línea ni conteos antiguos como autoridad |
| Planes anteriores | Propuestas marcadas no ejecutables; no declaradas completas por existir parte del código |

Las 65 rutas iniciales quedan contabilizadas en `_work/docs-audit/coverage.json`.
La revisión independiente confirmó que las 40 copias archivadas conservan el
contenido original normalizando BOM/CRLF/espacios exteriores. Git conserva las
versiones exactas anteriores. No se eliminó información única para lograr reducción.

## Correcciones importantes

- Retirados ejemplos de API/configuración no contrastados de ARCHITECTURE y copia
  de settings personales/paths VM de system_config; fuentes vigentes enlazadas.
- Changelog ya no inventa SemVer/release global ni enlaza releases a Context7.
- Eliminadas de la ruta activa estimaciones sin prueba de 30–45 min, 60–90% y
  afirmaciones de que un generador de headings valida semántica/frescura por hash.
- No recomendar maintenance `--fix` ni generación `--all` por cada cambio de notas.
  La fecha mtime no demuestra fidelidad de un digest; `token-report` no es billing.
- BAG1 permitido para Heat/Strike en la documentación del harness; P2/B y `-Finish`
  no se ocultan detrás del estado anterior «solo Heat/A».
- Ending View ya no mezcla varios «latest exe» ni afirma todas las capacidades
  de ending solo por aparecer una opción de versión.
- Tablas/patches Heat no se presentan como mapas universales de personajes.

## Verificación realizada

- Checker: `py -3.13 tools/workflow/test_audit_docs.py`, 32 tests aprobados.
  Las tres observaciones de revisión se reprodujeron con tests RED antes del fix:
  hash/procedencia obligatorios de digest, enlaces relativos sin fallback errado
  y metadatos obligatorios no vacíos/arrays/fechas válidas.
- Host: `py -3.13 -m unittest discover -s tools/test -p 'test_*.py'`, 110 tests
  aprobados en esta auditoría. No equivale a nueva aceptación del juego.
- Cinco CLI contrastados con `--help` sin arrancar juego, logs en
  `_work/docs-audit/cli-evidence.json`.
- Contenido: payload 3889152 <= DUMMY 27648000 bytes; 19 IDs únicos, hashes de
  slices correctos y manifest/exe coherentes. Dos result.json Strike conservados
  coinciden con exe y declaran restauración/retorno, no aceptación visual.
  Registro: `_work/docs-audit/content-evidence.json`.
- Comprobación estructural actual e inventario en `_work/docs-audit/`; las
  advertencias del histórico se conservan visibles, no se silencian como «resueltas».

## Límites y mantenimiento

### Contexto medido con el mismo conjunto

| Conjunto | Antes (bytes UTF-8) | Después (bytes UTF-8) |
|---|---:|---:|
| AGENTS + NOTES + estado compacto | 12542 | 11800 |
| Los anteriores + IMPORT_STANDARD | 23267 | 14126 |

Reducción observada: 5,9% en inicio general y 39,3% en inicio de importación.
Incluye el nuevo puntero de auditoría en el estado compacto. No son tokens
facturados, ahorro de tiempo ni garantía de mejor rendimiento en cualquier tarea.
Baseline/final usan el mismo script/conjunto y registran archivos ausentes.
El almacenamiento total aumenta por conservar originales: el objetivo es reducir
la ruta activa de lectura, no fingir ahorro borrando evidencia.

El checker final no encontró errores activos/IDs duplicados/hash de digest obsoleto.
Conserva nueve advertencias en histórico (fence y rutas antiguas), deliberadamente
fuera de recetas actuales. No se editan originales para poner el informe a cero.

`audit_docs.py` usa la convención local de frontmatter (scalars y arrays en una
línea), no un parser YAML ni CommonMark completo. Comprueba archivos destino,
no todos los anchors/referencias Markdown ni opciones CLI dentro de cada ejemplo.
URLs y rutas externas no se conectan ni se ejecutan. Un check verde no certifica
verdad de todo el texto; los controles semánticos siguen siendo revisión humana.

Ruling: histórico no revalidado se preserva fuera de la ruta operativa, en vez de
inventar aceptación actual. Coste si un lector ignora el aviso: puede reutilizar
comandos antiguos; por eso cada tema activo enlaza la fuente/alcance correctos.
Ruling: las rutas antiguas se conservan como redirects cortos por compatibilidad,
no se borran sin comprobar consumidores. Coste: unos bytes adicionales de inventario,
sin obligar a leerlos en el contexto mínimo.

Ver `MAINTENANCE_GUIDE.md`. No corregir el guard de capacidad del empaquetador ni
los pendientes visuales de Strike dentro de este task documental. Fuera de scope:
framework global, nuevas dependencias, publicación/remote y tests online reales.

## Progreso

| Fase | Estado |
|---|---|
| Inventario | Completo; baseline reproducible en JSON |
| Checker | 32 tests verdes; revisión independiente y fixes completados |
| Contraste y consolidación | Completos con límites/histórico explícitos |
| Medición y conservación | Conjuntos antes/después registrados; checkpoint/snapshot en informe de cierre |
