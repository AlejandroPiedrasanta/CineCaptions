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

## qt-kit — Widgets base, hilos y Pila

**Qué:** Widgets base, hilos (`correr_en_hilo`, `despues`), `Pila`

**Dónde:** `qt_kit.py`

## ajustes-tema — Ajustes y tema

**Qué:** Ajustes / tema

**Dónde:** `ajustes_ui.py`, `tema.py`

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
- Cálculos sobre todo el texto del editor: agruparlos (`_actualizar_contador_pronto`), no por clic.
- En Inicio la escena 3D tapa el fondo: `FondoVivo.poner_cubierto(True)`; la escena cachea su último fotograma.
- `plantillas.pack_incorporado()/packs_incorporados()` están memoizados; `fuentes_sistema` cachea en `~/DaVinciSubtitles/cache_fuentes.json`.
- Estilo «guion»: la palabra grande tiene que CABER en su estilo SIN zoom (`guion_planificador._cabe`): si el texto es más ancho que el comp de Resolve se recorta ANTES de ampliarlo. Las palabras grandes van en pistas INFERIORES: «Luxe Shine» es de cristal y refracta lo que tiene debajo.
- Banco de pruebas: sus datos se llaman `datos_<x>.<idioma>.guion.json` porque el render borra todo lo que empiece por su propio nombre. Resolve sale limpio con `limpiar_banco`.

## rendimiento-base — Caché de voz, GPU (CUDA), descargas, cola de fondo y Resolve colgado

**Qué (v5.4.8):** (1) `cache_voz.py`: la transcripción de un video ya hecha (huella = tamaño + fecha + 2 MB del inicio y del final + idioma + motor + modelo) se reutiliza: GO, «Generar» y los reintentos no la repiten (90 días / 200 MB). (2) `cuda_libs.py`: registra las DLL de CUDA del motor Qwen (`torch\lib`) para que Whisper use la tarjeta NVIDIA (antes caía a CPU: 6,7 s vs 17,5 s); `tipo_de_calculo()` elige float16 (≥ 6 GB) / int8_float16 (3-6 GB) / CPU; Ajustes › General › «Reparar GPU» las baja de PyPI (≈ 1,3 GB) si faltan; `salud.py` tiene la fila «GPU para la voz». (3) `descargas.py`: descargas con Range + reintentos (2/4/8/16 s) + SHA-256 (las usa `motor_voz._bajar`). (4) `cola_trabajos.py`: lo de fondo (máx. 2 a la vez) cede ante GO (`lanzar_bajo`, `registrar_alta`); `qt_kit.correr_en_hilo(..., baja=True)`. (5) `mantenimiento.py`: topes por caché (efectos, emojis, vistas, voz) a los 45 s de abrir + «Espacio de las cachés / Limpiar ahora» en Ajustes. (6) `resolve_bridge.resolve_colgado()` (IsHungAppWindow + vigía de 3 s): con Resolve colgado no se llama a fusionscript y `resolve_mcp.script()` avisa al instante; reintentos con espera creciente (10→20→40→60 s) y reciclaje del cliente tras 2 «no contestó». (7) `fuentes_sistema.indice_listo()`: la interfaz no espera al índice de fuentes.

**Medido:** NVDEC/D3D11 es MÁS LENTO que el decodificador por software con 4 hilos (4K: 98 vs 79 fps; 720p: 350 vs 200): se queda en software.

**Probar:** `cuda_libs.diagnostico()`; `cache_voz.CARPETA`; la reanudación de `descargas` se probó con un servidor local con Range que corta la conexión a mitad (reanuda, descarta un hash malo y reconoce lo ya completo).


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
