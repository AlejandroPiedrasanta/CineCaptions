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
