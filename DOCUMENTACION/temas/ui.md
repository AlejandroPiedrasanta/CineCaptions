# Interfaz Qt: ventana, diseño, rendimiento, ajustes

## ventana-paginas — Ventana principal, páginas y cambio de pestaña

**Qué:** Ventana principal, páginas, `ir_a()` (cambio de pestaña)

**Dónde:** script principal · `class SubtitleApp`, `ir_a`, `_build_ui`, `_nueva_pagina`

**Registro flotante (5.5.11):** el botón del Registro (`registro_flotante`, un `registro_ui.BotonRegistro`) va a la izquierda de los controles de la ventana en TODAS las páginas, Inicio incluida (`_reposicionar_isla` lo coloca, `ir_a` lo sube). Inicio ya no lleva su propio botón en la fila de `aviso_inicio`.

## fondo-animado — Fondo animado y entrada de tarjetas

**Qué:** Fondo animado, entrada de tarjetas

**Dónde:** `efectos_ui.py` (`FondoVivo`), `mograf_ui.py` (`entrada_escalonada`, `_EfectoEntrada`)

## liquid-glass — Liquid Glass de tarjetas

**Qué:** Liquid Glass de tarjetas (muestra de aurora bajo la tarjeta, refresco 2 Hz)

**Dónde:** `qt_kit.py` · `Tarjeta.paintEvent`; `efectos_ui.py` · `FondoVivo.muestra_aurora`, `_refrescar_tarjetas`

## ritmo-fps — Regulador de fps

**Qué:** Regulador de fps

**Dónde:** `ritmo_ui.py`

**v5.22 (el usuario: «al volver a Inicio las animaciones van trabadas, como que se reinician»):** (1) `EscenaGo._reanudar` (al volver a verse, al volver la ventana y al salir de minimizada): el primer 1,2 s no cuenta para la política «equipo lento» (antes los tirones de la transición la dejaban a 30 fps 8 s, 16 s… hasta 2 min, y cada vuelta más); `changeEvent(ActivationChange)` cambia 60↔30 fps al momento. (2) `TituloGo` solo entra letra a letra la PRIMERA vez (y al cambiar de texto). (3) `ir_a('inicio')` ya no repite `entrada_escalonada` (efectos Qt sobre la escena 3D). (4) `_refrescar_recientes` lee los proyectos (y si existe cada video) en un hilo y solo rehace las filas si cambió algo (`_pintar_recientes`, firma); `_pintar_go_reposo_sin_esperas` mira el video en un hilo antes de pintar: con los videos en un disco dormido, `Path.exists()` congelaba Inicio al volver. Probado sin pantalla: título sin repetir, 60 fps tras volver, lento_n 0, `ir_a` 10–35 ms.

**Reloj atado al monitor (v5.49, `ritmo_ui.RelojPantalla`):** un `QTimer` de 16 ms da 62,5 cuadros/s y el monitor refresca a 59,94-60 Hz: cada ~0,4 s dos cuadros caen en el mismo refresco y uno no se ve (un salto en todo lo que gira). `RelojPantalla` se usa como un QTimer (`timeout`, `start`, `setInterval`, `isActive`); a ≤ 40 ms, en Windows, un hilo `reloj-vblank` espera el vblank del monitor de la ventana (`D3DKMTWaitForVerticalBlankEvent`, el que usa Chromium; el monitor sale del HWND con `MonitorFromWindow`, porque en Qt 6 `QScreen.name()` es el nombre comercial, «GS34WQC», no «\\.\DISPLAY1») y avisa a la interfaz: 60 Hz → cada vblank, 30 fps → uno de cada dos, 120/144 Hz → cada 2. Nunca se amontonan (si la interfaz no atendió el anterior, se salta). Si no hay vblank (Mac, escritorio remoto, pantalla apagada: la guardia ve > 1,5 s sin latir) pasa a un QTimer normal y reintenta a los 20 s. Medido: intervalo 16,67 ms (antes 16,0); lo usa `EscenaGo` (y con ella el orbe).

