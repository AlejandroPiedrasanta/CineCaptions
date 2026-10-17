# Editor Creativo (palabras, Asistencia, Generar)

## editor-palabras — Editor de palabras (pintar roles)

**Qué:** Editor de palabras (pintar roles)

**Dónde:** script principal · `class WordTagWindow`, `_poner_rol`, `_actualizar_contador_pronto`, `_bloques_actuales`; lienzo: `class LienzoPalabras`

## creativo-ui — Editor Creativo: barra, tarjeta, play, Asistencia, Generar

**Qué:** Editor Creativo: barra, tarjeta del párrafo, play, panel de avance (Asistencia / Generar)

**Dónde:** `editor_ui.py` · `BarraHerramientas`, `MarcoPapel`, `ControlTamano`, `BotonPlay`, `PanelAsistencia`; flujo Generar: script principal · `_receta_generar`, `_gen_abrir`, `_gen_fase`, `_gen_fin`, `_regenerar_marcas`

**v5.5.10 (pedido: móvil + sin barra + Generar a Inicio):** «Así se verá este bloque» es un MÓVIL: `MarcoVista(movil=True)` (qt_kit: `_recursos_movil`, `geometria_movil`, `_pintar_movil`, `_pintar_en_pantalla`) pinta la foto de muestra `2_recursos/creativo/movil_fondo.jpg` dentro de la pantalla, los captions encima (franja abajo-centro) y el marco `movil_marco.png` (pantalla transparente; su caja en `movil.json`) por encima; el render real de Resolve se ve dentro de la pantalla. El estilo «guion» (`MarcoVistaGuion._pintar_en_pantalla`) pone el cuadro 9:16 entero a lo ancho de la pantalla, con cada palabra en su sitio real. La mini-posición ya no sale (el móvil la enseña). La barra de herramientas solo aparece con «Más herramientas»; el tamaño del párrafo (`ControlTamano`) y «Generar» van en la fila de arriba, junto a «Más herramientas». La columna derecha (`_derecha`, 400 px) es SOLO el móvil a todo el alto, con el play dentro de la pantalla (`MarcoVista.poner_boton_en_pantalla`); debajo, solo con «Más herramientas», los ajustes del bloque. La tarjeta «Así se verá este bloque» (título, tiempo, SFX, estilo del bloque, «Comprobar en Resolve», nº de bloques) se sigue creando para que el código la actualice, pero vive en `_piezas_ocultas` (nunca se enseña). **Generar** ya no abre el popup: `_sesion_editor` vuelve a Inicio y `_gen_abrir` usa el orbe de GO (`go_panel`: timeline/voz/IA «saltado»; armar/emojis → diseño, sfx → sonido, colocar → Resolve; `_GEN_A_PASO_GO`), sin «Cancelar» (es el de GO). Dentro de un GO, Inicio ya enseña el avance de GO. Capturas sin pantalla: crear `WordTagWindow`, meterla en `_editor_capa`, `ir_a('editor')`, `grab()`; luego `_gen_abrir` / `_gen_fase` / `_gen_fin`.

## nota — CREATIVO v5.7b

CREATIVO v5.7b: se quitó «Peso de conectores»: dyn.normalizar_peso_conector() devuelve SIEMPRE 1.0 (palabra por palabra). Los máximos Arriba/Principal/Abajo se reajustan EN VIVO (WordTagWindow._on_tamanos_change -> _reajustar_en_vivo, debounce 90 ms) si los roles son de la IA (_roles_auto; cualquier marca a mano lo apaga: aparece «Reajustar con IA»). _calcular_alternativas = las 4 versiones de la IA con los máximos actuales (usa el análisis cacheado _ia_cache: instantáneo); selector «Versión de la IA» 1-4. Todo con deshacer (un solo Ctrl+Z por tanda de clics).

## nota — v5.7 · Creativo

