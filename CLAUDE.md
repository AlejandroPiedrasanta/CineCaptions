# CineCaptions — leer SOLO esto; lo demás se consulta por demanda

App PySide6 (v5.3.2) que subtitula vídeos con IA local y coloca los subtítulos en DaVinci Resolve. Carpetas: `1_codigo` programa · `2_recursos` · `3_compilar` · `4_diseno` · `5_licencias` (otro producto) · `6_compilacion` (temporal, no tocar) · `7_mac` · `INSTALADORES/{Windows,Mac}` · `DOCUMENTACION`.

## Consultar SIN leer archivos (en este orden; ahorra tokens)
1. **MCP `cinecaptions`**: `mapa("palabras")` → temas con archivos y símbolos · `mapa(id="…")` → detalle del tema · `simbolo("nombre")` → solo esa función/clase/método · `modulo("archivo")` → qué es · `cambios(n)` · `resumen()`.
   Sin MCP: `6_compilacion/venv314/Scripts/python.exe 1_codigo/mapa_codigo.py mapa|tema|simbolo|modulo|cambios <x>`.
2. Si hace falta más: Grep del nombre + Read con `offset`/`limit` (~60 líneas).
3. **NUNCA leer enteros**: `CineCaptions (script principal).py` (12 000 líneas), `LEEME.txt`, `REGISTRO_DE_CAMBIOS.txt`, `6_compilacion/`, `2_recursos/`, `*.drb/.drt`, `.json` de packs, `__pycache__`. Primera vez en el proyecto: `DOCUMENTACION/RESUMEN.md` (una página).
4. Responde breve, muestra solo el cambio; salidas largas: solo errores/últimas líneas. Antes de cambios grandes, avisa qué archivos tocarás.
5. Al añadir o cambiar un tema: sección en `DOCUMENTACION/temas/<grupo>.md` + entrada en `DOCUMENTACION/mapa.json`, y `python 1_codigo/mapa_codigo.py generar` (reescribe el mapa de abajo y avisa de lo que ya no existe).

## Mapa de temas — `id` [archivos]; detalle con `mapa(id=…)`
<!-- MAPA:INICIO (lo escribe 1_codigo/mapa_codigo.py generar; no lo edites a mano) -->
- **general** (Visión general del programa): `documentacion` [mapa_codigo]
- **ui** (Interfaz Qt: ventana, diseño, rendimiento, ajustes): `ventana-paginas` [ir_a SubtitleApp] · `fondo-animado` [efectos_ui mograf_ui] · `liquid-glass` [qt_kit efectos_ui] · `ritmo-fps` [ritmo_ui] · `qt-kit` [qt_kit] · `ajustes-tema` [ajustes_ui tema] · `isla-nav` [isla_ui 2_recursos/logo_cinema_productions.png] · `aurora` [qt_kit efectos_ui] · `recorrido` [recorrido_ui ajustes_ui] · `reglas-rendimiento` [qt_kit]
- **go** (GO e Inicio (botón, escena, arrastrar un video)): `go-inicio` [un_clic_ui escena_go mograf_ui] · `estilos-inicio` [estilos_inicio] · `orbe-go` [orbe_mecanica] · `arrastrar-video` [resolve_mcp] · `fuente-unica` [principal]
- **creativo** (Editor Creativo (palabras, Asistencia, Generar)): `editor-palabras` [WordTagWindow _poner_rol] · `creativo-ui` [editor_ui] · `creativo-detecta-audio` [_estado_creativo _refrescar_editor_vacio]
- **estilos** (Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)): `pantalla-estilos` [PlantillasWindow _asegurar_estilos] · `packs-drt` [plantillas packs_drt] · `fuentes` [fuentes_sistema instalar_fuentes] · `generador-packs` [generar_comps luxe_macro construir_pack] · `crea-tu-estilo` [ejemplos_estilo vistas_guia crea_estilo_ui] · `editar-quitar-pack` [edicion_pack 2_recursos/guia_estilo/editar_pack] · `luxe-packs` [2_recursos/generador_packs/luxe_macro construir_pack plantillas]
- **bloques** (Bloques de subtítulos (cerebro, estilo por bloque, pausas)): `bloques` [dynamic_subtitles composicion] · `anim-cortos` [dynamic_subtitles resolve_scripts/CineCaptions CineCaptions_Subtitulos.lua] · `estilo-bloque` [estilos_bloque] · `colgantes` [dynamic_subtitles]
- **sonido** (Sonido y emojis (SFX Lab, reglas, emojis)): `sfx-lab` [sfx_studio sfx_rules sfx_editor] · `ducking-energia` [estilo_desde_imagen ducking energia] · `sonido-palabra` [sfx_rules] · `sonido-emojis` [emojis_sfx generar_sfx_emoji emojis_sfx_ui]
- **guion** (Estilo «guion» (pack Referencia, palabra a palabra)): `guion-planificador` [guion_planificador guion_referencia guion_captions] · `creativo-guion` [guion_editor guion_vista CineCaptions - Vista Real] · `estilo-oracion` [guion_planificador guion_captions]
- **voz-ia** (Voz e IA de texto): `voz-ia` [subtitle_transcriber motor_voz ia_texto]
- **resolve** (Resolve (API, MCP, scripts, vistas reales)): `resolve-api` [resolve_bridge resolve_mcp instalador_scripts] · `vista-real-previo` [vistas_reales] · `resolve-mcp-mac` [resolve_mcp resolve_bridge]
- **compilar** (Compilar, versiones, instaladores (Windows y Mac)): `instalador-cs` [3_compilar/Instalador.cs 4_diseno/banner/crear_banner] · `version` [version] · `mac` [Construir_Instalador_Mac.sh cinecaptions_mac.spec] · `compilar-win` [Actualizar_Windows.ps1 Construir_Instalador.ps1 3_compilar/sincronizar_version] · `actualizaciones` [1_codigo/actualizaciones Publicar_Version.ps1 1_codigo/ajustes_ui] · `mac-actualizar` [Actualizar_Mac.ps1]
- **vigilancia** (Vigilancia, logs y respaldo de modelos): `vigilancia` [vigilancia registro]
- **datos** (Datos del usuario, licencia y ajustes): `licencia` [licencia ventana_licencia] · `archivos-seguros` [archivos_seguros] · `carpetas-del-usuario` [archivos_seguros copias]
- **pruebas** (Pruebas y MCP del programa): `banco-mcp` [banco_pruebas mcp_cinecaptions probar_go] · `pruebas-sin-pantalla` [probar_go]
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
