# CineCaptions — leer SOLO esto; lo demás se consulta por demanda

App PySide6 (v5.94, Python 3.15.2) que subtitula vídeos con IA local y los coloca en DaVinci Resolve (Free y Studio, Windows y Mac).
**La raíz solo enseña 2 carpetas (2026-11-16, pedido del usuario): `PROGRAMA/` (todo el programa) e `INSTALADORES/{Windows,Mac}`.** Las rutas de este archivo son DENTRO de `PROGRAMA/` (los scripts y el MCP corren desde ahí). En la raíz quedan ocultos CLAUDE.md, .git, .github, .claude, .gitignore, .mcp.json y un acceso oculto `5_SFX` → `PROGRAMA/5_SFX`.
Carpetas (en `PROGRAMA/`): `1_codigo` programa · `2_recursos` lo que viaja en el .exe · `3_compilar` · `4_diseno` · `5_SFX` (biblioteca de sonido del autor, 8 GB, fuera de Git; reglas en su `MAPA_SFX.md`: nunca borrar, mover ni renombrar sonidos) · `6_compilacion` (temporal, no tocar; su Python base vive dentro: si se mueve, corregir `venv315/pyvenv.cfg`) · `7_mac` · `DOCUMENTACION` · `MEDIOS` (icono, renders 4K de Inicio, capturas 4K de las páginas y banners; fuera de Git) · `WEB CINECAPTIONS` (la web, su propio Git) · `Actualizar_Windows.ps1`, `Actualizar_Mac.ps1`, `Publicar_Version.ps1`. Cada carpeta lleva su icono negro (`.cf/icono.ico` + `desktop.ini`).
«Estilo N» de la interfaz (antes «Tema N»; en el código siguen siendo temas) → `id`: 1 `kinetic-planificador` · 2 `guion-planificador` · 3 `viral-planificador` · 4 `tema4` · 5 `tema5` · 6 `tema6` · 7 `tema7` · 8 `tema8` · 9 `tema9`.
Python con dependencias (`$PY`): `PROGRAMA/6_compilacion/venv315/Scripts/python.exe` (desde `PROGRAMA/`: `6_compilacion/venv315/Scripts/python.exe`).

## Encontrar algo sin leer archivos (en este orden)
1. MCP `cinecaptions` (ToolSearch «cinecaptions» las carga; cada una explica sus opciones): `mapa("palabras")`/`mapa(id=…)` temas · `donde` archivo:línea · `simbolo` solo esa función · `modulo` · `llamadas` quién la usa (`niveles=3`: qué se rompe) · `ruta` · `cambios` · `resumen`. Sin MCP: `$PY 1_codigo/mapa_codigo.py <orden> <x>`.
2. Si falta: Grep del nombre + Read con `offset`/`limit` (~60 líneas).
3. NUNCA leer enteros: `CineCaptions (script principal).py` (~15 600 líneas), `DOCUMENTACION/{LEEME.txt,REGISTRO_DE_CAMBIOS.txt,historial/}`, `6_compilacion/`, `2_recursos/`, `5_SFX/` (salvo su `MAPA_SFX.md`), `*.drb/.drt`, `.json` de packs, `__pycache__`. Primera vez: `DOCUMENTACION/RESUMEN.md`.

## Al cambiar algo
- Cambio grande: avisa antes qué archivos tocarás.
- Antes de darlo por terminado: `mapa(id="acoplamientos")` (gemelos `.lua`/`.py`, `REVISION_BIN`, versión, huella, mapa).
- Tema nuevo o cambiado: sección en `DOCUMENTACION/temas/<grupo>.md` (párrafos cortos que empiecen con `**Rótulo:**`) + entrada en `DOCUMENTACION/mapa.json` + `$PY 1_codigo/mapa_codigo.py generar`.
- Anota el porqué: `$PY 3_compilar/documentar.py --nota "…"`.
- Compilar (`Actualizar_Windows.ps1`; `-Comprobar` dice si está al día) y Mac (`Actualizar_Mac.ps1`, GitHub Actions ~15 min): SOLO cuando el usuario lo pida. Entregables en `INSTALADORES/`.
- Estado y pendientes: memoria `estado-y-pendientes` (solo lo actual; lo viejo a `DOCUMENTACION/historial/`).

