---
id: coding-standards-digest
title: "Estándares de desarrollo: resumen vigente"
tags: ["digest", "standards", "config"]
summary: "Requisitos de código/evidencia y configuración central obligatoria; distingue valores operativos de constantes nativas y no certifica cumplimiento del legado."
related: ["docs/coding-standards.md", "system_config.md", "docs/data-dictionary.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: digest
source: "docs/coding-standards.md"
source_sha256: "5b02608d4bdd411aa00173794016a5d2fccc7a2445ce705e2bbc88fcd5d57bd1"
---

# Estándar de desarrollo

- Aplica a código nuevo/modificado; no afirma que todo el legado ya lo cumpla.
- C: constantes nombradas, validación temprana, responsabilidad clara y explicar
  el porqué; verificar región/módulo/palabras antes de modificar MIPS.
- Python: tipos y docstrings públicos, pathlib, logging y excepciones específicas.
- Desde 2026-11-15, rutas de entorno y valores operativos configurables del código
  host (herramientas/generadores) salen del
  resolutor único `project_config.py`: defaults portables en TOML común, ubicaciones
  verificadas en local ignorado. Sin parser duplicado ni fallback de máquina.
- Reutilizar claves por significado. Nuevas claves requieren registro, significado,
  tipo/unidad, default/origen, validación, permisos, operaciones, consumidores y tests
  en el diccionario. Exigir solo claves usadas y proteger destinos antes de efectos.
- No convertir datos PSX, IDs, hashes, formatos, fixtures sintéticos ni guards de
  aceptación en ajustes libres. Runtime/título conservan su parser, sin Python host.
  Las excepciones se justifican por su autoridad; la tabla de settings es ilustrativa,
  no esquema host ni evidencia de rangos aceptados por el runtime vigente.
- Auditoría incluye herramientas de paquetes/generadores/dependencias reales de
  pruebas; preservar evidencia histórica, releases, saves/settings y terceros.
- Pruebas discriminantes RED→GREEN, baseline de fallos por causa, costura relevante
  y procedencia/hashes. Juego necesita su flujo aceptado; host no lo sustituye.
- Estado de migración: `system_config.md`; esta regla no certifica cumplimiento.
