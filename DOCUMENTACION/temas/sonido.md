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

## sonido-extra — Sonido extra de GO (v5.4.8)

**Qué:** (tarjeta «Sonido extra» de Efectos › Más efectos) **Música de fondo automática** (`musica_go`: archivo o carpeta, volumen, alinear al pulso): `musica_go.elegir` (de una carpeta, una de 85-130 BPM, la misma para el mismo video), `bpm.detectar` (autocorrelación de la novedad espectral con los graves reforzados; ±0,3 BPM y fase al ~0,05 s en pruebas) y `musica_go.preparar` hornea un WAV 48 kHz: bucle con cruce, nivel de fondo (−23 dB RMS con puerta), `ducking.curva_fina` (baja más cuanto más rápido se habla, sube deprisa en pausas largas, casi muda en el hueco del gancho) y fundidos. **Gancho** (`sonidos_extra`, `fx_sonido_gancho`): `palabra_del_gancho` (mejor frase por `puntuar_frase` entre 2,6 y 14 s), riser (últimos 1,6 s con contenido de la categoría Riser) que acaba 0,2 s antes de la palabra, hueco de 0,2 s en la música y golpe (Hit) en la palabra; el pulso de la música se desplaza (`bpm.desplazamiento_para`) para que un golpe de pulso caiga en la palabra. **Cortes** (`fx_sonido_cortes`): Whoosh/Glitch/Power Up según la transición (`SONIDO_CORTE`), 0,10 s antes del corte, y un Click en cada corte seco del «quitar pausas». Con música y «alinear», las entradas de iconos, números, pegatinas y énfasis se acercan al golpe de pulso a menos de 0,15 s. **Normalizar** (`sfx_normalizar`, `sfx_objetivo_db` −20): `sfx_rules.ganancia_de_normalizado_db` mide cada sonido una vez (RMS con puerta, pico ≤ −1 dBFS, ±9/−12 dB; `sfx_niveles.json`) y `con_volumen` lo aplica antes del volumen del usuario. **Emojis por contexto** (`sfx_emoji_contexto`): `sentimiento.valencia` (listas es/en/pt/fr/de/it con negaciones) cambia un sonido GENÉRICO (pop, tick, ding, swish) por `acierto` o `error`; los sonidos propios de cada emoji y los que eligió el usuario no cambian.

**Colocación:** `colocar_efectos._poner_audio` reparte los sonidos en pistas `FX-SONIDO`, `FX-SONIDO 2`… sin pisarse y la música en `FX-MUSICA`; sin efectos visuales el plan lleva `solo_audio` (las pistas visuales no se tocan). El audio extra se planifica en `_planificar_efectos` aunque «Visuales» esté apagado.

**Pendiente (Lote D):** limpieza de voz (S7), reglas por palabra con listas por idioma, prioridad y regex (S9), duplicados al importar sonidos (S13) y su tarjeta en la página Sonido.


## sonido-estilo — Sonido por estilo (v5.4.13, sin compilar)

**Qué:** el sonido deja de ser «un toque por palabra a todo». `sfx_rules.cargar_modo()` ahora trae `donde` = `todas` | `principal` | `ninguna` (SFX Lab › Simple: selector «Sonido por palabra»; la introducción y el final siguen) y el modo simple alterna **3** sonidos (`CUANTOS_SIMPLES['inicio'] = 3`: TAP_POP, typewriter e Iphone Taping). Con `principal`, el sonido cae en la palabra principal de cada bloque: `CineCaptions (script principal).py › _instantes_main(bloques, cues)` saca [(instante, clip del efecto)] y `sfx_rules._instantes_principales` los casa con las palabras habladas (≤ 0,35 s); el sonido PROPIO de cada efecto sale de `recomendaciones.SONIDO_POR_CLAVE` (v shatter → Slices, v select → Click, v drag → Whoosh, k hero → Hit; la principal sin efecto usa los 3 toques).

**Pico en la palabra:** muchos sonidos de la biblioteca tienen su pico tarde (Whoosh 1: 0,9 s; Slices 3: 0,9 s; Hit 4: 0,5 s) y se colocaban con el PRINCIPIO del archivo en la palabra → el golpe llegaba tarde. `sfx_rules.adelanto_natural` mide el pico (ventana de 10 ms) y `con_volumen(..., alinear=True)` deja un WAV que empieza `adelanto` s antes (máx. 0,40 s; el nombre acaba en `_a<ms>.wav`); `adelanto_de` lo lee y el evento se pone ese tiempo antes (`t_dueno` = la hora de la palabra, para elegir bloque). No se alinean: lo que el usuario eligió a mano, el riser de introducción y el boom del final. Los recortes de fábrica (`RECORTES_DE_FABRICA`: TAP_POP, typewriter) ya no dependen de que el usuario los haya hecho en su instalación.

**Riser:** `efectos_visuales.preparar_riser(ruta, antes_s=2.0)` = los últimos 2 s que ACABAN en el pico del archivo (el Viral Hooks Riser sube y se corta en el golpe), normalizado a −5 dBFS de pico (el original está a −17 dBFS). El destello de la intro cae EN ese pico y el zoom de intro también (`fusion_v1.texto_comp(zoom_intro=…)`). El gancho (`sonidos_extra.sonidos_del_gancho`) pone el pico del riser EN la palabra clave, y espera a que acabe el de la intro. Si Efectos ya pone riser en la intro, el modo simple no pone otro. **Transiciones:** `fx_sonido_corte` (auto | shutter | whoosh | …); «destello» → categoría Shutter (Shuter 11 y 13: el clic cae en el corte, `_clic_de`).

