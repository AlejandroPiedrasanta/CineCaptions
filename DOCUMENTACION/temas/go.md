# GO e Inicio (botón, escena, arrastrar un video)

## go-inicio — GO / Inicio (botón, escena 3D, HUD)

**Qué:** GO / Inicio

**Dónde:** `un_clic_ui.py`, escena 3D `escena_go.py`, HUD `mograf_ui.py`

## estilos-inicio — 10 estilos de Inicio (héroe, fondo, partículas, tema)

**Qué:** 10 estilos de Inicio (héroe + fondo + partículas + tema/acento/aurora de toda la UI; tarjetas en Ajustes > Interfaz)

**Dónde:** `estilos_inicio.py` · `ESTILOS`, `Estilo.heroe/fondo/frente`, `miniatura`; escena `EscenaGo.poner_estilo`; botón `BotonGo._poner_estilo`; Ajustes `_TarjetaEstilo`, `_elegir_estilo`; pref `go_estilo`

## orbe-go — Orbe GO (astrolabio mecánico)

**Qué:** Orbe GO (astrolabio mecánico: capas vectoriales cacheadas 1,5x, giran por rotación)

**Dónde:** `orbe_mecanica.py` · `OrbeMecanica.dibujar/avanzar`; lo usa `BotonGo.paintEvent`

## arrastrar-video — Arrastrar un video a Inicio = GO con timeline nuevo

**Qué:** Arrastrar un video a Inicio = GO solo, con timeline nuevo; pack por defecto de GO

**Dónde:** script principal · `_soltar_archivo` (en Inicio arranca `_go`; `EXTENSIONES_MEDIO`), `_go` (rama de archivo: `resolve_mcp.medir_medio` decide formato/pack y `_go_timeline_del_video` arma el timeline; `_go_tl_listo` hace esperar a `_run_pipeline` antes de «done»), `_esperar_vistas_reales` (GO no toca Resolve con una vista real en curso: su timeline temporal «RCS · temporal… vista» quedaba como el actual y GO exportaba un audio vacío → «Whisper no devolvió palabras»); `resolve_mcp.py` · `crear_timeline_con_video` (bin «CineCaptions · videos», timeline «CineCaptions · <nombre>», Scaling=Fit, 1080×1920 / 1920×1080 / 1080×1080 según el video); `_plantilla_un_clic` (pref `go_pack`: pack, `auto` = 3 líneas, vacío = el pack que uses y si no **Referencia**; los packs sin el formato del video no valen) y chip «Estilo» de Inicio (`_menu_estilo_go`). Ayuda «Crea tu estilo»: sección «palabra a palabra» (`crea_estilo_ui._dibujo_guion`: arriba = fina, abajo = NEGRITA, principal = grande). Cada video soltado crea un proyecto de Resolve **NUEVO** («CineCaptions», luego «CineCaptions 2»…): `resolve_mcp.preparar_proyecto` abre Resolve con `arrancar_resolve` (reintenta hasta 4 min: `launch_resolve` corta a los 60 s), guarda y CIERRA el proyecto abierto y crea el nuevo; recién abierto Resolve `CreateProject` devuelve None unos segundos (`no_creo`), así que se reintenta cada 5 s hasta 150 s. Chip «Proyecto» de Inicio / pref `go_proyecto='actual'` = usar el abierto (aunque esté vacío). **Si no se pudo armar el proyecto/timeline GO SE DETIENE** (`_go_tl_error` → `_abortar_si_fallo_el_timeline`, justo tras transcribir y antes de terminar) y NUNCA coloca captions en otro timeline (así se perdía el sonido del video y se ensuciaba el proyecto del usuario). `resolve_mcp.entorno_para_resolve`: ResolveMCP/Resolve se lanzan SIN variables de Qt/Python/PyInstaller del proceso (`QT_QPA_PLATFORM=offscreen` de las pruebas rompía el arranque de Resolve: «no Qt platform plugin could be initialized»). `conectado_recientemente` evita el falso «Falta un clic en Resolve» cuando la caché de estado (30 s) caduca tras un GO largo. MCP: `arrastrar_video` (todo el arrastre real + render + limpieza: borra su timeline y bin, vuelve a tu proyecto y timeline y borra «CineCaptions» solo si lo creó la prueba). Sonidos y emojis del estilo «guion» (v5.10): `_generar_con_guion` usa `_preparar_sfx` / `_preparar_emojis` / `_sfx_de_emojis` sobre los mismos bloques (cada palabra = una «línea» con su momento → el sonido cae cuando entra la palabra), `_emojis_con_la_palabra_grande` (el emoji entra con la palabra grande y dura lo que la pila), y copia `sfx*`/`emoji*`/`lines` a cada cue del .json; el cue lleva `caja` (alto de la pila, del planificador) para que `colocar_emojis` lo ponga encima/debajo (pref `emoji_posicion`); `place_guion_track` (py) = `place_guion` (lua) arman `planes_emoji` y llaman a `colocar_emojis` (y la lua ahora también a `place_sfx`). `_go_generar` respeta el chip «Efectos: no» (antes pasaba `con_sfx=True` fijo)

