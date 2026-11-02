---
id: coding-standards
title: "Estándares de desarrollo y evidencia"
tags: ["standards", "development", "evidence"]
summary: "Requisitos de código/documentación; no afirma que todo el código existente ya los cumpla."
related: ["AGENTS.md", "CONTRIBUTING.md", "MAINTENANCE_GUIDE.md"]
created: "2026-11-01"
updated: "2026-11-02"
edited: "2026-11-02"
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
| One purpose per function | Las funciones deben hacer una cosa; dividir funciones de más de 30 líneas. |
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
  comportamiento: regresión RED→GREEN y aceptación relevante del runtime.
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

| Estándar | Descripción |
|----------|-------------|
| Descriptive test names | `test_buffer_ms_rejects_out_of_range` no `test1`. |
| Edge cases | Probar valores límite (mín, máx, cero, vacío). |
| One assertion per test | Cuando sea posible, cada prueba verifica un comportamiento. |
| In-game acceptance | Un cambio de código está completo solo después de que el flujo en juego pase, no solo después de compilar. |
