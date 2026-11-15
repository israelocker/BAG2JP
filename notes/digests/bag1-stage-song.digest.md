---
id: bag1-stage-song-digest
title: "Escenario/canción: contrato por fases"
tags: ["digest", "stage"]
summary: "Checklist compartida de cámara por fase, geometría/VRAM, puntaje/props, render, música/SFX y modos; no aceptación ni conversor universal."
related: ["notes/bag1-stage-song.md"]
created: "2026-11-02"
updated: "2026-11-15"
edited: "2026-11-15"
doc_kind: digest
source: "notes/bag1-stage-song.md"
source_sha256: "780766da3ce9c02cac60a5b87a633435898987c6993fa548f1c0703be27b3008"
---

Leer «Ruta reutilizable» y «Contrato y checklist de aceptación por escenario» de
la [fuente](../bag1-stage-song.md), no todas las revisiones históricas.
- Identidad/disco/región/módulo y modo/layout; miembros/colas/chart/animaciones,
  tipos/instancias/transforms y escala demostrada, sin multiplicador universal.
- Cámara: intro/READY→GO, baile, entrada/fever/salida, final/retorno. Formato y
  consumidor, ojo/objetivo cuando aplique, recorrido/tiempo/interpolación/enlaces.
  Conservar adaptaciones aprobadas; un intro aceptado no acredita todas las fases.
- Recursos: atlas comunes/descriptores, CLUT/UV/tpage y uploads dinámicos por fase;
  comparar VRAM real aparte de simulación. Render: distinguir GTE/clipping/culling/
  OT/VRAM; corrección mínima respaldada, no sesgo o subdivisión universal.
- Puntaje obligatorio desde06-11: origen/umbrales/estados y adaptación aprobada;
  update/shim/residencia/reset, efecto visible de cada transición. Props/luces/
  partículas con reloj, ramas, recursos, evolución y retirada. RAM no prueba cadencia.
- Música/SFX: identidad/canal/chart/duración nativa y archivo; CD no se infiere de
  sample rate. Bancos/cues, reproducción y escucha humana son pruebas distintas.
- Versión por lado, regiones globales de modelo/escenario y opción musical separadas;
  vuelta a stock, P1/P2/mixtos/parejas y zoom/home/leash según layout. Robo-Z gigante/
  helicóptero y acceso campaña/VS pendientes de investigar; no desbloquear por norma.
- Campaña, VS y Ending View no se acreditan entre sí. Prueba nueva necesita sus
  permisos y grabación/revisión; todo desconocido o fuera de alcance queda explícito.

La explicación histórica «BAG2 no soporta tipo2» está retirada: existe case2;
flattening corrigió un candidato, no prueba incapacidad universal. Mejora Strike
de huecos/culling sigue aplazada; esta documentación no la reactiva.
`build_stage_package.py --root <project> --profile strike --output <new.dfs>`
crea DFS+JSON, no despliega. Perfiles Heat/Strike tienen símbolos/callbacks y
paquetes distintos: no es un relocador universal. Modelo, atlas, cámara, chart y
SFX requieren inventario específico; el reporte fijo de banco stock es obsoleto
cuando native_sfx_bank0=true. Strike usa bank0 nativo y banks1..3 stock.
La fuente conserva runs de canción/selector/SFX y regresiones con restauración,
no una nueva aceptación en esta auditoría. JP start920 no USA955; duración lógica
129 s no duración WAV132,053333 s. FLAC44100 estéreo y ruta son por perfil.
Grid/fondo negro aceptados por propietario; escucha/fidelidad/campaña final no
se infieren de logs ni de Ending View. Historia anterior queda fechada debajo.
