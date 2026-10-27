# Datos del usuario, licencia y ajustes

## licencia — Licencia

**Qué:** Licencia

**Dónde:** `licencia.py`, `ventana_licencia.py`

- v5.52: solo claves `CC-XXXX-XXXX-XXXX-XXXX` de cinecaptions.shop (se pagan con Recurrente; regex `_RX_CC`, sin distinguir mayúsculas ni espacios). Gumroad, Hotmart y Lemon Squeezy se quitaron (pedido de la dueña): sus licencias guardadas ya no valen. El botón de compra va a `LIC_URL_COMPRA` (`https://cinecaptions.shop/#precio`).
- Servidor `LIC_API` = `POST https://cinecaptions.shop/pagos/licencia.php` (form: `accion`=activar|verificar|desactivar, `clave`, `equipo`=`id_equipo()`, `nombre_equipo`); el código está en la carpeta WEB (`pagos/licencia.php`). `codigo` → motivo en `_motivo()`: `activa` · `invalida` (404) · `bloqueada` (403, reembolso/contracargo) · `en_uso` (409, límite de 2 equipos) · `desactivada` (este equipo ya no está). 5xx, 429 o sin red = `SinConexion`: vale `LIC_DIAS_SIN_INTERNET` (7) días desde la última verificación. `desactivar()` libera el equipo en el servidor al momento; sin internet NO quita la licencia (el equipo seguiría ocupado).
- La licencia de ESTE equipo va firmada en `~/DaVinciSubtitles/licencia/licencia.dat` (`plataforma: 'cinecaptions'`). Sin licencia no se abre. `CineCaptions.exe --licencia-liberar` libera la activación del equipo (lo usa el desinstalador con «Borrar mis datos»).
- Límite conocido: el HMAC de `licencia.dat` usa `_SAL` + ID del equipo, ambos dentro del programa; quien tenga el código puede fabricarlo (por eso el espejo de Mac pasó a privado). La cura de fondo sería una firma del servidor (clave privada fuera del programa).

## archivos-seguros — Guardar JSON/estado del usuario

**Qué:** Guardar JSON/estado del usuario (preferencias, marcas, proyectos, manifiestos)

**Dónde:** `archivos_seguros.py` · `escribir_json`, `mezclar_json` (atómico + cerrojo). NUNCA `write_text` directo

## carpetas-del-usuario — Dónde vive el estado (fuera del programa)

Se conserva al actualizar; al desinstalar el usuario elige.
- `~/DaVinciSubtitles/`: `preferencias.json` (ajustes), `licencia/`, `<video>.marcas.json`, `<video>.<idioma>.dynamic.json|.guion.json|.srt` (+ `.lua`), `subtitles_manifest.json` (la última orden de colocar), `proyectos/`, `plantillas/` y `plantillas_cache/` (packs del usuario y vistas reales), `emojis*/`, `jobs/` (cola del Puente), `sfx_rules.json`, `cinecaptions.log` y `errores.log`, `reporte_soporte.txt`, `instalador/` (logs de instalación), `banco/` (pruebas).
- `%LOCALAPPDATA%\Programs\CineCaptions\` el programa instalado · `%LOCALAPPDATA%\CineCaptions\motor_qwen\` el motor de voz e IA · `%LOCALAPPDATA%\CineCaptions\audio\` (Mac: `~/Library/Application Support/CineCaptions/audio/`) los audios que renderiza «Detectar video» (v5.4.45; antes `Descargas\CineCaptions Audio`, a la vista: `_podar_renders_viejos` vacía y quita esa carpeta vieja; los desinstaladores borran la nueva) · `~/.cache/huggingface/` modelos · `Documentos\CineCaptions\Copias de seguridad\` (`copias.py`) (v5.22: su fila de Ajustes se quitó a petición del usuario; `copias.py` queda sin uso) · `~/.cinecaptions.lock` (instancia única).

## proyectos-usuario — Registro de proyectos (vídeos) trabajados

`proyectos.py`: lista de vídeos trabajados (recientes, abrir, borrar). Su estado se guarda con `archivos_seguros`.