## nota — ORBE GO

ORBE GO (orbe_mecanica.py): 6 capas vectoriales (runas, engranaje, filigrana, domo, vidrio, botones) se dibujan una vez a 1,5x los pixeles reales y cada cuadro solo se giran; gema, rayos y progreso se dibujan en vivo. EscenaGo ya no dibuja la esfera de particulas: solo fondo verde-azulado y haces de luz.

## nota — INICIO A 60 FPS

INICIO A 60 FPS: temporizadores PreciseTimer de 16 ms (el normal de Windows salta a ~15,6/31 ms); el boton GO sigue el reloj de EscenaGo (un repintado por cuadro); fondo de la escena a 1/3 de resolucion (_fondo_bajo, haces = un QConicalGradient); objetos = sprites cacheados girados en 3D con QTransform (_sprite, precalentados); TituloGo cacheado a pixmap (los hijos sobre la escena se repintan cada cuadro: mantenerlos baratos). Clic en GO: 3 ondas + chispas + destello del orbe y la absorcion empieza 0,55 s despues; al terminar bien sale el final festivo (notas, ondas, emojis).

## nota — ABSORCION = PARTICULAS

ABSORCION = PARTICULAS (numpy, ~170 vivas, lineas+puntos agrupados por color: pocas llamadas Qt). CONGELACIONES: cada llamada a Qt suelta y retoma el GIL, asi que un hilo de Python puro dejaba la interfaz a ~1 fps con el intervalo de 5 ms: qt_kit.ajustar_planificacion() pone setswitchinterval(0.0001) y sube la prioridad del hilo de la UI; los hilos de trabajo (correr_en_hilo, _run_pipeline) bajan un escalon. Mantener BAJO el numero de llamadas Qt por cuadro (agrupar con drawLines/drawPoints). Registro: un oyente de la senal 'nueva' que falla se anotaba a si mismo en bucle (registro._emitiendo lo corta; los oyentes de ventanas deben ser metodos, no lambdas).

## nota — FINAL DE GO

FINAL DE GO (un_clic_ui.PanelGo.terminar): 3 tiempos = carga/temblor (0,7 s) -> destello+onda -> el engranaje se frena y la palomita se dibuja; contadores (ResumenGo) y botones (SalidaGo: Ver en Resolve / Editar palabras / Ver el Registro / Intentar de nuevo) entran 1,3 s despues; con avisos del Registro durante la tarea el tono pasa a ambar; con error el orbe se apaga y la linea propone el primer paso de registro_ayuda. A los 14 s vuelve solo al reposo (palomita residual que se desvanece). Cada fase (poner_fase) enciende una pieza del astrolabio (orbe_mecanica.FASES_ORBE) y cambia la corriente de particulas (EscenaGo.PERFIL). Pref go_animaciones = completo | suave | minimo (Ajustes > Interfaz, en vivo); ventana inactiva = 30 fps. PanelGo.reposo() ignora el refresco periodico de la app tras un final (14 s ok / 45 s error) salvo forzar=True.

## nota — UX DE GO v2

UX DE GO v2: el orbe NO se mueve con el raton (sin iman, sin escala, sin paralaje): el cursor es un foco de luz que se refleja en el bronce/runas/cristal (orbe_mecanica._luz_cursor) y enciende el borde; en la escena ilumina el fondo y aparta las particulas cercanas; en reposo hay motas de luz lentas. El final ya no suelta objetos 3D: ondas + rafaga de chispas + brasas que suben (EscenaGo._lanzar_burst). Se quito la cinta de demo «Sin EDITAR nada» (CintaViral ya no se usa en PanelGo).

## nota — ESTILOS DE INICIO

ESTILOS DE INICIO (estilos_inicio.py): 10 rediseños completos; cada uno = heroe() + fondo() a 1/3 de resolución + frente() + modo de partículas (espiral/ascenso/caida/orbita) + tema/acento/aurora. Elegir uno en Ajustes > Interfaz cambia Inicio en vivo (la escena relee la pref cada 2 s) y el tema+acento al reiniciar; la aurora de las páginas usa efectos_ui._paleta_de (solo si hay estilo elegido). La escena baja su resolución interna sola si no llega a 60 fps (_esc_cuadro) y el GC se congela tras arrancar (qt_kit.congelar_gc). Ya no hay luz que siga al ratón (ni foco en tarjetas, ni en el fondo, ni en el orbe). El instalador espera el botón INSTALAR y muestra todas las rutas (/empezar arranca solo; /silencioso sin ventana).

## nota — v5.8 · Prueba E2E y chips de Inicio

