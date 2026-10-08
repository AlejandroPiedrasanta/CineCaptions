# Estilo «Kinetic» (títulos de gancho, pack Kinetic)

## kinetic-planificador — Planificador y geometría

**Qué:** Estilo nuevo, independiente de «guion» y de las 3 líneas, que replica `referencia.mp4` («Vertical Kinetic Hook Titles»): cada bloque es una **pila de elementos** (líneas pequeñas, palabra HÉROE condensada con degradado y sombra, cintas de color, serif cursiva, pincel, anillo, subrayado) que entran con rebote y salen juntos. Solo vertical. Sin emojis; sí sonidos (un golpe cuando entra cada elemento / el héroe, según el modo de Sonido).

**Dónde:** `1_codigo/kinetic_planificador.py` · `planificar(palabras, idioma, ancho_tl, alto_tl, ancla, mains, recetas, fin_video)` → `{'cues','plan'}`; `RECETAS` (6: lima, blanco-rojo, magenta, amarillo, serif, blanco-cian), `S` (tabla de huecos: sup/lab/tp_*/ts_*/sc_*), `armar_bloque`, `_repartir`, `_heroe`, `AFINADO` (adelanto, hold, gap_minimo = 0,10 s, visible_min, desfase_max). Reutiliza `guion_planificador` (`_preparar`, `frases`, `puntajes`, `elegir_mains`, `_partir`). **Un bloque nunca se solapa con el siguiente:** primero se acorta lo que sobra y, si no cabe, el siguiente se retrasa (máx. 0,4 s). Geometría `1_codigo/kinetic_captions.py` · `apilar` (pila vertical con solape controlado de cintas sobre el héroe), `_medir` (Pillow con las fuentes reales; `K_PX = 640 px por unidad de Size @1080`), `construir_cues`, `escribir`. JSON `{language, cues:[{start,end,plantilla,caja,lines,runs:[{k,texto,t,x,y,size,rot,zx,zy}]}]}`. Vista aproximada (Pillow): `kinetic_vista.py`.

## kinetic-pack — El pack Kinetic y sus comps

**Qué:** Pack `2_recursos/plantillas_incluidas/Kinetic/` (`pack.json` con `"guion": "kinetic"`; `plantillas.Pack.kinetic` lo lee). 25 clips = elementos, no sets arriba/principal/abajo: `k hero blanco|lima|amarillo|magenta|rojo`, `k sup`, `k label`, `k serif blanco`, `k script amarillo|cian|rosa`, `k tape …`, `k tapes …` (cinta serif), `k ring …`, `k line …`. Cada uno lleva un Text+ «Template» (la app y el script le escriben `StyledText` y `Size`).

**Dónde:** generador `2_recursos/generador_packs/` · `pack_kinetic.py` (construye el .drb clonando un clip de `Referencia vertical.drb`), `kinetic_pack.py` (clona clips; arregla el nombre en el protobuf del FieldsBlob y el blob de posición), `kinetic_elementos.py` (catálogo + `comp_texto`, `comp_cinta`, `comp_anillo`, `comp_linea`, animaciones de entrada `pop|sube|giro|abre` y salida por `comp.RenderEnd`), `kinetic_comps.py` (utilidades de texto Fusion y comps de laboratorio), `leer_comp.py` (lee la comp de un clip de un .drb). Hallazgos de Fusion: degradado = `Type1=2` + `ShadingGradient1`; sombra = elementos 2 y 3 del Text+; el **Height de una máscara es fracción del ALTO** del cuadro (el Width, del ANCHO) → `ASPECTO = 9/16`; la cinta es un `RectangleMask` cuyo ancho sale de `Template.Output.DataWindow`. Al cambiar un comp: `python 2_recursos/generador_packs/pack_kinetic.py`, subir `plantillas.REVISION_BIN['Kinetic']` y rehacer la vista incluida.

## kinetic-app-resolve — Enganche en la app y en Resolve

**Qué:** GO y Generar usan el estilo si el pack elegido es Kinetic (chip «Estilo» de Inicio: «Kinetic · títulos de gancho»; tarjeta en Proyecto con su vista incluida).

**Dónde:** app: `_pack_kinetic`, `_generar_con_kinetic` (antes de `_pack_guion` en `_generar_con_motor`; `_pack_guion()` devuelve None para Kinetic); GO ignora las marcas, Generar respeta las palabras pintadas «Principal» como héroes forzados; pref `kinetic_ancla` (alto|medio|bajo, por defecto bajo). `plantillas.sirve_en_go`, `estructura_de` (`kinetic: True`), `revisar` (sin avisos de sets), `guion_editor.es_guion` (False para Kinetic). Vista de la tarjeta: `1_codigo/hacer_vista_kinetic.py` → `Kinetic/vista/` (5 fotogramas sobre negro + `indice.json`), servida por `vistas_reales.cacheadas/recortes` (no se pide nada a Resolve). Resolve: `place_kinetic_track` (py) = `place_kinetic` (lua), estilo de pista `'kinetic'`, pistas `ES-K1…` por capa (héroe abajo, líneas pequeñas arriba), limpieza de `L-K*` en los otros estilos.

## kinetic-pruebas — Cómo probarlo

**Qué:** Prueba de punta a punta sin tocar el video del usuario: voz SAPI → palabras con tiempos → plan → Resolve (timeline temporal `zz_BANCO`) → render → hoja de cuadros.

**Dónde:** `1_codigo/probar_kinetic.py [vista] [--fondo gris|video] [--ancla …] [--render nombre]` (usa `tts_prueba.ps1` y `banco_pruebas.colocar_kinetic`; espera `~/DaVinciSubtitles/mcp/palabras_voz_kinetic.json`); `hacer_vista_kinetic.py`. Acabar siempre con `banco_pruebas.limpiar()` (o el MCP `limpiar_banco`). Los arneses parchean `ajustes_ui.guardar_prefs`.
