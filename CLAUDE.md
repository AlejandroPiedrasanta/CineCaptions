# CineCaptions — leer SOLO esto; lo demás se consulta por demanda

App PySide6 (v5.5.6) que subtitula vídeos con IA local y coloca los subtítulos en DaVinci Resolve. Carpetas: `1_codigo` programa · `2_recursos` · `3_compilar` · `4_diseno` · `5_licencias` (otro producto) · `6_compilacion` (temporal, no tocar) · `7_mac` · `INSTALADORES/{Windows,Mac}` · `DOCUMENTACION`.

## Consultar SIN leer archivos (en este orden; ahorra tokens)
1. **MCP `cinecaptions`**: `mapa("palabras")` → temas con archivos y símbolos · `mapa(id="…")` → detalle del tema · `simbolo("nombre")` → solo esa función/clase/método · `modulo("archivo")` → qué es · `cambios(n)` · `resumen()`.
   Sin MCP: `6_compilacion/venv314/Scripts/python.exe 1_codigo/mapa_codigo.py mapa|tema|simbolo|modulo|cambios <x>`.
2. Si hace falta más: Grep del nombre + Read con `offset`/`limit` (~60 líneas).
3. **NUNCA leer enteros**: `CineCaptions (script principal).py` (13 600 líneas; usa `simbolo`), `DOCUMENTACION/{LEEME.txt,REGISTRO_DE_CAMBIOS.txt,historial/}`, `6_compilacion/`, `2_recursos/`, `*.drb/.drt`, `.json` de packs, `__pycache__`. Primera vez en el proyecto: `DOCUMENTACION/RESUMEN.md` (una página).
4. Responde breve, muestra solo el cambio; salidas largas: solo errores/últimas líneas. Antes de cambios grandes, avisa qué archivos tocarás.
5. Al añadir o cambiar un tema: sección en `DOCUMENTACION/temas/<grupo>.md` + entrada en `DOCUMENTACION/mapa.json`, y `python 1_codigo/mapa_codigo.py generar` (reescribe el mapa de abajo; avisa de lo que ya no existe y de código sin tema).
6. **Antes de dar un cambio por terminado**: `mapa(id="acoplamientos")` = qué más hay que cambiar (gemelos `.lua`/`.py`, `REVISION_BIN`, versión, huella, mapa). Estado de versiones y pendientes: memoria `estado-y-pendientes`. Arneses de prueba con Resolve: `mapa(id="herramientas-dev")`.

