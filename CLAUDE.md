# CineCaptions — leer SOLO esto; lo demás se consulta por demanda

App PySide6 (v5.38, Python 3.15.2) que subtitula vídeos con IA local y los coloca en DaVinci Resolve (Free y Studio, Windows y Mac).
Carpetas: `1_codigo` programa · `2_recursos` lo que viaja en el .exe · `3_compilar` · `4_diseno` · `5_SFX` (biblioteca de sonido del autor, 8 GB, fuera de Git; `Desktop\SFX` es un enlace a ella; reglas en su `MAPA_SFX.md`: nunca borrar, mover ni renombrar sonidos) · `6_compilacion` (temporal, no tocar) · `7_mac` · `INSTALADORES/{Windows,Mac}` · `DOCUMENTACION` · `MEDIOS` (icono, renders 4K de Inicio, capturas 4K de las páginas y banners; fuera de Git).
«Tema N» de la interfaz → `id`: 1 `kinetic-planificador` · 2 `guion-planificador` · 3 `viral-planificador` · 4 `tema4` · 5 `tema5` · 6 `tema6`.
Python con dependencias (`$PY`): `6_compilacion/venv315/Scripts/python.exe`.

## Encontrar algo sin leer archivos (en este orden)
1. MCP `cinecaptions`: `mapa("palabras")` → temas, archivos y símbolos · `mapa(id="…")` → detalle (si es largo, índice; luego `parte="N"`/`"palabras"`) · `simbolo("nombre")` → solo esa función · `modulo("archivo")` · `llamadas("nombre")` → quién la usa (`sentido="sale"`: a qué llama; `niveles=3`: qué se rompe si la cambias) · `ruta("A","B")` · `cambios(n)` · `resumen()`.
   Sin MCP: `$PY 1_codigo/mapa_codigo.py mapa|tema|simbolo|modulo|llamadas|ruta|cambios <x>` (`tema <id> <parte>`).
2. Si falta: Grep del nombre + Read con `offset`/`limit` (~60 líneas).
3. NUNCA leer enteros: `CineCaptions (script principal).py` (13 600 líneas), `DOCUMENTACION/{LEEME.txt,REGISTRO_DE_CAMBIOS.txt,historial/}`, `6_compilacion/`, `2_recursos/`, `5_SFX/` (salvo su `MAPA_SFX.md`), `*.drb/.drt`, `.json` de packs, `__pycache__`. Primera vez: `DOCUMENTACION/RESUMEN.md`.

## Al cambiar algo
- Cambio grande: avisa antes qué archivos tocarás.
- Antes de darlo por terminado: `mapa(id="acoplamientos")` (gemelos `.lua`/`.py`, `REVISION_BIN`, versión, huella, mapa).
- Tema nuevo o cambiado: sección en `DOCUMENTACION/temas/<grupo>.md` (párrafos cortos que empiecen con `**Rótulo:**`) + entrada en `DOCUMENTACION/mapa.json` + `$PY 1_codigo/mapa_codigo.py generar`.
- Anota el porqué: `$PY 3_compilar/documentar.py --nota "…"`.
- Compilar (`Actualizar_Windows.ps1`; `-Comprobar` dice si está al día) y Mac (`Actualizar_Mac.ps1`, GitHub Actions ~15 min): SOLO cuando el usuario lo pida. Entregables en `INSTALADORES/`.
- Estado y pendientes: memoria `estado-y-pendientes` (solo lo actual; lo viejo a `DOCUMENTACION/historial/`).