v5.8 · Prueba E2E y chips de Inicio: _pintar_opciones_go añade chips ámbar «Posición ajustada ✕» (composición no por defecto, resumen_composicion) y «Solo el estilo N ✕» (estilo_fijo con >1 variante); un clic llama a _quitar_ajuste_fino / _quitar_estilo_fijo (sincronizan ComposicionWindow). Los scripts de Resolve reconocen como «nuestras» las secuencias animadas de emoji (nombre e_[0001-NNNN].png en .../emojis_secuencia/) para limpiar y reutilizar la pista EMOJI al volver a generar; y no cuentan «mismo set seguido» cuando el bloque trae cue.estilo (lo decidió la app).

## fuente-unica — Un solo dueño por ajuste (auditoría del flujo v5.3.2)

Contradicciones que había entre Inicio (GO), Estilos, Creativo y Sonido, y cómo quedaron (no reintroducirlas):
- **Pack**: el pack de Estilos y el chip «Estilo» de GO son UNA elección: `_plantilla_elegida` → `_sincronizar_go_pack` guarda `go_pack`; `_poner_go_pack` actualiza `plantilla_sel` y la pantalla de Estilos. El editor se abre con `_asegurar_pack_luxe()` ya aplicado (antes se cambiaba DESPUÉS de editar, y el editor enseñaba otro diseño que el que se generaba).
- **Roles guardados tras GO**: con un pack «guion» GO ignora los roles de la IA (`planear(..., automatico=True)`); lo que se guarda con `guardar_marcas` son los del planificador (`guion_editor.roles_automaticos`), para que «Editar marcas» enseñe lo mismo que se colocó. «Asistencia» en modo guion también usa el planificador.
- **Emojis**: el chip «Emojis: no» pasa `con_emojis=self._go_emojis()` a `ia_texto.marcar_todo`.
- **Efectos**: `go_sfx` manda; `_sincronizar_sfx()` copia a `sfx_var` (la casilla vieja que miran los puntos de sonido del editor) al cambiar el chip y al abrir el editor.
- **Chips ámbar** «Posición ajustada» / «Solo el estilo N»: no salen con packs «guion» (esos ajustes solo valen en el diseño de 3 líneas).
- `_vigilar_tarea`/`_fin_tarea`/`_esperando_al_usuario`: ver tema `vigilancia`.

## go-progreso — Porcentaje, tiempo restante y errores de GO

**Qué:** Mientras GO trabaja, Inicio enseña el porcentaje, **justo debajo cuánto falta** («~ 75 s», «~ 2 min 10 s», «unos segundos»; «tarda más de lo normal…» si un paso se pasa del doble de lo esperado) y debajo el paso en curso («Transcribiendo · 2/6»). Al fallar, la línea de Inicio dice **en qué paso falló** y la causa concreta con el primer remedio («Falló en «Transcribiendo»: El archivo no se puede leer como video o audio. Prueba esto: …»).

**Dónde:** `un_clic_ui.py` · `EstimadorGo` (duración esperada por paso = base + coste por minuto de video, escalada por lo que tardó en las últimas veces: pref `go_ritmo`; el reloj de `PanelGo._tic_eta` corre cada 0,5 s y manda `boton.poner_eta`), `PanelGo.paso/avance_dentro/estimar_duracion/terminar` (`paso_fallido` lo pone la app: `_go_fallo` / `_go_fin`); dibujo del ETA bajo el %: `orbe_mecanica.py` y `estilos_inicio.centro_estado`; la duración del audio llega por la cola (`'duracion'`, `_run_pipeline`). Causas concretas en `registro_ayuda.py` (`_REGLAS`, las específicas van primero: video renombrado/movido, sin voz, pack no cargó, proyecto no creado, Resolve cerrado, Resolve no respondió, sin timeline, archivo ilegible). Soltar un archivo que no existe / una carpeta / mientras GO trabaja ahora avisa en Inicio (`_soltar_archivo`). **El audio original del video (A1) no se quita nunca:** `_CREAR_TIMELINE` lo comprueba al armar el timeline y `resolve_mcp.asegurar_audio_original()` al terminar GO; si faltara lo repone y lo anota en el Registro. Idioma: con «auto» GO usa el idioma que se OYÓ (`subtitle_transcriber.idioma_detectado`), no español por defecto. IA de texto: sin señal 100 s = se pasa al modelo ligero (aviso en pantalla a los 35 s) y se recuerda para el resto de la sesión (`ia_texto._PREFERIDO`).

**Probar:** `probar_go.py <archivo> - --soltar` ya no se cuelga con diálogos (los anota como `DIALOGO[…]`) e imprime el estado final de Inicio (`PANEL …`); MCP `arrastrar_video` (verifica A1 + audio del render, cuenta las pistas `XX-K/T`, muestrea los bloques ya asentados).