## Mapa de temas — `id` [archivos]; detalle con `mapa(id=…)`
<!-- MAPA:INICIO (lo escribe 1_codigo/mapa_codigo.py generar; no lo edites a mano) -->
- **general** (Visión general del programa): `documentacion` [mapa_codigo] · `acoplamientos` [version]
- **ui** (Interfaz Qt: ventana, diseño, rendimiento, ajustes): `ventana-paginas` [ir_a] · `fondo-animado` [efectos_ui] · `liquid-glass` [qt_kit] · `ritmo-fps` [ritmo_ui] · `qt-kit` [qt_kit] · `ajustes-tema` [ajustes_ui] · `isla-nav` [isla_ui] · `aurora` [qt_kit] · `recorrido` [recorrido_ui] · `reglas-rendimiento` [qt_kit] · `rendimiento-base` [cache_voz] · `ui-menores` [brillo_ui]
- **go** (GO e Inicio (botón, escena, arrastrar un video)): `go-inicio` [un_clic_ui] · `estilos-inicio` [estilos_inicio] · `orbe-go` [orbe_mecanica] · `arrastrar-video` [resolve_mcp] · `fuente-unica` [principal] · `go-progreso` [un_clic_ui] · `go-control` [un_clic_ui] · `go-colocacion-real` [colocacion] · `go-sin-resolve` [render_sin_resolve]
- **creativo** (Editor Creativo (palabras, Asistencia, Generar)): `editor-palabras` [WordTagWindow] · `creativo-ui` [editor_ui] · `creativo-detecta-audio` [_estado_creativo]
- **estilos** (Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)): `pantalla-estilos` [PlantillasWindow] · `estilos-slider` [1_codigo/estilos_slider] · `packs-drt` [plantillas] · `fuentes` [fuentes_sistema] · `generador-packs` [generar_comps] · `crea-tu-estilo` [ejemplos_estilo] · `mezcla-temas` [mezcla_planificador] · `tema4` [tema4_planificador] · `tema5` [edicion_pro_tema5] · `temas-ligero` [edicion_pro_temas] · `editar-quitar-pack` [edicion_pack] · `luxe-packs` [2_recursos/generador_packs/luxe_macro] · `tema6` [edicion_pro_tema6]
- **bloques** (Bloques de subtítulos (cerebro, estilo por bloque, pausas)): `bloques` [dynamic_subtitles] · `anim-cortos` [dynamic_subtitles] · `estilo-bloque` [estilos_bloque] · `colgantes` [dynamic_subtitles]
- **sonido** (Sonido y emojis (SFX Lab, reglas, emojis)): `sfx-lab` [sfx_studio] · `ducking-energia` [estilo_desde_imagen] · `sonido-palabra` [sfx_rules] · `sonido-emojis` [emojis_sfx] · `sonido-extra` [musica_go] · `sonido-estilo` [sfx_rules] · `emojis-estilos` [emojis_sets] · `emojis-posicion-free` [CineCaptions_Subtitulos.lua] · `biblioteca-sonidos` [herramientas_dev/importar_sonidos] · `emojis-coherentes` [emojis_conceptos] · `sonido-pro` [sfx_studio]
- **guion** (Estilo «guion» (pack Referencia, palabra a palabra)): `guion-planificador` [guion_planificador] · `creativo-guion` [guion_editor] · `estilo-oracion` [guion_planificador] · `barrido-referencia` [luxe_macro]
- **kinetic** (Estilo «Kinetic» (títulos de gancho: héroe, cintas, anillos)): `kinetic-planificador` [kinetic_planificador] · `kinetic-pack` [2_recursos/generador_packs/pack_kinetic] · `kinetic-app-resolve` [hacer_vista_kinetic] · `kinetic-pruebas` [probar_kinetic]
- **viral** (Estilo «VIRAL» (pila fina + negrita cursiva y los efectos shatter, select, drag)): `viral-planificador` [viral_planificador] · `viral-pack` [2_recursos/generador_packs/pack_viral] · `viral-app-resolve` [hacer_vista_viral] · `viral-pruebas` [probar_viral] · `viral-colores` [viral_captions]
- **voz-ia** (Voz e IA de texto): `voz-ia` [subtitle_transcriber] · `texto-ayudas` [ortografia] · `ortografia-temas` [ortografia]
- **resolve** (Resolve (API, MCP, scripts, vistas reales)): `resolve-api` [resolve_bridge] · `vista-real-previo` [vistas_reales] · `resolve-mcp-mac` [resolve_mcp] · `free-sin-io` [resolve_scripts/CineCaptions_Subtitulos.lua] · `resolve-colgado` [resolve_bridge] · `scripts-resolve-inventario` [CineCaptions_Puente.lua] · `conexion-auto` [resolve_bridge]
- **compilar** (Compilar, versiones, instaladores (Windows y Mac)): `instalador-cs` [3_compilar/Instalador.cs] · `version` [version] · `mac` [Construir_Instalador_Mac.sh] · `compilar-win` [Actualizar_Windows.ps1] · `actualizaciones` [1_codigo/actualizaciones] · `mac-actualizar` [Actualizar_Mac.ps1]
- **vigilancia** (Vigilancia, logs y respaldo de modelos): `vigilancia` [vigilancia]
- **datos** (Datos del usuario, licencia y ajustes): `licencia` [licencia] · `archivos-seguros` [archivos_seguros] · `carpetas-del-usuario` [archivos_seguros] · `proyectos-usuario` [proyectos]
- **pruebas** (Pruebas y MCP del programa): `banco-mcp` [banco_pruebas] · `pruebas-sin-pantalla` [probar_go] · `herramientas-dev` [herramientas_dev/probar_cuelgue_resolve]
- **efectos** (Efectos visuales (intro, transiciones en los cortes, iconos flotantes)): `efectos-visuales` [efectos_visuales] · `efectos-movimiento` [fusion_v1] · `efectos-extra` [efectos_extra] · `quitar-pausas` [pausas] · `broll` [broll] · `edicion-pro` [edicion_pro] · `kit8` [remotion/src/Kit8.tsx] · `escenas-pantalla` [edicion_pro_escenas] · `internet-broll` [fuentes_web] · `motions-pro` [motions_ui]
<!-- MAPA:FIN -->

## Reglas que no se rompen (detalle: `mapa(id="reglas-rendimiento")`)
- Estado del usuario (prefs, marcas, proyectos, manifiestos) SOLO con `archivos_seguros.escribir_json/mezclar_json`; nunca `write_text`.
- Hilo de la interfaz: sin red, `subprocess`, `sleep`, lectura masiva ni llamadas a `resolve_mcp/resolve_bridge`: `correr_en_hilo`. Sin `QEasingCurve.setCustomType`, sin efectos Qt sobre páginas; el vidrio de las tarjetas es FALSO a propósito.
- Packs: texto = solo macros Luxe reales (`MediaOut`, no `Saver`); al cambiar un pack subir `plantillas.REVISION_BIN`; Amro solo como principal; nunca `InsertFusionTitleIntoTimeline` con nombres dudosos (tumbó Resolve).
- Scripts de Resolve: `CineCaptions.py` y `.lua` son gemelos (mantenerlos iguales). Versión única: `version.py` (`3_compilar/sincronizar_version.py` la copia a los scripts).
- Estilo «guion»: la palabra grande debe caber SIN zoom; las grandes van en pistas inferiores.

## Después de CUALQUIER mejora del programa
`powershell -ExecutionPolicy Bypass -File Actualizar_Windows.ps1` (sube la versión si el código cambió; `-Comprobar` dice si está al día) y `…Actualizar_Mac.ps1` (GitHub Actions, ~15 min, en segundo plano). Entregables en `INSTALADORES/`. Anota el porqué con `python 3_compilar/documentar.py --nota "…"`.

## Probar (detalle: `mapa(id="pruebas-sin-pantalla")`)
Python con dependencias: `6_compilacion/venv314/Scripts/python.exe`; `QT_QPA_PLATFORM=offscreen`; los arneses escriben las prefs REALES del usuario: parchear `ajustes_ui.guardar_prefs`. MCP de pruebas con Resolve: `go_real`, `probar_video`, `probar_referencia`, `arrastrar_video`, `evaluar` (tras tocar `mcp_cinecaptions.py` hay que reconectar el MCP).
