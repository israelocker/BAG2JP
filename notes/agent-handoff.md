---
id: agent-handoff
title: "BAG2JP Agent Handoff"
tags: ["handoff", "resume", "context"]
summary: "Guía para retomar el trabajo entre agentes. Orquesta la transición de contexto sin sustituir notas temáticas"
related: ["AGENTS.md", "NOTES.md", "CHARACTER_IMPORT.md", "IMPORT_STANDARD.md", "_work/current-state.json"]
created: "2026-10-31"
updated: "2026-11-01"
---

# BAG2JP — traspaso de contexto Claude → Codex → OpenCode (actualizado 2026-10-31)

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

### Qué se integró realmente del entorno de Codex

- **Skills y reglas:** `C:/Users/israe/.codex/skills` es un junction a los skills compartidos bajo `.agents/skills`; la configuración global de OpenCode también apunta a `~/.agents/skills` y a `~/.agents/AGENTS.md`. Hay 147 carpetas de skills compartidos; los siete skills BAG2JP/PSX citados arriba están presentes. `.opencode/opencode.json` registra además los cuatro skills específicos de `agent-skills/`. Consultar la skill pertinente, no cargar toda la colección ni aplicar los flujos genéricos de Git sobre el método local de este proyecto.
- **Hooks:** el plugin global de OpenCode `C:/Users/israe/.agents/plugins/agents-hooks/index.ts` ya implementa una adaptación del hook de Codex `C:/Users/israe/.codex/hooks/claude-migration/runner.py`: contexto inicial y recordatorio de revisión focalizada, más avisos sobre patrones de seguridad después de ediciones. No duplica el bloqueo de `Stop` ni el sonido de `PermissionRequest`; no confundir ese recordatorio con una revisión completada. La configuración global también carga `agents-failover` y `opencode-auto-fallback`, que son plugins propios del entorno OpenCode, no instrucciones del port BAG2JP. Este inventario confirma archivos/configuración, no una prueba exhaustiva de todos los eventos de hooks.
- **Conectores:** `desktop_commander`, `ghidra`, `local_llm`, `local_vibes`, `gitkraken`, `brightdata`, `sanity`, `audiopod` y `auth0` figuran en la configuración global de OpenCode. `context7` se añadió solo al proyecto en `.opencode/opencode.json`, conectó y respondió a una búsqueda pública de Capstone; usarlo para documentación externa, no para reemplazar el código local fijado. Codex tenía los mismos nombres MCP y además `node_repl`; no inferir que `node_repl` o los plugins nativos de documentos, PDF, presentaciones, navegador, visualización y computer-use hayan sido importados. Auth0 estaba desactivado en Codex por decisión del propietario: que figure en la configuración de OpenCode **no** autoriza conectar su cuenta ni usarlo. Confirmar la disponibilidad y autorización de cada herramienta en la sesión antes de depender de ella; los scripts `bag2_run.ps1` y `bag2_report.py` siguen siendo la ruta de prueba del juego.
- **Resultados de Codex:** `C:/Users/israe/Documents/Codex/2026-10-30/ho/outputs/` guarda el informe inicial, retrospectiva y pruebas visuales/audio de Heat. Las notas actuales de `notes/` y los commits posteriores prevalecen sobre el estado del 30 de octubre. La retrospectiva recomienda preflight breve por tarea, validar rutas/hashes antes de copiar, revisar cambios por versión sin repetir revisiones, y medir duración real sin prometer ahorros no medidos; esas prácticas ya están recogidas en `AGENTS.md` y `tools/workflow/bag2_workflow.py`. No importar conversaciones completas, secretos o caches del perfil Codex como instrucciones de proyecto.

## Límites actuales y seguridad de datos

- Git `main` tiene modificaciones previas del propietario en `installer/LEEME.txt`, `installer/bag2jp_online.nsi` e `installer/build.sh`, y `.opencode/` sin seguimiento. Preservarlas; un commit de documentación debe incluir únicamente archivos propios. El árbol de compilación tiene cambios/no rastreados independientes; no restaurarlo ni sobrescribirlo.
- La migración activa quedó reparada: los junctions `C:/Users/israe/.agents`, `.claude` y `.codex` apuntan a sus perfiles en D:. La configuración nueva de C: se reconcilió con el perfil completo anterior sin sustituir bases SQLite ni credenciales; el propietario comprobó sus conversaciones y configuración al reabrir Codex/ChatGPT. La carpeta real anterior `C:/Users/israe/.codex.repair-preserved-20261031-224549` y las copias protegidas en `D:/Dev/Tools/agent-data/migration/codex-repair-20261031-224549` siguen como material de recuperación; no borrarlas sin decisión separada. Ver el registro detallado en `D:/Dev/Tools/agent-data/migration/progress.md`.
- La app empaquetada de Claude necesita `AppData/Local/claude` como carpeta real en C: (~32 MB); el resto de sus datos migrados está en D:. Se verificaron los 13 ZIP históricos (CRC/miembros/tamaños y SHA-256 contra el manifiesto) bajo `D:/Dev/Tools/agent-data/backups/2026-10-31` y, con autorización del propietario, se borraron únicamente las 13 carpetas originales `*.pre-migration-*` de C:. Los ZIP no son el estado activo ni reconstruyen por sí solos junctions/hardlinks/ACLs de NTFS.
- Trabajar en el build experimental, conservar tarjetas/settings y sesiones activas; distinguir evidencia histórica de prueba fresca. El proyecto principal no tiene remoto: no publicar ni presumir respaldo Git externo.

## Mensaje para un chat nuevo

> Retoma BAG2JP en `D:/Dev/Recomp/BAG2JP`. Lee `AGENTS.md`, `NOTES.md`, `notes/agent-handoff.md` y solo las notas/skills específicas de la tarea. No rehagas el port base ni declares importado Strike. Revisa Git y conserva los perfiles/copies de recuperación al tocar datos de agentes. Para código, usa el árbol de compilación y la instalación experimental; valida en juego antes de dar por terminado un personaje.
