# Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)

## pantalla-estilos — Pantalla Estilos / packs

**Qué:** La pantalla «Proyecto» (`_pagina_estilos`): tarjeta Audio (Obtener + motor de voz, se construye en `_pagina_nuevo`), «Pack de estilos» (slider; en su cabecera, a la par: el botón «Crea tu estilo» y «Vista real · Resolve»). Desde la v5.4.0 ya no hay banda «Crea tu estilo» ni «Estilo desde una imagen» en pantalla (el módulo `estilo_desde_imagen.py` sigue). **La rueda del ratón sobre cualquier punto de Proyecto mueve el slider** (`qt_kit.RuedaHacia` instala un filtro por widget en la zona desplazable + `Desplazable.rueda_a`; `CarruselPacks.desplazar_con_rueda`); la barra lateral y el teclado siguen desplazando la página. Ya NO existe la tarjeta «Tipografías que usa el pack» ni el filtro Horizontal/Vertical: las vistas son siempre verticales (`_formato_vista` prefiere 'v'; `_formato_edicion` conserva el formato del timeline para abrir un pack en Resolve). Si al pack le faltan fuentes, el panel de debajo del slider muestra «⚠ Faltan N tipografías · instalar» (`_instalar_fuentes_central`).

**Dónde:** script principal · `class PlantillasWindow`: `__init__` (arma slider + panel + `_construir_crear`), `_recargar` (rehace las tarjetas, se queda en la del centro; `_carta_simple` Media Pool/Diseño automático, `_carta_pack`, `_cartas_basicos` en el modo «normal» con las combinaciones como chips del panel), `_pintar_info` (panel del estilo central: nombre, nota, estructura, «Usar este estilo»/«En uso», ✎ 🗑 ⋯), `_elegir`, `_realzar`, `_valor_actual`. El slider en sí: `estilos-slider`.

## estilos-slider — Slider horizontal de «Pack de estilos» (tarjetas verticales sobre fotos)

**Qué:** v5.3.6. Un solo widget (`CarruselPacks`) pinta todas las tarjetas 9:16 con un resorte (arrastrar, rueda lateral, ← →, puntos, clic en la vecina = centrarla, clic en la central = usar el estilo). La del centro va grande, con la foto en paralaje, giro tipo coverflow en las vecinas, resplandor del color medio de la foto y los captions EN MOVIMIENTO; las de los lados se pintan una vez en un pixmap (`_pixmap_estatico`) y solo se estiran. Fondos: `2_recursos/fondos_estilos/fondo_NN.jpg` (11 fotos de video 9:16; una por tarjeta según el nombre del pack). Captions: la vista REAL de Resolve (`vistas_reales`: fotogramas sobre NEGRO) se compone en modo Screen sobre la foto, a su tiempo real (`CUADROS_S`), una variante tras otra; sin vista real se dibujan las líneas aproximadas (`lineas_de_vista` → `MarcoVista._pintar_contenido`, método que sale de `MarcoVista.paintEvent` para poder pintar en cualquier rect) con una banda oscura detrás. `Carta` = lo que sabe el carrusel de un estilo; `HeroCrear` = la banda de «Crea tu estilo» (ya sin uso en pantalla desde la v5.4.0).

**Dónde:** `estilos_slider.py` · `CarruselPacks` (`poner_cartas`, `poner_elegida`, señales `elegida` / `centrada` / `anadir`), `Carta`, `HeroCrear`, `fotos`; `qt_kit.MarcoVista._pintar_contenido`. Añadir fotos = soltar `fondo_NN.jpg` 9:16 en la carpeta y reconstruir (las listan los `.spec` como carpeta `fondos_estilos`). Pruebas: arnés con `resolve_mcp.estado_cacheado = lambda: {}` (la pantalla renderiza vistas reales sola si Resolve está conectado) y QTest para clics/arrastre.

## packs-drt — Packs .drt/.drb (Pack y lector)

**Qué:** Packs .drt/.drb

**Dónde:** `plantillas.py` (Pack, memo), `packs_drt.py` (lector)

## fuentes — Fuentes del sistema

**Qué:** Fuentes del sistema

**Dónde:** `fuentes_sistema.py` (índice + caché en disco), `instalar_fuentes.py`

## generador-packs — Generador de packs (.drb con Luxe)

**Qué:** Packs nuevos (.drb con Luxe Shine)

**Dónde:** `2_recursos/generador_packs/` · `generar_comps.py`, `luxe_macro.py`, `construir_pack.py` (usar MediaOut, no Saver)

## crea-tu-estilo — «Crea tu estilo» (48 ejemplos, vistas reales)

**Qué:** «Crea tu estilo» (Estilos): galería de 48 ejemplos (30 Luxe + 18 con principal de **Amro.Films Captions**; Amro SOLO como principal, arriba/abajo siempre Luxe Slide) con su vista REAL y ANIMADA renderizada por Resolve (7 fotogramas por ejemplo, en bucle con fundido; cada tarjeta lleva su botón «Vista real · Resolve» que carga SOLO ese estilo en la línea de tiempo) + «!» que explica la estructura de nombres; crea un pack de hasta 3 variantes en un clic o arma los 48 en Resolve