**«Equipo lento» sin falsos avisos (v5.49):** `_politica` ya no mira la media móvil del intervalo (un solo tirón de 80 ms al abrir la pasaba de 20,5 ms → 30 fps 8 s, 16 s…): cuenta los cuadros tarde desde la última vez (`_n_tics`, `_n_lentos`) y solo baja a 30 si más de 1 de cada 4 llegó tarde (vuelve a probar 60 con < 8 %). Al mostrarse la PRIMERA vez la gracia es de 4 s (el arranque carga fuentes, packs, el MCP…); las demás, 1,2 s.

## qt-kit — Widgets base, hilos y Pila

**Qué:** Widgets base, hilos (`correr_en_hilo`, `despues`), `Pila`

**Dónde:** `qt_kit.py`

## ajustes-tema — Ajustes y tema

**Qué:** Ajustes / tema

**Dónde:** `ajustes_ui.py`, `tema.py`

**v5.22 (pedidos del usuario):** el color de resaltado de fábrica es el **verde** (`tema.ACENTO_POR_DEFECTO`, primero en `tema.ACENTOS`). En Ajustes › Interfaz ya no son 7 tarjetas + «Elegir color…»: es UNA fila de muestras redondas a la derecha (`_MuestrasAcento`): el elegido con su aro y una marca, el ratón las hincha con resorte y debajo de cada una sale su nombre (sin tooltips); la última, «Mi color» (aro de arcoíris), abre el selector. En General se quitaron «Mantener CineCaptions encima» (queda el alfiler del menú lateral) y «Copias de seguridad» (`copias.py` sin uso).

**Negro + blanco de fábrica (v5.63; el usuario eligió la C entre tres maquetas de toda la app en negro, y pidió quitar los verdes sueltos y dejar el azul como opción):**
- **De fábrica:** `tema.TEMA_POR_DEFECTO = 'negro'` y `ACENTO_POR_DEFECTO = 'blanco'` (`#E6E8EB`, nuevo en `ACENTOS`). Las prefs sin la marca `tema_563` se leen así aunque guardaran otro tema; `Ajustes.aplicar` guarda `tema_563: True` y desde ahí manda lo elegido.
- **Fondo de la interfaz:** nueva fila en Ajustes › Interfaz, Negro / Azul (`_elegir_fondo`). Cambia el tema y, si el acento era el de la pareja contraria, el acento: blanco ↔ verde.
- **Azul de fábrica (v5.64, el usuario: «deja por default el azul de fondo de la interfaz» y, con una captura del verde elegido, «por default así»):** `TEMA_POR_DEFECTO = 'noche'` y `ACENTO_POR_DEFECTO = 'verde'`. La marca `tema_563` sigue igual: quien guardó un tema en Ajustes lo conserva y el resto pasa al azul. En la fila, Azul va primero. El negro + blanco de abajo queda como la opción «Negro».
- **Escenas de Inicio:** `_elegir_estilo` ya no pone el tema ni el acento de la escena (antes los dejaba en «noche» + verde) y la tarjeta ya no pinta el punto de su color.
- **Texto sobre el acento:** `tema.es_claro` / `texto_sobre` y `qt_kit.texto_acento()`. La hoja de estilo usa la ficha `TEXTO_ACENTO` en el botón primario, el menú elegido y la píldora marcada, la selección de texto y el centro del radio; también la palomita de la casilla, `HighlightedText`, la bolita del `Interruptor` encendido, la pastilla de `Segmentado`, el número de `Pasos`, el icono del menú lateral activo y la píldora de la isla (icono y texto).
- **Verdes:** con un acento claro, el traductor lleva al acento los verdes de interfaz (`tema.VERDES_UI`: `#24D18F` = `qt_kit.VERDE`, `#3FDC95`, `#22B573`, `#7FE0B5`, `#2BD4A4`), aunque `#24D18F` esté en `EXCLUIDOS`. `VERDE` se traduce también como constante en `_aplicar_tema_guardado`, así que el slider, Efectos, la barra PRO y el Registro pasan a blanco. Los roles del editor y el ámbar/rojo de aviso no cambian; con el azul (verde de acento) todo queda como antes.
- **Módulos con el `QColor` de Qt** (el traductor no los toca): `sonido_skill_ui` pasa al `QColor` del tema (sus azules eran tarjetas y tiras de Sonido); el fondo de su línea de tiempo pasa por `ui.traducir_hoja`. En `efectos_pro_ui` solo los chips «Personaliza» usan `ui.tc` (el color elegido por el usuario se pinta tal cual) y en `pro_lateral_ui` los verdes usan `ui.VERDE` / `ui.tc`.
- **Cielos:** `estilos_inicio._negro()` / `_cielo_negro` ponen en negro neutro los degradados de las 3 escenas (Astrolabio: también velos y vía láctea; Nebulosa conserva sus nubes de color; Proceso: la rejilla en gris). `proyecto_ui._PALETAS_CIELO` / `_paleta_cielo` lo hacen con el cielo de Proyecto. Las piezas de cristal (`ChipGo`, `BarraTema`, el velo de Inicio) usan colores de la casa con el `QColor` del tema.
- **Probado sin pantalla** con capturas de Inicio, Proyecto, Creativo, Sonido, Efectos, Ajustes y los controles, en Negro y en Azul. Queda verde a propósito la gema del astrolabio (dibujo del orbe).