## Mapa de temas — `id` [archivo principal]
<!-- MAPA:INICIO (lo escribe 1_codigo/mapa_codigo.py generar; no lo edites a mano) -->
- **general** (Visión general del programa): `documentacion` [mapa_codigo] · `acoplamientos` [version]
- **ui** (Interfaz Qt: ventana, diseño, rendimiento, ajustes): `ventana-paginas` [ir_a] · `fondo-animado` [efectos_ui] · `liquid-glass` [qt_kit] · `ritmo-fps` [ritmo_ui] · `qt-kit` [qt_kit] · `ajustes-tema` [ajustes_ui] · `isla-nav` [isla_ui] · `aurora` [qt_kit] · `recorrido` [recorrido_ui] · `reglas-rendimiento` [qt_kit] · `rendimiento-base` [cache_voz] · `ui-menores` [brillo_ui]
- **go** (GO e Inicio (botón, escena, arrastrar un video)): `go-inicio` [un_clic_ui] · `estilos-inicio` [estilos_inicio] · `orbe-go` [orbe_mecanica] · `arrastrar-video` [resolve_mcp] · `fuente-unica` [principal] · `go-progreso` [un_clic_ui] · `go-control` [un_clic_ui] · `go-colocacion-real` [colocacion] · `go-sin-resolve` [render_sin_resolve]
- **creativo** (Editor Creativo (palabras, Asistencia, Generar)): `editor-palabras` [WordTagWindow] · `creativo-ui` [editor_ui] · `creativo-vista-tema` [vista_tema] · `creativo-detecta-audio` [_estado_creativo]
- **estilos** (Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)): `pantalla-estilos` [proyecto_ui] · `estilos-slider` [1_codigo/estilos_slider] · `packs-drt` [plantillas] · `fuentes` [fuentes_sistema] · `generador-packs` [generar_comps] · `crea-tu-estilo` [ejemplos_estilo] · `mezcla-temas` [mezcla_planificador] · `tema4` [tema4_planificador] · `tema5` [edicion_pro_tema5] · `temas-ligero` [edicion_pro_temas] · `editar-quitar-pack` [edicion_pack] · `luxe-packs` [2_recursos/generador_packs/luxe_macro] · `captions-premium` [2_recursos/generador_packs/luxe_macro] · `tema6` [edicion_pro_tema6] · `banner-inspector` [2_recursos/generador_packs/banner_inspector] · `motions-resolve` [2_recursos/generador_packs/drfx_motions]
- **bloques** (Bloques de subtítulos (cerebro, estilo por bloque, pausas)): `bloques` [dynamic_subtitles] · `anim-cortos` [dynamic_subtitles] · `estilo-bloque` [estilos_bloque] · `colgantes` [dynamic_subtitles]
- **sonido** (Sonido y emojis (SFX Lab, reglas, emojis)): `sfx-lab` [sfx_studio] · `ducking-energia` [estilo_desde_imagen] · `sonido-palabra` [sfx_rules] · `sonido-emojis` [emojis_sfx] · `sonido-extra` [musica_go] · `sonido-estilo` [sfx_rules] · `emojis-estilos` [emojis_sets] · `emojis-posicion-free` [CineCaptions_Subtitulos.lua] · `biblioteca-sonidos` [herramientas_dev/importar_sonidos] · `emojis-coherentes` [emojis_conceptos] · `sonido-pro` [sfx_studio] · `sonido-biblioteca` [sonido_skill] · `ai-sound-director` [director_sonido]
- **guion** (Estilo «guion» (pack Referencia, palabra a palabra)): `guion-planificador` [guion_planificador] · `creativo-guion` [guion_editor] · `estilo-oracion` [guion_planificador] · `barrido-referencia` [luxe_macro]
- **kinetic** (Estilo «Kinetic» (títulos de gancho: héroe, cintas, anillos)): `kinetic-planificador` [kinetic_planificador] · `kinetic-pack` [2_recursos/generador_packs/pack_kinetic] · `kinetic-neon-kit` [kit_neon] · `kinetic-app-resolve` [hacer_vista_kinetic] · `kinetic-pruebas` [probar_kinetic]
- **viral** (Estilo «VIRAL» (pila fina + negrita cursiva y los efectos shatter, select, drag)): `viral-planificador` [viral_planificador] · `viral-pack` [2_recursos/generador_packs/pack_viral] · `viral-app-resolve` [hacer_vista_viral] · `viral-pruebas` [probar_viral] · `viral-colores` [viral_captions]
- **voz-ia** (Voz e IA de texto): `voz-ia` [subtitle_transcriber] · `texto-ayudas` [ortografia] · `ortografia-temas` [ortografia] · `voz-vocabulario` [vocabulario]
- **resolve** (Resolve (API, MCP, scripts, vistas reales)): `resolve-api` [resolve_bridge] · `vista-real-previo` [vistas_reales] · `resolve-mcp-mac` [resolve_mcp] · `free-sin-io` [resolve_scripts/CineCaptions_Subtitulos.lua] · `resolve-colgado` [resolve_bridge] · `scripts-resolve-inventario` [CineCaptions_Puente.lua] · `conexion-auto` [resolve_bridge]
- **compilar** (Compilar, versiones, instaladores (Windows y Mac)): `instalador-cs` [3_compilar/Instalador.cs] · `version` [version] · `mac` [Construir_Instalador_Mac.sh] · `compilar-win` [Actualizar_Windows.ps1] · `actualizaciones` [1_codigo/actualizaciones] · `mac-actualizar` [Actualizar_Mac.ps1]
- **vigilancia** (Vigilancia, logs y respaldo de modelos): `vigilancia` [vigilancia]
- **datos** (Datos del usuario, licencia y ajustes): `licencia` [licencia] · `archivos-seguros` [archivos_seguros] · `carpetas-del-usuario` [archivos_seguros] · `proyectos-usuario` [proyectos]
- **pruebas** (Pruebas y MCP del programa): `banco-mcp` [banco_pruebas] · `pruebas-sin-pantalla` [probar_go] · `herramientas-dev` [herramientas_dev/probar_cuelgue_resolve]
- **efectos** (Efectos visuales (intro, transiciones en los cortes, iconos flotantes)): `efectos-visuales` [efectos_visuales] · `efectos-movimiento` [fusion_v1] · `efectos-extra` [efectos_extra] · `quitar-pausas` [pausas] · `broll` [broll] · `edicion-pro` [edicion_pro] · `kit8` [remotion/src/Kit8.tsx] · `escenas-pantalla` [edicion_pro_escenas] · `internet-broll` [fuentes_web] · `motions-pro` [motions_ui] · `pro-lateral` [pro_lateral_ui] · `estilos-pro` [estilos_pro] · `intros-gancho` [intros_gancho] · `motions-completo` [motions_completo] · `vigilante-pro` [vigilante_pro] · `motions-editables` [edicion_pro_ograf] · `video-rotado-monedas` [rotacion_video] · `personajes-3d` [remotion/src/Pictos3D.tsx] · `posiciones-pro` [posiciones_pro] · `emojis-pro` [edicion_pro]
<!-- MAPA:FIN -->