**Dónde:** `ejemplos_estilo.py` · `EJEMPLOS`, `miniatura`, `crear_pack`, `datos_guia`; vistas reales `vistas_guia.py` + `ejemplos_estilo.CUADROS_VISTA_S`/`rutas_vista` (caché `~/DaVinciSubtitles/plantillas_cache/guia_estilo/vistas/ej_NN_K.jpg`, de fábrica `2_recursos/guia_estilo/vistas`); reproducción en `crea_estilo_ui._Tarjeta` (reloj de la galería: solo avanza las tarjetas visibles); UI `crea_estilo_ui.py` · `CreaEstiloDialogo`, `AyudaEstilo`; botón y callbacks en `PlantillasWindow` (`_crear_estilo`, `_ayuda_estilo`, `_crear_pack_de_ejemplos`); guía de Resolve: `2_recursos/guia_estilo/construir_guia.py` (modos 'guia' y 'vistas') + `Crea tu estilo.drb` + `Amro principales.drb`, lanzada por `resolve_mcp.abrir_guia`. NUNCA insertar efectos por `InsertFusionTitleIntoTimeline` con nombres dudosos: tumbó Resolve

## editar-quitar-pack — Botones ✎ editar en Resolve y 🗑 quitar pack

**Qué:** Botones ✎ (editar en Resolve; también doble clic) y 🗑 (quitar; los packs incluidos solo se ocultan: pref `packs_ocultos`) en cada tarjeta de «Pack de estilos»

**Dónde:** `PlantillasWindow._acciones_de` (los botones salen en el panel bajo el slider, `_pintar_info`), `_editar_en_resolve`, `_quitar_pack`; `edicion_pack.py` + `2_recursos/guia_estilo/editar_pack.py` (importa el .drt, o arma el timeline desde el .drb con los nombres exactos)

## luxe-packs — Packs de texto = solo macros reales Luxe

**Qué:** Packs de texto = SOLO macros reales del Luxe Title Pack (Shine = principal/base, Slide = el resto), sin Text+ sueltos

**Dónde:** `2_recursos/generador_packs/luxe_macro.py` (`comp_luxe`, bases `luxe_shine_*`/`luxe_slide_*`), `construir_pack.py`; pack con contenido nuevo = subir su `REVISION_BIN` en `plantillas.py` (si no, Resolve reutiliza el bin viejo del proyecto)

## nota — PACKS

2) PACKS (.drb / .drt) — LA ESTRUCTURA MANDA, EL NOMBRE ES LA LLAVE
   Un pack = una carpeta en 2_recursos/plantillas_incluidas/<Pack>/ con:
     pack.json                        {"formatos": {"v": {"drb": "<Pack> vertical.drb"}}}
     <Pack> vertical.drb              bin de Resolve con los clips (Fusion Title)
     <Pack> vertical.posiciones.json  Pan/Tilt/Zoom de cada clip (para la vista previa)
     <Pack> vertical.variantes.json   (opcional) nombre/color de cada variante
   Nombres de clip DENTRO del .drb (el script los busca por nombre exacto):
     contexto  / principal  / complemento        = variante 1  (arriba / grande / abajo)
     contexto 2 / principal 2 / complemento 2    = variante 2   ... hasta 3 en los packs viejos,
     base                                          5-6 en los nuevos (Crea tu estilo trae 5)
     imagen, imagen 2...                          = icono/emoji (arriba o debajo según su Tilt)
   - "base" = palabra suelta sin rol.  Sin base, las sueltas usan el estilo principal.
   - Variantes: se reparten bloque a bloque SIN repetir dos seguidas (orden barajado con
     semilla fija: mismo video = mismo reparto). «Fijo en este estilo» (Composición del
     bloque) obliga a todos a usar UNA variante (clave estilo_fijo del manifiesto).
   - El TEXTO se escribe en la herramienta llamada «Template» (si no existe, el 1.er Text+).
   - POSICIÓN: sale del Pan/Tilt del clip dentro del .drb. La vista previa y la guía leen
     esos mismos valores (packs_drt.posiciones_de_drb) => lo que ves en la app es lo que
     queda en el timeline.
   - Composición del bloque (layout 3x3 + Altura + Horizontal) se SUMA a esa posición.
   Packs nuevos (2_recursos/generador_packs/):  generar_comps.py escribe la comp Fusion de cada
   rol (2 palabras por línea: la 1.ª light/regular, la 2.ª bold; líneas pegadas; entrada
   animada pop/sube/abre) y construir_pack.py la mete en un .drb contenedor. Reglas del
   formato .drb: MediaOut (NO Saver), SavedOutputs=1, TEMPLATE_ID ASCII.
   TODO el texto de un pack (v5.8) es un macro REAL del «Luxe Title Pack» de Resolve: Luxe Shine (principal y palabra suelta) o Luxe Slide
   (contexto, complemento, arriba, abajo). luxe_macro.comp_luxe toma el macro tal cual de un .drb del pack (luxe_shine_*/luxe_slide_*) y solo
   le cambia tipografía, color, tamaño y posición. Ya no hay imitaciones con Text+ sueltos (antes contexto/complemento/base de los packs Viral
   solo se LLAMABAN «Luxe Slide»). «Generar» del editor usa un pack de verdad, igual que GO (_asegurar_pack_luxe).
   Un pack cuyo contenido cambia lleva una «revisión» (plantillas.REVISION_BIN → manifiesto plantilla.revision → los scripts la suman al nombre
   del bin: «RCS · <pack> · <revisión> · v»); sin ella un proyecto que ya tenía el bin viejo lo seguiría reutilizando.

