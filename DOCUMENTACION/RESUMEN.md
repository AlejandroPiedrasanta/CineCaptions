# CineCaptions 5.3.2 — qué es y cómo está hecho (una página)

Programa de escritorio (Python 3.14 + PySide6/Qt; Windows y Mac) que **subtitula vídeos con IA local** y coloca los subtítulos ya diseñados (macros Luxe del pack de títulos) en el timeline de **DaVinci Resolve**. Todo corre sin internet salvo la licencia (Lemon Squeezy).

## Flujo (botón GO, o soltar un vídeo en Inicio)
1. **Audio**: lo trae Resolve por MCP (`resolve_mcp`), o un vídeo soltado (se le arma un timeline nuevo en el proyecto «CineCaptions»).
2. **Voz**: `motor_voz` (Qwen3-ASR en GPU, Windows) o Whisper (`subtitle_transcriber`; en Mac siempre Whisper). Si un motor falla se cambia solo al respaldo.
3. **IA de texto** (`ia_texto`): corrige, quita signos, elige palabras clave y emojis. Sin IA → motor de reglas.
4. **Bloques** según el pack elegido: *3 líneas* (arriba / PRINCIPAL / abajo; `dynamic_subtitles`) o *guion* = palabra a palabra (pack **Referencia**, solo vertical; `guion_planificador` + `guion_captions`).
5. **Sonido y emojis**: `sfx_rules` (un sonido por palabra, modo simple/avanzado), `emojis`, `emojis_sfx`.
6. **Manifiesto** `.json` en `~/DaVinciSubtitles/` → script de Resolve (`2_recursos/resolve_scripts/CineCaptions.py` Studio / `.lua` Free, gemelos) coloca los clips en pistas.

## Pantallas (todo en `CineCaptions (script principal).py`, clase `SubtitleApp`)
Inicio (GO + chips Estilo/Emojis/Efectos/Formato/Proyecto) · Estilos (packs, «Crea tu estilo», vistas reales) · Creativo (`WordTagWindow`: pintar roles, Asistencia, Generar) · Sonido (SFX Lab) · Ajustes · Registro. «Generar» del editor usa la misma receta que GO (`_receta_generar`).

## Quién decide qué (una sola fuente por ajuste)
Pack: pref `go_pack` ⇄ `plantilla_sel` (Estilos y chip de GO son lo mismo) · Efectos: pref `go_sfx` (+ `sfx_var`) · Emojis: pref `go_emojis` · Posición/estilo fijo: solo en packs de 3 líneas · Sonido: modo en `sfx_rules` (Simple/Avanzado) · Estilo de cada bloque: `estilos_bloque.asignar` (el usuario lo cambia en Creativo).

## Estructura del proyecto
`1_codigo/` programa · `2_recursos/` lo que viaja en el .exe (scripts de Resolve, packs, fuentes, sfx, locales) · `3_compilar/` armar el instalador · `4_diseno/` banner e icono · `5_licencias/` Administrador de Licencias (otro producto) · `6_compilacion/` temporal (se rehace) · `7_mac/` instalador Mac · `INSTALADORES/` Windows y Mac listos · `DOCUMENTACION/` esta carpeta.
Datos del usuario (fuera del programa): `~/DaVinciSubtitles/` (ajustes, marcas, proyectos, registro, caches).

## Reglas que no se rompen
Estado del usuario solo con `archivos_seguros` (nunca `write_text`) · nada de red/subprocess/`sleep` en el hilo de la interfaz (`correr_en_hilo`) · packs = solo macros reales Luxe (MediaOut, no Saver; subir `REVISION_BIN` al cambiar uno) · Amro solo como texto principal · no insertar efectos por nombre dudoso en un Resolve vivo · versión única en `version.py` (`sincronizar_version.py` la copia a los scripts).

## Cómo encontrar algo SIN leer archivos enteros
`mapa(consulta)` → temas con archivos y símbolos · `mapa(id=…)` → detalle · `simbolo(nombre)` → solo esa función · `modulo(nombre)` → qué es un archivo · `cambios(n)` → últimos cambios. (MCP `cinecaptions`; sin MCP: `6_compilacion/venv315/Scripts/python.exe 1_codigo/mapa_codigo.py mapa <palabras>`.)
