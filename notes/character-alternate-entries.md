---
id: character-alternate-entries
title: "Integración reutilizable de personajes mediante entradas alternativas"
tags: ["bag1", "character", "dfs", "payload", "workflow"]
summary: "Reconstrucción DFS, preservación de personajes existentes, payload exacto en DUMMY.BIN y sincronización manual antes de compilar. Lecciones verificadas con Heat y Strike; límites explícitos."
related: ["CHARACTER_IMPORT.md", "notes/character-pipeline.md", "notes/character-import-testing.md", "notes/strike-recovery.md"]
created: "2026-11-02"
updated: "2026-11-02"
edited: "2026-11-02"
---

# Entradas alternativas: receta compartida

Usar después del inventario y del contrato de animaciones. Cambiar datos por
personaje, no clonar scripts Heat/Strike. Esta receta integra candidatos: no
certifica equivalencia de movimientos, fidelidad visual ni aceptación final.

## 1. Arquitectura que se conserva

```text
Discos originales → inventarios/hashes → conversión por contrato
  → miembros convertidos → contenedores DFS → payload exacto + índice C
  → manifest disc_user → staging explícito → build WSL → experimental
  → pruebas con mods activos → evidencia → aceptación o pendientes
```

El archivo original `BUST2.BIN` conserva las entradas BAG2. El overlay del mod
aporta alternativas en `DUMMY.BIN`; no se sobrescribe el BIN original del disco.
El plugin `bag2jp_bag1_versions.c` cambia offset **y tamaño** en la tabla DF2_
en RAM según versión/lado. Sí hay que recompilar el runtime cuando cambia su
índice C: no confundir «sin parchear el ejecutable PS1» con «sin nuevo exe nativo».

Fuente canónica: `mods-src/bag2jp.feature.bag1-content/`. No editar únicamente
el paquete instalado: el siguiente staging lo puede sustituir.

## 2. Inventario antes de modificar

- Verificar disco/región/hash, ID real del personaje y tablas nativas. Los IDs
  del selector no se deducen de posiciones aparentes en una cuadrícula.
- Separar pack/modelo, traje A/B y lado P1/P2. Registrar entrada, offset,
  tamaño y hashes de cada miembro. El mismo índice de miembro puede significar
  otra cosa en P2; no reutilizar el índice P1.
- Conservar originales, candidatos y referencias en directorios distintos.
- Comparar enlaces del esqueleto, no solo número de huesos. Un parche DBI
  de otro personaje requiere evidencia específica; por defecto conservar stock.
- Validar modelo hasta el final y lista de animaciones con terminador. Una
  política declarada válida no demuestra cobertura semántica o transiciones.
- Inspeccionar TIM: flags, dimensiones, imagen y CLUT en VRAM. Coincidencia de
  coordenadas no demuestra UV/paletas correctas en todos los trajes.

Herramientas existentes: `inspect_character_entries.py`,
`model_bag1_to_bag2.py`, `animation_policy.py`, `tim_retarget.py`, todas bajo
`tools/bag1import/`. `anim_remap.py` y `anim_remap_strike.py` conservan adaptación
específica; no hay asignador semántico universal implementado.

## 3. Reconstruir DFS por miembros

Usar `tools/bag1import/rebuild_dfs_members.py`. Spec de datos, ejemplo:

```json
{
  "containers": [{
    "source": "_work/character-import/<slug>/stock/model_a_p1.dfs",
    "out": "_work/character-import/<slug>/candidate/model_a_p1.dfs",
    "replace": {
      "0": "_work/character-import/<slug>/candidate/model.bin",
      "1": "_work/character-import/<slug>/candidate/animations.bin"
    }
  }]
}
```

```powershell
py -3.13 tools/bag1import/rebuild_dfs_members.py --spec <containers.json> --root .
py -3.13 -m unittest discover -s tools/test -p test_rebuild_dfs_members.py
```

Rutas del spec relativas a `--root`, **no** al directorio del spec.
Formato: `DFS_`, count u32 LE y pares `{offset, size}` u32 LE por miembro.
El escritor calcula cada offset a partir de la longitud real del buffer.
Valida orden, límites, solapes, vacíos y lectura posterior. Comparar además los
hashes de miembros no reemplazados: deben seguir siendo los originales.

**Límite:** el escritor compacta sin conservar huecos ni padding final; no es un
round-trip byte-idéntico del contenedor stock. Antes de aplicarlo a otro formato,
comprobar requisitos de alineación del loader. En Strike se ejercitaron los ocho
contenedores. No aceptar miembros solapados ni forzar otro layout para que pase.

El generador antiguo de `_work/versus-navigation/rebuild_strike_alternate_dfs.py`
es un experimento rechazado: todos los offsets quedaban iguales. Un tamaño total
correcto y un modelo visible en VS no detectaban el fallo. No reutilizarlo.

## 4. Preservar contenido ya aceptado

Antes de reconstruir el payload combinado, guardar copia con hash de payload,
índice y manifest que funcionan. Para cada entrada ya importada:

```text
start = old_alt_off - old_dummy_archive_relative_base
bytes = old_payload[start : start + old_alt_size]
```

Verificar límites, hash y lectura de cada entrada extraída. **No** leer la entrada
stock del disco creyendo que contiene BAG1, ni extraer `size` en vez de `alt_size`.
Así se perdieron temporalmente las versiones Heat y sus entradas fever/escenario.
Tras empaquetar, comparar hashes de todas las filas preservadas, no solo su número.

