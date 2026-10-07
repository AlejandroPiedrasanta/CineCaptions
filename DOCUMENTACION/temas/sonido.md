# Sonido y emojis (SFX Lab, reglas, emojis)

## sfx-lab — Sonido / SFX Lab

**Qué:** Sonido / SFX Lab

**Dónde:** `sfx_studio.py`, `sfx_rules.py`, `sfx_editor.py`, `sfx_audio.py`

## ducking-energia — Estilo desde imagen, ducking y curva de energía

**Qué:** Estilo desde una imagen / ducking / curva de energía

**Dónde:** `estilo_desde_imagen.py`, `ducking.py`, `energia.py`

## sonido-palabra — Sonido por palabra (simple/avanzado)

**Qué:** Sonido por palabra (simple/avanzado)

**Dónde:** `sfx_rules.py` · `asignar_eventos_por_palabra`, `_eventos_avanzados`, `REGLAS_PREDEFINIDAS`

## sonido-emojis — Sonido de cada emoji

**Qué:** Sonido de cada emoji (fuego → fuego, beso → beso…)

**Dónde:** `emojis_sfx.py` · `familia_de`, `sonido_de`, `asignar`, `agregar_eventos`; audios `2_recursos/sfx_emoji/` (67 son grabaciones CC0/dominio público de `generador_sfx_emoji/reales/` + `FUENTES.json`, el resto sintetizado; `generar_sfx_emoji.py` los junta y escribe `LICENCIAS.txt`); el usuario puede sustituir una familia en `~/DaVinciSubtitles/sfx_emoji/` o cambiar el sonido emoji por emoji en SFX Lab > Reglas > **Emojis** (`emojis_sfx_ui.py` · `PanelEmojis`; pref `sfx_emoji_sonidos`)

## nota — SONIDO — UN SONIDO POR PALABRA

3) SONIDO — UN SONIDO POR PALABRA (modo Simple y Avanzado)
   Cada palabra hablada es un EVENTO {t, archivo}. sfx_rules.asignar_eventos_por_palabra:
     Simple   : sonido al inicio de CADA palabra, alternando 2 archivos; 1.ª palabra = riser
                (intro), última = boom (final).
     Avanzado : las reglas se evalúan PALABRA por palabra con su entorno (pausa antes/después,
                mayúsculas, cifra, ?, !, primera/última, rol main, bloque largo, cada N).
                Gana la PRIMERA regla que se cumple. TODAS vienen apagadas. Después se aplican
                los filtros: separación mínima, omitir inicio/final, no repetir categoría,
                máx. por minuto, probabilidad.
   El archivo de cada evento se recorta a 1,2 s (fade 120 ms) y lleva su volumen: Resolve no
   deja cambiar el volumen por script, así que va dentro de un WAV (~/DaVinciSubtitles/sfx_volumen).
   Cambios manuales (clic en el punto de la palabra) pisan todo ('' = sin sonido).
   COLOCACIÓN en Resolve: el sonido arranca en el MISMO fotograma en que entra la palabra.
   Si pisa a otro, se mueve a la pista siguiente (SFX, SFX 2, SFX 3... hasta 8): nunca se
   encima en una misma pista y no se desplaza el momento de entrada.
   Duración de audio: en Resolve 21 el clip de audio no da «Frames»; se usa «Duration».

## nota — ICONOS / EMOJIS

4) ICONOS / EMOJIS
   Una palabra con emoji -> clip del emoji (arriba o abajo según «Icono o imagen») en el instante de su bloque.
   Si el emoji tiene versión animada (Noto, Google) viaja como SECUENCIA de PNG (~/DaVinciSubtitles/emojis_secuencia,
   256 px, 30 fps, máx. 3 s; manifiesto: emojis_secuencias) y se importa como un clip que se mueve (en bucle si el bloque
   dura más). Cada clip lleva una comp de Fusion: ENTRADA con rebote (8 fotogramas) y SALIDA (6) para que no aparezca de golpe.

## nota — AUDITORÍA — FALLAS ENCONTRADAS Y ESTADO

5) AUDITORÍA — FALLAS ENCONTRADAS Y ESTADO
   [ARREGLADO] Modo Avanzado decidía por BLOQUE aunque el sonido es por palabra: ahora por palabra.
   [ARREGLADO] «Último bloque» venía ENCENDIDO por defecto y sonaba aunque el usuario no
               lo pidiera: ahora todas las reglas vienen apagadas; sin categoría por defecto
               no suena nada hasta que se enciende algo.
   [ARREGLADO] «Palabra suelta» sonaba en todas (cada palabra es "un bloque de 1"): ahora mira el bloque real.
   [ARREGLADO] El rol de la palabra se saca por POSICIÓN en el bloque, no por texto (palabras repetidas).
   [ARREGLADO] La vista previa de los packs nuevos dibuja las dos palabras con sus dos pesos (lee <pack>.variantes.json).
   [PENDIENTE] Packs de usuario creados desde .drt solo conservan el Text+ (no la comp animada).
   [IDEAS] palabras clave por pack (lista que dispara sonido + icono + animación),
           curva de energía (más sonidos en tramos rápidos), «ducking» de la música.

