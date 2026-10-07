# Datos del usuario, licencia y ajustes

## licencia — Licencia

**Qué:** Licencia

**Dónde:** `licencia.py`, `ventana_licencia.py`

- Lemon Squeezy (el mismo sistema que CineSlide); la licencia de ESTE equipo va firmada en `~/DaVinciSubtitles/licencia/licencia.dat`. Sin licencia no se abre. `CineCaptions.exe --licencia-liberar` libera la activación del equipo (lo usa el desinstalador con «Borrar mis datos»).

## archivos-seguros — Guardar JSON/estado del usuario

**Qué:** Guardar JSON/estado del usuario (preferencias, marcas, proyectos, manifiestos)

**Dónde:** `archivos_seguros.py` · `escribir_json`, `mezclar_json` (atómico + cerrojo). NUNCA `write_text` directo

## carpetas-del-usuario — Dónde vive el estado (fuera del programa)

Se conserva al actualizar; al desinstalar el usuario elige.
- `~/DaVinciSubtitles/`: `preferencias.json` (ajustes), `licencia/`, `<video>.marcas.json`, `<video>.<idioma>.dynamic.json|.guion.json|.srt` (+ `.lua`), `subtitles_manifest.json` (la última orden de colocar), `proyectos/`, `plantillas/` y `plantillas_cache/` (packs del usuario y vistas reales), `emojis*/`, `jobs/` (cola del Puente), `sfx_rules.json`, `cinecaptions.log` y `errores.log`, `reporte_soporte.txt`, `instalador/` (logs de instalación), `banco/` (pruebas).
- `%LOCALAPPDATA%\Programs\CineCaptions\` el programa instalado · `%LOCALAPPDATA%\CineCaptions\motor_qwen\` el motor de voz e IA · `~/.cache/huggingface/` modelos · `Documentos\CineCaptions\Copias de seguridad\` (`copias.py`) · `~/.cinecaptions.lock` (instancia única).