## isla-nav — Isla de navegación y controles de ventana

**Qué:** Isla de navegación, controles de ventana, borde (ventana SIN barra del sistema)

**Dónde:** `isla_ui.py` · `IslaNav`, `ControlesVentana`, `BordesVentana`, `MarcaCinema` (logo blanco «CINEMA PRODUCTIONS» arriba a la izquierda, solo en Inicio, se oculta si no cabe junto a la isla; `2_recursos/logo_cinema_productions.png`, también en el instalador —recurso `marca.png`— y en Ajustes > Acerca de); en el script principal `_build_isla`, `_accion_isla`, `_alternar_pop_estado`. El lateral viejo se construye OCULTO (`_build_lateral`) porque sus piezas siguen en uso

## aurora — Diseño «Aurora» (vidrio, neón, resortes)

**Qué:** Diseño «Aurora» (vidrio, neón, resortes)

**Dónde:** `qt_kit.py` · `Resorte`, `motor_resortes`, `Tarjeta.paintEvent`, `Boton.paintEvent` (escala 0,97), `Segmentado`/`Interruptor` con resorte, `BarraProgreso` neón; fondo por página `efectos_ui.py` · `PALETAS_PAGINA`, `poner_pagina`; entrada `mograf_ui.entrada_escalonada`

## recorrido — Recorrido visual por pasos (RETIRADO en v5.3.7)

**Qué:** RETIRADO a petición del usuario (v5.3.7): ya no sale al abrir (se quitó `despues(4500, self._recorrido_auto, …)` de `__init__`) y no hay interruptor ni «Ver el recorrido ahora» en Ajustes. El código (`recorrido_ui.py`, `_pasos_recorrido`, `iniciar_recorrido`) sigue ahí sin conectar por si se reactiva. Tampoco existe ya el interruptor «Recibir versiones beta»: `canal_beta` se ignora (siempre canal estable).

Antes: Recorrido visual por pasos (13 pasos por toda la interfaz; se desactiva y se repite desde Ajustes)

**Dónde:** `recorrido_ui.py` · `Paso`, `Recorrido` (capa con foco que sigue a la zona, tarjeta, teclado ←/→/Esc); pasos y arranque en el script principal · `_pasos_recorrido`, `iniciar_recorrido`, `_recorrido_auto`, `_recorrido_fin`, `_recorrido_no_mostrar`; prefs `recorrido_activo` (interruptor) y `recorrido_visto`; interruptor en `ajustes_ui.py` · `PanelRapido` y pestaña Interfaz (`_guardar_recorrido`). Mientras dura NO se renderizan solas las vistas reales

## nota — LIQUID GLASS

