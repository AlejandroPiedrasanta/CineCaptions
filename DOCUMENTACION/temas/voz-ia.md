# Voz e IA de texto

## voz-ia — Voz e IA de texto

**Qué:** cómo se transcribe y cómo se corrige/elige con IA, con respaldos automáticos.

**Dónde:** `subtitle_transcriber.py` (`transcribe`: elige motor y respaldo), `motor_voz.py` (Qwen3-ASR en su propio Python 3.12, `%LOCALAPPDATA%\CineCaptions\motor_qwen`; servidor residente `_ServidorVoz`, `pedir(sin_senal)`, `abortar`, `_FALLOS`), `ia_texto.py` (Qwen3 de texto: `marcar_todo` = corregir + roles + emojis + sin signos; `analizar` con respaldo 4B→1.7B). `compat_av.py` (v5.4.44): PyAV 19 quitó `av.open(metadata_errors=…)` y faster-whisper 1.2.1 aún lo pasa (sin el puente NINGUNA transcripción funciona); `compat_av.aplicar()` va antes de cada uso de faster_whisper. Python 3.15: sin ruedas de ctranslate2 ni onnxruntime todavía (2026-10-11).

- **Orden de motores (voz):** Qwen3-ASR (solo Windows, GPU; modelo 1.7B, o 0.6B si hay poca VRAM) → misma pasada suelta con 0.6B → 0.6B en CPU → Whisper `large-v3-turbo` (CUDA si ve la GPU; si falla, CPU; si falta RAM, `small`/`base`). En Mac siempre Whisper en CPU. Dos fallos seguidos de Qwen3 = Whisper directo hasta reiniciar el programa (`motor_voz.motor_para`).
- **IA de texto:** modelo 4B (≥9,5 GB de VRAM) o 1.7B; si falla, 1.7B; si vuelve a fallar, motor de reglas (`sugerencias_ia`); dos fallos seguidos desactivan la IA hasta reiniciar.
- **La GPU se comparte con Resolve (v5.5.4).** Antes, `modo_gpu` y `modelo_texto` miraban la VRAM TOTAL. Con 16 GB eso daba «solapado»: la voz y la IA 4B cargadas a la vez mientras Resolve usaba 8–10 GB.
  - Medido en un GO real: la IA tardaba más de 100 s y fallaba siempre (los motions de los Temas 1–4 iban solo con reglas), Resolve reproducía a tirones y en un GO se cerró colocando la Magic Mask.
  - Ahora se decide con `motor_voz.vram_para_ia_gb()`: VRAM libre real (`nvidia-smi`, memorizada 5 s) + la que ya ocupan nuestros motores − 7 GB de reserva si Resolve aún no está abierto. Con eso, `modo_gpu` (solapado ≥ 16, residente ≥ 22) y `modelo_texto` (4B solo con ≥ 10,5 GB).
  - Llaman a `nvidia-smi`/`tasklist`: nunca desde la interfaz (`_precargar_al_abrir` decide en su hilo).
  - Las IA se sueltan (`edicion_pro.soltar_gpu`): al terminar `edicion_pro.planificar`, al empezar `aplicar` (el Tema 5 suelta la de texto él), antes de reproducir al final de GO y con «Refrescar» en Inicio.
- **Colgado:** el servidor de voz/IA que pasa 300 s / 240 s sin ninguna línea se mata y se pasa al respaldo; el vigía de `vigilancia.py` también los cierra (`motor_voz.abortar`, `ia_texto.abortar`). Todo queda en el Registro (`errores.log`).
- **Preferencia** `motor_voz` = `qwen3` (por defecto) o `whisper` (Ajustes > General). Modelos descargados en `~/.cache/huggingface/hub` (Whisper turbo, Qwen3-ASR, ForcedAligner, Qwen3-4B/1.7B).
- Los tiempos por palabra de Qwen3 salen de su alineador (idiomas alineables: zh en yue fr de it ja ko pt ru es); fuera de esa lista se usa Whisper.

## texto-ayudas — Ortografía, sugerencias, salud, medir texto

- `ortografia.py`: revisión del editor (marca y propone, nunca corrige solo). `sugerencias_ia.py`: palabra PRINCIPAL de cada bloque con el motor clásico (sin IA instalada).
- `salud.py`: chequeo de librerías al arrancar (versiones fijadas, motor de IA, MCP). `medir_texto.py`: cuánto ocupa cada palabra en pantalla (look «pintado»).

## ortografia-temas — Ortografía para los 6 temas: diccionario de lemas, GO y la PRO con el texto corregido (v5.5.7)

**El fallo:** el diccionario de pyspellchecker 0.9.1 (es) trae casi solo LEMAS: no tiene «voy», «hay», «estoy», «tiene», «dijo», «quiero»,
«hablando», los plurales ni los pronombres pegados («enseñarte»). La revisión de Creativo los subrayaba y la corrección automática los CAMBIABA
(«hay» → «ahí», «Voy» → «Boy»). **Arreglo:** `ortografia_es.conocida` (formas irregulares comunes, conjugación regular y con cambio de raíz de los
infinitivos del diccionario, futuro/condicional, plural/femenino/diminutivo/-mente, hasta dos pronombres pegados, tilde de más) filtra
`ortografia.revisar`; `corregir_fonetico` exige frecuencia ≥ 8000, busca también por clave fonética (`_por_clave`: «aser» → «hacer») y aplica
`ortografia_es.ERRATAS` (inequívocas: «kiero», «nesecito», «ubo», «esque», «osea», «despues»…).

**GO:** `ia_texto.marcar_todo` añade la pasada de diccionario + fonética de Asistencia (antes, sin IA, GO no corregía nada). **La PRO** (Temas 5 y 6,
titulares, rótulos, listas) recibía el texto CRUDO: ahora `_run_pipeline` guarda `texto_corregido(words, palabras_finales)` (las palabras con sus signos
y el texto corregido por IA, diccionario o Creativo; casadas por posición o por tiempo) y `_planificar_pro` lo usa. Kinetic, Referencia, VIRAL y
Tema 4 ya usaban `palabras_finales`.
