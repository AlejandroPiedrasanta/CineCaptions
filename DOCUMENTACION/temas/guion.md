# Estilo «guion» (pack Referencia, palabra a palabra)

## guion-planificador — Estilo «guion»: planificador y geometría

**Qué:** Estilo «guion» (pack **Referencia**: la frase se arma palabra a palabra, como REFERENCIA.mp4)

**Dónde:** planificador `guion_planificador.py` · `planificar`, `frases`, `elegir_mains`, `_partir`, `_cabe`/`_estilo_para`, `evaluar` (contra los 15 bloques reales de `guion_referencia.py`, que trae también `PALABRAS`); geometría `guion_captions.py` · `construir_cues`, `distribuir`, `ancho_main`, `AFINADO`; pack `2_recursos/plantillas_incluidas/Referencia/` (lo genera `2_recursos/generador_packs/pack_referencia.py`; su `pack.json` lleva `"guion"` y `plantillas.Pack.guion` lo lee); app: `_pack_guion`, `_generar_con_guion` (GO usa el planificador; Generar / Editar marcas respetan las palabras que el usuario pintó «principal»); Resolve: `place_guion_track` (py) = `place_guion` (lua), JSON `{language, cues:[{start,end,estilo,runs:[{rol,texto,t,fin,x,y,estilo,zoom,salto}]}]}`, pistas `ES-T1…` (las GRANDES abajo). Solo vertical

## creativo-guion — Creativo con el estilo «guion»

**Qué:** Editor **Creativo** con el estilo «guion» (pack Referencia): marcas → bloques; «Así se verá este bloque» == lo que Generar coloca

**Dónde:** `guion_editor.py` · `planear` (LA función única: la usan la vista del editor y `_generar_con_guion`; paridad por construcción), `parametros_de_marcas` (Principal=grande, Abajo=negrita, Arriba=fina, Simple=auto), `roles_automaticos`, `bloques_para_editor`; vista `guion_vista.py` · `MarcoVistaGuion` (`poner_cue`, `poner_real`; fuentes con `fuente_qt` = QFontDatabase + `setStyleName`); script principal · `WordTagWindow._guion`, `_construir_controles_guion`, `_guion_auto`, `_guion_limpiar`, `_guion_poner_ancla`, `_planear_guion`, `_guion_comprobar_en_resolve` (botón «Comprobar en Resolve» → `vistas_reales.renderizar_guion` → modo `'guion'` de `CineCaptions - Vista Real.py`, un fotograma, sin cola de render). Estilo de un bloque a mano = `w['estilo']` de su primera palabra. Pruebas: `test_paridad.py`/`test_creativo.py` (el arnés necesita `qt_kit.crear_app()`; para fuentes reales NO `offscreen`: ventana en x=-5000)

## estilo-oracion — Estilo por oración y animación de Amro en «guion»

**Qué:** Estilo por oración y animación de Amro en «guion»

**Dónde:** `guion_planificador.py` · `ESTILOS_BASE` (Luxe, uno por oración), `ESTILOS_ACENTO` (Amro: remate de la oración), `_intencion` (fuego/negación mandan), `AFINADO['pausa_oracion']`; `guion_captions.py` · `AFINADO['salto_amro']` (los presets de Amro se revelan letra a letra; la referencia los muestra enteros → el comp arranca adelantado: 0,2 s, subrayado 0,14 s; `place_guion_track` lo lee del `salto` de cada palabra). El pack elegido en Estilos tiene que ser **Referencia** para que GO use el estilo «guion» (con «Base títulos dinámicos» sale el diseño de 3 líneas)

## nota — v5.9 · Estilo «guion»