## nota — v5.8 · «Crea tu estilo»

v5.8 · «Crea tu estilo» (página Proyecto > Pack de estilos): ejemplos_estilo.py define 30 ejemplos = posición (5) × estilo tipográfico (6) × colores (principal y arriba/abajo); la galería
(crea_estilo_ui.CreaEstiloDialogo) los muestra con su imagen (pintada con las mismas fuentes y posiciones), se tocan hasta 3 (= variantes 1, 2 y 3) y «Crear mi pack» llama a
ejemplos_estilo.crear_pack: generador_packs/construir_pack.construir con y_por_comb (cada variante en su posición: se reescribe el Tilt del blob del clip en el .drb, zstd) y
nombres_nuevos (la estructura arriba / principal / abajo / simple), todo con macros REALES Luxe Shine/Slide. «Abrir los 30 en Resolve» escribe guia_estilo_ejemplos.json y corre
guia_estilo/construir_guia.py dentro de Resolve: importa «Crea tu estilo.drb» en el bin «RCS · Crea tu estilo (bloques)» y apila 3 clips por ejemplo (V1 principal, V2 arriba, V3 abajo)
con fuente/color/tamaño (Text1, sizeCtrl.RestingSize, texto en «Template»), Tilt y un marcador por ejemplo. Los clips se llaman «07 · principal» A PROPÓSITO: hay que ponerles el nombre
exacto. El «!» (crea_estilo_ui.AyudaEstilo) explica por qué: CineCaptions solo lee NOMBRES (packs_drt.parsear_nombre), las variantes se agrupan por número (máx. 3) y sin la estructura
el clip se ignora. OJO: Resolve lee el nombre del clip del FieldsBlob del .drb, NO del <Name> del XML (los .drb de packs nuevos se ven allí con los nombres viejos contexto/complemento/base).

## nota — v5.8 · «Crea tu estilo» v2

v5.8 · «Crea tu estilo» v2: 48 ejemplos (los 18 últimos llevan de PRINCIPAL un preset de Amro.Films Captions —Highlight naranja/rosa, Underline verde/amarillo, Fire, Strike— copiado tal cual de
guia_estilo/Amro principales.drb; arriba y abajo SIEMPRE Luxe Slide; construir_pack: combo['principal_drb'] + combo['rel']). Cada ejemplo muestra su VISTA REAL Y ANIMADA: vistas_guia.renderizar corre
construir_guia.py en modo 'vistas' (timeline temporal con la marca de los temporales, 7 fotogramas por ejemplo —ejemplos_estilo.CUADROS_VISTA_S: la entrada y el resultado final—; no borra nada
en caliente y deja timeline, cabezal y página como estaban), reduce con Pillow y guarda ej_NN_K.jpg en ~/DaVinciSubtitles/plantillas_cache/guia_estilo/vistas. La galería los REPRODUCE en bucle
(fundido entre fotogramas, resultado sostenido 1,7 s; un reloj de 40 ms solo mueve las tarjetas que se ven) y pide las vistas sola solo si faltan (las de fábrica viajan en guia_estilo/vistas).
Cada tarjeta lleva «Vista real · Resolve»: carga SOLO ese estilo en un timeline «Estilo · <nombre>» (construir_guia.py en modo 'guia' con datos['ejemplos'] filtrados por ids). Cada tarjeta de «Pack de estilos» lleva ✎ (doble clic igual): edicion_pack.abrir_en_resolve → editar_pack.py importa el .drt del pack o, si solo trae .drb, arma el timeline
con los clips ya nombrados (principal, arriba 2…) y su Tilt; y 🗑 (los packs del usuario se borran; los incluidos solo se quitan de la lista: pref packs_ocultos).

