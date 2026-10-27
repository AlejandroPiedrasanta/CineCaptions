# Pruebas y MCP del programa

## banco-mcp — Banco de pruebas y MCP del programa

**Qué:** Banco de pruebas y MCP del programa

**Dónde:** `banco_pruebas.py` (timeline temporal `zz_BANCO` con fondo gris + audio, `colocar_guion`, `renderizar`, `hoja`, `lado_a_lado`, `medir_texto`, `limpiar`); servidor MCP `mcp_cinecaptions.py` (stdio, sin dependencias; registrado en `.mcp.json`): `estado`, `packs`, `transcribir`, `planificar`, `banco_preparar`, `colocar`, `renderizar`, `cuadros`, `comparar`, `medir`, `limpiar_banco`, `probar_video` (todo el ciclo → hoja de cuadros), `go_real` (el botón GO de la app SIN pantalla vía `probar_go.py`: el flujo real del usuario → render → hoja), `probar_referencia` (los 15 bloques EXACTOS de la referencia → render → al lado del video: regresión del pack), `evaluar` (palabras grandes, cortes y estilos vs la referencia), `registro`. El servidor recarga solo los `guion_*`/`banco_pruebas` al cambiar en disco (`_recargar`); tras tocar `mcp_cinecaptions.py` hay que reconectar el MCP. `probar_go.py` necesita `w.show()` (offscreen): la animación final de GO es la que dispara la colocación, sin ella GO se cuelga tras «Armando los bloques…»

## pruebas-sin-pantalla — Probar la app sin pantalla (arneses Qt)

Python con dependencias: `6_compilacion/venv315/Scripts/python.exe`. Con `QT_QPA_PLATFORM=offscreen`; importar el script principal con `importlib`, parchear `licencia.vigente=lambda:True` y `SubtitleApp._revisar_licencia_al_arrancar=lambda s:None`. Los errores de pruebas se escriben en `~/DaVinciSubtitles/cinecaptions.log`.
- **Prefs reales:** `_poner_go_pack`, `_plantilla_elegida`, `poner_estilo_fijo`, `_alternar_*_go` escriben `~/DaVinciSubtitles/preferencias.json` de verdad: parchea `ajustes_ui.leer_prefs/guardar_prefs` en memoria (como `probar_go.py`) o haz copia antes.
- **GO sin Resolve:** `resolve_mcp.ruta_exe = lambda: None` (con solo `CINECAPTIONS_SIN_MCP` GO se detiene tras transcribir por `_abortar_si_fallo_el_timeline`) y anular `ui.error_con_acciones` (el diálogo modal bloquea el hilo UI). `w.show()` es obligatorio (la animación final de GO dispara la colocación).
- Este venv no trae las DLL de CUDA para Whisper: cae a CPU.
- Para fuentes reales NO `offscreen`: ventana en x=-5000 (`test_paridad.py`/`test_creativo.py` necesitan `qt_kit.crear_app()`). v5.49: con `offscreen` también salen reales con `QT_QPA_FONTDIR=C:/Windows/Fonts`; y para MEDIR repintados la ventana fuera de la pantalla no vale (Windows no la expone: Qt no pinta nada). Medir la animación de Inicio al tamaño del usuario: 2293×928 con `QT_SCALE_FACTOR=1.5` (tema `go-inicio`).
- v5.49: un arnés con su propia `QApplication` tiene que llamar igual a `qt_kit.crear_app()`: crea el despachador de `correr_en_hilo` y sin él NINGÚN resultado de hilo vuelve a la interfaz (la escena no se enteraba de un cambio de estilo y las medidas no contaban el trabajo de los `al_terminar`). Para cazar tirones: `faulthandler.dump_traceback_later(0.026, file=…)` rearmado en cada cuadro vuelca las pilas de TODOS los hilos cuando la interfaz no late (va en C, sin el GIL). Y anular `resolve_bridge.asegurar_conexion/conectar/modo_actual` y `colocacion.lanzar_puente_por_menu_windows`: a los 5 s la vigilancia de la conexión podría lanzar el Puente en el Resolve del usuario.

## herramientas-dev — Arneses de prueba con Resolve real y de estilos

Viven en `1_codigo/herramientas_dev/` (FUERA de la huella del instalador y del .exe) y calculan sus rutas desde `__file__`. Todos usan el Resolve real del usuario: pedir permiso antes si lo está usando (ver memoria `resolve-uso-paralelo-no-go-real`).
- `probar_cuelgue_resolve.py <video> <pack> <armar|colocar|efectos>`: suspende Resolve (NtSuspendProcess) en mitad de un GO real (armar / captions / efectos) y comprueba que el programa lo nota, lo cierra a la fuerza, lo reabre y termina.
- `probar_previo_resolve.py <video> <pack>`: Resolve suspendido ANTES de pulsar GO → `colocacion.preparar_resolve_para_go` lo reinicia.
- `probar_ciclos_go.py <video> <pack> <K>`: K GO seguidos (cuelgues intermitentes y tiempos). `probar_emojis_temas.py <video> <vertical:1|0> <pack>…`: GO solo con emojis + render + hoja de fotogramas (posición/animación).
- En `1_codigo/`: `probar_go_variantes.py` (GO sin pantalla con sonidos/emojis/efectos a mano), `probar_estilos_app.py` (3 estilos sin Resolve), `proyecto_pruebas.py` (proyecto temporal vacío de Resolve), `recortar_bucle_vistas.py` (clips de «Crea tu estilo» en bucle).
- Los arneses escriben las prefs REALES del usuario: parchear `ajustes_ui.guardar_prefs`. Para escribir parches con comillas usa la herramienta Write (los heredocs de bash se rompen).
