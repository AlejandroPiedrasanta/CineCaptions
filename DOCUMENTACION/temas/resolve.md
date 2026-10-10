# Resolve (API, MCP, scripts, vistas reales)

## resolve-api — Resolve (API, puente, MCP, scripts)

**Qué:** Resolve (API/puente/MCP)

**Dónde:** `resolve_bridge.py`, `resolve_mcp.py`, `instalador_scripts.py`

## vista-real-previo — Vista real cortada a medias

**Qué:** Vista real cortada a medias (el timeline temporal «· vista …» quedaba como el actual)

**Dónde:** `vistas_reales.py` · `anotar_previo`, `reparar_pendiente`, `PREVIO` (`~/DaVinciSubtitles/vista_previo.json`); se llama desde `resolve_mcp.ejecutar_py` / `preparar_resolve` (`_reparar_vistas`)

## nota — v5.8 segunda pasada de la auditoría

Los gemelos de Resolve son IGUALES también en emojis animados: el .lua (Free) ya importa la secuencia e_[0001-NNNN].png, la repite en bucle y le pone la comp de Fusion de entrada/salida (sin io, en Free 21.1, va en bucle pero sin rebote). Se comprobó ítem por ítem contra el .py en Resolve Studio (fuscript -l lua): pistas, tiempos, Tilt/Pan/Zoom, SFX y la expresión de la comp, idénticos.

## nota — v5.8 segunda pasada de la auditoría

vistas_reales.anotar_previo guarda en vista_previo.json el timeline en que estabas antes de la vista real; si el programa o Resolve se cortan a medias, resolve_mcp (ejecutar_py/preparar_resolve) llama a vistas_reales.reparar_pendiente: vuelve a ese timeline y borra los temporales (con 3 s de margen). Con una vista real en curso en este programa (_ACTIVOS) no repara.

## resolve-mcp-mac — Dónde está ResolveMCP en cada sistema (v5.3.4)

`resolve_mcp.ruta_exe()` (RESOLVE_MCP_PATH manda, como en el paquete oficial `DaVinciResolve.mcpb > server/index.js` que Blackmagic deja en la carpeta de Resolve):
- Windows: `<Resolve>\ResolveMCP.exe` (carpeta del registro de Resolve, o Program Files).
- **macOS: `/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolveMCP`** (antes se buscaba en `Contents/MacOS` y `Contents/Libraries`: NO existe, y en Mac GO caía al Puente de Resolve Free → «el Puente perdió la conexión» aunque tuvieras Studio).
- Linux: `/opt/resolve/bin/ResolveMCP`.
Orden de caminos de `resolve_bridge.ejecutar`: MCP → Puente vivo → API externa de Studio (`disponible()`; necesita Preferencias > Sistema > General > «External scripting using» = Local) → (Mac) Puente lanzado solo. Si Resolve contesta pero sin scripting externo (`scripting_desactivado()`), se devuelve `MENSAJE_SCRIPTING_DESACTIVADO` en vez de probar el Puente. Intérpretes propios de Resolve 21.1: macOS `Contents/Applications/ResolvePython`, Windows `ResolvePython\ResolvePython.exe`. Sin Mac real para probar: si un Mac falla, pedir `~/DaVinciSubtitles/errores.log`, `bridge_error.txt` y «Copiar informe» del Registro.

## free-sin-io — Resolve Free 21.1 (probado en un Resolve Free real, 2026-10-09)

**Qué:** en el menú de Free 21.1 los scripts Lua NO tienen `io` (`SIN_IO` en el Puente y en `CineCaptions_Subtitulos.lua`): el Puente se habla por señales (latido y respuestas = archivos creados con `ExportKeyboardPreset`, trabajos por el sidecar `<archivo>.lua`, reportes por `fusion:Execute` → `ResolveDebug.txt`). Todo dato que lea el Lua tiene que existir también como **sidecar `<archivo>.json.lua`** (`sidecar_lua.escribir_sidecar`): los datos de VIRAL/Kinetic/Referencia (`kinetic_captions.escribir`, `guion_captions.escribir`) no lo escribían y en Free se colocaban 0 líneas. El manifiesto también (`colocacion.vista_en_manifiesto` lo reescribe).

**Reglas para tocar el Lua:** nunca `io.open` directo: `archivo_existe(ruta)` (en SIN_IO da por bueno y decide la API: `ImportMedia`/`ImportFolderFromFile`); `dato_existe` es SOLO para `.json` con sidecar (un `.drb` es binario y no lo tiene). Sin MCP (`resolve_mcp.ruta_exe() is None`) = Free. **v5.4.17:** en Free TODO va por el Puente (1.0.38): `armar_video` (`CineCaptions_ArmarVideo.lua`: proyecto «CineCaptions» + timeline con el video soltado), `efectos` (`CineCaptions_Efectos.lua`, gemela de `colocar_efectos.py`) y `pausas` (`CineCaptions_Pausas.lua`, gemela de `pausas._CORTAR`). El registro de Resolve cambia lo que no es ASCII por `?` (el «·» de un nombre sale «??»): solo se ve en los reportes, no afecta a los datos.

