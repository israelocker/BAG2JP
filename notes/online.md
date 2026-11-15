---
id: online-play-netsync
title: "Online: implementación y límites de evidencia"
tags: ["online", "netsync", "reference"]
summary: "Distingue código netsync, pruebas locales históricas y aceptación real entre máquinas todavía no acreditada."
related: ["notes/character-import-testing.md", "notes/project.md"]
created: "2026-10-29"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: reference
---

# No equiparar versus local y online

Fuente propia: `mods-src/bag2jp.feature.netsync/src/bag2jp_netsync.c` y manifest
del paquete. Revisar código/pins del framework para mensajes/transporte: una
lista de servidores en una nota no demuestra disponibilidad ni seguridad actual.

Hay dos vías distintas: netplay del framework y sincronización de resultados
de pasos del título. No aplicar opciones/limitaciones de una a la otra.
Cambios de assets o timing requieren revisar identidad de contenido de ambos peers.
Dos selecciones que coinciden visualmente no prueban sincronización musical.
Inventariar qué cubre realmente la identidad/fingerprint de la implementación
activa y qué queda fuera: runtime, mods/opciones, payload/índice, región y timing
pertinentes. Un campo igual entre peers no prueba igualdad de inputs excluidos de
ese campo. Contrastar código/bytes antes de prescribir otro formato o afirmar un
bug; esta regla no cambia protocolo ni autoriza conexión o prueba online.

El [registro histórico](archive/online-before-audit.md) documenta experimentos de
dos procesos en una máquina (LAN, relay, direct IP), barreras, focus pause y audio.
No se revalidaron redes ni brokers durante la auditoría. Las pruebas entre dos
PC reales/redes distintas y rematch/resultados no quedan acreditadas por ese registro.
No presentar `test local` como Internet/NAT aceptado ni habilitar conexiones por
seguir un ejemplo histórico.

Para aceptar un cambio online: identidad igual, inputs de ambos peers,
avance/barriers, desconexión/focus, final/retorno, ajustes preservados y evidencia
de ambos extremos. Latencia subjetiva necesita escucha; `buffer_ms` no es medida
de latencia total ni un valor obligatorio para todos los equipos.
