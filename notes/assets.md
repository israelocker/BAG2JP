---
id: asset-toolkit-extracted-data
title: "Assets: inventario antes de nombres"
tags: ["assets", "archive", "reference"]
summary: "Identidad de assets, herramientas instaladas y uso pertinente obligatorio con historial individual de efectividad."
related: ["notes/character-alternate-entries.md", "notes/bag1-stage-song.md"]
created: "2026-10-26"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# Assets

Inventario compartido actual: `tools/bag1import/inspect_character_entries.py`
y `iso_extract.py`. La tabla DF2_ del disco original define offsets/tamaños;
el contenedor DFS define los miembros. Ver [integración](character-alternate-entries.md)
para sus espacios de offset, región y validaciones.

Los nombres de carpetas no son IDs del juego. Especialmente choreography/fever
requiere tabla nativa; no elegir una animación por nombre de personaje de carpeta.
`fever_entries.py` es una referencia del disco JP, no una tabla universal BAG1/BAG2.
Registrar input hash, entrada, miembro y longitud antes de convertir.

La [investigación original](archive/assets-before-audit.md) conserva catálogo,
BPE, loader y repack byte-idéntico reportado en octubre. No se reejecutó ese
repack en la auditoría. Los assets pesados están fuera de Git y su presencia
debe comprobarse, no suponerse porque una nota los enumera.

## Herramientas comunitarias instaladas (2026-11-06)

El dueño autorizó instalar las herramientas recomendadas y evaluar sus resultados
durante el desarrollo. Instalación aislada en `D:/Dev/Tools/ps1-community/`, sin
cambiar PATH, Python global, runtime, discos ni partidas. No sustituye el pipeline
compartido ni [Ghidra obligatorio](../AGENTS.md). **Instalada y capaz de arrancar
no significa validada para BAG2JP ni demuestra ahorro.**

| Herramienta / versión fijada | Ubicación relativa a esa raíz | Comprobación inicial / límite |
| --- | --- | --- |
| jPSXdec v2.1, distribución beta | `jpsxdec-2.1/jpsxdec_v2.1-beta/jpsxdec.jar` | Ayuda CLI; pendiente contrastar XA/STR. Licencia no comercial incluida en `doc/LICENSE.txt` |
| dumpsxiso / mkpsxiso 2.30 | `mkpsxiso-2.30/mkpsxiso-2.30-win64/` | Ayuda de dumpsxiso; no reconstrucción de disco ni extracción BAG nueva |
| TIMedit 0.10a | `timedit-0.10a/timedit.exe` | Ventana vacía abierta/cerrada; sin editar TIM personales ni confirmar CLUT/STP |
| spimdisasm 1.42.4 | `python-313/Scripts/spimdisasm.exe` | Ayuda CLI; verificar modo PSX/MIPS I, región, base y módulo antes de desensamblar |
| m2c c632946b8cfbe8fce442b522dba92dfa72f1f317 | `python-313/Scripts/m2c.exe` | Ayuda CLI; C propuesto no es fuente recuperada ni prueba de equivalencia |
| asm-differ 0dd09af8f8008f1f880327cf0aca3b26d2562ea2 | `python-313/Scripts/asm-differ.exe` | Requiere `diff_settings.py` antes incluso de `--help`; configurar inputs y GNU objdump MIPS por tarea. Comparación real pendiente |

Ghidra 12.1.4 conserva su loader `ghidra_psx_ldr` y los datos PsyQ ya instalados;
MCP identificó `SLPM_862.19` y encontró `InitHeap` en `0x80049f44`. No se reinstaló
ni se ejecutó análisis masivo de firmas sobre el proyecto. PCSX-Redux ya estaba
en `D:/Dev/Tools/pcsx-redux/pcsx-redux.exe`: se conserva sin abrirlo, actualizarlo,
activar servidores ni cambiar tarjetas/configuración. PSXRecomp nativo sigue
siendo la referencia de este proyecto; ningún emulador nuevo fue instalado.

### Invocaciones y procedencia

PowerShell, usando rutas absolutas; no hace falta activar el entorno:

```powershell
& D:/Dev/Tools/jdk-21.0.12.1+1/bin/java.exe -jar D:/Dev/Tools/ps1-community/jpsxdec-2.1/jpsxdec_v2.1-beta/jpsxdec.jar '-?'
& D:/Dev/Tools/ps1-community/mkpsxiso-2.30/mkpsxiso-2.30-win64/dumpsxiso.exe --help
& D:/Dev/Tools/ps1-community/python-313/Scripts/spimdisasm.exe --help
& D:/Dev/Tools/ps1-community/python-313/Scripts/m2c.exe --help
```

