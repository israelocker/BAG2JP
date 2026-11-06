---
id: ps1-community-tools-install
title: "Instalación aislada de herramientas PS1"
tags: ["tools", "installation", "validation"]
summary: "Instalar las herramientas recomendadas con versiones fijas; validar su utilidad después, por tarea y con evidencia."
related: ["notes/assets.md", "notes/documentation-audit.md"]
created: "2026-11-06"
updated: "2026-11-06"
edited: "2026-11-06"
doc_kind: plan
---

# PS1 community tools installation

Owner authorization: «Okay instala todas esas herramientas y las iremos probando
a lo largo del desarrollo y validaremos si realmente nos dan resultados positivos o no».
Scope: the recommended tools from the preceding report, not its deferred alternatives.
Existing PCSX-Redux and Ghidra/PsyQ are reused; no runtime or analysis upgrade.

## Decisions

- Portable installs under `D:/Dev/Tools/ps1-community/`; no global PATH or system Python changes.
- Upstream release binaries: jPSXdec v2.1 (asset labelled beta), mkpsxiso/dumpsxiso v2.30,
  TIMedit 0.10a. Verify available upstream SHA-256; otherwise record local hash and its limit.
- Python tools in a dedicated Python 3.13 environment: spimdisasm 1.42.4,
  m2c commit c632946b8cfbe8fce442b522dba92dfa72f1f317,
  asm-differ commit 0dd09af8f8008f1f880327cf0aca3b26d2562ea2.
- Existing Ghidra 12.1.4 PSX loader/PsyQ data stay unchanged. Existing PCSX-Redux
  is recorded only; no emulator launch, server activation or reference replacement.
- Dependencies remain isolated and are recorded by exact installed versions.

## Steps

| Step | Acceptance / verification | Files / seam | Blocked by | State |
| --- | --- | --- | --- | --- |
| 1 (S) | Git/preflight and Ghidra MCP identify current JP executable; inspect existing installs | `_work/workflow/`, MCP, extension properties | none | Passed |
| 2 (S) | Download pinned portable archives, check hashes and safe extraction, retain licenses | `_work/tool-install/`, new external tool directories | 1 | Passed; TIMedit has no upstream digest |
| 3 (S) | Inspect packaging, create isolated venv, install pinned Python tools and retain dependency versions | new external venv/source directories, installation log | 1 | Passed; pip check exit 0, exact versions retained |
| 4 (S) | CLI help/version or GUI startup proves basic availability without loading personal assets | smoke logs / task-owned empty working directory | 2, 3 | Passed; asm-differ needs the guarded task-local config |
| 5 (S) | Existing canonical note records commands, limitations and future comparison criteria; doc checker passes | `notes/assets.md`, plan, project config reference | 4 | Passed; 114 documents, 0 errors, 9 historical warnings |

## Always / never

Always distinguish downloaded, installed, smoke-tested and validated on BAG2JP.
Record each failure rather than claiming all tools work. Future trials compare
identical input hashes, correctness, manual work and elapsed time; retain negative results.
Never alter discs, saves, game installs, framework pins, active Ghidra analysis or
global settings. No new emulators, marketplace skills or deferred tools in this scope.
No claim of faster imports or fidelity from installation alone.

## Evidence

- Preflight: `_work/workflow/20261106T040126893069Z-ps1-community-tools/metrics.json`.
- Ghidra MCP: SLPM_862.19 SHA-256 ea5a166863f1b52782107680270f3879a8f069b1c0df6029b1db164087851efe;
  bounded `InitHeap` lookup returned 0x80049f44. No analysis changes.
- Installation results and smoke logs: `_work/tool-install/` (created during execution).

## Execution record

Six new tools installed. jPSXdec/dumpsxiso/spimdisasm/m2c help returned 0;
TIMedit's task-owned empty window opened and closed with exit 0. asm-differ first
failed because it imports task-local `diff_settings.py` before parsing `--help`;
the same help invocation passed with a guarded smoke fixture, with both results retained.
No vendor source patches, global packages or new emulators. Existing PCSX-Redux
and Ghidra/PsyQ preserved. Windows wheels were used instead of introducing a Linux
compiler/header dependency. Installed dependency versions and PyPI artifact hashes retained.
Real comparisons remain pending: asm-differ needs a verified MIPS objdump backend
and task-specific configuration; optional Graphviz dot was not installed.

Canonical reuse/status/trial protocol: `notes/assets.md`.
Durable external manifest: `D:/Dev/Tools/ps1-community/installation-manifest.json`.
Final documentary verification: `py -3.13 tools/workflow/audit_docs.py check --root D:/Dev/Recomp/BAG2JP --output D:/Dev/Recomp/BAG2JP/_work/tool-install/docs-check.json`.
No fresh gameplay campaign and no runtime snapshot are implied by this tooling milestone.
