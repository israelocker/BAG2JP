---
id: data-dictionary-digest
title: "Diccionario de configuración: uso y límites"
tags: ["digest", "config", "dictionary"]
summary: "45 campos; workspace y extracción Gas-O reutilizan claves. Perfil conserva layout/región del anunciador; resto S5 pendiente, sin permisos de juego."
related: ["docs/data-dictionary.md", "system_config.md", "tools/workflow/project_config.py"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "docs/data-dictionary.md"
source_sha256: "ea6abb2887c039de2fea57dab3e47ef46b9bb76f34bdbfa47db9400d6c7894e0"
---

# Diccionario: antes de consumir claves

- `gaso-source-usa/jp`: cada lector exige solo su clave, y que la raíz sea un
  directorio existente (sin validar identidad por hash);
  el build exige también la región independiente del anunciador del perfil.
  Directorios/IDs/cues siguen en perfil; no fallback a su ubicación extraction.
  Solo lector migrado, no stock/motions/glyphs/salidas ni guardas del builder.

- `FIELDS` define esquema; TOML común/local define valores; la tabla canónica
  describe los 45 campos y tests impiden divergencia de claves/tipos/unidades/
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
  Consumidos por bag2_record.py/recording_config.py: recording-record, finalize y
  frames exigen solo su contrato. CLI y override WGC registrados por ejecución.
  Herramientas con archivo existente, salidas guardadas, fuente copiada con nombre
  fijo; no calibración/gates nativos. PATH del look.py externo sigue pendiente S7.
- S4b registra tools.ffmpeg_native para native-capture, sin default de máquina.
- Piloto character-workspace usa repo_root/work_root/stable_install: outputs
  plan/prepare/state bajo work/character-import, guardas y provenance. No migra
  perfiles, caches, init-profile ni generadores Gas-O/Heat. write_state directo
  exige que el llamador indique inputs protegidos ajenos a la configuración.