LIQUID GLASS: Tarjeta dibuja la aurora (imagen 1/8 de FondoVivo) bajo un tinte oscuro translucido (alfa ~196) + reflejo especular; FondoVivo repinta las Tarjeta visibles cada 0,5 s.

## nota — ESTETICA v5.7

ESTETICA v5.7 (criterio): fondo casi neutro con 3 luces muy tenues y desaturadas (efectos_ui._apagar), tarjetas de cristal casi opacas (alfa 228) que pasan por el traductor del tema (Noche/Negro/Grafito), neon de reposo minimo, insignia de pagina con el acento (no naranja). No volver a banos de color saturados. El selector de estilos de Ajustes es un carrusel horizontal (_CarruselEstilos: flechas, arrastre, puntos).

## nota — v5.8 segunda pasada de la auditoría

Recorrido visual (recorrido_ui.py): 14 pasos con foco animado (el hueco sigue a la zona cada 33 ms: listas que se desplazan, animaciones de pantalla y cambios de tamaño), tarjeta que se coloca sola donde cabe, ←/→/Intro/Esc. Arranca solo la primera vez (pref recorrido_visto) salvo que recorrido_activo sea False; «No volver a mostrar» y el interruptor de Ajustes lo apagan; «Ver el recorrido ahora» lo lanza siempre.

## reglas-rendimiento — Reglas de rendimiento de la interfaz (no romper)

