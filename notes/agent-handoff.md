# BAG2JP — traspaso de contexto Claude → Codex → OpenCode (2026-10-31)

## Cómo retomar el trabajo

Repositorio canónico: `D:/Dev/Recomp/BAG2JP`. Leer primero `AGENTS.md` y `NOTES.md`; abrir únicamente la nota temática de la tarea. Este archivo orienta a un agente nuevo, **no sustituye** `notes/bag1-character.md`, `notes/bag1-stage-song.md` ni `notes/character-pipeline.md`. El informe anterior `C:/Users/israe/Documents/Codex/2026-10-30/ho/outputs/bag2jp-project-handoff.md` recoge la transferencia inicial de Claude a Codex; sus afirmaciones del 30 de octubre deben contrastarse con las notas y commits del 31.

La secuencia real fue: Claude inició el port, Codex continuó al agotarse los tokens de Claude y registró el método y sus hallazgos en este repositorio. OpenCode retoma ese proyecto ahora; **no** hay que presuponer una orquestación simultánea entre Claude y Codex, ni reconstruir el proyecto desde los ZIP del perfil.

## Estado técnico comprobado

- El port nativo de `Bust A Move 2: Dance Tengoku Mix (Japan)` (SLPM-86219) ya existe mediante PSXRecomp; no es una reescritura desde cero. El trabajo actual amplía contenido de Bust A Groove 1 dentro del runtime BAG2JP.
- **Heat** es el port BAG1 con modelo, vestuario, movimientos, voces, escenario, canción 2Bad, selección de versión y pruebas de juego documentadas. El commit `6820b84` registra aceptación **local** de guard/reflect con entradas reales; no equivale a una prueba online remota. Las tres transiciones no adyacentes de la cuadrícula se aplazaron por decisión del propietario (`5b566b5`). Ver `notes/bag1-character.md` (final), `notes/bag1-stage-song.md` y los hashes/evidencias allí citados.
- **Strike** tiene perfil e inventario de 84 animaciones validado, pero `target_character_id` sigue `null` y su etapa es `inventory`. No está importado ni probado en juego. `tools/bag1import/profiles/heat.json` tampoco cambia de etapa automáticamente por existir un port anterior de Heat.
- El flujo compartido `tools/bag1import/character_workflow.py` valida perfiles, catálogos y caché de referencias. `animation_policy.py`, `alternate_payload.py` y `rebuild_animation_payload.py` aportan políticas y repack reutilizables; los auditores y recetas de Heat conservan adaptadores específicos. Un asignador semántico/optimizador general para personajes nuevos **no** está implementado ni validado entre personajes. No copiar el pipeline de Heat para Strike.
- Antes de declarar un nuevo personaje listo: inventario y contratos semánticos, animaciones y transiciones nativas, eventos/sonidos, cobertura, paquete, prueba visual y recorrido completo de juego (canción, fever aplicable, regreso a selección). Un cache hit no prueba gameplay.

## Árboles, método y herramientas

| Uso | Ruta / regla |
| --- | --- |
| Registro durable | `D:/Dev/Recomp/BAG2JP`: `NOTES.md`, `notes/`, `mods-src/`, `patches/`, `tools/`; Git local sin remoto propio. |
| Árbol de compilación | `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP`; los plugins C se compilan en su `src/`, con copias conservadas en `mods-src/` del proyecto canónico. |
| Entorno y comandos | `C:/Users/israe/.agents/skills/project-config/bag2jp.md`; helper `tools/workflow/bag2_workflow.py preflight/build/test-stage-select/report --tag <tag>`, Python `D:/Dev/Tools/ghidra-mcp-python/python.exe`, WSL Ubuntu + llvm-mingw fijado y `-j 2`. |
| Pruebas | `D:/Dev/Tools/winshot/bag2_run.ps1` y `tools/test/bag2_report.py`; instalación experimental `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`. No tocar la estable `BAG2JP-win` sin pedirlo. |
| RE/audio | Ghidra 12.1.4 en `D:/Dev/Tools/ghidra_12.1.4_PUBLIC`, proyecto Ghidra del juego, Capstone, `D:/Dev/Tools/audio-probe`, FFmpeg/ffprobe y scripts `tools/bag1import/`. Confirmar programa abierto antes de usar Ghidra MCP. |
| Skills compartidos | `D:/Dev/Tools/agent-data/shared/agents/skills`: `bag1-import`, `bag-character-pipeline`, `bag-animation-matching`, `bag-reference-cache`, `bag2jp-build-deploy-test`, `psx-game-reverse-engineering`, `psx-recomp-disc-mod`. Copias específicas del proyecto en `agent-skills/` y registro `.opencode/opencode.json`. |

Codex conservaba plugins nativos de documentos, navegador, visualización y computer-use, y hooks `SessionStart`, `PostToolUse`, `PermissionRequest`, `Stop`; **no** pasan a ser plugins/hooks de OpenCode por copiar un perfil. Este OpenCode configura MCP para desktop_commander, ghidra, local_llm, local_vibes, gitkraken, brightdata, sanity, audiopod y auth0 (este último estaba desactivado en Codex). Confirmar disponibilidad de cada herramienta en la sesión concreta antes de depender de ella; usar scripts locales de prueba cuando no haya control gráfico nativo. Los skills compartidos sí son legibles desde D:, no hace falta extraer los ZIP para usarlos. Evitar leer o mostrar valores de credenciales al inspeccionar configuraciones.

## Límites actuales y seguridad de datos

- Git `main` tiene modificaciones previas del propietario en `installer/LEEME.txt`, `installer/bag2jp_online.nsi` e `installer/build.sh`, y `.opencode/` sin seguimiento. Preservarlas; un commit de documentación debe incluir únicamente archivos propios. El árbol de compilación tiene cambios/no rastreados independientes; no restaurarlo ni sobrescribirlo.
- Tras una limpieza de perfiles errónea, se restauraron los junctions `C:/Users/israe/.agents` y `.claude` hacia D:. `C:/Users/israe/.codex` se recreó como carpeta real mientras Codex/ChatGPT estaban activos y contiene cambios nuevos (incluida una configuración diferente); su destino migrado `D:/Dev/Tools/agent-data/codex/profile` sigue presente. **No borrar, sobrescribir ni sustituir la carpeta activa de Codex** hasta cerrar la aplicación y reconciliar los cambios de C: con D:. Ver `D:/Dev/Tools/agent-data/migration/progress.md` para la incidencia.
- La app empaquetada de Claude necesita `AppData/Local/claude` como carpeta real en C: (~32 MB); el resto de sus datos migrados está en D:. Los 13 ZIP históricos y el manifiesto están bajo `D:/Dev/Tools/agent-data/backups/2026-10-31`, pero no son el estado activo ni validan por sí solos una reversión NTFS. Los originales `*.pre-migration-*` seguían presentes en la última inspección; no repetir limpiezas basadas en recuentos incompletos.
- Trabajar en el build experimental, conservar tarjetas/settings y sesiones activas; distinguir evidencia histórica de prueba fresca. El proyecto principal no tiene remoto: no publicar ni presumir respaldo Git externo.

## Mensaje para un chat nuevo

> Retoma BAG2JP en `D:/Dev/Recomp/BAG2JP`. Lee `AGENTS.md`, `NOTES.md`, `notes/agent-handoff.md` y solo las notas/skills específicas de la tarea. No rehagas el port base ni declares importado Strike. Revisa Git y la advertencia sobre `.codex` de C: antes de tocar perfiles. Para código, usa el árbol de compilación y la instalación experimental; valida en juego antes de dar por terminado un personaje.