## Reglas que no se rompen (detalle: `mapa(id="reglas-rendimiento")`)
- Estado del usuario (prefs, marcas, proyectos, manifiestos) SOLO con `archivos_seguros.escribir_json/mezclar_json`; nunca `write_text`.
- Hilo de la interfaz: sin red, `subprocess`, `sleep`, lectura masiva ni `resolve_mcp/resolve_bridge` → `correr_en_hilo`. Sin `QEasingCurve.setCustomType` ni efectos Qt sobre páginas; el vidrio de las tarjetas es FALSO a propósito.
- Packs: texto = solo macros Luxe reales (`MediaOut`, no `Saver`); al cambiar un pack subir `plantillas.REVISION_BIN`; Amro solo como principal; nunca `InsertFusionTitleIntoTimeline` con nombres dudosos (tumbó Resolve).
- Scripts de Resolve: `CineCaptions.py` y `.lua` son gemelos. Versión única en `version.py` (`3_compilar/sincronizar_version.py` la copia).
- Rutas de recursos con `base_recursos()` (en el .exe no están junto al .py).
- Python 3.15: nada de `from concurrent.futures import ThreadPoolExecutor` (el paquete la expone «lazy» y en el .exe salió `'lazy_import' object is not callable`, Tema 1 placa): `from concurrent.futures.thread import ThreadPoolExecutor`.
- Estilo «guion»: la palabra grande cabe SIN zoom; las grandes van en pistas inferiores.
- Interfaz simple: sin toasts ni tooltips (avisos al Registro); en la UI solo «Tema N».

## Ejemplos visuales («dame ejemplos de cómo queda»)
- Son SOLO propuestas: no se toca el código hasta que el usuario elige una.
- Siempre REALISTAS: HTML a tamaño real con los recursos de verdad (banner, logo, capas, colores y fuentes del programa o instalador), capturado a PNG con `2_recursos/edicion_pro/remotion/runtime/chrome/chrome-headless-shell-win64/chrome-headless-shell.exe --headless --force-device-scale-factor=1.5 --window-size=W,H --screenshot=…` y enviado con SendUserFile. Nada de esquemas genéricos.
- Normalmente 3 (A, B, C); se mantiene el estilo actual salvo que pida otro. Todo en el scratchpad, nunca en el proyecto.

## Probar (detalle: `mapa(id="pruebas-sin-pantalla")`)
- **Nada de pruebas dentro de esta carpeta.** Scripts, videos, renders, logs y salidas de prueba van al scratchpad de la sesión (o una carpeta temporal fuera del proyecto). Si algo de prueba tiene que crearse aquí, se BORRA al terminar y se comprueba con `git status --short` que no queda nada suelto.
- Sin pantalla: `QT_QPA_PLATFORM=offscreen` y parchear `ajustes_ui.guardar_prefs` (los arneses escriben las prefs REALES).
- El usuario usa Resolve a la vez: NO `go_real` ni lanzar el Puente en Studio; probar efectos con Resolve simulado. MCP: `probar_video`, `probar_referencia`, `arrastrar_video`, `evaluar` (tras tocar `mcp_cinecaptions.py`, reconectar el MCP).
