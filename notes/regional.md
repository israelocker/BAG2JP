---
id: regional-content-launcher
title: "Contenido regional: configuración y evidencia"
tags: ["regional", "audio", "reference"]
summary: "Fuente del manifest y distinción entre defaults, opciones efectivas y aceptación visual/audio."
related: ["system_config.md", "notes/ui-mods.md", "notes/project.md"]
created: "2026-10-29"
updated: "2026-11-02"
edited: "2026-11-02"
doc_kind: reference
---

# Regional

Autoridad de opciones/defaults del paquete:
`mods-src/bag2jp.localization.regional/1.0.0/manifest.toml`.
Estado seleccionado: `mods/state.toml` de la instalación probada.
No convertir el default del paquete ni una captura antigua del launcher en
estado vivo. Confirmar compatibilidad de combinaciones/overlays antes de cambiar.

Builders en `mods-src/bag2jp.localization.regional/tools/`. Las diferencias
JP/US de tablas, TIM y XA requieren inventario del disco real; no aplicar
offsets de una región a otra por nombre de archivo.

El [registro de investigación](archive/regional-before-audit.md) conserva
opciones, versiones de reconstrucción CD y pruebas de imagen/sonido. No se
reprodujeron todas durante la auditoría. «Se abre el FLAC y corre la partida»
no acredita fidelidad por oído ni todas las canciones. Conservar versiones
rechazadas como tales, sin publicarlas como el resultado preferido.
