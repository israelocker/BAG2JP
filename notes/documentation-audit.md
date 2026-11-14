---
id: documentation-audit
title: "Auditoría documental: evidencia y mantenimiento"
tags: ["documentation", "audit", "workflow"]
summary: "Auditoría ejecutada: procedimientos contrastados, histórico separado, fuentes únicas y checker probado; no revalida gameplay ni todas las afirmaciones históricas."
related: ["plans/archive/documentation-evidence-audit.md", "NOTES.md", "docs/coding-standards.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: reference
---

# Auditoría documental

## Auditoría de procesos reutilizables (2026-11-06)

Plan aprobado y cerrado: `plans/archive/reusable-import-process-audit.md`. Esta ampliación
contrasta fuentes y evidencia conservada; no ejecuta juego, conversiones sobre
assets activos, deploy ni escucha/aceptación visual nueva. Las secciones del
02-11 de abajo conservan el resultado de aquella revisión, no el estado actual.

### Cobertura y autoridades

Inventario con SHA-256 en `_work/process-audit/coverage.json`: 196 archivos
canónicos, 86 del build tree y 205 scripts locales de investigación. Es cobertura
de rutas/procesos, **no revisión semántica exhaustiva de cada línea** ni aprobación
para ejecutar los 205 scripts. Se excluyen terceros, código recompilado generado,
binarios como recetas y `_work` ajeno a los cinco ámbitos enumerados en el JSON.
Los medios se comprobaron por metadatos referenciados, sin abrir imágenes.

| Familia / proceso | Autoridad operativa y alcance comprobado |
|---|---|
| Inventario de disco y región | `CHARACTER_IMPORT.md`, `inspect_character_entries`, `iso_extract`; sectores útiles de 2048 B no sustituyen raw XA/STR |
| Modelo/esqueleto/escala | `CHARACTER_IMPORT.md`, `notes/character-pipeline.md`; conversión de cabecera, topología por traje y RAM 8 MB son problemas distintos |
| TIM/CLUT/atlas | Mismas notas; retarget preserva filas extra solo con ancho compatible; diagnóstico VRAM y contratos de copias DBI, no supresión global |
| Motions/roles/transiciones/fever | Pipeline y `notes/bag1-character.md`; adaptadores Heat/Strike, slots vacíos documentados, política no aceptada y dueto BAG2 explícitos; sin solver universal |
| DFS/payload/manifest | `notes/character-alternate-entries.md`; alineación 4 B, capacidad en bytes, hashes originales y preservación de filas compartidas |
| Efectos/DBI/proyección | `notes/strike-recovery.md`; disparo Strike con aceptación histórica concreta, Heat experimental; actor lighting rechazado, callbacks protegidos |
| Escenario/cámara/luces/selector | `notes/bag1-stage-song.md`; porter con perfiles Heat/Strike, lista de símbolos explícita, helper nativo y paquete experimental; no relocador universal |
| Canción/chart/XA/FLAC | Misma nota; JP frente a USA, duración lógica frente a WAV, sincronía/retorno y recursos por perfil; escucha pendiente |
| Voces/anunciador/SFX | `CHARACTER_IMPORT.md` y stage/song; rebase banco+eventos, anunciador stock, SFX bank0 nativo con banks1..3 stock; SPU no demuestra calidad perceptiva |
| Vídeo/baile/créditos/Ending View/campaña | `notes/endings-view.md`; plugin+recurso, extracción raw/transcode, pruebas host y media reales; campaña final no probada |
| Referencia/captura/fixtures/restauración | `notes/character-import-testing.md`, pipeline y `tools/bag1native/README.md`; scripts de entrada/RAM no son lectura pasiva ni sustituyen calibración |
| Build/staging/recuperación | `notes/project.md`, AGENTS y receta de integración; WSL dos jobs, staging manual, experimental únicamente, backups y restore verificado |
| Popup/previews/HQ/UI y localización | `notes/assets.md`, `notes/ui-mods.md` y scripts inventariados; auxiliares/experimentos o contenido regional, no prueba de HD corporal ni pipeline BAG1 general |
| Herramientas RE, mantenimiento y otros plugins | Inventariadas como soporte: disasm/funcmatch no aceptan comportamiento; netsync/autoplay/mods-menu no son conversores de personajes |

El build tree no es una copia intercambiable: 23 archivos sin hash canónico
equivalente; diferencias en `_work/process-audit/build-differences.diff` y lista
en `build-unmatched.txt`. Incluye herramientas antiguas, tests y manifests/build
plumbing. No se sincronizó ningún archivo ni se reparó el drift netsync ajeno.
El generador exacto canónico ya tiene capacidad en bytes por cambios previos;
el build no queda certificado y AGENTS mantiene el control independiente.

### Hallazgos y límites conservados

- Corregida la recomendación DFS sin alineación y la iluminación Strike ya
  descartada; conservados contratos y pruebas históricas, sin reactivarla.
- Separados sha del payload, bytes originales reemplazados y disco completo.
  `rebuild_animation_payload` aún presupone bytes originales cero: no usarlo
  saltando su rechazo sobre manifests corregidos/no cero.
- Stage y preserve_announcer no son exclusivamente Heat, pero los perfiles y
  adaptadores siguen acotados. `init-profile` schema1 no resuelve bootstrap schema2.
- El reporte de `build_stage_package` contiene una limitación fija de banco stock
  que no describe el caso `native_sfx_bank0=true`; fuente/bytes prevalecen.
- Cronologías y digests ya no presentan PIDs, prioridades o dos casos diagonales
  antiguos como estado actual. No se afirma aceptación global de Heat/Strike.

### Evidencia conservada contrastada, no partida nueva

`_work/process-audit/retained-evidence.json` conserva hashes/resultados de 18
directorios. Runs del 06-11: `000303289538Z`/`002321415753Z` canción Strike;
`004800028681Z`/`010056170156Z` selector/SFX; `012500289564Z` HeatB1 y
`012746447672Z` StrikeB2 regresiones. Resultados declaran restauración verificada,
pero varios siguen `awaiting_visual_review`.

Media Ending View: prefijo `20261106T` + `014236347408Z` StrikeB1/A,
`014508143093Z` B, `014745480316Z` StrikeB2/A y `015016909315Z` HeatB1/A;
runtime `2519854b5c6f65b14c24d0493418e8b71615888cd83be0ad49bfa3c871da4bb4`.
Resultados observados pendientes de revisión y restauración verificada; no campaña.
Salida natural A anterior: `20261105T204502725335Z`, `204954184810Z`,
`205447147749Z`; no extrapolar a salida B.

Los directorios de ataque `20261105T062700041177Z` Strike y
`20261105T143352068565Z` Heat no contienen `result.json`; sus capturas/ledger
no se convierten en un resultado automatizado inexistente. El full-match Strike
`20261105T063254774562Z` declara retorno, pero no el campo
`restoration.verified`; ausencia del campo no demuestra ni éxito ni fallo de restore.
El run Heat `20261105T143617747233Z` sí declara restauración; sigue pendiente de
revisión visual. Nunca reutilizar PIDs históricos sin comprobar la sesión actual.

### Comprobaciones de esta ampliación

- Host discovery: **155 tests**, exit 0; `_work/process-audit/host-tests.log`.
  Subprocesos/side effects inspeccionados antes de ejecutar: fixtures en `_work`
  o temporales y lectura de assets; no arranque ni escritura en instalación.
- Ending View C: **9/9 casos**, exit 0, mediante el script WSL independiente
  `tools/test/test_endings_view.py` (no forma parte del discovery unittest).
- Checker documental: **113 documentos, 0 errores, 9 warnings históricos**, exit 0;
  `docs-check.json`. Regresión del checker: **32 tests**, exit 0. Digests
  contrastados por SHA-256 sin discrepancias. Revisión de whitespace con
  `git -c core.whitespace=cr-at-eol diff --check` sin errores; se preservan los
  finales de línea de los archivos previamente editados.
- Ghidra: la primera comprobación falló porque estaba cerrado. Tras la indicación
  del propietario, el agente abrió la instalación y el proyecto existentes y abrió
  `SLPM_862.19` en CodeBrowser; **MCP validado** con `get_program_info` y lectura
  `decompile_function_by_address` de `start` en `0x80035d98` (sin truncamiento).
  Binario PSX little-endian, base `0x80000000`, SHA-256
  `ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe`.
  La lectura incluye warnings del decompilador en el terminador; es una prueba
  de conexión/lectura, no aceptación del juego ni análisis nuevo de overlays.
  Sin instalaciones ni cambios de configuración. Regla permanente de verificar,
  abrir si está cerrado y usar MCP en `AGENTS.md`; evidencia en
  `_work/process-audit/ghidra-status.json`.
- Checkpoint acotado a documentos sin cambios previos. El pipeline y tres digests
  que ya tenían trabajo del propietario no se incluyen en ese commit; sus versiones
  de trabajo se conservan además con hashes en
  `_work/process-audit/preserved-working-documents/`. Plan cerrado en
  `plans/archive/reusable-import-process-audit.md`. Sin build ni despliegue;
  este cierre documental no constituye un nuevo milestone del runtime.

## Herramientas comunitarias investigadas (2026-11-06)

Por petición del propietario, `AGENTS.md` y `notes/character-pipeline.md` requieren
usar `funcmatch.py` cuando corresponda, con advertencia explícita de validación
incompleta. Es búsqueda por bytes enmascarados, no equivalencia semántica ni
matching de overlays; confirmar en Ghidra. No se declara una nueva prueba del helper.

Investigación online y fuentes:
`_work/ps1-tools-research/reports/ps1_import_tools.md`, con notas de respaldo en
`_work/ps1-tools-research/research_notes/ps1_import_tools/`. Priorizar evaluación
de jPSXdec para XA/STR, inspección de firmas PsyQ existentes y dumpsxiso como
contraste raw; TIMedit, spimdisasm/m2c y asm-differ solo ante una necesidad concreta.
Se distingue capacidad upstream, uso comunitario y recomendación explícita.
No se instaló ni ejecutó ningún candidato; no hay ahorro medido ni compatibilidad
BAG demostrada. Emuladores diagnósticos requieren aprobación separada y no
sustituyen la referencia nativa. No se encontró evidencia suficiente para recomendar
instalar una skill PS1 de terceros. Próximo paso opcional: acordar un ensayo
acotado sobre copias antes de adoptar herramientas nuevas.

## Auditoría anterior (2026-11-02)

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

Medición del cierre de auditoría `646663d`, anterior al ajuste posterior de AGENTS.
No extrapolar estas cifras a versiones futuras del contexto.

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

## Ajuste de política aprobado después de la auditoría

El propietario aprobó aplicar en AGENTS el ciclo objetivo → evidencia → cambio
mínimo → verificación → checkpoint. Se consolidaron instrucciones repetidas y
se distinguieron planes amplios de correcciones pequeñas ya autorizadas, tests
documentales/host de aceptación del juego y WIP de trabajo aceptado. Los snapshots
se generan al cerrar hitos verificados, no tras cada commit/edición de Markdown;
los assets fuera de Git siguen necesitando backup propio. No cambian las
protecciones de saves, estable, GPU, pins o workflow Git local.

Staging sigue manual y el control de capacidad DUMMY requiere comprobación
independiente: esta política no implementa las dos mejoras de tooling pendientes.

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
