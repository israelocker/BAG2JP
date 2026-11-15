---
id: data-dictionary-digest
title: "Diccionario de configuración: uso y límites"
tags: ["digest", "config", "dictionary"]
summary: "44 campos: S1/S3a/S3b y 13 campos S4a-prep sin operación ni consumidor. Consultar tabla canónica antes de reutilizar claves; grabador todavía pendiente."
related: ["docs/data-dictionary.md", "system_config.md", "tools/workflow/project_config.py"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "docs/data-dictionary.md"
source_sha256: "29733a94a55880da5920f3509bcd345451019d36e922c4e5f18b1bf79f89a508"
---

# Diccionario: antes de consumir claves

- `FIELDS` define esquema; TOML común/local define valores; la tabla canónica
  describe los 44 campos y tests impiden divergencia de claves/tipos/unidades/
  origen/permisos/operaciones. Reutilizar por significado; no duplicar defaults.
- Política: build.jobs2 y pins no se pueden sobrescribir localmente; repo_root se
  deriva. Ubicaciones locales verificadas no se copian al común ni a consumidores.
- `payload-manifest`: raíces build/experimental para 4 copias; paquete explícito no
  necesita configuración. `workflow`: work_root/estable/build/experimental/script,
  pins/jobs/WSL; `workflow-report` añade Python, que en preflight es diagnóstico.
- `report`: experimental/work_root; `report-audio` añade probe si se busca un WAV
  real; `report-sheet` exige estable para la guarda antes de escribir capturas.
- Operaciones son requisitos, no permisos. Existencia/configuración no prueba
  disponibilidad ni buen funcionamiento de discos, herramientas o instalaciones.
- Native facts siguen en perfiles/contratos/notas. Ubicaciones equivalentes de
  perfiles aún no migrados conservan su lector/evidencia; divergencia se investiga,
  nunca se escoge silenciosamente una autoridad. S5 migra esos lectores por lotes.
- Estado base significa que el resolver valida, no que cada consumidor migró.
  Consumidores reales de S1 documentados; numéricos legacy y otras familias siguen
  pendientes. Consultar tabla completa al registrar una clave y ejecutar sus tests.
- Tipo `número`: finito y positivo; `harness.*` de presupuesto ≤ 86400 s con
  override local; hold/gap/fade son política exacta sin override. CLI explícito
   `--finish-timeout` ya prevalece sobre TOML en S3a. Batch Strike los alcanza
   vía resolve_settings/Session; no hay parser propio.
- S3b usa cinco claves existentes por view_config.py/export_config JSON. Operaciones
   endings-view/endings-acceptance: experimental/work/estable/helpers; dance-capture:
   work/estable y helpers condicionales a falta de overrides. ExpectedExe explícito
   se conserva. Padre/hijo fijan inputs/archivos/destinos; rutas literales, overrides
   relativos intactos y acceptance no reutiliza salidas/backups existentes.
- Guardas no race-safe; tiempos/estados/direcciones de vistas permanecen en fuente,
    no consumen la política versus. Configuración nunca es permiso de partida.
- S4a-prep: diez recording.* (host, positivos, segundos≤86400; fps entero≤240 y
  extra_seconds entero≤86400) y tres rutas opcionales de FFprobe/look/fuente.
  Sin operación activa ni consumo en bag2_record.py; no calibración/gates nativos.