**Reglas (no romper):**
- NO usar `QEasingCurve.setCustomType` con una función de Python: tumba el proceso (access violation). Usar curvas de Qt (`OutBack`) o un `Resorte` + `motor_resortes`.
- Las tarjetas son «Liquid Glass» FALSO a propósito: no son transparentes de verdad (el fondo no se repinta debajo); pintan una muestra cacheada de la aurora (`FondoVivo.muestra_aurora`) y el fondo las refresca a 2 Hz. No usar `setWindowOpacity`/efectos de Qt para el vidrio.
- Nada de red, `subprocess`, lectura de muchos archivos o `time.sleep` en el hilo UI: usar `correr_en_hilo(widget, trabajo, al_terminar)`.
- No poner `QGraphicsOpacityEffect`/efectos sobre páginas enteras ni widgets hijos que se repinten cada fotograma dentro de un efecto (invalida su caché). Pintar dentro del efecto.
- NUNCA llames a `resolve_mcp`/`resolve_bridge` (`modo_actual()` sin `pasivo`, `disponible()`, `estado()`) en el hilo de la interfaz: esperan a Resolve hasta ~3 s (el registro lo mostró 7 veces). Usa `correr_en_hilo`.
- v5.47 (el usuario: «va lento y trabado cuando doy clic y a veces se congela»): `resolve_mcp.estado()` llamado desde la ventana ya NO espera nunca: devuelve el último estado conocido (o `{'comprobando': True}`) y lanza la pregunta en un hilo (`_refrescar_en_hilo`). El registro lo mostraba en cada ir_a → `_pintar_go_reposo` → `colocacion.detectar_resolve` (2,5–3 s). Y `_prearmar_paginas` arma Efectos y Estilos en reposo tras abrir (en Inicio y sin GO, una cada 2 s): primer clic en Efectos 766 → 102 ms, Estilos 369 → 74 ms (medido sin pantalla con la ventana real).
- v5.47, probado con Resolve abierto (contesta en 0,26 s sin trabar): la vuelta a Inicio desde Efectos tardaba 120 ms → 50. Tres causas: (1) `vistas_slider.Reproductor` usa un decodificador de UN hilo, abre el mp4 una vez y rebobina con `seek(0)` (con `thread_type='AUTO'` y reabriendo en cada vuelta, Python quedaba parado 50-90 ms; peor tirón en Efectos 89 → 33 ms); (2) `ajustes_ui.leer_prefs` cachea por tamaño + fecha (`os.stat`; abrir el archivo con el antivirus llegaba a 90 ms y se hacía en cada cambio de página); (3) `correr_en_hilo` reutiliza hilos libres (`_lanzar_en_hilo`; `Thread.start()` esperaba con el equipo ocupado). Media de clics 42 → 32 ms.
- Cálculos sobre todo el texto del editor: agruparlos (`_actualizar_contador_pronto`), no por clic.
- En Inicio la escena 3D tapa el fondo: `FondoVivo.poner_cubierto(True)`; la escena cachea su último fotograma.
- `plantillas.pack_incorporado()/packs_incorporados()` están memoizados; `fuentes_sistema` cachea en `~/DaVinciSubtitles/cache_fuentes.json`. Desde v5.39 `packs_drt.leer_drb` también guarda en disco (`~/DaVinciSubtitles/cache_drb.pickle`, con la versión del programa en la clave), `EstimadorGo` calcula el perfil del equipo (nvidia-smi + motor auxiliar) en un hilo y `_refrescar_destinos` pregunta los idiomas instalados en su hilo: la ventana abre en ~0,8 s (antes 1,3 s, medido sin pantalla).
- Páginas: Estilos, Sonido, Editor y Efectos ya se construyen al abrirlas (1–3 ms al arrancar); solo «nuevo» se construye entera porque de ella salen las variables que lee `_cargar_preferencias`. Iconos: `qt_kit.icono_linea` hace que qtawesome cargue solo Phosphor («ph.»; otra familia carga todas).
- Animaciones con reloj propio: pararlo en `hideEvent` (una página oculta no recibe `leaveEvent`) y reanudar en `showEvent` (así `BarraProgreso` y `ajustes_ui._TarjetaEstilo`).
- v5.49: a 60 fps usar `ritmo_ui.RelojPantalla` (late con el monitor), no un `QTimer` de 16 ms (62,5 Hz contra 60 Hz: un cuadro perdido cada ~0,4 s). Y lo que no cambia de un cuadro a otro (halos, degradados, elipses fijas, capas sin girar) se pinta UNA vez a los píxeles reales y se copia: copiar un sprite sin escalar y CON `SmoothPixmapTransform` cuesta ~0,08 ms (sin el hint, ~0,27: Qt toma el camino transformado); un degradado radial de 200 px, ~0,5 ms; una elipse girada con pluma de 1 px, ~0,8 ms. `_prearmar_paginas` (v5.47) espera a que la ventana no tenga el foco: armar Efectos congela ~0,36 s y con la animación de Inicio a la vista era un tirón.
- v5.49 (el usuario: «que no haya tirones jamás»): un hilo de FONDO también traba la interfaz si hace llamadas largas en C que no sueltan el GIL o mucho Python seguido: `json.loads` de un archivo grande (usar `archivos_seguros.leer_json_cediendo`, que decodifica por partes y cede cada 2 ms), importar módulos con DLL (PyAV: `sfx_studio` se importa con la ventana sin foco), `gc.collect()` (nunca con la ventana a la vista: `congelar_gc` solo congela), recorrer miles de archivos con `pathlib` (usar `os.scandir` + pausa de 1 ms cada 200, como `mantenimiento._medir_entrada`). El mismo JSON leído muchas veces: caché por `os.stat` (fecha + tamaño), como `sfx_rules._leer_json`. Y en los `al_terminar` de `correr_en_hilo` solo tocar widgets: lo que se calcula o se escribe a disco (Registro incluido) va en el hilo; si hay que crear muchas filas, una por vuelta del bucle (`_pintar_recientes`). Cazarlos: tema `pruebas-sin-pantalla` (vigía con `faulthandler`).
- Estilo «guion»: la palabra grande tiene que CABER en su estilo SIN zoom (`guion_planificador._cabe`): si el texto es más ancho que el comp de Resolve se recorta ANTES de ampliarlo. Las palabras grandes van en pistas INFERIORES: «Luxe Shine» es de cristal y refracta lo que tiene debajo.
- Banco de pruebas: sus datos se llaman `datos_<x>.<idioma>.guion.json` porque el render borra todo lo que empiece por su propio nombre. Resolve sale limpio con `limpiar_banco`.

## rendimiento-base — Caché de voz, GPU (CUDA), descargas, cola de fondo y Resolve colgado

