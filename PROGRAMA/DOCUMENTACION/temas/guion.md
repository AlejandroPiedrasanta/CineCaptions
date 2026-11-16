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

## nota — v5.5.7 · líneas juntas y emoji arriba (pedido del usuario: «muy separados»)

`guion_planificador.AFINADO`: `hueco` 0,03 → 0,004 y `alto_linea` 0,039 → 0,036 (las líneas quedan pegadas a la de abajo; antes ~58 px entre
una y otra en vertical). Ya NO calca la separación de REFERENCIA.mp4 (≈0,08 entre centros): el usuario la quiere más junta. El emoji va ARRIBA
(`plantillas.EMOJI_ARRIBA` incluye Referencia y VIRAL) y pegado a la caja de la pila: los planes de emoji de `place_guion(_track)` y de VIRAL llevan
`junto` y `colocar_emojis` usa un margen de 0,012 del alto (0,02 en horizontal) en vez de `EMOJI_MARGEN` (0,065), en el .py y en el .lua.

## nota — v5.5.8 · aire para las palabras grandes editoriales

Con `hueco` 0,004 las palabras grandes en letra editorial / de pincel (estilos 2 y 5 y sus barridos 10, 12, 14, 16 = `ESTILOS_EDITORIAL`)
pisaban la línea de al lado en el render real: llevan `AIRE_EDITORIAL` (0,012 del alto) arriba y abajo. El resto sigue pegado.

## nota — v5.48 · más fluido, números que cuentan (pedido: «muy rápido, no fluye», «mucha tabulación»)

**Ritmo:** `_respiro`: la última palabra de cada bloque se ve al menos `respiro` s; el bloque siguiente espera hasta 0,35 s y sus palabras no entran antes que él (valores medidos contra la referencia, abajo). Antes el fin del bloque se cortaba en el inicio del siguiente y la última palabra podía verse 0,1 s.

**Espaciado:** `guion_captions.AFINADO['espacio']` 0,55 → 0,2 (las referencias del usuario van con las palabras juntas).

**Estilos quitados (pedido):** el pack ya no trae 4, 11, 15 («Moderno blanco» y sus barridos).

**Números con Luxe Count (17)** (pedido: «usa Luxe Count para números y si habla de dinero pon el signo de la moneda»): `cifras(pal)` → {índice: (texto, [índices])}: cifras («430,000», «9.99», «50%», «$1,200»), números escritos («tres» → 3), «mil»/«millones» juntos con su número, «1.500» → «1,500»; si la sigue una moneda («dólares/pesos» $, «quetzales» Q, «euros» €, «libras» £) lleva el signo y la palabra de la moneda va DENTRO de la cifra (no se repite). Los años (1900-2099) no cuentan. La cifra va grande con la 17 (zoom ≤ `zoom_max_cifra` 1,7). El macro (`luxe_macro`, tipo count) saca del texto del clip el prefijo («$»), el sufijo («%») y los decimales; cuenta de 0 en ≤0,9 s. Los demás conservan su número (`pack_referencia.QUITAR`); `_estilo_para` solo elige variantes que el pack trae. Con el subrayado (8) la línea de debajo va CENTRADA bajo la grande (`ESTILOS_LINEA3_CENTRADA`).

**Tachado:** el 7 (Strike) y el 6 (Fire) solo los pide el significado; ya no son el último recurso cuando ninguna otra cabe (salía «Quetzaltenango» tachado).

**Líneas pequeñas hacia la derecha:** las de Luxe Slide (Poppins Light / Bold) van con POSITION «Mirror Out» desactivado y dirección «→» (Start Direction 180, End Direction 0): entran y salen hacia la derecha, como se leen. Desmarcar «Mirror Out» en el Inspector ejecuta un Script del macro que cambia las expresiones de `positionVector`; `luxe_macro._deslizar` las deja escritas igual (pack: `'deslizar': 'derecha'`).

