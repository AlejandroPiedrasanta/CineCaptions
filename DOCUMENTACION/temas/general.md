# Visión general del programa

## nota — FLUJO

1) FLUJO
   Audio (Obtener por MCP) -> transcripción (Qwen3-ASR/Whisper) -> palabras con tiempo
   -> ortografía/IA marca ROLES por palabra -> grupos de 3 líneas (arriba/principal/abajo)
   -> manifiesto .json (bloques + estilos + sfx + emojis + composición)
   -> script de Resolve (CineCaptions.py / .lua) coloca clips de títulos y audios.

## nota — ARCHIVOS CLAVE

6) ARCHIVOS CLAVE
   Mapa de código: CLAUDE.md.  Guía de packs: 4_diseno/packs_nuevos/.  Old: 4_diseno/packs_anteriores/.

## documentacion — Cómo está ordenada la documentación (y cómo consultarla)

- `DOCUMENTACION/RESUMEN.md`: una página, qué hace el programa. Léela primero si no sabes nada.
- `DOCUMENTACION/mapa.json` + `temas/<grupo>.md`: un tema por sección (`## id — título`; las `## nota — …` son lógica histórica). `mapa(consulta)` busca; `mapa(id=…)` da el detalle.
- `CLAUDE.md` (raíz): reglas + el mapa compacto de temas (lo reescribe `mapa_codigo.py generar` desde `mapa.json`, entre las marcas MAPA).
- `DOCUMENTACION/LEEME.txt` (~34 KB): explicación humana por secciones 1-12; NO leer entero. `DOCUMENTACION/REGISTRO_DE_CAMBIOS.txt`: solo con `cambios(n)`; lo antiguo rota a `DOCUMENTACION/historial/`.
- `DOCUMENTACION/historial/`: auditorías y contexto viejos (solo con Grep).
- Al añadir un tema: sección en `temas/<grupo>.md` + entrada en `mapa.json` (id, grupo, claves, archivos, símbolos, resumen) y correr `mapa_codigo.py generar` (avisa de archivos/símbolos que ya no existen).
- Código: `simbolo(nombre)` devuelve solo esa función/clase (ast); `modulo(nombre)` qué hay en un archivo.
- Llamadas: `llamadas(nombre)` dice quién la usa, con la línea de cada llamada; con `sentido="sale"`, a qué llama ella; con `niveles=3`, la cadena entera (lo que se puede romper al cambiarla). `ruta(A, B)` da la cadena más corta de A a B. Es un grafo de `.py` (ast) y `.lua` (regex), sin dependencias; se rehace solo con los archivos que cambian (~5 s la primera vez, 0,2 s después). Cuenta como uso pasar la función sin llamarla (connect, hilos, tablas): sale como «(callback)». `obj.metodo()` sin saber qué es `obj` se une por el nombre solo si hay ≤3 candidatos (prefiere los módulos que importa el archivo) y sale con «?». No ve señales Qt por nombre, `getattr` ni lo que pasa entre procesos o de Python a Lua. La idea viene de Graphify: se copió en lugar de instalarlo porque el mapa por temas ya existía y así no hay dependencias ni avisos que gasten tokens.

## acoplamientos — Si cambias X, cambia también Y (acoplamientos)

Antes de dar un cambio por terminado, repasa esta tabla (cada fila costó un fallo real).

| Si cambias… | Cambia / revisa también… |
|---|---|
| `CineCaptions_Subtitulos.lua` (Free) | su gemelo `CineCaptions.py` (Studio) y al revés; el Lua NO tiene `io`: lo que necesite de disco lo escribe la app (sidecars, `emoji_comps`) |
| un pack `.drb` o una macro Luxe | `plantillas.REVISION_BIN['<Pack>']` +1; solo macros Luxe reales (`MediaOut`, no `Saver`); Amro solo como principal; probar con `.drb`, nunca `InsertFusionTitleIntoTimeline` con nombres dudosos |
| una librería de `3_compilar/requirements.txt` | su versión fijada en `salud.LIBRERIAS` (el chequeo de cada arranque): si no, avisa «X con problemas» aunque esté bien (pasó con Pillow 13, v5.5.10). Y `3_compilar/requirements.txt` es la fuente: el venv `6_compilacion/venv315` se instala de ahí |
| la versión | SOLO `1_codigo/version.py`; `3_compilar/sincronizar_version.py` la copia a los scripts; las novedades van en `ajustes_ui.NOTAS_VERSION`. Compilar/publicar solo si el usuario lo pide |
| el orden de colocación en Resolve | emojis ANTES que sonidos (`place_guion` / `place_guion_track`); al revés Resolve Free se cae (tema `emojis-posicion-free`) |
| `CineCaptions_ArmarVideo.lua` | las `pausa(…)` tras `CreateEmptyTimeline` y cada `SetSetting` NO se acortan: son la cura del cuelgue de Resolve (tema `resolve-colgado`) |
| `CineCaptions_Puente.lua` | su versión (se anuncia UNA vez en el log de Resolve), `resolve_bridge` (relevo de un Puente viejo) e `instalador_scripts` (copias del menú) |
| el nombre de un script de Resolve | `instalador_scripts.NOMBRES_VIEJOS` (para que el menú no quede duplicado) |
| algo que guarda el usuario (prefs, marcas, proyectos) | solo `archivos_seguros.escribir_json/mezclar_json`; nunca `write_text` |
| texto visible de la interfaz | envolverlo en `tr("…")` (catálogos en `2_recursos/locales`) |
| código de la app en `1_codigo/*.py` | cambia la huella del instalador: la siguiente `Actualizar_Windows.ps1` subirá la versión. Las herramientas de desarrollo van en `1_codigo/herramientas_dev/` (no entran en la huella). Edita esos archivos con Edit o Python `newline=''`, NUNCA con `sed -i` (quita los CRLF y la huella dice «desactualizado») |
| un tema, un módulo o un símbolo | sección en `temas/<grupo>.md` + entrada en `mapa.json`; `python 1_codigo/mapa_codigo.py generar` reescribe el mapa de CLAUDE.md y AVISA de código sin tema, archivos o símbolos que ya no existen |
| cualquier mejora del programa | `python 3_compilar/documentar.py --nota "…"` (el porqué) y, si el usuario pide instalador: `Actualizar_Windows.ps1` y `Actualizar_Mac.ps1` |

Comprobar el mapa: `python 1_codigo/mapa_codigo.py sin_tema` (código que ningún tema nombra) y `… generar` (avisos). Publicar: `Publicar_Version.ps1`; su error «el manifiesto publicado dice X» justo después de subir es la caché de GitHub: verificar con `gh release view`.