v5.7 · Creativo (párrafo): el lienzo (LienzoPalabras) es transparente y vive en editor_ui.MarcoPapel (tarjeta de esquinas redondeadas); cada frase se dibuja en su panel redondeado con la hora en pastilla (_paneles/_pastillas en dibujar). editor_ui.PistaPincel dice qué hace el pincel elegido (_actualizar_pista_pincel). «Capitalizar palabras de contenido» está en la barra de herramientas, junto a ✕ Emojis.

## nota — v5.7 · «Marcar con IA» ahora se llama «Asistencia»

v5.7 · «Marcar con IA» ahora se llama «Asistencia» (chip del editor, diálogo, avisos y traducciones en 2_recursos/locales). Su diálogo es editor_ui.PanelAsistencia: orbe animado + 4 pasos reales (estado['fase'] lo pone el hilo de _sugerir_con_ia) + barra; al acabar muestra «Listo» 650 ms. El deslizador de tamaño del párrafo (editor_ui.ControlTamano, junto a «Capitalizar») llama a WordTagWindow._poner_tam_letra (aplica con 45 ms de debounce y guarda a los 700 ms).

## nota — v5.7 · «Generar» del editor

v5.7 · «Generar» del editor (WordTagWindow._continuar -> SubtitleApp._sesion_editor -> _receta_generar): aplica la receta de GO (efectos según el
interruptor «Efectos» de Inicio = pref go_sfx; los emojis son los de las palabras) y abre un popup (editor_ui.PanelAsistencia con los pasos armar /
sfx / emojis / colocar). El avance es REAL: el hilo manda ('gen_fase', clave) por msg_queue; _colocar_en_resolve marca «colocar»; 'colocado_en_resolve',
'error' o un fallo lo cierran (_gen_fin). «Editar marcas y regenerar» (_on_update) ya no genera en el hilo de la interfaz: _regenerar_marcas corre en un hilo.
Archivos: archivos_seguros.py (escritura atómica + cerrojo; preferencias, marcas con .bak, proyectos, manifiestos). Nada de write_text() directo para estado del usuario.
Regla: ninguna llamada a resolve_mcp/resolve_bridge que espere a Resolve (modo_actual() sin pasivo, disponible(), estado()) en el hilo de la interfaz: usar correr_en_hilo.

## creativo-vista-tema — Creativo: vista EXACTA del tema elegido en el móvil (v5.5.10)

**Qué:** pedido «en Creativo la vista previa real de cómo se verá en Resolve: que detecte el tema que uso, que al dar play se vea exactamente como ese tema y que si cambio la principal se vea en tiempo real». El móvil de la columna derecha enseña el bloque con el DIBUJO del tema elegido en Proyecto (`plantilla_sel`), no la maqueta aproximada.

**Cómo:** `vista_tema.py` · `estilo_de_pack` (los 6 de `plantillas.FABRICA`: Kinetic → `kinetic`, VIRAL → `viral`, Referencia/Tema4/5/6 → `guion`; lo demás → None y queda la vista de siempre) · `planificar` (el MISMO planificador que Generar: `guion_editor.planear` o `kinetic_/viral_planificador.planificar` con `mains` = las marcas de Principal; anclas de las prefs; el emoji de una palabra del bloque va al cue, salvo Kinetic) · `Cuadros` (la foto `2_recursos/creativo/movil_fondo.jpg` cubriendo la pantalla + `render_sin_resolve.preparar`: el 9:16 a lo ancho y centrado, como un reel; `cuadro(t)` compone con `componer`). En `WordTagWindow`: `_vt_preparar` replanifica y rasteriza EN UN HILO (`correr_en_hilo`) cuando cambia la clave `(_version, tema, ancho, alto)` —cada marca nueva sube `_version`—; mientras tanto se ve el cuadro anterior (o la primera vez la maqueta). `_vt_quieto(idx)` (desde `_mostrar_bloque`) pone el cue donde cae esa palabra con todo dentro (`instante_quieto`); `_tic_reproduccion` pone `cuadro(t)` a 30 fps y la barrita de avance; `showEvent` y el cambio de tamaño del móvil (`al_cambiar_tamano`) lo rehacen (otro tema elegido en Proyecto). El móvil (`qt_kit.MarcoVista` en modo móvil): `poner_cuadro`, `poner_progreso`, `tamano_pantalla` (píxeles reales, HiDPI), sombra, barra de estado (9:41, cobertura, wifi, batería), indicador de inicio y reflejo del cristal.