**Qué (v5.4.8):** (1) `cache_voz.py`: la transcripción de un video ya hecha (huella = tamaño + fecha + 2 MB del inicio y del final + idioma + motor + modelo) se reutiliza: GO, «Generar» y los reintentos no la repiten (90 días / 200 MB). (2) `cuda_libs.py`: registra las DLL de CUDA del motor Qwen (`torch\lib`) para que Whisper use la tarjeta NVIDIA (antes caía a CPU: 6,7 s vs 17,5 s); `tipo_de_calculo()` elige float16 (≥ 6 GB) / int8_float16 (3-6 GB) / CPU; Ajustes › General › «Reparar GPU» las baja de PyPI (≈ 1,3 GB) si faltan; `salud.py` tiene la fila «GPU para la voz». (3) `descargas.py`: descargas con Range + reintentos (2/4/8/16 s) + SHA-256 (las usa `motor_voz._bajar`). (4) `cola_trabajos.py`: lo de fondo (máx. 2 a la vez) cede ante GO (`lanzar_bajo`, `registrar_alta`); `qt_kit.correr_en_hilo(..., baja=True)`. (5) `mantenimiento.py`: topes por caché (efectos, emojis, vistas, voz) a los 45 s de abrir + «Espacio de las cachés / Limpiar ahora» en Ajustes. (6) `resolve_bridge.resolve_colgado()` (IsHungAppWindow + vigía de 3 s): con Resolve colgado no se llama a fusionscript y `resolve_mcp.script()` avisa al instante; reintentos con espera creciente (10→20→40→60 s) y reciclaje del cliente tras 2 «no contestó». (7) `fuentes_sistema.indice_listo()`: la interfaz no espera al índice de fuentes.

**Medido:** NVDEC/D3D11 es MÁS LENTO que el decodificador por software con 4 hilos (4K: 98 vs 79 fps; 720p: 350 vs 200): se queda en software.

**Probar:** `cuda_libs.diagnostico()`; `cache_voz.CARPETA`; la reanudación de `descargas` se probó con un servidor local con Range que corta la conexión a mitad (reanuda, descarta un hash malo y reconoce lo ya completo).

**v5.53 · Voz en caché = soltar el motor de voz:** al pulsar GO, `_precargar_motores` arranca siempre el servidor de voz; si luego `cache_voz.leer` acierta, `st.transcribe` no corre y su `liberar()` tampoco. El servidor seguía vivo 120 s y `vram_para_ia_gb` le sumaba 6 GB «liberables»: con 16 GB y Resolve cerrado salían 14,3 GB → Gemma, cuando el GO sin caché había usado la 1.7B (8,3 GB), y la caché de la IA (su clave lleva el modelo) fallaba: paso ia de 2-3 min en vez de ~10 s. Ahora la rama `if words:` del pipeline (hilo del GO) llama a `motor_voz.soltar()` si `modo_gpu() != 'residente'`: lo saca de `_SRV_VOZ` al momento y lo cierra en otro hilo (`cerrar()` espera hasta 6 s porque el servidor no lee stdin mientras carga). Arnés con servidor falso: `soltar()` vuelve en 1 ms, 14,3 → 8,3 GB, Gemma → 1.7B, el cierre termina en el hilo `voz-soltar`; AST: solo la rama de la caché lo llama. Queda una carrera rara (la precarga lanza la voz después del acierto): se vuelve a lo de antes, sin daño.


## nota — v5.4.21 · listas desplegables en píldoras

