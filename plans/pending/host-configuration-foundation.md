---
id: host-configuration-foundation-plan
title: "Configuración host: base compartida y piloto de lectura"
tags: ["plan", "config", "dictionary", "testing"]
summary: "Plan pendiente de aprobación/ejecución: resolver común/local, diccionario y piloto check_payload_manifest; demás consumidores en lotes posteriores."
related: ["docs/superpowers/specs/2026-11-15-host-configuration-design.md", "system_config.md", "docs/paths.md", "AGENTS.md"]
created: "2026-11-15"
updated: "2026-11-15"
doc_kind: plan
---

# Host Configuration Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or
> executing-plans according to the owner's selected method. Steps use checkbox
> syntax. BAG2JP/AGENTS overrides imported branch/push/PR/snapshot workflows.

**Goal:** entregar una configuración host validada y documentada, utilizada por un
primer consumidor real de solo lectura, sin modificar juego, build ni instalaciones.

**Architecture:** TOML común versionado + TOML local ignorado; un resolutor Python
inmutable con JSON para PowerShell. Campos nativos siguen en perfiles/contratos.

**Tech Stack:** Python3.13, stdlib/tomllib/unittest; PowerShell instalado para la
prueba de interoperabilidad. Sin dependencias ni instalación nuevas.

**Spec:** [diseño aprobado](../../docs/superpowers/specs/2026-11-15-host-configuration-design.md).
Owner aprobó alcance/diseño y luego especificación con «si». Este plan y el método
de ejecución todavía requieren su aprobación. No iniciar implementación aquí.

## Global Constraints

- Solo herramientas host; no runtime C, paquetes, assets, settings, tarjetas,
  state de mods, builds, partidas ni conexiones. Ninguna autorización implícita.
- Inglés para nombres/código; español para comunicación y documentación.
- `schema_version=1`; raíz desde módulo, no CWD; overlay local por clave, no tablas
  enteras; versión local, si existe, debe coincidir. Sin capa nueva de env vars.
- Claves/tipos desconocidos o override local de política fallan antes de efectos.
  `build.jobs=2`; pins comunes conservan valores actuales, no se cambian por este lote.
- No fallback a rutas viejas ni strings ejecutables. Config local no autoriza
  acciones y no demuestra seguridad si el usuario etiqueta mal ambas instalaciones.
- CLI anterior y guards se conservan. No alterar defaults de audio/captura, schemas
  de perfiles1/2 ni allowlists. Escrituras de pruebas solo en fixtures propias.
- RED debe importar/compilar y fallar por aserción del caso, no por import roto.
  Goldfish según lista canónica antes del checkpoint aplicable; no repetir sin cambios.
- Plan de alcance deliberado: base + piloto. No declarar cero hardcodes globales
  ni todos los consumidores migrados cuando este plan termine.

## Evidence and Scope

Inventario `_work/configuration/tracked-path-inventory.json`:48 archivos/95
coincidencias textuales de drive/mount en fuentes/config versionados. Incluye
comentarios/fixtures y puede omitir rutas construidas con home; no son95defectos.
El listado completo se conserva y se reclasifica en cada lote, sin barrido destructivo.

Consumidor piloto: `tools/bag1import/check_payload_manifest.py`; `check(package)`
ya es lectura pura. Su CLI permite múltiples `--package` y por defecto comprueba
las cuatro copias actuales. No confundir ese número con regla de todos los paquetes.

Dependencia posterior comprobada: `D:/Dev/Tools/codex-integrations/build_bag2jp.sh`
tiene6líneas, toolchain y árbol absolutos y `-j 2`. No consume un build_root externo.
Workflow no se migra suponiendo que ese script respeta config; necesita su lote y
adaptador reproducible dentro del alcance, nunca edición silenciosa de la herramienta
instalada. El harness tampoco se toca para demostrar esta primera entrega.

## Review Focus

1. Config parcial/ausente: `inspect` funciona sin discos/tools; el consumidor exige
   solo sus claves. Overrides ilegales fallan incluso si otra operación no los usa.
2. CWD/prioridad: config relativa ancla al repo; `--package` conserva su semántica
   relativa al CWD y evita requerir ubicaciones default que no necesita.
3. Alias/contención: destino estable o alias se rechaza por el helper de escritura,
   incluso si el texto de la ruta parece otro; ningún test toca la instalación real.
4. JSON/PowerShell/WSL: espacios/Unicode/metacaracteres permanecen datos y argumentos;
   conversión no soportada falla, sin `eval`, `Invoke-Expression` ni shell libre.
5. Temporalidad: no cargar rutas locales al importar el consumidor ni guardar un
   objeto mutable global que mezcle dos configuraciones/operaciones.