**Bloques de tres líneas + cortos** (pedido: «más entretenido»): `_complejos` alterna un bloque pequeña · PRINCIPAL · pequeña con al menos `cortos_entre` (2) bloques cortos. Un bloque que acaba en su palabra grande se lleva hasta `complejo_max` (4) palabras pequeñas del principio del siguiente (sin pausa > `pausa_frase`, bloque ≤ `complejo_s` 3,2 s, sin cortar tras «de/la/que»); el siguiente queda corto. Con mains forzados a mano no se toca.

**La grande al ancho de su línea** (pedido: «el principal debe ser grande para que el Luxe Slide esté encima casi al ras»): con una línea pequeña encima (o debajo, si no hay encima), la grande ocupa el ancho de esa línea: nunca menos que su tamaño natural (zoom 1) ni más de 2,2× ni del 90 % del cuadro. Sin línea pequeña sigue el tope `zoom_max`. `_alto_main` sube su tope de 0,10 a 0,13 del alto para dejarle sitio.

**Nunca 4 líneas · más junto · grande algo mayor** (pedido): UNA palabra grande por bloque (en `planificar`, después de `_partir`, que no se toca porque lo usan los temas 1 y 3): el corte va justo tras la primera grande. La grande = `grande_linea` (1,1) × el ancho de su línea pequeña y ≥ `grande_min` (1,1) × su tamaño natural (tope 2,4× y 92 % del cuadro). Alturas más ceñidas a la tinta: `hueco` 0,005, `alto_linea` 0,031 y `_alto_main` con k por letra (medido en Resolve): serif cursiva `k_alto` 1,35, Poppins/Inter `k_alto_sans` 1,7 (con un solo k las gruesas pisaban la línea de al lado). `_complejos` solo roba palabras a un bloque siguiente que tenga grande, y si caben todas las de antes de su grande se las lleva todas.

**Ritmo de pesos** (pedido: «jamás 4 en light, tiene que tener un bold; máximo 2 en bold y 3 en light»): `_ritmo_pesos` (tras `_pesos_linea`, solo si el usuario no marcó finas a mano): toda línea de 2+ palabras lleva una negrita (la palabra con contenido más larga), nunca más de `MAX_FINAS` (3) finas ni `MAX_NEGRITAS` (2) negritas seguidas.

**Al ras, medido con la tinta** (pedido: «jamás va separado, va al ras»): `guion_captions.extension_tinta` da cuánto sube y baja la tinta de la grande respecto a la y del clip, con su tipografía y el ancho que ocupa. Medido en Resolve: Fusion centra la CAJA de la letra (ascent/descent), no la tinta («Maquillaje» cuelga por abajo); Amro ≈ 45 % arriba / 75 % abajo. El planificador apila con eso (`arriba[j]`). Se quitó `dy {1: -0.021}`: con el Shine v1.09 abría 40 px de hueco bajo «EMPEZAMOS». Resultado medido: 3-18 px de tinta a tinta. Herramienta de medida (fuera del proyecto): fotograma de cada bloque → bandas de filas con tinta → hueco entre líneas.

**Reglas de líneas** (pedido): `_reglas_lineas` (tras `_complejos`): ninguna línea pequeña pasa de `max_linea` (4) palabras (lo que sobra forma un bloque corto de ≥2, que se vuelve a revisar) y la línea de DEBAJO de la grande nunca lleva una sola palabra (pasa al bloque siguiente; si es el último, va sola). `_complejos` solo arma la línea 3 con ≥2 palabras. La línea de debajo de la grande empieza en el centro del cuadro y va hacia la derecha, y NUNCA se sale del borde derecho de la grande (margen 0,03): la grande toma el ancho de su línea pequeña más ancha (encima o debajo, `_ancho_linea`) y, si aun así la de debajo es más ancha, esta se reduce al ancho de la grande. Comprobado en 177 bloques de 5 transcripciones: 0 fallos (4 líneas, 5+ palabras, pesos, línea 3 de 1 palabra).

