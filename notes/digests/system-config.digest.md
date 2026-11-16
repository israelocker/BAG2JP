---
id: system-config-digest
title: "Configuración host: autoridades y estado"
tags: ["digest", "config", "migration"]
summary: "Control conciliado: 495 archivos por lote, 9 alcances host históricos; 22/471 con disposición acotada (4,67 %, no avance global). Esfuerzo/ETA aún sin baseline."
related: ["system_config.md", "docs/data-dictionary.md", "plans/pending/host-configuration-migration.md"]
created: "2026-11-15"
updated: "2026-11-16"
doc_kind: digest
source: "system_config.md"
source_sha256: "67ea9ed187e4a2c5dd705bb33d695b4a451e056b37a5990d39385d1c8d0d50bc"
---

# Configuración: estado mínimo

- Control actual en la primera sección de la fuente y en el inventario existente:
  471 originales +24 incorporados =495, cada archivo con lote principal, estado,
  alcance/restante y evidencia. Nueve alcances host entregados, doce grupos pendientes;
  no equivalen a tareas de igual esfuerzo ni a 42,86 % de avance global.
- Disposiciones acotadas de consumidores iniciales: 22/471 (4,67 %): 12 entregados,
  5 parciales, 2 pendientes, 3 sin cambio host identificado históricamente.
  Otros 19 son soporte registrado y 430 sin revisión consolidada. Treinta archivos
  con bytes cambiados no equivalen a treinta archivos totalmente migrados.
- Reusar evidencia por alcance/hashes; deriva exige análisis de impacto, no rerun
  global. Heat V6 conserva 169 inputs; otros manifiestos tienen deriva compartida.
  F0/S1/workspace aquí solo comparados contra commit. No se repitieron suites.
- Se retira ~60 %. Avance ponderado/ETA quedan desconocidos hasta baselinar esfuerzo,
  fecha y capacidad; cada sublote tendrá presupuesto, tiempo real/retrabajo y aviso
  de riesgo al consumir el presupuesto, sin ampliación silenciosa.
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
   Snapshot original y respuestas preservados; S4a posterior figura abajo.
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
- Gas-O builder (b1b585c/1ca68e5): inputs.bag1_usa_extraction/jp_extraction sustituyen ubicación
  del perfil; perfil conserva directorios y región independiente del anunciador.
  Un config/perfil por build y raíz existente antes de mkdir; v10: 12 lectores
  +120 workflow +7 HUD sin reutilizar logs, 17 mutantes; Goldfish corregido sin
  segunda revisión (detalle en fuente). Seis claves para perfil/stock/motions/salidas
  con defaults TOML y guardas antes de mkdir; no hubo paquetes ni prueba nativa.
- Piloto S5a: character_workflow plan/prepare/state consume work_root y protege
  estable, inputs conocidos y configuración antes de escribir. Snapshot por
  ejecución y provenance; API write_state requiere protected_inputs del llamador
   cuando el perfil no se conoce. 38 readers (37 OK, 1 file-symlink omitido por
   privilegio), 120 workflow OK y 17 mutantes por aserción. Goldfish A/B CON HALLAZGOS
   corregidos sin segunda revisión; comparación física de salidas y provenance fijadas
    en tests. Es evidencia del piloto, no de todos los importadores.
- Heat: adaptador host único para dos scripts legacy; cinco claves nuevas, 56 campos.
  Plan JSON sin ejecución por defecto; preparar/empaquetar son pasos explícitos.
  Stage reutiliza extracción USA con SCUS sin cabecera; selectores no son TOML.
  Goldfish A/B confirmó enlaces copiados, inputs ausentes tardíos y scoring ERROR;
  correcciones con junctions reales y fixtures, sin segunda revisión. V4 no prueba
   22 kills por aserción; v5 con deriva/timeout no se puntúa. V6: 32 lectores,
   120 workflow, 7 HUD y sintaxis Bash OK; 34 mutantes por aserción sin ERROR,
   hashes de entrada iguales. Cierre host, no prueba de conversión ejecutada.
  No sandbox concurrente/WSL ni validación de conversión/make-mod. S5b y externos
  siguen pendientes; no adaptadores, paquetes, runtime ni juego ejecutados.
