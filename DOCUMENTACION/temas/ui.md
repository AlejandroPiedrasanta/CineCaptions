# Interfaz Qt: ventana, diseño, rendimiento, ajustes

## ventana-paginas — Ventana principal, páginas y cambio de pestaña

**Qué:** Ventana principal, páginas, `ir_a()` (cambio de pestaña)

**Dónde:** script principal · `class SubtitleApp`, `ir_a`, `_build_ui`, `_nueva_pagina`

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

## recorrido — Recorrido visual por pasos

**Qué:** Recorrido visual por pasos (13 pasos por toda la interfaz; se desactiva y se repite desde Ajustes)

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
