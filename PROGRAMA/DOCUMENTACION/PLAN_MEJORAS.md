# Plan de mejoras elegidas (2026-10-08)

Lista elegida por el usuario sobre las 7 × 30 ideas. Se hacen por lotes, cada uno probado sin pantalla y, si toca Resolve, con `probar_efectos.py` / `probar_go.py`. **No se compila ni publica sin que el usuario lo pida.**
Marca: `[ ]` pendiente · `[x]` hecho · `[~]` hecho a medias (nota).

## Lote A — Rendimiento y robustez (base de todo lo demás)
- [x] R20 Resolve colgado no debe congelar la app: `resolve_bridge.resolve_colgado()` (IsHungAppWindow + vigía de 3 s); `conectar()` ni llama a fusionscript y `resolve_mcp.script()` avisa al instante tras 25 s colgado (probado con una ventana bloqueada)
- [x] R21 Espera creciente al arrancar ResolveMCP (10→20→40→60 s) y reciclaje del cliente tras 2 «no contestó» seguidos si Resolve NO está colgado
- [x] R22 `cola_trabajos.py`: lo de fondo (máx. 2 a la vez) cede ante GO; `correr_en_hilo(..., baja=True)`
- [x] R3  `cache_voz.py` (huella = tamaño+fecha+2 MB inicio/fin+idioma+motor+modelo; 90 días / 200 MB)
- [x] R4  `cuda_libs.tipo_de_calculo()`: float16 ≥ 6 GB, int8_float16 3-6 GB, CPU < 3 GB
- [x] R5  Fila «GPU para la voz (CUDA)» en `salud.comprobar()`; además `register_cuda_dlls()` ahora registra las DLL del motor Qwen (arregló el fallo real: Whisper GPU 6,7 s vs CPU 17,5 s)
- [x] R6  Ajustes › General › «Reparar GPU» (reutiliza las del motor Qwen; si no, descarga cuBLAS+cuDNN de PyPI ≈1,3 GB)
- [x] R17 `descargas.py` (Range + reintentos 2/4/8/16 s + SHA-256; probado con un servidor que corta a mitad); `motor_voz._bajar` la usa
- [x] R8  Caché de fuentes se guarda cada 120 archivos y la interfaz no espera al índice (`indice_listo`, «Comprobando tipografías…»)
- [x] R9  `mantenimiento.py` (topes por caché, a los 45 s de abrir) + «Espacio de las cachés / Limpiar ahora» en Ajustes
- [x] R13 `efectos_visuales.precalentar_secuencias()` arranca con GO (mientras se transcribe)
- [~] R27 Medido: NVDEC/D3D11 es MÁS LENTO que el software con 4 hilos (4K: 98 fps CPU vs 79 GPU; 720p: 350 vs 200). Se queda en software; hilo paralelo a la voz ya existe

## Lote B — Inicio
- [x] I4 Tiempo estimado calibrado: el ritmo aprendido se guarda por perfil del equipo (`go_ritmo_perfiles`, p. ej. whisper-gpu / qwen3-cpu) y suma el coste de los efectos visuales
- [x] I6 Pausar/cancelar GO: botones «Pausar»/«Cancelar» en el panel (puntos de control en el hilo; cancelar estando en pausa también sale) — probado sin pantalla
- [x] I7 Reanudar un GO interrumpido: `go_en_curso.json`; al abrir (1,8 s) el orbe ofrece «pulsa GO para reanudarlo» y la voz sale de la caché — probado
- [x] I9 Idioma detectado: chip «Idioma: …» en Inicio (con «automático» dice el idioma oído); cambiarlo tras un GO deja el video listo para repetirlo
- [x] I18 `avisos_sistema.py`: notificación del sistema al terminar/fallar GO si la ventana no está al frente (Ajustes › General › «Avisarme al terminar»)
- [x] I28 `novedades_visuales.py`: tira de clips en bucle (los mp4 de vista previa ya incluidos) en el cuadro de «Novedades»; `CLIPS_POR_VERSION` dice cuáles

