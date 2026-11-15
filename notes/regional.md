---
id: regional-content-launcher
title: "Contenido regional: configuración y evidencia"
tags: ["regional", "audio", "reference"]
summary: "Fuente del manifest y distinción entre defaults, opciones efectivas y aceptación visual/audio."
related: ["system_config.md", "notes/ui-mods.md", "notes/project.md"]
created: "2026-10-29"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Regional

Autoridad de opciones/defaults del paquete:
`mods-src/bag2jp.localization.regional/1.0.0/manifest.toml`.
Estado seleccionado: `mods/state.toml` de la instalación probada.
No convertir el default del paquete ni una captura antigua del launcher en
estado vivo. Confirmar compatibilidad de combinaciones/overlays antes de cambiar.

## Tres decisiones distintas, sin duplicar selectores

- Versión BAG1/BAG2: selección del personaje **por lado**; no es una región visual.
  El popup abre BAG2 por defecto según la decisión aprobada; verificar selección
  efectiva, disponibilidad y contenido cargado por el consumidor.
- Región visual global: `mods-src/bag2jp.content.bag1-visuals/1.0.0/manifest.toml`,
  feature `regional`, opciones independientes `models` y `stages`, ambas con
  default aprobado `japanese`. Se aplica en la siguiente carga de assets; no añade
  versiones de personajes ni crea región por jugador.
- Canciones: conservar `bag2jp.localization.regional` / `regional` / `songs`
  (`japanese`, `international`, `cd`). La región visual no elige música ni prueba
  que un FLAC sea del CD. No crear otro selector de canciones por importar BAG1.

Esta es la separación aprobada y contrastada con manifiestos fuente, no prueba de
opciones instaladas/activas. Registrar manifest/state/hashes de la prueba real.
Para ambas regiones comparar miembros; ausencia JP no es equivalencia USA, ni
fallback stock aceptación de una variante que falta. Ver el contrato regional de
[integración](character-alternate-entries.md).

Builders en `mods-src/bag2jp.localization.regional/tools/`. Las diferencias
JP/US de tablas, TIM y XA requieren inventario del disco real; no aplicar
offsets de una región a otra por nombre de archivo.

El [registro de investigación](archive/regional-before-audit.md) conserva
opciones, versiones de reconstrucción CD y pruebas de imagen/sonido. No se
reprodujeron todas durante la auditoría. «Se abre el FLAC y corre la partida»
no acredita fidelidad por oído ni todas las canciones. Conservar versiones
rechazadas como tales, sin publicarlas como el resultado preferido.
