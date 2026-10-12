# Voz e IA de texto

## voz-ia — Voz e IA de texto

**Qué:** cómo se transcribe y cómo se corrige/elige con IA, con respaldos automáticos.

**Dónde:** `subtitle_transcriber.py` (`transcribe`: elige motor y respaldo), `motor_voz.py` (Qwen3-ASR en su propio Python 3.12, `%LOCALAPPDATA%\CineCaptions\motor_qwen`; servidor residente `_ServidorVoz`, `pedir(sin_senal)`, `abortar`, `_FALLOS`), `ia_texto.py` (Qwen3 de texto: `marcar_todo` = corregir + roles + emojis + sin signos; `analizar` con respaldo 4B→1.7B). `compat_av.py` (v5.4.44): PyAV 19 quitó `av.open(metadata_errors=…)` y faster-whisper 1.2.1 aún lo pasa (sin el puente NINGUNA transcripción funciona); `compat_av.aplicar()` va antes de cada uso de faster_whisper. Python 3.15: sin ruedas de ctranslate2 ni onnxruntime todavía (2026-10-11).

- **Orden de motores (voz):** Qwen3-ASR (solo Windows, GPU; modelo 1.7B, o 0.6B si hay poca VRAM) → misma pasada suelta con 0.6B → 0.6B en CPU → Whisper `large-v3-turbo` (CUDA si ve la GPU; si falla, CPU; si falta RAM, `small`/`base`). En Mac siempre Whisper en CPU. Dos fallos seguidos de Qwen3 = Whisper directo hasta reiniciar el programa (`motor_voz.motor_para`).
- **IA de texto:** modelo 4B (≥9,5 GB de VRAM) o 1.7B; si falla, 1.7B; si vuelve a fallar, motor de reglas (`sugerencias_ia`); dos fallos seguidos desactivan la IA hasta reiniciar.
- **Colgado:** el servidor de voz/IA que pasa 300 s / 240 s sin ninguna línea se mata y se pasa al respaldo; el vigía de `vigilancia.py` también los cierra (`motor_voz.abortar`, `ia_texto.abortar`). Todo queda en el Registro (`errores.log`).
- **Preferencia** `motor_voz` = `qwen3` (por defecto) o `whisper` (Ajustes > General). Modelos descargados en `~/.cache/huggingface/hub` (Whisper turbo, Qwen3-ASR, ForcedAligner, Qwen3-4B/1.7B).
- Los tiempos por palabra de Qwen3 salen de su alineador (idiomas alineables: zh en yue fr de it ja ko pt ru es); fuera de esa lista se usa Whisper.

## texto-ayudas — Ortografía, sugerencias, salud, medir texto

- `ortografia.py`: revisión del editor (marca y propone, nunca corrige solo). `sugerencias_ia.py`: palabra PRINCIPAL de cada bloque con el motor clásico (sin IA instalada).
- `salud.py`: chequeo de librerías al arrancar (versiones fijadas, motor de IA, MCP). `medir_texto.py`: cuánto ocupa cada palabra en pantalla (look «pintado»).