## File Map (future files are not present yet)

```text
config/project.toml                           common defaults/policy
config/project.local.example.toml             commented portable local template
config/project.local.toml                     actual local paths; ignored
tools/workflow/project_config.py              schema, resolution and pure adapters
tools/workflow/test_project_config.py          isolated core/CLI regression suite
docs/data-dictionary.md                       catalog of fields and native references
tools/workflow/test_data_dictionary.py         schema/dictionary consistency
tools/test/test_payload_manifest_config.py    pilot regression suite
```

Modify only `.gitignore`, the pilot script and authoritative docs/digests in these
tasks. Do not create another config parser or a general service/container framework.

## Shared Interfaces

The new module owns these names (future code; definitions locked for the tasks):

```python
class ConfigError(ValueError): ...
# frozen dataclass; mappings are read-only, not just a frozen mutable dict
class ProjectConfig:
    repo_root: Path
    values: Mapping[str, Path | str | int]       # flattened dotted keys
    origins: Mapping[str, str]                 # common/local/derived per key
    input_hashes: Mapping[str, str | None]      # common/local/schema; missing local=None
    input_files: Mapping[str, str | None]       # paths actually read; schema is the resolver

def load_config(*, repo_root: Path | None = None,
                local_config: Path | None = None) -> ProjectConfig: ...
def require_paths(config: ProjectConfig, keys: Sequence[str]) -> tuple[Path, ...]: ...
def assert_write_target(config: ProjectConfig, target: Path, *, role: str) -> Path: ...
def to_wsl_path(path: Path) -> str: ...
def export_config(config: ProjectConfig, *, operation: str) -> dict[str, object]: ...
def main(argv: Sequence[str] | None = None) -> int: ...
```

`FIELDS` is one immutable registry of spec field names/type/unit/local-override
permission/path-role/operation-use; defaults remain in TOML, not a second set of
absolute-path constants. Dictionary tests use this registry. Register all initial
spec fields, explicitly marking consumers planned vs adopted. Native symbols are
cross-references, not configuration values or new fields in a character profile.

### Task 1: common/local resolver (M; Blocked by: none)

Files: create common/template TOML and core module/test above; modify `.gitignore`
to ignore exactly the real local config, not the whole config directory.
Produces `ProjectConfig`, `ConfigError`, `FIELDS`, `load_config`, `require_paths`.

- [ ] Write tests named `test_local_overlay_preserves_other_common_keys`,
  `test_policy_cannot_be_overridden_locally`, `test_wrong_schema_and_unknown_key`,
  `test_bool_is_not_build_jobs`, `test_bool_is_not_schema_version`,
  `test_path_literal_nul_rejected`, `test_partial_config_and_missing_local`,
  `test_relative_paths_ignore_cwd`, `test_loaded_mappings_are_immutable` and
  `test_load_does_not_create_dirs_or_processes`. Expected jobs2, exact common pins
  `1a3fc0db`/`3f1d6f1` (preserve current prefix semantics), work_root=repo/_work.
  Missing requested path raises ConfigError naming the key; unused missing path
  is not invented. Hashes identify exact common/local bytes and, for `schema`,
  bytes of the resolver module implementing FIELDS/validation; export all three.
  Representative assertions inside the owned fixture:
  ```python
  self.assertEqual(cfg.values["build.jobs"], 2)
  self.assertEqual(cfg.values["paths.work_root"], root / "_work")
  self.assertEqual(cfg.values["pins.recomp_ui"], "3f1d6f1")
  with self.assertRaises(ConfigError):
      require_paths(cfg_without_inputs, ("inputs.bag1_jp_disc",))
  ```
- [ ] Supply importable minimal stubs after writing tests; run
  `py -3.13 -m unittest tools.workflow.test_project_config -v`. RED must be an
  assertion on behavior, not module-not-found. Keep failed output for the seam.
- [ ] Implement typed parsing, schema/type checks (including bool vs int), permitted
  per-key overlay and immutable output. Common policy is not locally overrideable.
  Discover module root by file; optional repo_root exists for isolated fixtures.
  Treat path values as literals, not interpolation or commands. No live FS writes.
- [ ] Run the same command GREEN. Test fixtures use unique owned dirs under repo
  `_work/`; do not depend on real discs, settings, installed game or user home paths.
- [ ] Verify `git check-ignore` excludes actual local config but not common/template.
  Freeze this source for checkpoint with Task2, not a premature runtime acceptance.

### Task 2: safe path/JSON adapters (M; Blocked by: Task1)

Files: same core module and test. Produces remaining Shared Interfaces.
Consumes immutable load result; does not invoke games/builds or authorize actions.

