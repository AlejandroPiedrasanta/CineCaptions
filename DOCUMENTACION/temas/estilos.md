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