Para asm-differ, invocar su ejecutable desde una carpeta de tarea con
`diff_settings.py` revisado. La configuración bajo `_work/tool-install/empty-workdir/`
solo permite probar ayuda y rechaza comparaciones reales; no copiarla como receta
de importación. No se encontró GNU objdump MIPS en el PATH de WSL durante esta
instalación: comprobar/provisionar ese backend antes de depender de asm-differ.
Graphviz Python está instalado como dependencia de m2c; no se afirma que exista
el ejecutable `dot` para gráficos opcionales.

Versiones exactas de dependencias: `D:/Dev/Tools/ps1-community/installed-requirements.txt`.
Manifiesto duradero fuera de `_work/`: `D:/Dev/Tools/ps1-community/installation-manifest.json`,
con copia de los reportes PyPI y resultados de arranque.
Procedencia, SHA-256, resultados y logs en `_work/tool-install/`: `installation.json`,
`pip-dependencies.json`, `smoke-results.json` y `asm-differ-smoke.json`. Los archivos
descargados se conservan en la raíz externa, subcarpeta `downloads/`; las fuentes
de m2c/asm-differ se conservan en carpetas con su commit. Los SHA upstream de
jPSXdec/mkpsxiso se verificaron; TIMedit no publica digest en su release y su hash
local **no** es una verificación independiente de autenticidad. Dependencias PyPI
instaladas desde wheels, sin compilar ni instalar paquetes del sistema.

### Evaluación progresiva, no aceptación automática

**Uso obligatorio cuando sea pertinente**, según AGENTS; no ejecutar todas en
cada tarea. Antes de usarla, leer su historial de la tabla siguiente. Después de
cada ensayo, añadir su resultado al log propio, incluidos errores y omisiones
justificadas. La nota canónica del tema enlaza esa entrada, sin duplicar otro
historial. Por ensayo registrar:

1. Pregunta, herramienta/versión, hashes de entrada, región/módulo y procedimiento
   previo con el que se compara. Salidas nuevas separadas; nunca sobrescribir originales.
2. Comprobación independiente: sectores/canales/duración para XA/STR; píxeles,
   coordenadas/CLUT/STP para TIM; instrucciones, callers y papel en Ghidra para
   MIPS/C. asm-differ compara MIPS con MIPS, no MIPS con el binario host recompilado.
3. Resultado correcto/incorrecto/no concluyente, tiempo medido y trabajo manual.
   Registrar también errores y resultados negativos; decidir si ayuda **a ese uso**.
4. Mantener la aceptación real del juego y la escucha humana donde correspondan.
   Un primer éxito no valida todos los personajes, overlays ni formatos propietarios.

En la instalación del06-11 quedó pendiente un primer ensayo XA/STR; no es estado
actual de la herramienta. Los ensayos posteriores y sus límites se consultan en
su [historial jPSXdec](tool-evidence/jpsxdec.md); no inferir éxito para STR de un uso XA.

### Historial por herramienta y pertinencia

Los logs son registros duraderos en Git; los archivos completos de evidencia
pueden vivir en `_work/` o en la instalación externa, con ruta y SHA-256. No cargar
todos los historiales como contexto de inicio. Consultar solo los pertinentes.

| Herramienta / log | Usarla cuando… |
| --- | --- |
| [jPSXdec](tool-evidence/jpsxdec.md) | Se deba contrastar identificación/decodificación XA o STR de PS1 |
| [dumpsxiso](tool-evidence/dumpsxiso.md) | Haga falta verificar extracción, sectores raw, canales, CUE/LBA frente al extractor local |
| [mkpsxiso](tool-evidence/mkpsxiso.md) | Una tarea autorizada requiera reconstruir un disco; no para un simple overlay DFS |
| [TIMedit](tool-evidence/timedit.md) | Haya dudas de píxeles, coordenadas, CLUT o STP en TIM; trabajar sobre copias |
| [spimdisasm](tool-evidence/spimdisasm.md) | Se necesite desensamblado MIPS estructurado independiente de un rango identificado |
| [m2c](tool-evidence/m2c.md) | Convenga obtener C revisable de MIPS ya delimitado; contrastarlo en Ghidra |
| [ffmpeg-skill](tool-evidence/ffmpeg-skill.md) | Cuando haga falta medir, recortar, comparar frames, extraer o medir audio, generar montajes o comprobar archivos de video/audio en el proyecto |
| [bag2_record.py](tool-evidence/bag2-record.md) | Siempre en toda validación en juego (AGENTS «Validación en juego grabada»): video + audio exacto del juego alineado a fotogramas; skill `bag2-game-recording` |