Para actualizar filas existentes, `alternate_payload.py` ofrece `repack`; conserva
metadatos y rechaza entradas desconocidas, pero tiene base/capacidad fijas JP.
No añade automáticamente personajes nuevos. La reconstrucción completa usa un
spec que enumera tanto filas preservadas como nuevas.

La recuperación histórica de Heat desde una copia anidada y el índice de Git
`096533d` está descrita en `notes/strike-recovery.md`. Esa copia fue una fuente
de rescate verificada, no un diseño de carpetas ni dependencia para nuevas importaciones.
`_work/versus-navigation/build_alt_spec.py` sigue siendo un adaptador local de
rescate con rutas/commit fijos, no el generador compartido a copiar.

## 5. Empaquetar bytes exactos

`tools/bag1import/make_alt_entries_exact.py` consume este contrato:

```json
{"rows": [{"entry": 73, "chr": 1, "kind": 0,
           "file": "_work/character-import/<slug>/candidate/pack_a_p1.dfs"}]}
```

73/1 son **ejemplo Strike**, no valores universales. `kind`: 0=P1, 1=P2,
2=fever del ganador, 3=escenario. Rutas relativas al CWD o absolutas.

```powershell
py -3.13 tools/bag1import/make_alt_entries_exact.py <original-disc.bin> <entries.json> <output-dir>
```

Produce `payload/bag1_alt.bin`, `bag2jp_bag1_alt_index.h`, `alt_report.json`.
Deduplica bytes idénticos, alinea comienzos a 2048 B y mantiene longitud exacta
en `alt_size`. Nunca truncar un pack para imitar el tamaño stock.
`make_alt_entries.py` reconstruye desde overlays sobre un rango stock y no debe
usarse para alternativas que crezcan. `finalize_alternate_dfs.py` de `_work/`
también queda rechazado como paso de ajuste destructivo de tamaños.

Coordenadas distintas que no deben mezclarse:

```text
manifest.offset = DUMMY_LBA * 2048             # absoluto disc_user
alt_off = (DUMMY_LBA + payload_sector - ARCHIVE_LBA) * 2048
                                               # relativo a BUST2.BIN
raw file position ≠ disc_user offset             # imagen raw usa sectores 2352
```

En el disco JP verificado: DUMMY_LBA=224035, ARCHIVE_LBA=179,
manifest.offset=458823680 y base relativa=0x1B538000. Volver a verificar para otra
imagen. `sha256` del overlay es el del payload; `expected_sha256` es el hash de
los bytes originales que reemplaza, **no** el del payload. En DUMMY verificado
eran ceros de longitud igual al payload; no asumir ceros en otro destino.

**Validaciones manuales todavía obligatorias:** el script lee solo 4096 B de
tabla DF2_, no valida exhaustivamente count/IDs duplicados/kind/chr; el extent
ISO entrega longitud en bytes, pero su variable `dummy_sectors` se multiplica
por 2048 en el control de capacidad. Ese control sobreestima capacidad y no sirve
como prueba. Exigir `payload_bytes <= DUMMY extent bytes`, entradas únicas dentro
de count/tabla disponible y hashes de slices correctos antes de desplegar.
No se corrigieron estas limitaciones en la tarea de documentación.

## 6. Plugin y manifiesto: descubrir, no asumir

En la integración actual Heat y Strike comparten feature `bag1-heat`.
`strike_p1`/`strike_p2` son opciones de ese feature; **no existe** `bag1-strike`.
El popup consulta disponibilidad en el índice y cambia versión por selección.
Añadir filas no generaliza por sí solo opciones/estado interno del plugin:
revisar límites de arrays, registro de opciones, routing de lado/fever y netsync
para el nuevo ID. Conservar guards y restauración de entradas stock.

Actualizar juntos payload, índice, manifest y opciones. Los cambios de assets o
timing requieren revisar identidad de contenido online; estas pruebas locales
no certifican netplay. No reemplazar todo `mods/state.toml` por una plantilla.

## 7. Staging, compilación y despliegue reversible

El helper **diagnostica drift, no sincroniza fuentes**. Antes del build:

1. Copiar solo fuentes del task `mods-src/<package>/*.c|h|inc` a
   `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP/src/`.
2. Copiar archivos de recursos cambiados de `mods-src/<package>/1.0.0/` a
   `.../BAG2JP/mods/preloaded/packages/<package>/1.0.0/`.
3. Revisar hashes de origen/destino; no sobreescribir drift ajeno.
4. Ejecutar helper `build --tag <tag>` con Python registrado en project-config:
   WSL Ubuntu, llvm-mingw fijado y dos jobs. Esperar proceso completo.
5. Verificar exe en `build-win-codex/` y paquete en
   `build-win-codex/mods/bundled/<package>/1.0.0/`: tamaño, hash y manifest.
6. Sin partida activa, guardar backup único del exe y archivos de paquete
   experimentales a reemplazar, con hashes. Copiar solo esos archivos.
7. Comparar hashes desplegados. La línea de log del nuevo personaje confirma
   código efectivo; fecha del archivo o «build passed» no bastan.

Prohibido tocar instalación estable. Conservar mods ya existentes y sus estados;
no desactivarlos en masa para ocultar interacciones. Restaurar en rollback el
conjunto coherente exe+payload+manifest, no una combinación de generaciones.
Continuar con [pruebas y diagnóstico](character-import-testing.md).