## Mapa de temas — `id` (su archivo: `donde("id")`)
<!-- MAPA:INICIO (lo escribe 1_codigo/mapa_codigo.py generar; no lo edites a mano) -->
- **general** (Visión general del programa): documentacion acoplamientos
- **ui** (Interfaz Qt: ventana, diseño, rendimiento, ajustes): ventana-paginas fondo-animado liquid-glass ritmo-fps qt-kit ajustes-tema isla-nav aurora recorrido reglas-rendimiento rendimiento-base ui-menores idioma-ui
- **go** (GO e Inicio (botón, escena, arrastrar un video)): go-inicio estilos-inicio orbe-go arrastrar-video nitidez-4k fuente-unica go-progreso go-control go-colocacion-real go-sin-resolve go-premiere
- **creativo** (Editor Creativo (palabras, Asistencia, Generar)): editor-palabras creativo-ui creativo-vista-tema creativo-detecta-audio
- **estilos** (Estilos y packs (.drb/.drt, Luxe, Crea tu estilo)): pantalla-estilos estilos-slider packs-drt fuentes generador-packs crea-tu-estilo mezcla-temas tema4 tema4-recuadro tema5 zona-segura tema5-tipo temas-ligero editar-quitar-pack luxe-packs captions-premium tema6 tema7 tema8 tema9 banner-inspector motions-resolve
- **bloques** (Bloques de subtítulos (cerebro, estilo por bloque, pausas)): bloques anim-cortos estilo-bloque colgantes
- **sonido** (Sonido y emojis (SFX Lab, reglas, emojis)): sfx-lab ducking-energia sonido-palabra sonido-emojis sonido-extra sonido-estilo emojis-estilos emojis-posicion-free biblioteca-sonidos emojis-coherentes sonido-pro sonido-biblioteca sonido-oido sonido-por-estilo ai-sound-director
- **guion** (Estilo «guion» (pack Referencia, palabra a palabra)): guion-planificador creativo-guion estilo-oracion barrido-referencia
- **kinetic** (Estilo «Kinetic» (títulos de gancho: héroe, cintas, anillos)): kinetic-planificador kinetic-pack kinetic-neon-kit kinetic-app-resolve kinetic-pruebas
- **viral** (Estilo «VIRAL» (pila fina + negrita cursiva y los efectos shatter, select, drag)): viral-planificador viral-pack viral-app-resolve viral-pruebas viral-select-drag viral-crea-efectos tema3-linea viral-colores
- **voz-ia** (Voz e IA de texto): voz-ia texto-ayudas ortografia-temas voz-vocabulario
- **resolve** (Resolve (API, MCP, scripts, vistas reales)): resolve-api fluidez-resolve vista-real-previo resolve-mcp-mac free-sin-io resolve-colgado scripts-resolve-inventario conexion-auto correcciones-en-resolve
- **compilar** (Compilar, versiones, instaladores (Windows y Mac)): instalador-cs version mac compilar-win actualizaciones mac-actualizar equipo-al-dia
- **vigilancia** (Vigilancia, logs y respaldo de modelos): vigilancia arranque-seguro
- **datos** (Datos del usuario, licencia y ajustes): licencia archivos-seguros carpetas-del-usuario proyectos-usuario telemetria-errores ficha-equipo
- **pruebas** (Pruebas y MCP del programa): banco-mcp pruebas-sin-pantalla simular-equipos herramientas-dev
- **efectos** (Efectos visuales (intro, transiciones en los cortes, iconos flotantes)): efectos-visuales efectos-movimiento efectos-extra quitar-pausas broll edicion-pro kit8 escenas-pantalla internet-broll motions-pro pro-lateral estilos-pro intros-gancho motions-completo vigilante-pro motions-editables video-rotado-monedas personajes-3d posiciones-pro emojis-pro motions-pila efectos-panel
<!-- MAPA:FIN -->

## Reglas que no se rompen (detalle: `mapa(id="reglas-rendimiento")`)
- Estado del usuario (prefs, marcas, proyectos, manifiestos) SOLO con `archivos_seguros.escribir_json/mezclar_json`; nunca `write_text`.
- Hilo de la interfaz: sin red, `subprocess`, `sleep`, lectura masiva ni `resolve_mcp/resolve_bridge` → `correr_en_hilo`. Sin `QEasingCurve.setCustomType` ni efectos Qt sobre páginas; el vidrio de las tarjetas es FALSO a propósito.
- Packs: texto = solo macros Luxe reales (`MediaOut`, no `Saver`); al cambiar un pack subir `plantillas.REVISION_BIN`; Amro solo como principal; nunca `InsertFusionTitleIntoTimeline` con nombres dudosos (tumbó Resolve).
- Scripts de Resolve: `CineCaptions.py` y `.lua` son gemelos. Versión única en `version.py` (`3_compilar/sincronizar_version.py` la copia).
- Rutas de recursos con `base_recursos()` (en el .exe no están junto al .py).
- Python 3.15: nada de `from concurrent.futures import ThreadPoolExecutor` (el paquete la expone «lazy» y en el .exe salió `'lazy_import' object is not callable`, Tema 1 placa): `from concurrent.futures.thread import ThreadPoolExecutor`.
- Estilo «guion»: la palabra grande cabe SIN zoom; las grandes van en pistas inferiores.
- Interfaz simple: sin toasts ni tooltips (avisos al Registro); en la UI solo «Estilo N» y «estilo», nunca «tema».

## Ejemplos visuales («dame ejemplos de cómo queda»)
- Solo propuestas (normalmente A, B, C; estilo actual salvo que pida otro): el código no se toca hasta que elija. Todo en el scratchpad.
- REALISTAS: HTML a tamaño real con los recursos de verdad (banner, logo, capas, colores, fuentes), a PNG con `2_recursos/edicion_pro/remotion/runtime/chrome/chrome-headless-shell-win64/chrome-headless-shell.exe --headless --force-device-scale-factor=1.5 --window-size=W,H --screenshot=…` y SendUserFile. Nada de esquemas.

## Probar (detalle: `mapa(id="pruebas-sin-pantalla")`)
- **Nada de pruebas en esta carpeta**: al scratchpad; lo que haya que crear aquí se BORRA al terminar (comprobar con `git status --short`).
- Sin pantalla: `QT_QPA_PLATFORM=offscreen` y parchear `ajustes_ui.guardar_prefs` (los arneses escriben las prefs REALES).
- El usuario usa Resolve a la vez: NO `go_real` ni lanzar el Puente en Studio; probar efectos con Resolve simulado. MCP: `probar_video`, `probar_referencia`, `arrastrar_video`, `evaluar` (tras tocar `mcp_cinecaptions.py`, reconectar el MCP).