**Palabra → bloque:** `vista_tema.cue_de_palabra` busca el bloque que LLEVA la palabra escrita (el más cercano en el tiempo), no el que cubre su instante: un bloque de Kinetic puede empezar después de su primera palabra (se retrasa para no pisar el anterior) y al tocar «licensed» se veía el bloque de antes.

**Banco (2026-10-17):** `python 1_codigo/herramientas_dev/probar_vista_creativo.py <salida>` con los ejemplos reales del slider (`~/DaVinciSubtitles/ejemplo_<tema>.marcas.json` + los cues que GO mandó a Resolve + `banco/slider_<tema>.mov` o `vistas_slider/<tema>_captions.mp4`). A: el planificador de hoy = los cues que recibió Resolve (6/6 idénticos). B: hoja Resolve | Creativo | contorno (para mirar; no hace fallar: esos renders llevan la Edición PRO). C: marcar Principal (quitando las Principal vecinas, como en Creativo) hace de esa palabra la grande del bloque (22/22). Hallazgos: Kinetic y VIRAL casan casi exactos con Resolve (posición, tamaño, colores, cintas, anillos); los temas «guion» casan en tipografía y tamaño. **Límites:** con la Edición PRO (siempre en Temas 5/6) Resolve sube o baja los captions que taparían una cara de TU video (`edicion_pro._captions_sin_cara`) y a veces pone motions encima: la vista usa la foto de muestra, así que eso no se ve; las animaciones propias de los macros de Fusion tampoco. Arreglado gracias al banco: `kinetic_planificador.planificar` tomaba los índices de `mains` como índices de la lista limpia (`pal`) y la Principal marcada podía caer en la palabra de al lado (en la vista y en lo que Generar manda a Resolve); ahora usa `orig`, como VIRAL y los temas «guion».

**Medido (texto de 30 palabras, 7 bloques, pantalla 280×607):** planificar 0,01–0,03 s, rasterizar 0,04–0,16 s, cada cuadro 1–6 ms. Las animaciones propias de los macros de Fusion (rebotes, barridos) no se copian: cada elemento entra con el fundido corto de GO sin Resolve. **Prueba sin pantalla:** el arnés DEBE crear la app con `qt_kit.crear_app()` (sin el despachador, `correr_en_hilo` nunca devuelve el resultado).

## creativo-detecta-audio — Creativo detecta solo el audio / la línea de tiempo de Proyecto (v5.3.3)

Al abrir Creativo SIN sesión (`SubtitleApp._al_entrar_en_creativo` desde `ir_a('editor')`), la tarjeta vacía mira `_estado_creativo()` = (modo, audio, timeline, proyecto) sin tocar Resolve (usa `_estado_sistema['mcp']` en caché y `video_var` de Proyecto) y se adapta (`_refrescar_editor_vacio`, que se mantiene al día cada 1,5 s con `_vigilar_editor_vacio` y al cambiar `video_var` en `_al_cambiar_video`):
- `marcas`: el audio de Proyecto YA tiene `<video>.marcas.json` → botón «Retocar las palabras» (`_on_update`) y **el editor se abre solo** (`_abrir_editor_solo`, una vez por entrada).
- `audio`: hay audio sin palabras → «Transcribir y retocar» (`_on_generate`; el editor se abre al terminar la transcripción).
- `timeline`: no hay audio pero Resolve tiene una línea de tiempo abierta → «Traer el audio de Resolve» (`_detectar_desde_resolve`; al llegar el audio pasa a `audio`).
- `ocupado`: GO / transcripción en curso → texto de espera, sin botón. `nada`: indicaciones (Obtener / soltar un video / GO).
