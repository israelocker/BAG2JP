---
id: system-config
title: "Configuración: fuentes de verdad"
tags: ["config", "reference"]
summary: "Distingue configuración del título, plantilla y ajustes efectivos sin copiar defaults personales."
related: ["docs/paths.md", "notes/project.md", "notes/game-controls.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Configuración

## Configuración host: especificación aprobada, implementación pendiente

El owner eligió «Host primero» y aprobó diseñar configuración común/local,
cargador y diccionario de datos, y después aprobó la
[especificación escrita](docs/superpowers/specs/2026-11-15-host-configuration-design.md).
Los archivos operativos `config/project.toml`/`project.local.toml` y el cargador
**aún no existen**; las rutas actuales siguen en sus consumidores/documentación.
No confundir esta propuesta con settings vivos ni con datos nativos de perfiles.
Siguiente: revisión del [plan de base/piloto](plans/pending/host-configuration-foundation.md)
y elección de método antes de código. Primer lote: resolver/diccionario y checker
de manifiestos de lectura; workflow/harness/captura/perfiles siguen en roadmap, no
migrados por crear TOML. El script Bash instalado tiene root fijo y requiere su
lote explícito; no se da por configurable cambiando solo Python.
Omisión Goldfish de esta unidad documental: solo spec/plan y sistema de referencia, fuera
de la lista cerrada; auto-revisión de alcance, tipos/unidades, precedencia,
bootstrap, permisos y preservación de perfiles/CLI, no prueba de implementación.

## Fuentes vigentes

- `patches/BAG2JP-game.toml`: configuración reproducible del título, no todos los
  ajustes del usuario. Comparar con `game.toml` del árbol de build efectivo.
- `installer/settings.toml`: plantilla del instalador, no estado vivo del usuario.
- `settings.toml`, `keybinds.ini`, `mods/state.toml` de la instalación que se prueba:
  ajustes efectivos; guardarlos/restaurarlos byte a byte al probar.
- Ver `tools/test/versus_navigation.py` (`IsolatedFiles`) y
  `tools/test/versus_session.py` para aislamiento del harness local.

No copiar una configuración de ejemplo encima de tarjetas/opciones personales.
No asumir que un valor como `buffer_ms=90` sigue activo porque apareció en una nota.
Validar nombres/rangos contra el parser del framework fijado cuando se cambien.

La [copia anterior](docs/archive/system_config-before-audit.md) incluía una ruta
de sesión obsoleta y defaults particulares; queda solo como histórico.