v5.9 · Estilo «guion» (pack Referencia), planificador, banco de pruebas y MCP:
- guion_planificador.planificar(palabras): FRASES (signo fuerte, coma con pausa, pausa de 0,22 s, «a ver/oye…», conjunción tras pausa) -> PALABRA GRANDE por frase (puntaje: longitud, sustantivo tras artículo, adjetivo evaluativo, última palabra con peso, gancho en la 1.ª; sin peso = frase de reacción sin palabra grande) -> BLOQUES (entre dos grandes se corta en la pausa, sin dejar un artículo colgando) -> LÍNEAS en orden de lectura [fina] GRANDE [fina], una negrita por línea -> ESTILO por rotación (fuego/negación piden el suyo) donde la palabra CAIGA -> TIEMPOS (cada palabra entra cuando se dice; la pila se va 0,22 s después, sin pisar al siguiente). Contra REFERENCIA.mp4: 12/13 palabras grandes, 16 bloques (15), 13/15 cortes.
- guion_captions.construir_cues convierte esos bloques en runs {rol,texto,t,x,y,zoom,estilo}: el ancho de cada línea sale de la tipografía real (Pillow) y el zoom ajusta al ancho pedido; place_guion_track / place_guion los colocan (cada palabra = un clip; grandes en las pistas de abajo).
- GO con un pack «guion»: _generar_con_motor -> _generar_con_guion escribe <proyecto>.<idioma>.guion.json y la pista style='guion'. Fuera de GO, las palabras pintadas «principal» en el editor mandan (varias seguidas = una sola palabra grande).
- banco_pruebas: timeline temporal zz_BANCO (fondo gris + audio) -> colocar -> render H.264 Master -> hoja/lado a lado/medir -> limpiar. mcp_cinecaptions expone todo eso (y la transcripción y el planificador) por MCP.

## barrido-referencia — Barrido de luz de «Referencia» (v5.4.13, sin compilar)

**Causa raíz del barrido «a medias»:** el macro Luxe Shine empieza el barrido a los 0,25 s y tarda 1,5 s (acaba a los 1,75 s) pero una palabra grande de «guion» se ve 0,3-0,9 s (mediana 0,55 s; 43 de 59 < 0,8 s en los videos de prueba). Además el recorrido de la banda sale del `DataWindow` del texto, que dentro de un macro no llega: recorre siempre ~0,31 del ancho del cuadro (IMPACT, REMARKABLE sólo se barrían por el centro). Y la curva era un ease cúbico (4x³): la banda pasa ~60 % del tiempo fuera de las letras.

**Arreglo:** `luxe_macro._barrido`: Offset 0,06 / Length 0,40 de fábrica y EaseIn/EaseOut «Linear» en `AnimCurves2`. `ajustar_barrido(item, visible_s, salto_s, ancho_rel)` (CineCaptions.py = .lua, gemelos) pone por clip `inputOffset` = salto + 0,10 s (después de la entrada del macro, 0,14 s), `inputLength` = clamp(visible − 0,22; 0,16; 0,50) y `inputShine` = (ancho_rel + 0,16)/2,17 − 0,193 (recorrido ≈ 2,17 × (0,193 + inputShine) anchos de cuadro; `ancho_rel` lo pone `guion_captions.construir_cues` en cada run principal). La macro se llama `LuxeShine` en la comp del clip; `GetToolList()` lista también sus herramientas internas.

**Variantes:** `pack_referencia.combinaciones()` → 16 combos: 1-8 de siempre; 9-12 «Screen» y 13-16 «Sólido» de los estilos Luxe 1, 2, 4 y 5 (`VARIANTES_BARRIDO` da el color de la banda de cada una). El color va en un Background con `EffectMask = shineCombine` (banda ∩ letras) + Merge (Screen o Normal) antes de `dropShadow`; un EffectMask directamente en el Merge dejaba fuera el texto. `guion_planificador.BARRIDOS` las alterna (original → Screen → Sólido) en las palabras grandes (`variar_barrido`, no en `evaluar`); lo que el usuario fijó a mano no se toca.

**Trampa del pack (arreglada):** los clones de combinación ≥ 10 salían corruptos en Resolve («sin Text+»): el FieldsBlob lleva el nombre con LARGOS protobuf y «contexto 10» mide 1 más que «contexto 3» (`construir_pack._blob_con_nombre` ahora corrige los tres largos). El script de Resolve sólo buscaba 10 sets (`MAX_SETS`/`MAX_VARIANTES` = 16 ahora; el .lua tenía `max_variantes = 3`). `REVISION_BIN['Referencia'] = 'Ref 2'`.

**Probar (en Resolve, SIEMPRE en un proyecto temporal):** `1_codigo/probar_barrido.py [--estilos …] [--duraciones …]` (banco zz_BANCO + hoja de cuadros) y `1_codigo/medir_barrido.py <render.mov> …` (en qué fracción del ancho empieza y acaba la banda). Medido tras el arreglo: GO 0,7 s → 6-10 % a 90-92 %, REMARKABLE 1,1 s → 24 % a 76 % del cuadro (= todo el texto, que ocupa 20-80 %).