- [ ] Add RED cases `test_stable_alias_and_overlap_are_not_writable`,
  `test_unknown_write_role_or_missing_protected_root`, `test_nonexistent_child_uses_resolved_parent`,
  `test_windows_drive_to_wsl_spaces_unicode`, `test_unsupported_conversion_fails`,
  `test_json_keeps_sources_and_unresolved_fields`, `test_two_loads_do_not_share_state`.
  Probe lexical/physical containment, case-insensitive Windows paths and symlink/
  junction aliases where supported. Unsupported native alias testing is a declared
  missing check, not green; do not install features or request privilege to fake it.
- [ ] Run core test command; require behavioral RED. Implement write roles `work`,
  `build`, `experimental`: require their configured root and stable_install, reject
  stable/ancestor/descendant conflicts and targets outside the requested root.
  Resolve the existing filesystem ancestry, not just string prefixes. A validation
  result is not immunity to a later filesystem race; callers retain their own guards.
- [ ] Implement converter for verified local Windows drive paths to `/mnt/<drive>`;
  reject ambiguous drive-relative/device/unsupported paths instead of guessing a mount.
  Conversion alone does not prove a WSL mount/tool is available: that remains a
  consuming-operation preflight, never a reason to create mounts or install tools.
  `assert_write_target` returns a checked Path, never writes/creates it.
  ```python
  self.assertEqual(to_wsl_path(Path("D:/Space ñ/one file")),
                   "/mnt/d/Space ñ/one file")
  with self.assertRaises(ConfigError):
      assert_write_target(cfg, stable / "BAG2JP.exe", role="experimental")
  ```
- [ ] Implement CLI `--local-config`, `--operation inspect|payload-manifest` (default
  inspect), JSON stdout on success, diagnostic stderr and exit2 on ConfigError.
  Export schema_version1, repo_root, resolved values/origins, config hashes and
  missing/unresolved keys; unused missing keys are explicit, not substituted.
- [ ] Test CLI in a subprocess from another CWD and consume JSON using installed
  PowerShell `ConvertFrom-Json` with structured argv. Assert identical paths/hashes;
  a path containing `;`/`&` must remain data, not cause a shell action. No parser
  duplicated in PowerShell. If PowerShell is unavailable, report that integration
  unverified; never claim support from a JSON-only test.
- [ ] GREEN core/CLI suite. Goldfish of frozen Tasks1–2 + checkpoint under AGENTS;
  no duplicate review of unchanged inputs and no generic branch/rebase/push workflow.

### Task 3: dictionary and actual local setup (S; Blocked by: Task2)

Files: create dictionary/test from File Map; populate ignored local config only if
absent, using the currently verified paths. Existing local config is user work:
compare/report, never overwrite it. No settings/card writes.

- [ ] Write RED dictionary tests: every FIELDS key has meaning/type/unit/origin/
  default-or-local-source/validation/consumer/status; no undocumented schema keys,
  mismatched units or false claim that a planned consumer is already migrated.
- [ ] Add registry-driven dictionary rows for the spec fields. For native/shared
  data include references to current profile schema, cue/entry/layout contracts and
  policy, not copies of addresses as editable TOML. Unit test names and source
  references must identify config data vs verified native facts vs pending evidence.
- [ ] Record machine values in ignored local config from prior consumers and
  `docs/paths.md`; print a proposed equivalence map before accepting that file.
  Never change installations to satisfy config, infer a missing runtime or activate
  any feature. Fields not verified remain unset/diagnosed for operations needing them.
- [ ] GREEN: `py -3.13 -m unittest tools.workflow.test_data_dictionary tools.workflow.test_project_config -v`.
  Validate actual config with inspect only; retain resolved map and hashes under
  `_work/configuration/`. Do not put local paths into the portable common/template.

### Task 4: manifest-checker pilot (S; Blocked by: Task3)

Modify `tools/bag1import/check_payload_manifest.py`; create pilot test from File Map.
Keep `check(package)` semantics and no subprocess/write side effects.

Produces:
```python
def default_packages(config: ProjectConfig) -> tuple[Path, ...]: ...
def main(argv: list[str] | None = None) -> int: ...
```

- [ ] RED cases: default copies derive from repo/build/experimental roots; explicit
  repeated `--package` checks only requested paths; partial config works when those
  defaults are unused; invalid config fails before package access; importing module
  neither loads local config nor caches the four machine paths; two CLI calls can
  use different local configs without leakage.
- [ ] Sandbox case: four fake package dirs with manifests/payloads, one corrupted
  payload, one missing member; preserve per-package OK/FAIL text, summary and exit0/1.
  CLI syntax/config error remains exit2. Do not use real bundled packages as output.
