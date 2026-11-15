---
id: system-config-digest
title: "Configuración host: autoridades y estado"
tags: ["digest", "config", "migration"]
summary: "S5a parcial: workspace cerrado y lector de extracción Gas-O cerrado en host; restantes rutas Gas-O/Heat y perfiles/caches pendientes. Sin juego."
related: ["system_config.md", "docs/data-dictionary.md", "plans/pending/host-configuration-migration.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "system_config.md"
source_sha256: "5d0d4eee65874dbd689787cac768034144711d329893bfb35a8638447630c284"
---

# Configuración: estado mínimo

- Autoridad: resolutor único `tools/workflow/project_config.py`, TOML común con
  defaults/política, local ignorado para ubicaciones verificadas, diccionario con
  significado/tipo/unidad/origen/validación/permisos/operaciones/consumidores.
- Base/piloto: `7fefc07` y `28fc1e9`; checker de manifiestos configurado, 4 copias.
- S1 (`46d528c`): workflow/report migran rutas/pins/WSL y contrastan jobs. Usan work_root y
  guardas de escritura para logs, sheets y destino build. Overlay absoluto al child,
  valores/orígenes/hashes en métricas; Python/probe opcionales según operación real.
- Bash instalado sigue fijo. Adaptador estricto de seis líneas, paths literales,
  árbol/jobs comprobados antes de lanzar build; no se ha modificado ni ejecutado.
- Verificación: 101 pruebas dirigidas, 103 workflow discovery, 8 mutantes en copias;
  ruta real workflow→report con logs existentes. No nueva evidencia de partida.
- Goldfish S1 encontró build sin guarda, sintaxis Bash no literal y carrera del WAV;
  corregidos RED→GREEN y tests antes enmascarados corregidos. Source tiene hashes,
  consultas y evidencias. Veredicto no es permiso de despliegue ni aceptación humana.
- 471 archivos versionados inventariados automáticamente, con hashes/procedencia.
  No equivalen a análisis semántico ni ausencia de hardcodes. S2 y demás familias
  pendientes; plan ampliado aprobado. Defaults numéricos legacy siguen candidatos.
- S2a familia harness: runner, tres lectores y tres tests leídos; disposiciones por
  hash en `plans/pending/host-configuration-harness-audit.json`; nav parcial, global
  471 pendiente. No retirar globals rompiendo lectores; discovery legacy conservado.
- Preparación S3: siete `harness.*` (deadlines 25/35/40/420 s, tope 86400;
  hold/gap/fade 100 ms/350 ms/1.3 s observados y bloqueados, sin override local).
   Consumidos por S3a (`e9236e7`): settings por ejecución, fixtures de solo lectura,
   batch sin Popen global, CLI explícita prevalece. 108 harness + 113 workflow OK,
   31 mutantes listados; snapshots Goldfish originales no retenidos exactamente.
- S3b: endings/view/acceptance y Dance View usan JSON del resolver; work/estable
   guardados, helpers explícitos prevalecen y falta parcial exige winshot_root.
   Dance conserva ExpectedExe nativo; padre/hijo fijan destino/archivos/overlay/hashes.
   Rutas literales, overrides relativos intactos y salida acceptance nueva.
   Goldfish A/B CON HALLAZGOS, corregidos sin segunda revisión; pruebas y mutantes
   posteriores: 19 vistas + 113 workflow + 108 harness OK, 24 mutantes en copias.
   Snapshot original y respuestas preservados; siguiente S4a grabador (solo host).
   Sin partida/build/deploy ni edición de herramientas instaladas.
- S4a-prep `1058670` registró diez defaults recording y tres rutas; no migró consumidor.
- S4a consumidor usa settings inmutables, CLI/entorno con provenance y operaciones
  condicionales. Work/recordings/artefactos guardados, font basename fijo; gates,
  PID/HWND/audio/clocks/codecs/cierre conservados. 73 recording + 119 workflow +
  108 harness OK (reutilización por hash explícita), 28 mutantes; Goldfish en fuente.
  Dependencias PATH de look.py instalado pendientes S7; no partida/captura autorizada.
- Nuevo/modificado host sigue el estándar central; runtime, hechos PSX y guards
  conservan su autoridad. No tocar historia, releases, settings, saves o terceros.
- Límites: config no demuestra identidad de estable; TOCTOU no garantizado,
  POSIX no probado, locals alternativos no ignorados automáticamente.
- S4a `1ed6f81` y S4b nativo `18d0c51` son checkpoints históricos; inventario
  bag1native `b60449f`. No equivalen a migrar todos los lectores de referencia.
- Gas-O extracción: inputs.bag1_usa_extraction/jp_extraction sustituyen ubicación
  del perfil; perfil conserva directorios y región independiente del anunciador.
  Un config/perfil por build y raíz existente antes de mkdir; v8: 12 lectores
  +120 workflow +7 HUD sin reutilizar logs, 17 mutantes; Goldfish corregido sin
  segunda revisión (detalle en fuente). Stock/motions/
  glyphs/perfil/salida y guardas del builder aún pendientes; no hubo paquetes.
- Piloto S5a: character_workflow plan/prepare/state consume work_root y protege
  estable, inputs conocidos y configuración antes de escribir. Snapshot por
  ejecución y provenance; API write_state requiere protected_inputs del llamador
   cuando el perfil no se conoce. 38 readers (37 OK, 1 file-symlink omitido por
   privilegio), 120 workflow OK y 17 mutantes por aserción. Goldfish A/B CON HALLAZGOS
   corregidos sin segunda revisión; comparación física de salidas y provenance fijadas
   en tests. No es S5a completo: Gas-O/Heat,
  rutas de perfiles, cache/init y dependencias externas siguen pendientes.
