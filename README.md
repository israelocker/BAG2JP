---
id: readme
title: "BAG2JP"
tags: ["project", "index"]
summary: "Entrada al repositorio local; NOTES enruta a fuentes canónicas por tema."
related: ["AGENTS.md", "NOTES.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: index
---

# BAG2JP

Recompilación nativa a Windows de **Bust A Move 2 - Dance Tengoku Mix** (`SLPM-86219`, versión japonesa de *Bust A Groove 2*) usando **PSXRecomp**, junto con un ecosistema de mods, mejoras gráficas/audio y herramientas de ingeniería inversa e importación de contenido de *Bust A Groove 1*.

> **Índice de documentación:** Consulta [NOTES.md](NOTES.md) para navegar por las notas canónicas de cada tema. Los documentos en carpetas `archive/` son registros históricos, no instrucciones operativas actuales.

---

## 🎯 Contexto y objetivo del proyecto

El objetivo principal de **BAG2JP** es llevar *Bust A Move 2: Dance Tengoku Mix* a PC de forma nativa (sin emulador tradicional), manteniendo fidelidad de juego y ampliándolo con:

- **Mejoras técnicas y de calidad de vida:** soporte de audio HQ, texturas HD (`bag2jp.hd-texture-pack`), visor de finales (`bag2jp.feature.endings-view`), sincronización de red (`bag2jp.feature.netsync`), logs de rendimiento (`bag2jp.diagnostics.perf-log`), y localización regional.
- **Importación de contenido de BAG1:** pipeline compartido para traer personajes, movimientos y escenarios de *Bust A Groove 1* a *Bust A Groove 2* con validación por evidencia y grabación en juego (`bag2jp.feature.bag1-content`).
- **Flujo reproducible:** parches al runtime de PSXRecomp, scripts de automatización, pruebas de host y validación en partida grabada.

---

## 📂 Qué encontrarás en el repositorio

- `mods-src/` — Código fuente de cada mod (plugins en C, headers, `manifest.toml`, scripts de empaquetado).
- `patches/` — Parches locales aplicados al runtime de `PSXRecomp`.
- `tools/` — Herramientas de flujo de trabajo (`tools/workflow/bag2_workflow.py`), importación BAG1 (`tools/bag1import/`), visor de movimientos (`tools/move_viewer/`) y pruebas/grabación (`tools/test/`).
- `config/` — Configuración portable del host ([config/project.toml](config/project.toml)) y plantilla local ([config/project.local.example.toml](config/project.local.example.toml)).
- `ghidra-scripts/` — Scripts auxiliares para análisis en Ghidra.
- `installer/` — Scripts y configuración del instalador NSIS (`bag2jp_release.nsi`, `settings.toml`).
- `docs/`, `notes/`, `plans/` — Estándares de código, arquitectura, notas técnicas por tema y planes.
- `.agents/` y `agent-skills/` — Skills y reglas especializadas para trabajar con agentes de IA.

### Qué NO está en Git (y por qué)
- **Archivos del juego con copyright:** `SLPM_862.19`, ISOs originales y la carpeta `assets/` extraída del disco.
- **Carpetas locales/pesadas:** `_work/`, `releases/`, `ghidra/`, `*.tar.gz`, `mods-src/**/payload/`, `music_hq/`, `vs_hd/`, `replacements/` (se reconstruyen con las herramientas o se distribuyen aparte).
- **Configuración de tu PC:** `config/project.local.toml` y `.sentry-native/`.

---

## 🛠️ Requisitos previos

Para compilar y trabajar en el proyecto necesitarás:

1. **Git** y **Python 3.13** (o compatible con el entorno del proyecto).
2. **WSL (Ubuntu)** con **llvm-mingw** para compilar los binarios y plugins de Windows.
3. **PSXRecomp** (revisar el commit fijado en `config/project.toml` bajo `[pins]`).
4. **Copia propia del juego:** imagen/archivos de *Bust A Move 2: Dance Tengoku Mix* (`SLPM-86219`), y opcionalmente *Bust A Groove 1* si trabajas en importación BAG1.
5. **Herramientas opcionales según la tarea:**
   - **Ghidra** (para análisis e ingeniería inversa).
   - **FFmpeg** (para grabación y análisis de video/audio).
   - **NSIS (`makensis`)** (para generar el instalador).
   - **realesrgan-ncnn-vulkan** (para el pack de texturas HD).

---

## 🚀 Instalación y configuración paso a paso

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/israelocker/BAG2JP.git
   cd BAG2JP
   ```

2. **Crear tu configuración local:**
   Copia la plantilla [config/project.local.example.toml](config/project.local.example.toml) a `config/project.local.toml` (este archivo está en `.gitignore` y nunca se sube):
   ```powershell
   Copy-Item config/project.local.example.toml config/project.local.toml
   ```

3. **Editar `config/project.local.toml`:**
   Rellena únicamente las rutas reales de tu PC (instalación experimental del juego, raíz de compilación, rutas a tus ISOs/extracciones, Ghidra, FFmpeg, etc.).
   - Las rutas relativas en `config/project.toml` se resuelven automáticamente respecto a la raíz del repositorio.

4. **Verificar el entorno (`preflight`):**
   Ejecuta el chequeo previo del workflow para confirmar que Python, WSL y las rutas configuradas están listas:
   ```powershell
   py -3.13 tools/workflow/bag2_workflow.py preflight
   ```

5. **Compilar (`build`):**
   Usa el flujo de compilación del proyecto (por defecto con 2 trabajos en paralelo según `config/project.toml`):
   ```powershell
   py -3.13 tools/workflow/bag2_workflow.py build
   ```

---

## 🤖 Recomendaciones de uso con Agentes IA

Este repositorio está optimizado para trabajar asistido por agentes de IA (Antigravity, OpenCode, Claude Code, etc.):

- **Reglas del proyecto ([AGENTS.md](AGENTS.md)):** Define el método de trabajo, el orden de lectura inicial (`AGENTS.md` → `NOTES.md` → `_work/current-state.json`), el uso obligatorio de Ghidra vía MCP para análisis binario y los criterios de validación en juego.
- **Skills incluidas (`.agents/` y `agent-skills/`):** Contienen flujos especializados como `bag-character-pipeline`, `bag-animation-matching`, `bag-reference-cache`, `bag1-import` y `ffmpeg-skill`.
- **Consejos prácticos:**
  - Si retomas una tarea pendiente, basta con pedirle al agente *"continúa"* o *"sigue con lo pendiente"* para que lea `_work/current-state.json` y siga desde `active_task.next_action`.
  - Mantén `config/project.local.toml` actualizado: los scripts y los agentes lo usan para no hardcodear rutas de tu PC.
  - Consulta [ARCHITECTURE.md](ARCHITECTURE.md) y [docs/coding-standards.md](docs/coding-standards.md) antes de introducir cambios grandes en código o configuración.