| [Ghidra / PSX / PsyQ](tool-evidence/ghidra-psx-psyq.md) | Siempre según AGENTS; firmas PsyQ solo cuando aporten a la identificación concreta |
| [PCSX-Redux](tool-evidence/pcsx-redux.md) | Un diagnóstico complementario necesite GPU/GTE/breakpoints y no lo resuelva la referencia nativa; respetar autorización y sesiones |
| [funcmatch.py](tool-evidence/funcmatch.md) | Se busquen equivalentes de funciones de los ejecutables principales BAG1/BAG2, no overlays |
| [Intérprete PSXRecomp](tool-evidence/psxrecomp-interpreter.md) | Haga falta ejecutar un tramo MIPS real fuera del juego con RAM/callees delimitados; no sustituye render/cadencia ni aceptación en partida |

### ffmpeg-skill (instalación histórica y ruta operativa)

Instalación del10-11 en `tools/ffmpeg-skill` v3.2.3: doctor84 capacidades,0 requeridas
faltantes,1 opcional (`parakeet`). Desde12-11 se carga `.agents/skills/ffmpeg-skill`
v3.6.0; la copia antigua se conserva hasta decisión del owner, no se borra aquí.
Ver [historial](tool-evidence/ffmpeg-skill.md), entrada ffmpeg-skill-002. Usar cuando
sea pertinente, sin confundir doctor con aceptación de media/juego ni normalizar,
eliminar silencios o alterar velocidad de evidencia original sin autorización.

No se impone una prueba peligrosa ni un cambio de configuración ajeno al objetivo.
Si procede la herramienta pero está bloqueada, ya existe evidencia reutilizable
o el ensayo requiere autorización adicional, registrar la omisión y su motivo.
Una omisión no cuenta como uso ni como resultado negativo de la herramienta.

### Clasificación y medición obligatorias

- **Útil / buenos resultados:** resolvió la pregunta y la comprobación independiente
  sustenta la corrección. Precisar el alcance; una respuesta válida sin ahorro
  medido sigue siendo útil, pero no demuestra optimización.
- **Irrelevante:** se ejecutó, pero no añadió información aplicable a esa pregunta.
- **Contraproducente:** produjo un resultado demostrado incorrecto o añadió coste,
  confusión o retrabajo frente al procedimiento de referencia; describir la causa.
- **Inconcluso:** falta contraste o evidencia suficiente, o solo se probó arranque.
- **No ejecutado / bloqueado:** precondición, seguridad, permiso o reutilización
  impidió/necesitó evitar el uso; no atribuirle un fallo práctico inexistente.

Un código de salida distinto de cero no decide por sí solo la utilidad ni la causa.
Separar fallo de configuración, limitación conocida y fallo propio de la herramienta.
Medir por ensayo tiempo de ejecución y tiempo de preparación/revisión/retrabajo;
registrar el método y el procedimiento de referencia con su tiempo, si existe.
Sin referencia comparable, declarar **ahorro no medido**. No inventar tiempos,
porcentajes ni trasladar un éxito a otros módulos, regiones o versiones.
Al decidir reutilización, revisar aciertos, falsos positivos/negativos y costes
del mismo tipo de tarea; no declarar eficacia general a partir de una ayuda CLI.

### Plantilla para añadir una entrada

Añadir al final del log tras cada ensayo (una entrada puede agrupar sus llamadas
relacionadas). Usar ID único `YYYYMMDD-tool-NNN`, fecha UTC y referencia a la tarea.
No borrar resultados desfavorables; corregir mediante una nueva entrada que cite
el ID previo. Los antecedentes iniciales están transcritos de evidencia retenida,
no son ejecuciones nuevas ni un historial exhaustivo de usos antiguos.

```text
## <ID> — <fecha UTC> — <pregunta/tarea>
- Tipo: uso real | arranque | omisión justificada | corrección de <ID>.
- Versión, entorno y comando/MCP/configuración exactos:
- Entradas: rutas y SHA-256; juego, región, módulo/base (o no aplica y por qué).
- Resultado observado: salida/código, hallazgos, errores y límites.
- Evidencia: rutas/consultas y SHA-256 de archivos; salidas separadas de originales.
- Contraste independiente y procedimiento de referencia: resultado o pendiente.
- Dictamen: útil / buenos resultados | irrelevante | contraproducente |
  inconcluso | no ejecutado / bloqueado. Justificación y alcance:
- Medición: ejecución, preparación, revisión/retrabajo y referencia; método.
  Ahorro medido o no medido (si no hay datos, escribir no medido).
- Decisión / siguiente paso: reutilizar para <caso>, ajustar, evitar o pendiente.
```