**Proyecto compacto (v5.4.3):** la pantalla NO se desplaza (`_nueva_pagina(..., desplazable=False)`): una sola tarjeta con, de arriba abajo, la **franja de audio** (`_tarjeta_fuente`, construida en `_pagina_nuevo` como `Tarjeta(nombre='franja_audio')`: Obtener · archivo · onda · duración · «Transcribir con» + motor; el detalle de GPU/modelo va al tooltip del selector), la cabecera «Pack de estilos» (+ «Crea tu estilo» y «Vista real · Resolve»), el slider (`CarruselPacks(flexible=True)`: se estira con el alto libre, las tarjetas se escalan con él) y el panel del estilo central. `PlantillasWindow(franja=…)` la coloca dentro de su tarjeta (`_asegurar_estilos`). La rueda del ratón mueve el slider en cualquier punto de la página (`qt_kit.RuedaHacia` sobre `self._paginas['estilos']`).

**Simplificación (v5.4.4):** el slider de Proyecto muestra SOLO packs (`PlantillasWindow._recargar` ya no crea las cartas `media_pool` / `auto`; esos valores siguen existiendo internamente en `plantilla_sel` para GO y proyectos viejos, y si es el guardado el slider simplemente no marca ninguna «En uso»). Sin botón «Vista real · Resolve» (`real_btn` eliminado): las vistas reales se piden solas con `_vistas_reales_solas()` (cada vez que se entra a Proyecto con Resolve conectado y al terminar el recorrido; silencioso, no abre Resolve). «Crea tu estilo» (`crea_estilo_ui.CreaEstiloDialogo(padre, al_crear, …)`) es una sola galería de los 48 ejemplos: sin filtros Posición/Estilo, sin botón por tarjeta, sin «Abrir los 48 en Resolve» ni «!»; `al_resolve/al_ayuda/al_resolve_uno` se aceptan por compatibilidad pero no se usan. Pie: resumen + nombre + «Crear mi pack».

**Packs de fábrica «Shine» y video en el slider (v5.4.5):** `plantillas.FABRICA = {'Kinetic': 'Shine Kinetic', 'Referencia': 'Shine Referencia'}`; el nombre INTERNO no cambia (prefs, GO, carpetas) y `plantillas.nombre_visible()` / `es_de_fabrica()` se usan para mostrar el nombre (tarjeta, chip «Estilo» de Inicio, menú de GO) y para que NO se puedan quitar (sin 🗑, `_quitar_pack` no hace nada, `packs_ocultos` los ignora). Cada tarjeta de fábrica reproduce un VIDEO con los captions reales de Resolve: `2_recursos/vistas_slider/<pack interno>.mp4` (+ `.jpg` = fotograma fijo para las tarjetas que no están al centro; sin audio; viaja en los instaladores, carpeta `vistas_slider` en los dos .spec). `vistas_slider.Reproductor` decodifica con PyAV en un hilo (en bucle, desde el principio al llegar al centro; se para al cambiar de tarjeta o al ocultar el slider) y `estilos_slider.CarruselPacks._cuadro_video` lo pinta en la tarjeta (`Carta.video/poster`); sin video se usa la foto + captions de siempre. Para (re)hacer un video: `python 1_codigo/hacer_vista_slider.py <video.mp4> <pack interno> 2_recursos/vistas_slider/<pack>.mp4` (suelta el video en la app sin pantalla con el pack forzado, Resolve renderiza el timeline y ffmpeg lo reduce; limpia y restaura el proyecto). Hay que repetirlo si cambian el pack o su planificador. Fuentes: Kinetic ← `PRUEBAS (5).mp4` (32 s), Referencia ← `PRUEBAS (6).mp4` (2 min), del Escritorio del usuario. Los packs con video ya no piden la «vista real» a Resolve.

**«Crea tu estilo» con animación completa y fondo (v5.4.5):** cada ejemplo es un CLIP de 4 s (entrada, texto sostenido y SALIDA) renderizado por Resolve sobre negro: `2_recursos/guia_estilo/vistas/ej_NN.mp4` (48 clips, ~700 KB; sin fotogramas sueltos ni `ExportCurrentFrameAsStill`). Se generan con `python 1_codigo/hacer_vistas_guia_video.py [carpeta] [--ids 1,2]`: `construir_guia.py` modo 'vistas' arma el timeline temporal con los 48 (macros Luxe + presets Amro), la cola de render de Resolve lo renderiza y ffmpeg lo corta (duración real = fotogramas/fps: a 29,97 fps son 4,004 s, si no se acumula deriva), limpia timeline y bins. `ejemplos_estilo.ruta_video(ej)` los localiza (manda el del equipo en `~/DaVinciSubtitles/plantillas_cache/guia_estilo/vistas`); `vistas_guia.faltan()` ya no pide nada si el clip de fábrica existe. `crea_estilo_ui._Tarjeta` pinta la FOTO de muestra (`estilos_slider.fotos()`, una distinta por tarjeta vecina, oscurecida) y el clip encima en modo Screen (`vistas_slider.Reproductor`, solo suenan las tarjetas que se ven); sin clip, los 7 fotogramas de la entrada y, sin ellos, la aproximación pintada. Tres botones `Texto alto / Texto medio / Texto bajo` (`CreaEstiloDialogo.GRUPOS`: alto = superior+alto, medio = centro, bajo = bajo+inferior; inicial «Texto medio») ordenan la galería. Proyecto ya no muestra «Mostrar los packs quitados» (`ocultos_lnk` siempre oculto).

