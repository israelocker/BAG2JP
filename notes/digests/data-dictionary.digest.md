---
id: data-dictionary-digest
title: "Diccionario de configuración: uso y límites"
tags: ["digest", "config", "dictionary"]
summary: "Resumen del diccionario de 31 campos y requisitos por operación; consultar tabla canónica al añadir/reutilizar claves. Consumidores S1 no implican migración de todos los defaults legacy."
related: ["docs/data-dictionary.md", "system_config.md", "tools/workflow/project_config.py"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "docs/data-dictionary.md"
source_sha256: "d40a1ef27106f36f6dcceb0d6b1962354332f276bc9936bfb88985d4b6bece3b"
---

# Diccionario: antes de consumir claves

- `FIELDS` define esquema; TOML común/local define valores; la tabla canónica
  describe los 31 campos y tests impiden divergencia de claves/tipos/unidades/
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
  `--finish-timeout` prevalecerá sobre TOML al migrar. Batch Strike los alcanza
  vía Session. Aún sin consumidor: registrar no elimina literales del runner.
