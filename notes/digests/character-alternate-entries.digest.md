---
id: character-alternate-entries-digest
title: "Alternate entry integration digest"
tags: ["digest", "character", "payload"]
summary: "Checklist de integración DFS/DUMMY y límites antes de desplegar otro personaje."
related: ["notes/character-alternate-entries.md", "notes/character-import-testing.md"]
created: "2026-11-02"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: digest
source: "notes/character-alternate-entries.md"
source_sha256: "f344113a7c6a4d2ceb3456204ba26326ec3c781c4d4099998fd871c6bba12a78"
---

# Integración: resumen

- Inventariar pack/modelo por lado/traje y hash de miembro; conservar stock DBI
  salvo evidencia específica. No copiar parches Heat ni IDs Strike.
- `rebuild_dfs_members.py --spec <json> --root .`: offsets efectivos y lectura
  posterior; alinea inicios a 4 B sin incluir padding en tamaños. No preserva
  huecos originales; el lector no exige alineación, comprobar offset % 4 aparte.
- Preservar entradas ya aceptadas del payload viejo usando **alt_size**, no
  leerlas del disco stock. Hash por fila antes/después, no solo count.
- `make_alt_entries_exact.py <disc> <rows.json> <out>`: bytes exactos, sectores
  2048, deduplicación; jamás truncar alternativas mayores que stock.
- El generador canónico ya usa capacidad en bytes por cambios previos, no el
  build divergente. Sigue obligatorio validar `payload_bytes <= DUMMY extent
  bytes` aparte; revisar count/IDs únicos/kind/chr y tabla 4096 B.
- Manifest `disc_user` absoluto; índice relativo a BUST2; raw2352 es otro espacio.
- SHA payload ≠ expected SHA de bytes originales reemplazados.
- Opciones/plugin no son genéricos por añadir una fila. Strike está bajo
  feature `bag1-heat`; no existe `bag1-strike`.
- Sincronizar mods-src→build/src y recursos→mods/preloaded antes de build.
  Luego revisar build/bundled→experimental por hashes. Backup coherente para rollback.
- Fallo Strike VS: offsets DFS iguales; tamaño correcto/modelo visible no bastaban.
- Scripts ad-hoc `_work/` son evidencia de rescate/experimentos, no recetas a clonar.