**Video de VIRAL en el slider (2026-10-09, sin compilar):** `2_recursos/vistas_slider/VIRAL.mp4` (16,6 s, 486×864, 1,5 MB, sin audio) + `VIRAL.jpg` (póster: fotograma de 14,5 s) se hicieron con `hacer_vista_slider.py "<PRUEBAS (9).mp4>" VIRAL …` (GO real en un proyecto nuevo de Resolve, render y ffmpeg); la tarjeta lo reproduce al quedar al centro y muestra TODA la secuencia (pila, shatter, select, drag, emojis, intro, zoom). `vistas_slider.ruta_video(pack.nombre)` lo coge por el nombre del pack. Quedan sin video «Base títulos dinámicos», «Viral · inferior» y «Viral · superior». Repetir cuando cambie el aspecto de VIRAL.

**Solo los tres temas (v5.4.19, pedido del usuario):** `plantillas.FABRICA = {'Kinetic': 'Tema 1', 'Referencia': 'Tema 2', 'VIRAL': 'Tema 3'}` (el nombre interno no cambia: prefs, carpetas, bins de Resolve y vistas siguen con Kinetic/Referencia/VIRAL) y `plantillas.SOLO_TEMAS = True`: el slider de «Pack de estilos» (`PlantillasWindow._recargar`) y el chip «Estilo» de Inicio (`_menu_estilo_go`) enseñan SOLO esos tres (sin packs importados, «Viral · superior/inferior», «Añadir plantilla», «Diseño automático» ni el botón «Crea tu estilo», que además se quita del recorrido). Son de fábrica: sin 🗑 ni «Quitar». Un `go_pack` guardado que no sea uno de los tres cuenta como «sin elegir» (`_go_pack_pref`) y GO usa el pack en uso/Tema 2; el diseño automático sigue existiendo por dentro como respaldo (vídeos horizontales con un tema solo vertical). Los avisos de GO usan `plantillas.nombre_visible`. Poner `SOLO_TEMAS = False` devuelve todo lo anterior.

**Ajuste v5.4.22 (el usuario devolvió lo propio):** `plantillas.SOLO_TEMAS` ya no esconde TODO lo que no sean los tres temas: esconde solo los packs que TRAE el programa y no son de fábrica («Viral · superior/inferior»…); los packs del usuario («Crea tu estilo», «Añadir plantilla .drb») salen en el slider junto a Tema 1, 2 y 3 (`plantillas.pack_permitido`). La cabecera de Proyecto es solo el título «Temas» y el botón «Crea tu estilo»; el slider termina con la tarjeta «Añadir plantilla (.drb)». El panel de un tema de fábrica es solo nombre + botón; el de un pack del usuario conserva ✎ / 🗑 / ⋯. El menú del chip «Estilo» lista los tres temas y los packs del usuario (sin «Diseño automático»).

## mezcla-temas — «Crea tu estilo» mezclando los 3 temas (v5.4.30)

**Qué:** la galería de «Crea tu estilo» trae, además de los 48 ejemplos de Luxe (grupos «Texto alto/medio/bajo»), TODOS los looks de los tres temas en tres grupos nuevos (inicial «Tema 1»): Tema 1 = las 6 recetas de `kinetic_planificador.RECETAS`, Tema 2 = los 8 estilos de palabra grande de «Referencia» (`guion_captions.datos_variantes`), Tema 3 = pila fina + negrita y los efectos shatter / select / drag. Se tocan hasta 8 (`mezcla_planificador.MAX_LOOKS`); los looks de los Temas y los ejemplos de Luxe NO se mezclan (tocar de la otra familia empieza una elección nueva). «Crear mi pack» guarda un pack `pack.json` `{"guion": "mezcla", "looks": ["t1:lima", "t3:shatter", "t2:3"], "formatos": {"v": {"mezcla": true}}}` + `vista_mezcla.jpg` (la foto de su tarjeta) en la carpeta de packs del usuario; en el slider de temas sale como «Mezcla de temas» (sin ✎: no tiene timeline que editar; su nota lista los looks).

**Cómo funciona:** `mezcla_planificador.planificar(palabras, looks, …)` parte lo hablado en TRAMOS (una o varias frases, ≥5 palabras o ≥2,6 s), da a cada tramo un look (rotando) y llama al planificador de ESE tema solo con las palabras del tramo (`KP.planificar(recetas=_Fijo(n))`, `VP.planificar` con `ROTACION=(efecto,)`, `GP.planificar(estilos=…, variar_barrido=False)`); luego junta, ordena y acorta lo que se pise. `SubtitleApp._generar_con_mezcla` (la despacha `_generar_con_motor` antes que Kinetic y «guion») saca DOS pistas de datos: `kinetic` (Tema 1 + Tema 3: mismo colocador; pack principal Kinetic, o VIRAL si no hay Tema 1, y `plantillas_extra` con el pack VIRAL si hay de los dos) y `guion` (Tema 2, pack Referencia); sonidos por todos los bloques, emojis solo en los de VIRAL y «guion». `_poner_pistas_motor` las mete al manifiesto y marca `manifest['mezcla'] = True`.

