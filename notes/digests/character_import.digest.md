# CHARACTER_IMPORT.md Digest

**Source:** `CHARACTER_IMPORT.md` (~10 KB, 314 lines)

## Resumen
Manual canónico para importar cualquier personaje BAG1 a BAG2JP. Es el único documento que un nuevo chat debe leer antes de importar un personaje (después de AGENTS.md y NOTES.md).

## Secciones Clave

| Sección | Línea | Propósito |
|---------|-------|-----------|
| 1. Qué significa éxito | 7 | Criterios de aceptación para completar importación |
| 2. Reglas no negociables | 26 | Reglas duras del proyecto |
| 3. Herramientas estándar | 43 | Comandos de preflight y build |
| 4. Orden de comandos requerido | 62 | Flujo paso a paso (1-5) |
| 5. Schema de perfil | 121 | Campos requeridos del perfil |
| 6. Reglas de inventario | 147 | Verificación antes de conversión |
| 7. Reglas de contrato de animación | 164 | Mapeo de roles semánticos |
| 8. Reglas de audio | 180 | Gestión de cues y voices |
| 9. Reglas de assets y paquete | 190 | Generación de candidatos |
| 10. Matriz de aceptación | 200 | Casos base y condicionales |
| 11. Disciplina de pruebas | 223 | Reglas de testing |
| 12. Evidencia y contexto | 234 | Estructura de directorios y estado |
| 13. Adapters específicos de Heat | 258 | Legado, no reglas generales |
| 14. Modos de fallo comunes | 273 | Errores a evitar |
| 15. Checklist de completado | 287 | Lista final antes de cerrar |
| 16. Mínimo inicio de chat | 303 | Comandos de inicio |

## Flujo Paso a Paso (Sección 4)

| Paso | Comando | Propósito |
|------|---------|-----------|
| 1 | `init-profile` o `validate-profile` | Crear o validar perfil |
| 2 | `plan` + `acceptance-plan` | Verificar gaps |
| 3 | `prepare` | Crear candidato (no deploy) |
| 4 | `cache-record` | Registrar evidencia de referencia |
| 5 | `cache-check` | Verificar cache (hit/miss) |

**Regla crítica:** Si `gaps` no está vacío, NO preparar.

## Reglas No Negociables (Sección 2)

- Trabajar solo en `D:/Dev/Recomp/BAG2JP`
- Build solo en `D:/Dev/Recomp/BAG2JP-codex-build/BAG2JP`
- Deploy/test solo en `D:/Games/Bust A Groove 2 (Japan)/BAG2JP-exp-8mb`
- NUNCA tocar `BAG2JP-win` sin permiso explícito del owner
- Nunca publicar ni subir
- No reclamar importación por existir un profile
- No copiar el pipeline de Heat para otro carácter
- No ejecutar comandos almacenados en un profile
- No auto-deployar assets candidatos
- No generalizar fixes específicos de Heat (huesos, DBI, cues, stage)
- Mantener roles no resueltos sin adaptación documentada

## Schema de Perfil (Sección 5)

**Campos requeridos:** schema, character, display_name, source_character_id, target_character_id, stage, exception_assessment, source_animation_list, game_catalog, reference_runtime, capabilities, exceptions, assets, validation_evidence.

**Perfiles son datos únicamente** - sin código ejecutable ni instrucciones de deploy.

## Reglas de Animación (Sección 7)

- Match por rol semántico primero
- Preservar duración musical en beats
- Preservar eventos requeridos: audio, efectos, lanzamientos, voces
- Separar: pasos normales, especiales, poses sostenidas, ataques, defensas, hit reactions, estados de cansado, knockdown, recuperación, wins, losses, fever
- Mantener predecessor dispatch original como check independiente
- Reportar todas las entradas source y target
- Reportar duplicados, motions sin uso, contrapartes faltantes, entradas vacías, repeticiones deliberadas
- Si un rol target no existe en source, marcar como unresolved
- No mapear hit reaction fallido a defensa exitosa silenciosamente

## Reglas de Audio (Sección 8)

- Cada carácter tiene su base de cues
- Rebasear cues de BAG1 cuando sea necesario
- Detectar colisiones en mirror matches
- Preservar nombres de announcer de victoria solo cuando el carácter existe en ambos juegos
- No asumir que un segundo banco VAB carga
- Mantener cues de fever muteados cuando corresponde

## Matriz de Aceptación (Sección 10)

**Casos base (siempre):**
- inventory validation
- model on both sides and both costumes
- game flow
- song end
- return to selection

**Casos condicionales (si capability es true):**
- costume selection
- mixed-version match
- solo fever
- duet fever
- stage load
- ending video, credits, dance and return
- announcer name
- online content identity

## Modos de Fallo Comunes (Sección 14) - EVITAR

- Tratar números de request iguales como roles iguales
- Tratar conversión que funciona como importación exitosa
- Ocultar roles no resueltos con sustituciones plausibles
- Asumir que un segundo banco VAB carga
- Asumir que esqueletos BAG1 y BAG2 coinciden
- Asumir que BAG1 tiene mismos costumes, stages, songs o nombres de announcer
- Tratar evidencia visual cacheada como prueba de gameplay
- Declarar completado antes de que un match completo regrese a selección
- Repetir navegación manual cuando hay índices observados disponibles
- Re-running el mismo log o suite sin nueva evidencia

## Checklist de Completado (Sección 15)

Antes de cerrar una importación de carácter:
- [ ] Profile validates
- [ ] Plan has no gaps
- [ ] Candidate prepared
- [ ] Required acceptance cases pass
- [ ] Fresh gameplay evidence recorded
- [ ] Settings and cards preserved
- [ ] Source and candidate hashes recorded
- [ ] Notes updated with current state and evidence
- [ ] Read-only review performed
- [ ] Local commit contains only task-owned changes
- [ ] Snapshot refreshed after all related work
- [ ] Stable installation untouched

## Mínimo Inicio de Chat (Sección 16)

```powershell
& $PY $HELPER preflight --tag <task>
py -3.13 tools/bag1import/character_workflow.py validate-profile --profile tools/bag1import/profiles/<slug>.json
py -3.13 tools/bag1import/character_workflow.py plan --profile tools/bag1import/profiles/<slug>.json
```

Luego leer este runbook y solo las notas relevantes. NO reconstruir el proyecto de conversaciones antiguas.

## Referencias Rápidas
- `notes/character-pipeline.md` - Referencia técnica detallada
- `IMPORT_STANDARD.md` - Guía de tarea estándar
- `tools/bag1import/character_workflow.py` - Herramienta de workflow
- `tools/bag1import/profiles/` - Perfiles por carácter