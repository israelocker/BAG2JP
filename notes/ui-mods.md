---
id: ui-hd-fonts-mods
title: "UI/mods: fuentes y experimentos"
tags: ["ui", "mods", "reference"]
summary: "Separa implementación del menú, pruebas históricas y pack visual rechazado sin asumir estado instalado."
related: ["notes/game-controls.md", "notes/regional.md", "notes/endings-view.md"]
created: "2026-10-27"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# UI y mods

Fuente del menú: `mods-src/bag2jp.feature.mods-menu/bag2jp_mods_menu.c`.
Endings tiene [fuente propia](endings-view.md); opciones regionales en
[regional](regional.md). No inferir controles reales de comentarios: consultar
`keybinds.ini`, settings y logs de la instalación. Para harness aislado ver
[controles](game-controls.md).

[Registro técnico anterior](archive/ui-mods-before-audit.md): tablas glyph,
patch sites, edición de teclas y aceptación visual fechada. No equivale a una
nueva ejecución del código actual. El pack UI ESRGAN fue apartado por criterio
del propietario; no reactivarlo porque exista en disco o tenga validación numérica.
Similitud RGB no reemplaza juicio visual ni escucha para audio.
