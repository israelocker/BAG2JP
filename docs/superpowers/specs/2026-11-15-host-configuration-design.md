---
id: host-configuration-design
title: "Configuración host y diccionario de datos: diseño"
tags: ["design", "config", "dictionary", "workflow"]
summary: "Especificación aprobada: configuración común/local y resolución compartida host; implementación pendiente de plan aprobado, sin cambiar runtime ni datos nativos."
related: ["system_config.md", "docs/paths.md", "CHARACTER_IMPORT.md", "AGENTS.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: requirements
---

# Configuración host y diccionario de datos

**Estado:** especificación aprobada por el owner el15-11 («si»); no implementada.
**Decisor:** owner. Alcance elegido: «Host primero (Recomendado)»; diseño común +
local + cargador + diccionario aprobado en chat con «si». Esa aprobación permite
esta especificación. La aprobación posterior del documento permite redactar el
plan; no autoriza saltar la revisión del plan ni elegir su método de ejecución.

## 1. Objetivo y evidencia

Eliminar rutas locales duplicadas de herramientas host y dar significado inequívoco
a los datos reutilizados, sin convertir todo literal en una opción editable.

Evidencia leída, no búsqueda exhaustiva de todos los hardcodes:
- `tools/workflow/bag2_workflow.py:12-17`: build, instalación, script, Python y pins.
- `tools/test/versus_session.py:18-28`: instalación/Winshot junto a constantes nativas.
- `tools/bag1import/check_payload_manifest.py:15-22`: rutas de copias duplicadas.
- `tools/bag1import/profiles/gaso.json:12-14,28`: discos/runtime locales entre datos
  de personaje. La migración no cambia sus IDs, capabilities ni evidencia.
- `tools/workflow/validate_toml_config.py:9-11,28-37` valida ajustes del juego/
  instalador; no es un cargador común del entorno y no se sustituye por este diseño.
- `system_config.md` y `docs/paths.md` ya separan plantillas, rutas y ajustes vivos;
  siguen vigentes hasta migrar cada consumidor, no basta crear un TOML.

## 2. Decisión y alternativas

Adoptar configuración común portable + valores locales + resolución única. Frente
a un archivo gigante, separa entorno de reglas del juego; frente a variables de
entorno dispersas, permite tipos, trazabilidad y diagnóstico reproducible.
Coste: introducir un contrato compartido y adaptar consumidores por lotes.

No duplicar perfiles de personaje/escenario ni crear otro registro de aceptación.
Los settings/keybinds/state del juego permanecen independientes y protegidos.

## 3. Autoridades y archivos previstos

| Autoridad | Responsabilidad |
|---|---|
| `config/project.toml` | Esquema1, valores portables y política revisada del proyecto |
| `config/project.local.toml` | Rutas reales de la máquina; no versionado; nunca secretos |
| Cargador host compartido | Resolución/validación común; salida JSON para adaptadores host |
| Diccionario de datos | Significado y contrato de campos, con referencias a fuentes existentes |
| Perfiles/contratos actuales | IDs, regiones, recursos relativos y valores nativos con evidencia |

Rutas propuestas para los dos componentes nuevos (no archivos existentes):

```text
tools/workflow/project_config.py
docs/data-dictionary.md
```

No se crean estos componentes durante la fase de diseño. La implementación
añadirá una plantilla local sin rutas personales y la exclusión Git antes de
escribir el archivo local real; copiará únicamente valores actuales contrastados.

## 4. Campos y datos derivados

Catálogo inicial; un campo se adopta cuando su consumidor entra en el lote:

| Grupo | Claves | Tipo/unidad y procedencia |
|---|---|---|
| Raíz | `repo_root` | Path calculado desde la ubicación del módulo; no override de CWD |
| `paths` | `build_root`, `experimental_install`, `stable_install`, `tools_root`, `work_root` | Paths; locales salvo `work_root="_work"` relativo al repo |
| `inputs` | `bag1_usa_disc`, `bag1_jp_disc`, `bag1_usa_extraction`, `bag1_jp_extraction`, `bag1_reference_runtime` | Paths a fuentes, extracciones y referencia; no IDs del juego |
| `tools` | `python_report`, `winshot_root`, `build_script`, `ffmpeg_review`, `ffmpeg_wgc`, `ghidra_launcher`, `ghidra_project` | Paths; presencia exigida solo por la operación correspondiente |
| `wsl` | `distribution` | Nombre de distribución; conservar la actualmente verificada |
| `build` | `jobs` | Entero;2 según política vigente, no aumento libre de paralelismo |
| `pins` | `psxrecomp`, `recomp_ui` | Identificadores hex de revisión con semántica actual; política común, no override local |

Subdirectorios estables del layout (`mods-src`, `src`, preloaded/bundled, generated,
exe de build) se derivan de sus raíces; no mantener cada concatenación en el TOML.
Las claves son nombres, no comandos ni expresiones. No interpolación libre,
`eval`, ejecución de shell o sustitución arbitraria de variables dentro de strings.

No incluir automáticamente cada timeout o literal: solo parámetros host con
reutilización/necesidad demostrada, tipo/unidad/rango y dueño. Nuevos campos requieren
diccionario y pruebas. Límites de seguridad, fixtures y gates de captura no se
vuelven ajustes libres por estar repetidos. No cambiar defaults funcionales como
backend de audio/captura en una migración de rutas.

## 5. Resolución y consumo

1. Descubrir raíz por módulo, no por carpeta desde la que se lanza el comando.
2. Leer común y después local. El común declara `schema_version=1`; si el local
   declara versión, debe coincidir. Superponer por clave de sección, no reemplazar
   tablas enteras: solo claves marcadas como locales admiten override. Rechazar
   versión/clave/tipo desconocidos y overrides de política. No escribir al leer ni
   buscar otros archivos ocultos.
3. Permitir seleccionar explícitamente otro archivo local mediante
   `--local-config`; el default es el archivo local del repo. Sin capa nueva de
   variables de entorno que cambie rutas silenciosamente.
4. Resolver paths relativos de configuración respecto al repo. Flags de operación
   existentes mantienen precedencia y semántica documentadas; sus destinos efectivos
   pasan por las mismas validaciones antes de actuar.
5. Derivar rutas y validar el grupo requerido por la operación. Un comando documental
   no exige disponer de todos los discos o ejecutables; una operación que los usa
   falla claramente si falta su clave/input. No fallback a un literal antiguo.
   Conservar distinción actual entre diagnóstico y requisito fatal: por ejemplo,
   `report_python_present` del preflight no exige ejecutar ni habilitar el reporte.
6. Entregar estructura tipada no mutable y diagnóstico de valores efectivos,
   origen común/local/derivado y archivo/esquema usados. El local puede faltar si
   la operación dispone de todos sus valores; no adivinar ubicaciones para completarlo.

Python consume el módulo. PowerShell consume su JSON, nunca otra copia del parser
ni una cadena para `Invoke-Expression`. El intérprete de bootstrap es el Python
3.13 ya documentado: el cargador no puede elegir el intérprete que lo inicia.
No instalar Python/dependencias automáticamente.

Inicialmente Windows resuelve la configuración; los comandos WSL reciben argumentos
estructurados con conversión en la frontera. No concatenar sustituciones de texto
dispersas. Paths con espacios/Unicode deben conservarse; rutas sin conversión
soportada fallan, sin simular un mount. Scripts externos sin interfaz compatible
quedan como dependencia/límite explícito, no se reescriben fuera del alcance.

## 6. Diccionario y perfiles

Cada entrada del diccionario incluye nombre, significado, tipo, unidad/formato,
obligatoriedad por operación, origen/default, override permitido, validaciones,
consumidores, ejemplo y carácter derivado/editable/protegido. Diccionario y esquema
deben concordar en claves; una prueba detectará claves sin documentar.

Documentar datos nativos/perfiles por referencia a su autoridad: juego/región,
módulo/revisión/hash, unidades, evidencia y consumidores. No copiar sus valores a
`project.toml`. Direcciones MIPS, offsets/índices, poses y presupuestos específicos
siguen en contratos/perfiles; la política de seguridad sigue en AGENTS/estándares.

Primero se entrega el cargador sin cambiar esquemas1/2 de perfiles. La retirada de
rutas locales de perfiles necesita un lote propio con lectores/validadores y
compatibilidad explícitos: no añadir referencias mágicas a strings ni retirar
campos que los lectores actuales requieren. Recursos relativos y evidencia histórica
con hashes no se renormalizan ni reubican masivamente.

## 7. Seguridad y reproducibilidad

- Leer/validar antes de crear directorios, arrancar procesos, copiar o modificar.
  Resolver identidad/aliases y solapes entre raíces antes de operaciones de escritura;
  no tratar una ruta mal formada/no comprobable como un destino seguro.
- `stable_install` es rol protegido, no destino habilitable con un booleano. No
  cambiar las instalaciones efectivas durante la migración; contrastar equivalencia
  con rutas actuales. Cambiar config no otorga permiso de deploy/prueba ni para
  trasladar instalaciones. Una configuración local que etiquete mal ambas rutas
  no puede demostrar por sí misma cuál es estable: no prometer esa garantía.
  Los guards y autorización independientes de cada operación deben conservarse.
- No escribir settings, tarjetas, `mods/state.toml`, instalaciones o assets fuente
  como efecto del loader. No ampliar allowlists de diagnóstico ni activar features.
- Registrar huella de archivos config/esquema y valores efectivos pertinentes en
  evidencia de operaciones migradas; las rutas no sustituyen hashes de inputs/runtime.

## 8. Migración y criterios de aceptación

El plan posterior definirá lotes independientes y su orden: cargador/diccionario,
consumidor de lectura pequeño, workflow, harness/adaptadores e importadores/perfiles.
No activar todos los consumidores en un salto ni modificar scripts históricos de
`_work/`, binarios C, plugins, paquetes o herramientas instaladas por barrido.

Se acepta cada lote solo si:
- Con las rutas actuales resuelve los mismos inputs/destinos y preserva CLI y
  guards. Campos ilegales, política sobrescrita o destino protegido fallan antes
  de efectos; casos negativos no se arreglan con un fallback silencioso.
- Tests host con fixtures cubren común/local/derivadas, CWD distinto, espacios/
  Unicode, archivos faltantes, esquema/tipos/keys, prioridad CLI, conversión WSL y
  aliases/solapes relevantes. No tocan juegos, saves ni disco fuente reales.
- El consumidor migrado deja de contener rutas absolutas operativas duplicadas;
  usos restantes/excepciones quedan inventariados. No declarar cero hardcodes en
  todo el repositorio por haber migrado un lote. Diccionario y esquema concuerdan.

Comprobaciones de código y Goldfish del plan correspondiente no equivalen a una
partida ni autorizan una. Esta especificación no contiene implementación ni
resultados de esas pruebas futuras.

## 9. Gate siguiente

Especificación aprobada. Revisar ahora el plan de base/piloto y elegir ejecución
antes de implementar; la adopción de otros consumidores seguirá sus propios lotes.
Hasta entonces, solo planificación/lectura; Bloque5/Robo-Z y demás tareas conservadas.