**Resolve (los dos scripts gemelos):** con `manifest.mezcla` se limpia UNA vez todo lo nuestro de cada idioma y se marca `no_retirar` en las pistas (ningún estilo borra las pistas del otro: `place_kinetic`, `place_guion`, `colocar_emojis`); `place_kinetic` prepara también los bins de `plantillas_extra` y busca cada clip en el bin principal y en los extra; los EMOJIS y los SONIDOS se apartan en `MEZCLA_ACUM` (Lua) / `_MEZCLA_ACUM` (Python) y se colocan UNA vez al final (`colocar_emojis` y `place_sfx` limpian la pista que reutilizan: dos llamadas se borrarían entre sí).

**Vistas:** `mezcla_vista.vista(id, foto, ancho)` / `poster(ids)` (solo Pillow, sin Resolve ni Qt: se hacen en un hilo) planifican una frase de muestra con el planificador real de cada tema y dibujan el bloque que enseña el look sobre una foto de `2_recursos/fondos_estilos`: es una MAQUETA (sin animaciones, brillos Luxe ni Fusion).

**Clips REALES de cada look (v5.4.32):** cada tarjeta de un Tema reproduce `2_recursos/guia_estilo/mezcla/<id>.mp4` (6 s, 304 px, sin audio, sobre NEGRO; `t1_lima`, `t2_3`, `t3_shatter`…; ~320 KB los 18) mezclado en «Screen» sobre una foto, igual que las de Luxe (`crea_estilo_ui._TarjetaLook._ruta_video` + `vistas_slider.Reproductor`). Sin clip (aún no se hizo) vuelve la maqueta de Pillow. Se hacen con `python 1_codigo/hacer_vistas_mezcla.py [salida]`: video negro de 18×6,5 s + transcripción inventada → GO sin pantalla con un pack de mezcla de los 18 looks (sin sonidos, emojis ni efectos; `colocacion.reproducir_desde_inicio` anulado) → render por el Puente de Free con `CineCaptions_Vista.lua` (acciones `render`, `render_estado`, `render_parar`; MarkIn/MarkOut para un tramo) → ffmpeg corta un clip por look. **Se renderiza POR TEMAS** (39 s, 52 s y 26 s): un render de los 117 s se quedó quieto en 33 % (CPU a 0, archivo de 0 bytes) con 73 comps de Fusion; `_renderizar` vigila el avance (120 s sin moverse → `render_parar`). Resolve Free se cierra solo si GO reproduce el timeline mientras se renderiza. Repetir si cambian planificadores, packs o `FRASE`.

**Prueba:** `python 1_codigo/probar_mezcla_app.py <palabras.json> [--looks t1:lima,t3:shatter,t2:3] [--manifiesto salida.json]` (sin pantalla ni Resolve, packs en una carpeta temporal); en Resolve, `CINECAPTIONS_PACKS=<carpeta con el pack> python probar_go.py <video> "<nombre del pack>" --soltar`. Solo vertical.

## tema4 — Tema 4 «Captions limpios» (v5.4.33, sin compilar)

**Qué:** replica `TEMA 4.mp4` del usuario (1080×1920, 23 s). Medido sobre el video: UN recuadro de texto centrado (x de 320 a 762 px de 1080), primera línea de base fija al 57,6 % del alto, máximo dos líneas CENTRADAS, una sola tipografía (Inter, blanca, letras apretadas) con un halo blanco suave, y TRES tamaños sobre la misma línea de base: la palabra clave grande, las normales y las conectoras (es, lo, que, de, y…) pequeñas. Cada LÍNEA se escala por su cuenta hasta llenar el recuadro (con un tope: una línea corta no se infla sin fin), así que las frases cortas salen grandes y las largas pequeñas. Las palabras aparecen una a una en su sitio final y la frase siguiente reemplaza a la anterior. Entrada rápida (~3 fotogramas).

**Cómo está hecho:** mismo motor que «guion» (un clip por palabra con x, y y zoom; `place_guion` sin cambios). `pack_tema4.py` arma el pack `plantillas_incluidas/Tema4/` (`pack.json` `"guion": "tema4"`, 1 variante «Blanco»): los tres roles son Inter 24pt Bold blanca con el MISMO «Size» base grande (0,14) para que el texto se rasterice grande y solo se REDUZCA con el zoom; `principal` = Luxe Shine (barrido corto), `arriba`/`abajo` = Luxe Slide; el halo de los macros (nodo `glow1`) se refuerza con `luxe_macro.comp_luxe(brillo=(26, 0,95))` (de fábrica 17,3 · 0,48). `guion_planificador.cues_de(pack='Tema4')` despacha a `tema4_planificador.cues_de`, que parte lo hablado en bloques por PESO (palabra normal 1, conectora 0,5, máx. 5,5 y 38 letras), elige la clave (la primera palabra con peso de cada oración, o la marca «Principal» de Creativo), prueba cada corte de línea y calcula tamaño y posición con la tipografía de verdad (Pillow); la palabra suelta final se lleva su determinante («…hasta | tu negocio»). Salida en el formato de `place_guion` (`rol` main/complement/context = clave/normal/conectora, `zoom`, `caja` para el emoji). `plantillas.FABRICA['Tema4'] = 'Tema 4'`, `REVISION_BIN['Tema4']` (subir al cambiar el pack), `recomendaciones.py` (como Referencia).

