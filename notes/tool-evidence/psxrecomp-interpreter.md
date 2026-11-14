---
id: tool-evidence-psxrecomp-interpreter
title: "Evidencias: intérprete PSXRecomp como prueba host"
tags: ["tools", "evidence", "mips"]
summary: "Pruebas acotadas de instrucciones reales en dirty_ram_run_span; no equivalen a aceptación del juego."
related: ["notes/gaso-import.md", "notes/assets.md"]
created: "2026-11-13"
updated: "2026-11-13"
doc_kind: evidence
---

# PSXRecomp interpreter — historial

## 20261113-interpreter-fan — cálculo y ruta del nivel

- Propósito: contrastar las instrucciones originales/portadas del ventilador,
  no duplicar el motor en Python. Se reutilizó fixture_link y el shim de RAM
  ya verificado del controlador; ninguna partida/proceso de juego abierto.
- Comando: `wsl.exe -d Ubuntu --exec python3 /mnt/d/Dev/Recomp/BAG2JP/_work/gaso/stage-fan/run_interpreter_probe.py`.
  Compila el probe con GCC y fuentes reales GPU/mod_immediate/dirty_ram_interp;
  aborta en seams inesperados. El tramo no llega a render ni callees externos.
- Versión/hash local dirty_ram_interp.c:
  7439cdbb38d8142ab4719d7a9667e16259e7edc27273962b43f67f9de9f8f8b7.
  Entradas: stage-fan/before/native-usa-fan.bin y ported-fan.bin;
  candidato-v2/ported-fan.bin. DBI original USA SHA0d3a49731d5d44f62e108ce925aa37fafc044896a3e7ce5ab80f1efdc430a320;
  candidato DFS00d613392023b33655dfce425cfda0f6a7cbd536e17a74bbadd6776a7f7d02e6.
- 144casos por variante: tres niveles,8 velocidades cerca de topes, delta-1..4,
  wrapu16 y80070108 envenenada. Assertions: nativo0mismatches, port previo>0,
  corregido0. Ejecución exit0/passedtrue;3,122s compilación+ejecución. stdout
  del fixture helper no se conservó, por lo que no se afirma número de
  discrepancias del port viejo. Código y hashes en interpreter/report.json.
- Comprobación independiente: decompiles Ghidra, instrucciones Capstone,
  21tests de generador/escenario y diff entero del DFS (3bytes/2 instrucciones).
- Resultado **útil** para cálculo/ruta de memoria, no para cadencia efectiva,
  FPS/RPM, eventos completos ni apariencia en juego. Tiempo manual/ahorro no
  medidos. Siguiente: conservar el ensayo sin repetirlo si no cambian inputs.
- Disponibilidad alternativa: `py -3.13 -c "import unicorn"` falló con
  ModuleNotFoundError. No se instaló nada; esa sonda no prueba utilidad de
  Unicorn. Se eligió el intérprete ya instalado y probado.