**Recomendación por estilo:** `recomendaciones.py` (VIRAL/Kinetic → solo principal; Referencia → cada palabra) se aplica al ELEGIR el estilo (`_poner_go_pack` y `_sincronizar_go_pack` → `_aplicar_recomendacion`, aviso con ui_toast; pref `recomendar_estilo` = False la apaga). Escribe `fx_*` y `donde`; no toca quitar pausas, música, B-roll, cierre, overlays ni intensidad.

**Emojis y toques:** el sonido del emoji sustituye al toque de la palabra que cae a ≤ 0,15 s (`emojis_sfx._quitar_toque_de_palabra`).

**Probar:** `python 1_codigo/probar_estilos_app.py <palabras.json> --pack VIRAL|Kinetic|Referencia [--donde principal] [--detalle]` (sin pantalla y sin Resolve): cuántos sonidos por minuto, qué archivos, emojis, estilos usados. Con el modo por defecto había ~111 sonidos/min (94 % de las palabras); «solo principal» deja ~24/min.

## emojis-estilos — Estilos de emoji (v5.4.13, sin compilar)

**Qué:** pref `emoji_estilo` = `animado` (por defecto: los Noto Animated cuando existen y, si no, 3D), `fluent3d` (3D fijo, Microsoft, MIT), `noto` (Google, CC BY 4.0) o `sistema` (la fuente del equipo, planos). `emojis.estilo()` lo guarda en memoria, `emojis_sets.py` baja cada PNG (256 px) la primera vez que se usa a `~/DaVinciSubtitles/emojis_sets/<set>/<id>.png`: Fluent desde jsDelivr/GitHub (`2_recursos/emojis/fluent_mapa.json` = id → ruta; 1 354 de 1 390 tienen 3D; se regenera con `2_recursos/emojis/construir_mapa_fluent.py`, una petición a la API de GitHub) y Noto desde fonts.gstatic.com. Sin internet o sin versión, sale el Fluent que trae el programa o el del sistema. El selector (EmojiPickerWindow) tiene el selector «Animado · 3D · Google · Sistema» y «⬇ Bajar todos» (~40 MB, con progreso y «Parar»). `copia_para_resolve` baja el emoji AL MOMENTO si falta (GO corre en su hilo). Las secuencias animadas sólo viajan con el estilo `animado` (`emojis.animados_activo()`).

**Por qué no LottieFiles:** bajar de allí exige una cuenta y su licencia no permite redistribuir las animaciones dentro de otra aplicación; Microsoft Teams Animated (Tarikul-Islam-Anik) es «all rights reserved». Con licencias abiertas hay Fluent 3D (MIT) y Noto (animado y fijo, CC BY 4.0). Un Lottie/GIF/WebP propio sigue entrando como «Mi PNG…» / archivos en `~/DaVinciSubtitles/emojis`.

**v5.4.29 — pantalla Sonido más simple (pedido del usuario):** `sfx_studio._pintar_reglas` solo ofrece «Simple» y «Emojis» (fuera el modo Avanzado, la curva de energía, el interruptor «Sonidos de emojis» y el botón «Música con ducking…»). `sfx_rules.cargar_modo()` devuelve SIEMPRE `modo='simple'` (un `avanzado` viejo se ignora), `curva_energia_activa()` devuelve False, y trae `principal` (el efecto sonoro elegido para la palabra principal, 1 ruta; vacío = automático: `categoria_por_clave`, el sonido propio de cada efecto del estilo) y `activas` = {palabra, principal, intro, final} (`TARJETAS_SONIDO`). `_aplicar_modo` convierte los interruptores en `simple_donde='ninguna'` (palabra o principal apagadas), `simple_intro`/`simple_final` en False y pone `simple_principal`; `asignar_eventos_por_palabra` usa el efecto elegido en «principal» antes que `categoria_por_clave`. UI: con «Solo la principal» la tarjeta de las palabras pasa a «Sonido del texto principal» (`_cuerpo_principal`: «Automático» o el archivo elegido, ▶, Editar, Usar el elegido, Archivo…, Volver a automático) junto a Introducción y Final; con «Ninguna» solo quedan Introducción y Final. Cada tarjeta lleva un interruptor (`_cambiar_tarjeta`) que atenúa y bloquea su cuerpo. Prueba sin tocar tus archivos: `sfx_rules.CARPETA_USUARIO/ARCHIVO_MODO` a una carpeta temporal. Inicio: se quitó el chip «Idioma»; GO pone el idioma en «Detectar automáticamente» al empezar.

## emojis-posicion-free — Emojis en Resolve Free: posición, animación y orden

- **Pan/Tilt de un PNG con `Scaling=Fit`** (medido en Resolve Free 21.1, timeline 1080×1920): `Pan` se aplica ×1, `Tilt` solo ×`min(ancho,alto)/alto` (0,5625 en vertical) y NO depende del zoom. `colocar_emojis` (`.lua` y gemelo `.py`) lo compensa: Pan ×`ancho/min`, Tilt ×`alto/min`. En horizontal es hipótesis sin comprobar. El texto (Fusion) no tiene este factor.
- **Animación**: Free no tiene `io`; `emojis.comps_animacion` escribe las comps en `~/DaVinciSubtitles/emoji_comps/` y el manifiesto lleva `emoji_comps={carpeta, ids}`; `animar_emoji(…, comps)` importa la de largo más cercano (±3).
- **Orden**: en `place_guion` los emojis se colocan ANTES que los sonidos por palabra; al revés Resolve Free se cae («El puente no respondió en 90 s»).
- **Tema 4**: emoji ARRIBA del texto (`plantillas.EMOJI_ARRIBA`; `bloque_imagen` da `donde='arriba'`). Antes de tocar posiciones, medir con render real (`herramientas_dev/probar_emojis_temas.py`; diagnóstico `Vista.lua` `inspeccionar`/`ajustar_clip`).