**Espaciado de letras:** todos los textos Luxe del pack con Character Spacing `pack_referencia.ESPACIADO` = 0,99 (se probó 0,95 y el usuario prefirió 0,99). Medido en Resolve: Fusion quita por LETRA (1 − espaciado) × 1,4 × tamaño de letra (con 0,95 las palabras encogían ~15 %); `guion_captions._apretado` lo descuenta en `ancho_px` / `ancho_main` (`AFINADO['espaciado']` debe ser igual a `ESPACIADO`) para que los huecos entre palabras no se abran.

**Colores y Amro (vista de los 17 estilos):** el Luxe Shine v1.09 trae su propio color (azul verdoso, Red1/Green1/Blue1 en Text1) DESPUÉS del que ponía `comp_luxe`, así que ganaba: «Moderno blanco» salía azul y los rosa, azul verdoso. `comp_luxe` lo quita antes de poner el del estilo. «Moderno blanco» (4, 11, 15) sube de 0,118 (el tamaño de las pequeñas) a 0,18. Los presets de Amro reservan su alto medido (`guion_captions.AFINADO['amro_ext']`, px a zoom 1: pastilla 3 = 82/94, fuego 6 = 64/118, tachado 7 = 30/36, subrayado 8 = 38/98): la pastilla tapaba las líneas pequeñas y el subrayado tocaba la de abajo.

**Pulido de cortes** (pedido: «pule más los captions»): `_corte` elige dónde partir una línea larga: nunca tras «de/la/y…», repartiendo el TIEMPO en pantalla entre los dos trozos (pausa como desempate) → «La Unión Europea» | «trae a / Quetzaltenango». La línea 3 nunca acaba en palabra vacía: esas pasan al bloque siguiente con su palabra («y del / Salvador»), salvo por encima de un fin de frase (pausa ≥ `pausa_frase` o «.?!»). Un bloque sin grande de 5-8 palabras va en dos líneas del MISMO bloque (`_lineas_pequenas`), no en dos bloques fugaces. `respiro` 0,4 → 0,55. Tachado (7): `amro_ext` 30/36 → 32/50 (la línea de debajo quedaba pegada).

**Menos rápido** (pedido: «se ve muy rápido»): `_juntar_cortos` (tras `_reglas_lineas`) junta un bloque de menos de `bloque_min` (1,2 s) con su vecino de la misma frase como una línea más, si se cumplen las reglas (una grande por bloque, ≤3 líneas, ≤4 palabras/línea, línea 3 de ≥2 sin palabra vacía al final, ≤ `complejo_s` + 0,6 s): «Se pasaron / me hicieron el día». En REFERENCIA la mediana pasó de 0,94 a 1,42 s por bloque. Las grandes sueltas («EMPEZAMOS») siguen solas: dos grandes no van juntas.

**Emojis solo con la PRO** (pedido): el Tema 2 pone emojis SOLO con la Edición PRO encendida (`go_edicion_pro`) y su opción «Emojis animados» (`pro_emojis`) activada: `edicion_pro.emojis_del_tema(pack)`. Si no, `_generar_con_guion` no llama a `_preparar_emojis` y quita `emoji`/`emoji_ini`/`emoji_fin`/`emoji_linea` de los bloques Y de los cues (el planificador ya los deja ahí). Desde la v5.54 vale para TODOS los temas (tema `emojis-pro`, `SubtitleApp._emojis_permitidos`).

**Medido contra REFERENCIA.mp4** (`ref_exacta.guion.json`): la palabra entra ~0,08 s DESPUÉS de la voz (`adelanto` 0), entre bloques queda un hueco de 0,15-0,25 s (`gap_minimo` 0,15), la última palabra se ve ≥0,35 s (`respiro` 0,4) y las grandes van a zoom 0,9-1,3 (`zoom_max` 1,3; antes las cortas se inflaban hasta 2,5).

