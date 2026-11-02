# BAG2JP — Enrutamiento de Modelos (Model Routing)

Este documento define qué modelo de IA usar para cada tipo de tarea, optimizando el uso de tokens y el costo sin perder calidad.

## Principio General

> Usa el modelo más barato que pueda hacer el trabajo bien. Usa modelos de razonamiento solo para tareas complejas que requieran juicio, arquitectura o depuración profunda.

## Capas de Modelo

| Nivel | Modelo (ejemplo) | Uso | Ahorro de Tokens |
|-------|-----------------|-----|------------------|
| **Ligero** | Modelo pequeño/rápido | Preguntas simples, resumen de notas, búsqueda de archivos, formateo | ~60-90% |
| **Estándar** | Modelo general | Implementación de código, corrección de bugs, escritura de documentación | Línea base |
| **Razonamiento** | Modelo grande/reasoning | Arquitectura, decisiones de diseño, depuración compleja, planificación | Solo cuando sea necesario |

## Reglas de Enrutamiento

### ✅ Usa Modelo Ligero para:

| Tarea | Ejemplo | Por qué |
|-------|---------|---------|
| Resumir notas | "Resuma qué hace notes/bag1-character.md" | No requiere razonamiento profundo |
| Buscar archivos | "¿Dónde está la definición de buffer_ms?" | Búsqueda directa, no razonamiento |
| Formatear código | "Convierte esto a Markdown con frontmatter" | Transformación mecánica |
| Extraer datos | "Extrae todos los IDs de las notas" | Patrón de búsqueda simple |
| Verificar existencia | "¿Existe el archivo tools/workflow/maintenance_check.py?" | Consulta de sistema de archivos |
| Contar líneas/palabras | "¿Cuántas líneas tiene CHARACTER_IMPORT.md?" | Operación de conteo |

### ✅ Usa Modelo Estándar para:

| Tarea | Ejemplo | Por qué |
|-------|---------|---------|
| Escribir código Python/C | Implementar un script de mantenimiento | Requiere sintaxis correcta y lógica |
| Corregir bugs | Arreglar un fallo en un test | Requiere comprensión del código |
| Escribir documentación | Crear una nota con frontmatter completo | Requiere estructura y claridad |
| Revisar código | Comparar dos versiones de una función | Requiere entendimiento semántico |

### ✅ Usa Modelo de Razonamiento para:

| Tarea | Ejemplo | Por qué |
|-------|---------|---------|
| Arquitectura | Diseñar el sistema de plugins | Requiere visión sistémica |
| Decisiones de diseño | Elegir entre dos enfoques de implementación | Requiere trade-offs |
| Depuración compleja | Encontrar causa raíz de un fallo intermitente | Requiere rastreo lógico profundo |
| Planificación | Crear un plan de implementación de 6 fases | Requiere anticipación de dependencias |

---

## 📊 Matriz de Decisión Rápida

| ¿Qué necesitas hacer? | Modelo recomendado | Contexto estimado |
|-----------------------|-------------------|-------------------|
| "¿Qué notas existen?" | Ligero | ~2 KB |
| "¿Cuál es el estado actual?" | Ligero | ~1 KB |
| "Escribe un script de validación" | Estándar | ~5-10 KB |
| "Arregla este test que falla" | Estándar | ~5-15 KB |
| "Diseña el sistema de plugins" | Razonamiento | ~10-20 KB |
| "Encuentra por qué el test falla" | Razonamiento | ~10-25 KB |
| "Planifica la próxima fase" | Razonamiento | ~10-15 KB |

---

## 🔍 Cómo Aplicar el Enrutamiento

### Antes de pedir algo al agente:

1. **Identifica el tipo de tarea** (ligera / estándar / razonamiento)
2. **Proporciona solo el contexto necesario** para ese tipo
3. **No cargues archivos completos** si un resumen o digest basta

### Ejemplos de Buena Práctica

#### ❌ Mal: Pedir demasiado contexto para una tarea simple

```
"Lee todo CHARACTER_IMPORT.md (314 líneas), todas las notas de bag1-character.md (227 líneas), y dime cómo importar un personaje."
```
**Problema:** ~30 KB de contexto para una tarea que podría resolverse con 5 KB.

#### ✅ Bien: Contexto específico y mínimo

```
"Necesito importar un nuevo personaje. Lee IMPORT_STANDARD.md (8 KB) y _work/current-state.json (0.4 KB) para entender el flujo y el estado actual."
```
**Solución:** ~8.4 KB de contexto, tarea resuelta igual de bien.

---

## 📏 Medición y Monitoreo

Para verificar que el enrutamiento funciona:

```bash
# Medir tamaño de contexto antes de una tarea
py tools/workflow/measure_context.py --detailed

# Ver uso de tokens en la sesión actual (si el agente lo soporta)
# Ejemplo: /cost en Claude Code
```

### Objetivos de Contexto por Tipo de Tarea

| Tipo de Tarea | Contexto Máximo Recomendado |
|---------------|----------------------------|
| Ligera (búsqueda, resumen) | < 5 KB |
| Estándar (implementación, corrección) | < 15 KB |
| Razonamiento (arquitectura, planificación) | < 25 KB |

---

## 🔄 Rotación de Sesiones

> "Nuevos hilos para nuevo contexto" — Towards Data Science, Ene 2026

| Situación | Acción |
|-----------|--------|
| Terminaste una tarea y empieza otra diferente | Nueva conversación |
| El contexto se siente "contaminado" con información irrelevante | Nueva conversación |
| Has cambiado de personaje o de característica | Nueva conversación |
| Solo necesitas hacer una pregunta rápida | Mismo conversación, usa modelo ligero |

**Regla:** Si el contexto acumulado supera los 20 KB y no es relevante para la tarea actual, inicia una nueva conversación.

---

## 🛠️ Herramientas de Apoyo

| Herramienta | Propósito | Comando |
|-------------|-----------|---------|
| `measure_context.py` | Mide tamaño de contexto de inicio | `py tools/workflow/measure_context.py --detailed` |
| `token-report.py` | Reporta uso de tokens por sesión | `py tools/workflow/token-report.py` |
| `validate_frontmatter.py` | Valida notas sin cargar contenido completo | `py tools/workflow/validate_frontmatter.py` |
| `generate_digests.py` | Crea resúmenes de archivos grandes | `py tools/workflow/generate_digests.py --all` |

---

## 📊 Objetivos de Ahorro de Tokens

| Área | Antes | Después | Ahorro |
|------|-------|---------|--------|
| Contexto de inicio (tarea general) | ~80 KB | ~7.8 KB | 90% |
| Contexto de inicio (importación) | ~80 KB | ~16 KB | 80% |
| Preguntas simples | ~20 KB (cargar notas completas) | ~2 KB (usar índice/digest) | 90% |
| Búsqueda de archivos | Cargar directorio completo | Usar NOTES.idx o grep específico | 95% |

---

*Última actualización: 2026-11-01*