**Menú:** en Resolve (español) es «Área de trabajo ▸ Secuencias de comandos ▸ CineCaptions_Puente» (en inglés Workspace ▸ Scripts ▸ …); los scripts de la carpeta `Utility` salen directos en ese menú, no hay submenú «Utility». **El Puente se lanza solo** (`resolve_bridge.lanzar_puente_auto`): Windows = consola F6 de Resolve + `dofile([[…/CineCaptions_Puente.lua]])` (`colocacion.lanzar_puente_windows`; Resolve cerrado → `abrir_resolve_windows` lo abre y espera a que reabra el último proyecto); Mac = `lanzar_puente_mac` pulsa el menú por System Events (necesita permiso de Accesibilidad; con Resolve cerrado hace `open -a «DaVinci Resolve»` y espera a que aparezca el menú de Scripts = proyecto abierto). Layout presets: «Distribución de interfaz».

**Teclear en Resolve (Windows) con seguridad:** nunca teclear sin comprobar el foco. `_escribir_texto(texto, hwnd=consola)` mira `GetForegroundWindow()` ANTES de cada carácter y para si el foco se va (en un Resolve recién abierto el foco se escapaba a media orden y el resto del texto, ~200 caracteres, caía en OTRA aplicación); el Enter solo se pulsa con la consola al frente; reintenta 3 veces limpiando la línea (Ctrl+A, Retroceso). La consola de Resolve es una sola ventana que se oculta al cerrarla (WM_CLOSE no mata el Puente) y se vuelve a mostrar con F6.

**Puente viejo tras actualizar:** el Puente que ya corría sigue con el código viejo y responde «Accion desconocida» a las acciones nuevas. `resolve_bridge.VERSION_DE_ACCION` dice desde qué versión existe cada acción; `ejecutar` (si `puente_no_conoce(accion)`) lanza el Puente nuevo con `forzar=True` (el nuevo pide el relevo al viejo con la señal `puente.relevo`) y espera a que lata la versión actual; si no puede, devuelve `MENSAJE_PUENTE_VIEJO`. Al subir una acción nueva al Puente: subir `VERSION` en el .lua, `VERSION_PUENTE_ESPERADA` y añadirla a `VERSION_DE_ACCION`.

**Pruebas:** abrir Resolve Free, proyecto temporal, lanzar el Puente por el menú (Windows-MCP: clic en las coordenadas absolutas del escritorio virtual), y correr GO sin MCP con un arnés que use `qt_kit.crear_app()` (con `QApplication([])` suelto no hay despachador y `correr_en_hilo` nunca devuelve el resultado: GO parece colgado en el paso «timeline»). Resolve en primer plano para reproducir: `colocacion._al_frente` (AttachThreadInput + SwitchToThisWindow).

**Organizador de proyectos (v5.4.24, Windows Free):** Resolve recién abierto muestra el «Organizador de proyectos» y sin proyecto abierto no hay Scripts ni consola F6, así que el Puente no arranca. `colocacion.abrir_resolve_windows` llama a `pasar_organizador_windows(nombre)`: un PowerShell con UI Automation pulsa `…projActionBottomFrame.btnAddProject` («Crear proyecto») y, en el diálogo `UiNewProjectOptionsDlg`, pone el nombre `CineCaptions_nuevo_HHMMSS` (`lineEdit_ProjectName`) y pulsa `pushButton_Create`. Los ids (AutomationId) de Resolve NO cambian con el idioma, los textos sí. `colocacion.PROYECTO_INICIAL` guarda el nombre; la orden de ArmarVideo lleva `descartar` y `CineCaptions_ArmarVideo.lua` borra ese proyecto vacío (también por el prefijo `CineCaptions_nuevo`) al crear «CineCaptions». Mac: sin hacer (queda la espera de siempre). **Expandir vista:** `colocacion.expandir_vista_windows()` activa la casilla `…frameExpandControls.btnEditExpandViewer` (barra del timeline, TogglePattern: Off→On deja el visor a toda la altura; también abre un panel con disposiciones de panel) y `reproducir_desde_inicio` la llama antes de Inicio+Espacio (log «GO · vista»). Sin mouse ni foco, idempotente (1 s). Otros ids: `btnLoad` («Abrir»). No cambia con presets de disposición: el preset «CineCaptions vertical» sigue siendo opcional.