**Entrada, salida y encadenado (v5.50, pedido: «entrada y salida muy rápidas»):** medido a 30 fps contra PRUEBAS (3) (editado con el Luxe Title Pack), la referencia entra en 8-9 fotogramas (la grande) y 4-6 (las pequeñas), sale en 4-5 y encadena los bloques; el Tema 2 entraba y salía en la mitad y dejaba 0,2-0,6 s en negro entre bloques. Ahora `pack_referencia.ANIM` = (0,60, 0,45, 0,50, 0,35): entrada 0,6 s y salida 0,45 s con tope del 50 % / 35 % del clip (`luxe_macro._anim_auto` con tope por pack); en el planificador `gap_minimo` 0 y `pegar` 1,2 (una pausa de la voz de hasta 1,2 s deja el bloque en pantalla hasta que llega el siguiente). Los huecos medidos en REFERENCIA.mp4 (párrafo de abajo) ya no se imitan.

**Barra del estilo 8 al ras (v5.50, pedido):** la barra del Underline de Amro es el Text+ «Line» (su recuadro encogido con `ExtendVertical8` y bajado con `Offset8`, en fracción del alto). Medido en Resolve quedaba 12 px (a zoom 1) bajo la tinta; `pack_referencia.BARRA_AL_RAS` cambia `Offset8` de -0,042 a -0,036 con `construir_pack.retocar_comp` (la comp de Amro se copia tal cual salvo esos textos) y `amro_ext[8]` pasa de (38, 98) a (38, 87). Ojo al medir: la tinta de Amro acaba en gris (degradado), contar solo lo blanco da la base 10 px más arriba.

**Barra del estilo 8 a lo ancho (v5.50, pedido: «al inicio y fin de la palabra también»):** la caja de «Line» medía su propio texto en Inter Black, pero el script pone en Text1 la fuente de «Crea tu estilo» (`fuente_principal`, en el PC del autor Arial Black): la barra sobraba un 7 % del ancho más 18 px por lado. Ahora `Font`, `Style` y `CharacterSpacing` de «Line» siguen a Text1 por expresión y `ExtendHorizontal8` -0,16 recorta el margen de la caja (-0,1 = 22 px por lado a zoom 1; medido). Ojo: esa fuente de «Crea tu estilo» solo cambia los presets de Amro (3, 6, 7, 8); en los Luxe el script la pone en «Template», que el macro no usa para la forma.

**Halftone en 1, 9 y 13 (v5.50, propuesta A elegida):** `pack_referencia.TRAMA_IMPACTO` en el Impacto cian (sus barridos 9 y 13 lo heredan) y `luxe_macro._trama`: entre la salida del macro y MediaOut1, «TramaPuntos» (Custom sobre un Background, sin depender del fotograma) dibuja la rejilla y «Trama» (Custom simple con Image2) la pinta solo donde la letra es casi opaca (alfa > 0,6): ni halo ni sombra se puntean. Primero fueron puntos que crecían en la mitad baja (4,8 px en 11 px); el usuario: «están feos, debe ser todo, sutil y difuminado» → ahora puntos #16357A por TODA la letra, de 2,4 px de radio en 9 px con 1,6 px de borde suave y opacidad del 40 % en la base al 12 % arriba (`TRAMA_IMPACTO`).

**Ojo al probar:** el script de Resolve solo buscaba 16 sets (`MAX_SETS`/`MAX_VARIANTES` en el .py y el .lua): la variante 17 caía en silencio al estilo 1. Ahora 20.

**Amro Fire sin cortes (v5.53, pedido: «arréglalo»):** el 6 cortaba las palabras largas («PRINCIPAL» → «Principa», también a 1080): la comp de Amro dibuja las letras en un cuadro de 1080 y las encoge DESPUÉS (Transform1 al 0,66), y lo que no cabía antes de encoger se perdía. `pack_referencia.FUEGO_SIN_RECORTE`: la curva `Follower1Tamaño` (la que da el tamaño de cada letra; el Size del Text+ y el «tam» de la variante NO cambian nada, medido) × 0,66 y el Transform a 1; rejilla, ruido, difuminado y sombra ajustados a la misma escala. Comprobado en Resolve: «FUEGO» igual que antes y «Principal» entera (tinta de x 76 a 1002 en 1080). REVISION_BIN «Ref 19».
