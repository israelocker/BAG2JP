---
id: coding-standards
title: "Estándares de desarrollo y evidencia"
tags: ["standards", "development", "evidence"]
summary: "Requisitos de código/documentación; no afirma que todo el código existente ya los cumpla."
related: ["AGENTS.md", "CONTRIBUTING.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-01"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: requirements
---

# BAG2JP — Coding Standards

Estándares de código para todo el proyecto. Se aplican a todo código nuevo y modificado.

Son requisitos, no prueba de cumplimiento del código existente. Mantener seams
compartidos y perfiles de datos; extraer abstracciones solo ante variaciones
demostradas, sin clonar pipelines ni crear capas por anticipación. Función larga
es señal para revisar responsabilidades, no motivo para fragmentarla mecánicamente.

## C (plugins en mods-src/)

| Estándar | Descripción |
|----------|-------------|
| No magic constants | Reemplazar literales numéricos con `#define` o `enum` con nombres descriptivos. Direcciones, puertos, tamaños de buffer, límites de frames deben ser constantes nombradas. |
| Validate input early | Verificar punteros, rangos y valores de retorno al inicio de cada función. |
| One purpose per function | Una responsabilidad por función; revisar funciones largas sin dividir mecánicamente por número de líneas. |
| Comment the "why" | El código explica qué; los comentarios explican por qué se tomó una decisión. |
| Group related `#define` | Colocar constantes al inicio del archivo, antes de su primer uso, con comentarios inline explicando su propósito. |

### Ejemplo de constante nombrada

```c
/* Antes: constante mágica */
if (n < 20 || memcmp(b, "B2NS", 4) || b[4] != 2) return;

/* Después: constante nombrada */
#define NS_PKT_HDR 20  /* Protocol packet header size */
if (n < NS_PKT_HDR || memcmp(b, "B2NS", 4) || b[4] != 2) return;
```

## Python (scripts en tools/)

| Estándar | Descripción |
|----------|-------------|
| Type hints | Todas las funciones públicas deben tener anotaciones de tipo en parámetros y retorno. |
| Logging over print | Usar módulo `logging` con niveles (INFO, WARNING, ERROR) en lugar de `print`. |
| pathlib over strings | Usar `Path` para toda manipulación de rutas de archivo. |
| Specific exception handling | Capturar excepciones concretas (ej. `FileNotFoundError`, `json.JSONDecodeError`), nunca bare `except Exception`. |
| Docstrings | Documentar todas las funciones públicas con propósito, parámetros y valor de retorno. |

### Ejemplo de función Python

```python
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("my_script")


def validate_file(path: Path, fix: bool = False) -> list[str]:
    """Validate a single note file.

    Args:
        path: Path to the markdown file to validate.
        fix: If True, auto-fill missing frontmatter fields.

    Returns:
        List of issue descriptions found during validation.
    """
    issues: list[str] = []
    # ... implementación
    return issues
```

## TOML Configuration

| Estándar | Descripción |
|----------|-------------|
| Validate on load | Los valores numéricos deben estar dentro de rangos documentados (ej. `buffer_ms` 30-500). |
| Document defaults | Comentar qué hace cada opción y su valor por defecto. |
| No secrets or personal paths | Los archivos de configuración no deben contener rutas de usuario ni credenciales. |

### Reglas de validación TOML

| Sección | Clave | Tipo | Mín | Máx | Requerido |
|---------|-------|------|-----|-----|-----------|
| `[audio]` | `buffer_ms` | numeric | 30 | 500 | Sí |
| `[video]` | `internal_resolution` | string | — | — | No |
| `[video]` | `anisotropic_filtering` | numeric | 1 | 16 | No |
| `[video]` | `window_width` | numeric | 640 | 7680 | No |
| `[controller]` | `p1_deadzone` | numeric | 0 | 32767 | No |
| `[controller]` | `p2_deadzone` | numeric | 0 | 32767 | No |

## Documentation (notes/)

| Estándar | Descripción |
|----------|-------------|
| Frontmatter required | Cada nota debe tener `id`, `title`, `tags`, `summary`, `related`, `created`, `updated`. |
| Update `updated` | Cualquier modificación en una nota debe refrescar el timestamp `updated`. |
| Evidence, not noise | Guardar logs/pilots completos fuera de notas activas. Conservar hashes, rutas de evidencia y direcciones técnicas necesarias; no borrar pruebas únicas ni confundir rutas autorizadas del entorno con secretos. |
| Digests for large files | Archivos fuente >10 KB deben tener un digest correspondiente en `notes/digests/`. |

### Verdad y estado documental

- Hecho: citar fuente/input/versiones y seam que lo acredita (código, tests host,
  runtime o escucha humana). Existencia de una función no demuestra uso correcto.
- Requisito: expresar «debe», sin presentarlo como implementación aceptada.
- Hipótesis/propuesta: fuera de recetas operativas hasta contrastar.
- Histórico: preservar separado y fechado; no usar «último exe» sin hash vigente.
- Una autoridad por tema; índices enlazan y digests resumen con `source` y hash.
  No mantener variantes clean/optimized con aceptación independiente.
- Cambio documental: checker y revisión de afirmaciones/enlaces. Cambio de
  comportamiento del juego: regresión RED→GREEN y aceptación relevante del runtime.
  Tooling host: regresiones en su costura, no partida por defecto; rige AGENTS.
- No se certifica ahorro con porcentajes genéricos ni con tests no relacionados.

### Plantilla de frontmatter

```markdown
---
id: <identificador-unico-kebab-case>
title: "<Título Descriptivo>"
tags: ["tag1", "tag2", "tag3"]
summary: "Un párrafo de resumen (máximo 2 líneas) sobre qué contiene esta nota."
related: ["CHARACTER_IMPORT.md", "NOTES.md", "_work/current-state.json"]
created: "YYYY-MM-DD"
updated: "YYYY-MM-DD"
---
```

## Testing

### Regresiones aprendidas en Gas-O

- **Guards independientes:** derivar palabras esperadas del ejecutable/módulo
  original ligado por hash, no de la misma macro que se prueba. Para hooks AOT,
  verificar `mod_instruction_sites`, registro y llamada en el C generado. Host
  callbacks que pasan aislados no prueban ejecución del hook ni integración.
- **RED/mutación:** el stub debe compilar y fallar por el comportamiento esperado.
  Un compilador roto, import fallido, timeout o runner inválido no mata un mutante.
  Exigir baseline verde y aserción causal registrada. En harness C con `assert`,
  desactivar NDEBUG antes de incluir assert y comprobar ASAN/UBSAN cuando aplique.
- **Toolchain real:** antes del build caro, comprobar sintaxis/includes/API con las
  flags del destino; GCC host con stubs no demuestra compatibilidad Windows ni link.
- **RAM/lifecycle:** validar alineación y rangos con el tamaño efectivo de RAM;
  reservar memoria guest por la API existente, nunca por elegir una dirección libre
  aparente. Un puntero actor fijo no es una generación: invalidar registros host
  en reset, load y reinicialización nativa. No eludir el gate de layout de savestate
  cuando cambian asignaciones/mods; no crear otro sistema de guardado.
- **Suite conocida no verde:** ejecutar tests de la costura cambiada y comparar una
  suite global pertinente por nombres/causas con baseline persistida. No presentar
  los ~32 errores históricos como cifra fija ni como éxito; nuevos fallos son
  regresiones hasta aislarlos. No repetir toda la suite sin cambios por inercia.
  Reparar o proponer cuarentena explícita como tarea separada, no ocultarlos aquí.
- **Reproducibilidad:** nuevas herramientas se ejercitan con input real acotado,
  no solo `py_compile`/help. Preferir scripts/argumentos estructurados al quoting
  inline repetido; escribir texto nuevo UTF-8/LF, sin renormalizar historia ajena.
- **Build/payload:** comparar hashes fuente→build y recursos→paquetes antes de
  atribuir un resultado al cambio. Generar por la cadena canónica, nunca editar a
  mano el índice. `overlay.sha256` es del payload; `expected_sha256`, de la extensión
  original del disco con su longitud real. Revisar copias implicadas y capacidad
  independientemente de guards incompletos. Preflight sigue siendo diagnóstico.

Evidencia histórica y alcance: [retrospectiva Gas-O](../notes/gaso-import.md#retrospectiva-incorporada-al-estándar-2026-11-15).
Estos son requisitos; no cambian herramientas ni corrigen deuda por sí mismos.

| Estándar | Descripción |
|----------|-------------|
| Descriptive test names | `test_buffer_ms_rejects_out_of_range` no `test1`. |
| Edge cases | Probar valores límite (mín, máx, cero, vacío). |
| One assertion per test | Cuando sea posible, cada prueba verifica un comportamiento. |
| Verification at the relevant seam | Un cambio de comportamiento del juego requiere su flujo en juego, no solo compilar. Tooling host requiere sus regresiones; documentación, comprobación documental. Rigen los permisos de AGENTS. |