- [ ] Implement derived tuple: repo/mods-src/PACKAGE, build/mods/preloaded/packages/
  PACKAGE, build/build-win-codex/mods/bundled/PACKAGE, experimental/mods/bundled/PACKAGE.
  Keep PACKAGE/overlay identity as game/package constants, not editable machine paths.
  Config roots needed in default mode: build_root and experimental_install. Missing
  manifest/payload remains a per-copy FAIL, not silently skipped by pre-validation.
- [ ] Add `--local-config` without breaking repeated `--package` or their existing
  relative-to-CWD semantics. Default mode uses resolved config; explicit mode does
  not require unused default roots. No fallback to DEFAULT_PACKAGES hardcodes.
- [ ] GREEN: `py -3.13 -m unittest tools.test.test_payload_manifest_config tools.workflow.test_project_config tools.workflow.test_data_dictionary -v`.
  Capture diagnostics/config provenance in the regression report; do not change the
  established normal OK/FAIL stdout contract just to add a new status format.

### Task 5: acceptance, docs and checkpoint (S; Blocked by: Task4)

Modify `system_config.md`, `docs/paths.md`, existing workflow/character integration
notes only where the pilot's authority changed, plus affected digests. Record each
remaining literal/consumer as planned, fixture, historical, native or unresolved.

- [ ] Run targeted suites above and unchanged
  `py -3.13 tools/workflow/test_bag2_workflow.py`; previous workflow behavior must
  remain unchanged because it is not migrated here. Use existing baseline for
  unrelated discovery failures; no broad suite reruns without changed inputs.
- [ ] Demonstrate relocated-root fixture + different CWD + local override + bad
  config no-effects. Confirm migrated pilot has no machine-specific drive literal
  and original input hashes/installed/config/save files were not changed by tests.
- [ ] Optional real checker use is READ ONLY, if current config/inputs permit;
  distinguish pre-existing package mismatches from loader regressions. Sandbox
  acceptance remains mandatory and reproducible; no game/build required.
- [ ] Documentary checker and digest SHA, exact diff, Goldfish on task-owned frozen
  inputs with spec/plan. Classify findings, correct at same seam; capture any omitted
  platform checks. No claims of time savings or migration of other consumers.
- [ ] Local checkpoint with explicit file list, update canonical config note and
  next_action; archive this plan only when its deliverables pass. No heavy project
  snapshot for a host-tool checkpoint and no remote publishing.

## Subsequent Migration Roadmap (not executable tasks in this first plan)

| Next lot | Prerequisite and preserved boundary |
|---|---|
| Workflow/build/report | Baseline config + handling of fixed installed Bash root/toolchain; tests of actual argv/metadata, no false new-target build claim |
| PowerShell harness + versus | Adopt JSON/helper and phase-specific keys; preserve CLI, calibrated inputs, process ownership, allowlists, cards and restoration; offline tests before any authorized game proof |
| Capture/FFmpeg/reference tools | Preserve backend defaults, clock/audio gates, selected process and shutdown ordering; no config-based relaxation |
| Importers/profiles | Inventory fields/readers; explicit compatible schema migration and path references, preserving assets/evidence hashes and region/side meaning |
| Remaining tracked candidates | Classify complete inventory and verify actual consumers before a bounded migration; external scripts and `_work/` history are not bulk rewritten |

These lots require their own concrete plan before execution; completion of this
foundation does not satisfy their migration or runtime acceptance. They preserve
the already-approved host-first design, not a request to reopen all decisions.

## Spec coverage and self-review

- Spec1–4: fields/authority/separation → Tasks1/3; no profile/runtime move.
- Spec5: precedence/operation requirements/JSON/WSL → Tasks1/2/4.
- Spec6: dictionary + native references → Task3; profile path removal is the roadmap lot.
- Spec7: side effects/roles/traceability → Tasks1–5, with configured-root trust limits declared.
- Spec8: lot acceptance → Task5; broad migration remains explicitly unimplemented.
- Spec9: this written plan and method need approval before any code.

Self-review: consistent API names/types across tasks; five Review Focus cases have
owning tests; no undefined behavior or unowned implementation step. Tests/expected outputs
above are future instructions, not results from this planning session.

## Progress

| Task | Status |
|---|---|
| 1. Resolver | Done: 41-test suite green, Goldfish applied |
| 2. Adapters/guards | Done: guards mutation-killed, Goldfish applied |
| 3. Dictionary/local setup | Not started |
| 4. Manifest pilot | Not started |
| 5. Acceptance/checkpoint | Not started |