## nota — v5.5 — IDEAS NUEVAS

7) v5.5 — IDEAS NUEVAS
   Estilo desde una imagen (estilo_desde_imagen.py): de un fotograma saca acento, base, grosor de letra y arriba/abajo, y arma
     un pack de 3 variantes en tu carpeta de packs con el generador de packs Viral.
   Curva de energía (energia.py): palabras/segundo alrededor de cada palabra -> 0..1; en tramos calmados no suenan todas
     (siempre la principal, la primera y la última). Interruptor en Sonido (preferencia sfx_curva_energia).
   Música con ducking (ducking.py): copia de la música con -14 dB mientras hay voz (ataque 100 ms, relajación 550 ms),
     calculada de las palabras de la última transcripción; se pone en la pista MUSICA de Resolve.
   Ortografía incremental (ia_texto.correcciones_ortografia): se guarda la respuesta por trozo de ~40 palabras
     (~/DaVinciSubtitles/orto_cache.json); solo se corrige lo nuevo.

## nota — v5.7 · Sonidos de emojis

v5.7 · Sonidos de emojis: 1_codigo/emojis_sfx.py asigna a cada emoji (por palabras de su id: fire → fuego, kiss → beso, money → dinero…, y por grupo con variantes)
una de ~100 «familias»; los audios viven en 2_recursos/sfx_emoji/<familia>.wav (los fabrica 2_recursos/generador_sfx_emoji/generar_sfx_emoji.py por síntesis, sin
derechos; --hoja saca los espectrogramas para revisarlos). Un .wav/.mp3 con el mismo nombre en ~/DaVinciSubtitles/sfx_emoji/ manda sobre el del programa.
SubtitleApp._sfx_de_emojis suma un evento 'sfx_eventos' (categoría «Emojis») al bloque que lleva el emoji, en el instante en que sale su línea; los scripts de Resolve ya
colocan esos eventos (pistas SFX, SFX 2…). Interruptor: SFX Lab > «Sonidos de emojis» (pref sfx_emojis). Solo con los efectos activos.
Fix de animación: dynamic_subtitles.proteger_animaciones marca 'salto_anim' (s) en las LÍNEAS que se ven menos de ANIM_ENTRADA_S + MIN_VISIBLE_S (0,75 s); CineCaptions.py
y CineCaptions_Subtitulos.lua (gemelos) arrancan el comp esos segundos adelantado (solo con pack/plantillas). Las líneas con tiempo reproducen su entrada entera (regla v1.0.68).

## nota — v5.7 · Grabaciones reales de los emojis

v5.7 · Grabaciones reales de los emojis: 2_recursos/generador_sfx_emoji/reales/ guarda las grabaciones CC0 / dominio público elegidas (OpenGameArt, Kenney, Wikimedia Commons;
FUENTES.json dice de dónde sale cada una) y generar_sfx_emoji.py las usa en vez de la síntesis cuando existen (el resto sigue sintetizado). sfx_emoji/LICENCIAS.txt se genera solo.
Colores en la línea de tiempo (CineCaptions.py y CineCaptions_Subtitulos.lua): texto y sonidos = Orange, emojis (imagen) y su sonido = Yellow, sonido de introducción/final = Purple
(TimelineItem.SetClipColor; nunca falla: es solo para identificar).

## nota — v5.8 · Sonido emoji por emoji

v5.8 · Sonido emoji por emoji: SFX Lab > Reglas automáticas > pestaña «Emojis» (tercera opción junto a Simple y Avanzado; solo cambia la vista, no el modo de las reglas).
emojis_sfx_ui.PanelEmojis: rejilla de los ~1 400 emojis (un solo widget que pinta lo visible) + el sonido del elegido; se puede poner otra familia, el sonido elegido en la
biblioteca, un archivo propio, «sin sonido» o volver al original. Se guarda en la pref sfx_emoji_sonidos {id: familia | ruta | ''}; emojis_sfx.sonido_de decide qué suena
(un archivo propio que ya no existe cae al original) y agregar_eventos lo usa al generar (GO, Generar del editor y regeneraciones).