## Lote C — Efectos (motor)
- [x] E27 Intensidad global (suave/normal/fuerte: mueve zoom, temblor, cuántos cortes e iconos y la fuerza del ambiente)
- [x] E5 Zoom lento continuo · [x] E4 Temblor con los golpes de sonido (SFX hit/slam/impact/bass; sin ellos, el arranque de las frases clave) · [x] E21 Fondo desenfocado cuando el clip no tiene la forma del timeline — todo en una comp de Fusion sobre V1 (`fusion_v1.py`; antes del color, sin duplicar el video)
- [x] E2 Más transiciones: zoom desenfocado, barrido (whip pan) y glitch RGB (en la misma comp; probado en Resolve con render)
- [x] E15 Quitar pausas (`pausas.py`: recorta V1/A1 del timeline de GO, las palabras pasan a los tiempos nuevos; deja las pausas muy largas por ser tomas de apoyo) + zoom alterno en cada corte seco
- [x] E1 Efectos propios (MOV/MP4 tal cual, PNG/GIF/WebP animado/APNG → secuencia; intro/cortes/todo el video/palabras; Screen/Multiply/Normal) · [~] E9 animados: GIF/WebP/APNG sí; Lottie JSON no (exportar a WebP/GIF/MOV con alfa)
- [x] E13 Números 1-2-3 · [x] E8 Pegatinas (emojis con borde, 270 del catálogo) · [x] E7 Iconos/pegatinas por palabra concreta (palabras propias del usuario) · [x] E11 Subrayado y círculo a mano (altura elegible: la posición del texto depende del pack)
- [x] E20 Overlays continuos (polvo, grano, luz suave) · [x] E23 Logo animado · [x] E24 Pantalla final · [x] E26 Cierre con sonido
- [x] E30 No tapar la franja de los captions · [~] E6 Cara: estimación sin modelos por color de piel (devuelve nada si no es concluyente; no hay detector de caras instalado y no se descargó ninguno)
- [x] E28 Vista previa de 3 s (clips reales; zoom/temblor/transiciones de Fusion aproximados)
- [~] E17 B-roll de Pexels (`broll.py`): probado de punta a punta con un servidor falso (la toma cae en `FX-BROLL`, DEBAJO de los captions); NO probado con una clave real de Pexels

## Lote D — Sonido (parcial: se publicó en la 5.4.8 lo de abajo marcado [x])
- [x] S1 Normalizar los SFX + ducking más fino · [x] S2 Música de fondo automática (ducking según la voz) · [x] S4 BPM (pulso alineado con el golpe del gancho y efectos al pulso)
- [x] S15 Sonido de emoji por contexto · [x] S16 Sonidos de los cortes · [x] S17 Riser antes de la palabra clave · [x] S18 Golpe + hueco de 0,2 s
- [ ] S7 Limpieza de voz · [ ] S9 Reglas por palabra más potentes · [ ] S13 Duplicados al importar

## Lote E — Creativo
- [ ] C1 Reproductor con palabra activa · [ ] C2 Teclas de rol · [ ] C3 Multiselección · [ ] C6 Deshacer/rehacer + comparar con la IA · [ ] C7 Ortografía en línea
- [ ] C11 Ajustar tiempos sobre la onda · [ ] C14 Estilo por emoción · [ ] C16 «Poner efecto aquí» · [ ] C26 Vista fiel de Resolve con caché

## Lote F — Proyecto
- [ ] P4 Duplicar un pack · [ ] P5 Exportar/importar pack · [ ] P8 Descargar fuentes que falten · [ ] P15 Zonas seguras · [ ] P22 Plantillas nombre/CTA · [ ] P28 Importar SRT/VTT

## Lote G — Conexiones
- [ ] K6 Asistente de conexión con Resolve · [ ] K7 Reconexión automática · [ ] K8 API local / línea de comandos · [ ] K19 Traducción opcional DeepL/LLM
- [ ] K5 Resolve gratuito (Lua) con efectos visuales · [ ] K1 Exportar a Premiere (XML) y After Effects

## Notas
- E17 y K19 necesitan una clave de API del usuario (Pexels/Pixabay; DeepL). K1 y K5 son los más grandes: van al final.
