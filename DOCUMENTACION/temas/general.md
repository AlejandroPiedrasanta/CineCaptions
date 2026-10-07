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
- `LEEME.txt` (raíz, ~30 KB): explicación humana por secciones 1-12; NO leer entero. `REGISTRO_DE_CAMBIOS.txt`: solo con `cambios(n)`; lo antiguo rota a `DOCUMENTACION/historial/`.
- `DOCUMENTACION/historial/`: auditorías y contexto viejos (solo con Grep).
- Al añadir un tema: sección en `temas/<grupo>.md` + entrada en `mapa.json` (id, grupo, claves, archivos, símbolos, resumen) y correr `mapa_codigo.py generar` (avisa de archivos/símbolos que ya no existen).
- Código: `simbolo(nombre)` devuelve solo esa función/clase (ast); `modulo(nombre)` qué hay en un archivo.
