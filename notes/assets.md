---
id: asset-toolkit-extracted-data
title: "Assets: inventario antes de nombres"
tags: ["assets", "archive", "reference"]
summary: "Disc/table/member hashes como identidad; nombres extraídos y resultados antiguos no son evidencia actual automática."
related: ["notes/character-alternate-entries.md", "notes/bag1-stage-song.md"]
created: "2026-10-26"
updated: "2026-11-06"
edited: "2026-11-06"
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

Usar cada herramienta cuando responda a una necesidad concreta; no ejecutar todas
en cada tarea. Por ensayo registrar en la nota canónica del tema:

1. Pregunta, herramienta/versión, hashes de entrada, región/módulo y procedimiento
   previo con el que se compara. Salidas nuevas separadas; nunca sobrescribir originales.
2. Comprobación independiente: sectores/canales/duración para XA/STR; píxeles,
   coordenadas/CLUT/STP para TIM; instrucciones, callers y papel en Ghidra para
   MIPS/C. asm-differ compara MIPS con MIPS, no MIPS con el binario host recompilado.
3. Resultado correcto/incorrecto/no concluyente, tiempo medido y trabajo manual.
   Registrar también errores y resultados negativos; decidir si ayuda **a ese uso**.
4. Mantener la aceptación real del juego y la escucha humana donde correspondan.
   Un primer éxito no valida todos los personajes, overlays ni formatos propietarios.

Primer ensayo recomendado, aún pendiente: decodificar copias de XA/STR ya
inventariadas con jPSXdec y contrastar canal, duración y contenido con la evidencia
existente. La instalación no ejecutó ese ensayo ni modificó assets.
