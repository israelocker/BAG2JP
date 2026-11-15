---
id: host-configuration-design-digest
title: "Diseño de configuración host: aprobado, sin implementar"
tags: ["digest", "design", "config"]
summary: "Especificación host aprobada; plan de base/piloto pendiente de revisión y método, sin loader/config/diccionario implementados."
related: ["system_config.md", "docs/superpowers/specs/2026-11-15-host-configuration-design.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "docs/superpowers/specs/2026-11-15-host-configuration-design.md"
source_sha256: "460dc5bf90e68fd7d5096a0be3f97529b6838b4dcc6f5c54f0a0e34b103277a3"
---

# Configuración host: diseño para revisar

- Owner eligió host primero y aprobó diseño y especificación escrita común/local +
  resolver + diccionario. Siguiente gate: plan base/piloto y método de ejecución.
- Proyecto común portable, archivo local no versionado para rutas de máquina y
  cargador único para Python/JSON-PowerShell; Windows convierte rutas al pasar a
  WSL. Bootstrap Python3.13 ya disponible, no instalación ni parser duplicado.
- Raíz desde módulo; rutas relativas de config desde repo, no CWD. Claves/tipos/
  esquema/precedencia explícitos; validar solo requisitos de la operación. Sin
  fallback a literales viejos ni interpolación/ejecución libre desde valores.
- Derivar layout estable desde raíces; no repetir cada concatenación. Diccionario
  detalla significado/tipo/unidad/procedencia/consumidores y política de cada clave.
- Native IDs/direcciones y datos por personaje/escenario siguen en contratos/
  perfiles. No nuevos esquemas de perfil por crear TOML: su migración es otro lote.
- Sin cambio de instalaciones, settings/saves, defaults funcionales, fixtures,
  permisos de partida/deploy o runtime. Config local no autoriza acciones ni
  demuestra seguridad si etiqueta mal un destino; conservar guards independientes.
- Lotes posteriores con tests host y equivalencia de rutas/CLI. Solo el consumidor
  migrado deja hardcodes; no afirmar migración global ni aceptar juego por tests.
- Los archivos operativos futuros aún no existen. Fuente y estado canónicos en
  `system_config.md`; normas y pendientes previos conservados.
