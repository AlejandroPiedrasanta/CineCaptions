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

**Reglas para tocar el Lua:** nunca `io.open` directo: `archivo_existe(ruta)` (en SIN_IO da por bueno y decide la API: `ImportMedia`/`ImportFolderFromFile`); `dato_existe` es SOLO para `.json` con sidecar (un `.drb` es binario y no lo tiene). `animar_emoji` y los efectos visuales (`colocar_efectos`, comps de Fusion en V1) no funcionan en Free (el efecto se omite con un aviso `info`). Sin MCP (`resolve_mcp.ruta_exe() is None`) = Free.

**Menú:** en Resolve (español) es «Área de trabajo ▸ Secuencias de comandos ▸ CineCaptions_Puente» (en inglés Workspace ▸ Scripts ▸ …); los scripts de la carpeta `Utility` salen directos en ese menú, no hay submenú «Utility». El Puente se lanza a mano UNA vez por sesión en Windows (en Mac `lanzar_puente_mac` lo pulsa solo). Layout presets: «Distribución de interfaz».

**Pruebas:** abrir Resolve Free, proyecto temporal, lanzar el Puente por el menú (Windows-MCP: clic en las coordenadas absolutas del escritorio virtual), y correr GO sin MCP con un arnés que use `qt_kit.crear_app()` (con `QApplication([])` suelto no hay despachador y `correr_en_hilo` nunca devuelve el resultado: GO parece colgado en el paso «timeline»). Resolve en primer plano para reproducir: `colocacion._al_frente` (AttachThreadInput + SwitchToThisWindow).
