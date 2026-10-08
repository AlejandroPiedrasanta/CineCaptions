# Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)

## pantalla-estilos — Pantalla Estilos / packs

**Qué:** La pantalla «Proyecto» (`_pagina_estilos`): tarjeta Audio (Obtener + motor de voz, se construye en `_pagina_nuevo`), «Pack de estilos» (slider) y la banda «Crea tu estilo» justo debajo (v5.3.6). Ya NO existe la tarjeta «Tipografías que usa el pack» ni el filtro Horizontal/Vertical: las vistas son siempre verticales (`_formato_vista` prefiere 'v'; `_formato_edicion` conserva el formato del timeline para abrir un pack en Resolve). Si al pack le faltan fuentes, el panel de debajo del slider muestra «⚠ Faltan N tipografías · instalar» (`_instalar_fuentes_central`).

**Dónde:** script principal · `class PlantillasWindow`: `__init__` (arma slider + panel + `_construir_crear`), `_recargar` (rehace las tarjetas, se queda en la del centro; `_carta_simple` Media Pool/Diseño automático, `_carta_pack`, `_cartas_basicos` en el modo «normal» con las combinaciones como chips del panel), `_pintar_info` (panel del estilo central: nombre, nota, estructura, «Usar este estilo»/«En uso», ✎ 🗑 ⋯), `_elegir`, `_realzar`, `_valor_actual`. El slider en sí: `estilos-slider`.

## estilos-slider — Slider horizontal de «Pack de estilos» (tarjetas verticales sobre fotos)

**Qué:** v5.3.6. Un solo widget (`CarruselPacks`) pinta todas las tarjetas 9:16 con un resorte (arrastrar, rueda lateral, ← →, puntos, clic en la vecina = centrarla, clic en la central = usar el estilo). La del centro va grande, con la foto en paralaje, giro tipo coverflow en las vecinas, resplandor del color medio de la foto y los captions EN MOVIMIENTO; las de los lados se pintan una vez en un pixmap (`_pixmap_estatico`) y solo se estiran. Fondos: `2_recursos/fondos_estilos/fondo_NN.jpg` (11 fotos de video 9:16; una por tarjeta según el nombre del pack). Captions: la vista REAL de Resolve (`vistas_reales`: fotogramas sobre NEGRO) se compone en modo Screen sobre la foto, a su tiempo real (`CUADROS_S`), una variante tras otra; sin vista real se dibujan las líneas aproximadas (`lineas_de_vista` → `MarcoVista._pintar_contenido`, método que sale de `MarcoVista.paintEvent` para poder pintar en cualquier rect) con una banda oscura detrás. `Carta` = lo que sabe el carrusel de un estilo; `HeroCrear` = la banda de «Crea tu estilo».

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