Todas las listas desplegables de la app (`qt_kit.Combo`, `ComboBuscable` y sus sugerencias, y `qt_kit.Menu` —chips de Inicio, clic derecho…) usan el estilo «píldoras» (pedido del usuario): cada opción es una cápsula con borde fino; la que toca el ratón o el teclado, con fondo y borde claros; la que está en uso, rellena del color de acento con un visto. `Combo`: `_DelegadoPildora` (pinta la píldora, el visto y los separadores; sabe cuál es la actual por `currentIndex`) + el panel redondeado y translúcido (`_panel_translucido` sobre la ventana de la lista: sin fondo ni sombra del sistema). `Menu`: propiedad `pildora=true` + reglas `QMenu[pildora="true"]` de la hoja de estilos (el radio de la píldora tiene que ser ≤ la mitad del alto del ítem o Qt lo ignora); una opción cuyo texto empieza por «✓» se marca como `checked` y sale rellena. Las sugerencias del idioma llevan el mismo delegado pero con panel opaco (un popup propio translúcido no pinta el fondo de su lista). Los `QMenu` que no son `Menu` (p. ej. el de copiar/pegar de un campo) conservan el estilo de antes. Sin Mac real para probar: ahí `QMenu` puede ser nativo y ignorar la hoja.

## nota — v5.4.22 · sin cuadros emergentes ni globos de ayuda; Proyecto más limpio

Pedido del usuario: **ningún cuadro emergente** (toasts) y **ningún mensaje al dejar el ratón quieto**. `ui_toast.MOSTRAR_CUADROS = False` (`mostrar()` solo anota el aviso en el Registro; los llamadores no cambian) y `qt_kit.Tooltip` no hace nada + `QWidget.setToolTip` está anulado en `qt_kit` (así valen también los `setToolTip` sueltos). El «?» de ayuda que el usuario PULSA (`QToolTip.showText` en la ventana de Proyecto) sigue. En Proyecto, con `plantillas.SOLO_TEMAS`, el panel de cada tema es solo el nombre y el botón «Usar este tema»/«En uso» (sin frase, descripción, leyenda, lápiz ni «⋯»; el aviso de tipografías que faltan sigue saliendo si hace falta) y el slider crece con la ventana (`estilos_slider._medidas`: tarjeta hasta 860 px de alto; `CarruselPacks(alto=480)`).

**v5.4.28 — panel «Acerca de» sin pisarse:** `ajustes_ui.PanelRapido` tenía todo en un `QVBoxLayout` de alto fijo: en una ventana baja o con escala 165 % el panel se colocaba más bajo que su contenido (`posicion()` recorta a lo que cabe) y el layout apretaba las filas (el texto de las notas tapaba el enlace; los enlaces de la licencia salían cortados). Ahora la cabecera es fija y el resto va en un `QScrollArea` con los márgenes de los lados DENTRO del contenido (si aparece la barra el contenido se estrecha, no se corta); `sizeHint()` devuelve el alto del contenido entero. Prueba sin pantalla: `QT_SCALE_FACTOR=1.65` + `qt_kit.crear_app()` (con `QApplication([])` suelto no hay la hoja de estilos ni las fuentes) y `p.resize(420, 430)`. «Buscar actualizaciones»: `actualizaciones.comprobar` reintenta una vez; `explicar_fallo(mensaje)` da la causa legible y el crudo va al Registro (`actualizaciones`).

## nota — v5.5.10 · salida limpia

Al volver de `app.exec()` (final de `main`) quedan hilos de fondo vivos (vista de Creativo, emojis animados, vigía de Resolve) que usan numpy/Qt sin el GIL; mientras Python se desmontaba podían tocar memoria liberada («access violation» al cerrar). Ahora `main` cierra el MCP, corre los `atexit` (la marca de sesión «cerrada bien» de `registro`), vacía los registros y sale con `os._exit(0)`. Comprobado que al cerrar solo quedan hilos *daemon* (`vigia-resolve-colgado`, `emojis-secuencias`): ninguno retenía el proceso.

## ui-menores — Brillo de botones, ventana Registro, avisos, idiomas

- `brillo_ui.py`: barridos de luz y ondas al pulsar (todos los botones). `registro_ui.py`: aviso en la barra de título, botón del Registro con contador y la ventana Registro.
- `ui_toast.py`: avisos que se cierran solos; desde 5.4.22 NO se muestran cuadros ni globos (los avisos van al Registro).
- `i18n.py`: `tr("texto en español")` + catálogos en `2_recursos/locales`; `ensure_lang_pack.py` instala sin internet los paquetes de traducción (Argos) que falten.