**Prueba contra la referencia:** `python 1_codigo/probar_tema4.py <palabras.json> [--salida carpeta] [--tramo 8]` (palabras de la referencia: `~/DaVinciSubtitles/mcp/palabras_TEMA 4.json`, hechas con el MCP `transcribir`): video negro + GO sin pantalla + render por tramos en Resolve Free (acciones `render`, `render_estado`, `render_parar` de `CineCaptions_Vista.lua`) y los .mov salen en la carpeta; se comparan fotogramas con la referencia. `tema4_vista.dibujar` es la maqueta de Pillow (sin Resolve). **Trampa:** Resolve Free se queda «No responde» (5-8 GB) tras 3-4 proyectos y renders: `hacer_vistas_mezcla.resolve_colgado()` lo detecta y el GO se niega a lanzarse; hay que cerrar Resolve a mano. **Pendiente:** el video del slider (`vistas_slider/Tema4.mp4/.jpg`), el Tema 4 en «Crea tu estilo» y en la mezcla (dos pistas «guion» chocarían en los nombres `L-T<n>`: haría falta un sufijo propio), emojis y efectos probados con los videos de PARA PRUEBAS.

## tema5 — Tema 5 «Edición total» (sistema de la skill «Edit VIRAL Reels with AI»)

`edicion_pro_tema5.planificar` arma la edición entera con la Edición PRO (va siempre con este tema): pasos y deslizador sobre cristal oscuro,
escenas de papel con cuadrícula (pantalla completa o dividida), órbita, tarjeta tachada, acompañantes, final y sonido (guía de sonido). Su
diseño de captions es sans pequeña + frase clave serif cursiva (DM Serif Text) en el acento del video (`acento_de_video`), hecho en Remotion
(`Subtitulo.tsx`, pista PRO-SUBS). v5.5.8: por defecto (`pro_captions_editables`) esos captions de Remotion NO se ponen: quedan los Text+ del
pack «Tema5», editables en el Inspector. Las piezas de la PRO general que no son de este sistema se quitan (`PIEZAS_QUE_QUEDAN`). Vista de
desarrollo: `herramientas_dev/vista_tema5.py`.

**Text+ editables con el diseño de Remotion (v5.5.8):** `guion_planificador.cues_de` → `tema4_planificador` con `DISENOS['Tema5']`: los
MISMOS bloques y tiempos que el Tema 4, pero `_planificar_skill` elige la frase clave como `Subtitulo.tsx` (`edicion_pro_tema5.marcar_claves`;
con marcas de Creativo, las palabras «Principal») y `_disponer_skill` copia su maquetación: lo dicho en Inter 18pt Medium blanca (S = 3,5 %
del lado corto ≈ 38 px), la clave en DM Serif Text Italic ×2,4 en su propia línea (o en la de 1-2 palabras cortas de delante), líneas de ≤ 34
letras, hueco 0,27 em, todo centrado en `y` 56 % y reducido si la línea más ancha pasa del 86 % del ancho. Cada palabra se MIDE con su
tipografía (`_ancho_em(texto, fuente, espaciado)`, `_metricas`: línea de base y centro del Text+ desde hhea —Inter da 0,364 = `CENTRO_CAP`—)
y, a diferencia de Remotion (donde la serif y la sans «se tocan»), `_tinta` + `AIRE_SKILL` bajan la línea siguiente si un descendente de la
clave la pisaría. Rol `main` = la clave, `complement` = lo demás; zoom = letra / (Size del rol × `K_PX` × `CALIBRADO[fuente]['em']`).
`CALIBRADO` (MEDIDO en renders a 1080 de Resolve Studio 21.1, GO reales v5.5.8): Fusion escala cada tipografía por su alto de línea, em ≈ 1,30 /
(asc + desc de hhea): Instrument Serif 1,0 (alto 114 px medido / 113 previsto; ancho de tinta 0,94–0,97 del avance; centros a ±4 px), DM Serif
Text Italic 0,948 (alto 94 / 91; ancho 0,97–1,0), Inter 18pt Medium 1,074 (por el mismo modelo; cuadra con el 1,08 medido del Inter Bold del
Tema 4). Con eso el `ancho` de las tres es 1,0 (el 1,08 de `AFINADO` es solo del Tema 4, con su espaciado 0,95). Para medir:
palabras clave sueltas, por su color, en el render. El
color: el pack trae una variante por acento (`pack_tema5.py`: 1 azul · 2 ámbar · 3 lima · 4 lila, = `ACENTOS`) y `_variante_acento` pone en
el `estilo` de cada cue la del video (`acento_de_video`, en caché por ruta y fecha; el video llega por `guion_editor.planear(video=…)` desde
`_generar_con_guion`; sin video —vista del editor—, azul). Los scripts de Resolve no cambian (Pan/Tilt/Zoom por palabra, variante por bloque).

## tema6 — Tema 6 «Editorial»

`edicion_pro_tema6`: el motor del Tema 5 con `estilo='editorial'` y el look del reel de referencia del usuario: serif alta y fina (Instrument
Serif) con la frase clave en lima (`color_clave`) o blanco, escenas melocotón con cartas blancas y destello, y los elementos de Remotion
«EditorialT6» (visor sobre la cara, barra de búsqueda que escribe la palabra a comentar, perfil con la cifra de seguidores, píldora del
equipo). Sin pasos ni deslizador. Captions: igual que el Tema 5 (v5.5.8: Text+ editables del pack «Tema6» por defecto).

**Text+ editables (v5.5.8):** `DISENOS['Tema6']` (estilo «editorial» de `Subtitulo.tsx`): todo en Instrument Serif Regular, lo dicho pequeño
y blanco (S = 4,8 %), la clave ×2,3; cada bloque lleva su línea grande (`marcar_claves(…, editorial=True)`) y su color sale de
`edicion_pro_tema6.color_clave` con `temas_del_video` (lima `#DDF25E` = variante 1, blanco = variante 2 del pack «Tema6»); centro en `y` 52 %.
La tipografía: `2_recursos/fonts/InstrumentSerif-Regular.ttf` (OFL; convertida a TTF con fontTools desde el `serif-400.woff2` de Remotion, ver
`fonts/LICENCIAS.txt`); el instalador la instala con las demás de los packs (`pack.fuentes()`).

**Packs «Tema5»/«Tema6»:** `2_recursos/generador_packs/pack_tema5.py [Tema5|Tema6]` (armado de `pack_tema4.construir`, que ahora acepta
`combos`/`guion`): principal = Luxe Shine con la clave (Size base 0,15 / 0,19), arriba/abajo = Luxe Slide con lo dicho (0,065 / 0,085), halo
suave (10 · 0,30), entrada/salida 0,16/0,10 s. Tipografías, tamaños y espaciado salen de `tema4_planificador.DISENOS` (una sola fuente de
verdad). `REVISION_BIN` 'T5 2' / 'T6 2'.

## temas-ligero — Temas 1–4: pase ligero sin la Edición PRO

`edicion_pro_temas.piezas` (v5.4.51): sin activar la PRO, los captions Text+ de los Temas 1–4 se ven mejor: velo oscuro suave detrás de cada
pila en videos claros (`VELO_CAPTIONS`, apagado desde v5.4.52), acompañantes pequeños bajo el caption, la palabra destacada con el acento
del video (`color_claves`, estilo «guion») y la regla de la cara (`edicion_pro._captions_sin_cara`). Lo coloca `colocar_pro.py` /
`CineCaptions_EdicionPro.lua` con `ligero`.

## nota — v5.5.8 · Tema 4 (y 5/6): hueco entre palabras

`tema4_planificador.HUECO` 0,12 → 0,28 (× la letra normal de la línea) y `AFINADO['ancho']` 1,0 → 1,08 (cada palabra sale en Resolve un 5–13 % más ancha que lo que mide Pillow; medido en el render del Tema 5: «héroes» 142 px contra 129 calculados). MEDIDO en el render a 1080 de Resolve (Tema 6): 7 px de hueco con
letra de 58 px; se leían pegadas («Numberone», «stopoversizing»).

## banner-inspector — El banner de CineCaptions ARRIBA DE TODO en el Inspector (v5.5.8)

**Qué:** cada caption de los packs lleva un LabelControl HTML «CINECAPTIONS · Personaliza aquí tu caption…» (`2_recursos/generador_packs/banner_inspector.py`).
Va con `IC_ControlPage = -1`: ENCIMA de la fila de pestañas del Text+ (Texto, Distribución…), visible en todas; es la misma técnica que usa la
cabecera del propio macro Luxe. En los macros (Luxe Shine/Slide) va en el Text+ de dentro y además se publica como el PRIMER InstanceInput del macro;
en Kinetic/VIRAL va en el Text+ `Template`. `python banner_inspector.py <carpeta|.drb>` reescribe los blobs (mismo prefijo y longitudes) y es
idempotente (pone al día el banner viejo); `construir_pack.blob_de_comp` lo aplica a los packs nuevos. Al cambiarlo, subir `plantillas.REVISION_BIN`.
Los clips de video (motions de Remotion, efectos sobre V1, emojis) no pueden llevarlo: Resolve no enseña controles de Fusion para ellos.
