# Sonido y emojis (SFX Lab, reglas, emojis)

## sfx-lab — Sonido / SFX Lab

**Qué:** Sonido / SFX Lab

**Dónde:** `sfx_studio.py`, `sfx_rules.py`, `sfx_editor.py`, `sfx_audio.py`

**Biblioteca en popup (5.5.10, pedido del usuario):** la barra de la biblioteca (buscador, chips de categorías/sonidos, «Atajo global (Enviar)», «+ Mi carpeta») ya NO va en la página: `SfxStudio._riel` se crea hijo del Lab y oculto, y `_acomodar` solo coloca `_centro` y `_der`. Cada sonido de las reglas (y la principal) tiene un solo botón «Buscar archivo…» (`_buscar_sonido(seccion, indice)`) en vez de «Usar el elegido» + «Archivo…»; abre `abrir_biblioteca(subtitulo, al_usar)` → `_DialogoBiblioteca` (modal), que toma prestado el riel dentro de un `Desplazable`. Tocar un chip llama a `_cargar_sonido`, que avisa al popup por `_al_cargar_dialogo`; «Usar este sonido» o «Desde mi computadora…» llaman a `al_usar(Path)` y cierran. Al terminar (`finished`, o `hideEvent` no espontáneo) `_devolver` para el sonido y re-cuelga el riel oculto del Lab: si no, `WA_DeleteOnClose` lo borraría con el diálogo. La pestaña Emojis usa el mismo popup (`PanelEmojis(oir, buscar, aviso)`; «Buscar archivo…» → `_buscar_archivo`). Prueba: harness con prefs en memoria, `lab._buscar_sonido('inicio', 1)` + `lab._cargar_sonido(ruta)` + `dlg._usar_este()`, parcheando `sfx_rules.guardar_modo`.

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

**v5.4.29 — pantalla Sonido más simple (pedido del usuario):** `sfx_studio._pintar_reglas` solo ofrece «Simple» y «Emojis» (fuera el modo Avanzado, la curva de energía, el interruptor «Sonidos de emojis» y el botón «Música con ducking…»). `sfx_rules.cargar_modo()` devuelve SIEMPRE `modo='simple'` (un `avanzado` viejo se ignora), `curva_energia_activa()` devuelve False, y trae `principal` (el efecto sonoro elegido para la palabra principal, 1 ruta; vacío = automático: `categoria_por_clave`, el sonido propio de cada efecto del estilo) y `activas` = {palabra, principal, intro, final} (`TARJETAS_SONIDO`). `_aplicar_modo` convierte los interruptores en `simple_donde='ninguna'` (palabra o principal apagadas), `simple_intro`/`simple_final` en False y pone `simple_principal`; `asignar_eventos_por_palabra` usa el efecto elegido en «principal» antes que `categoria_por_clave`. UI: con «Solo la principal» la tarjeta de las palabras pasa a «Sonido del texto principal» (`_cuerpo_principal`: «Automático» o el archivo elegido, ▶, Editar, «Buscar archivo…» (desde 5.5.10; antes «Usar el elegido» + «Archivo…»), Volver a automático) junto a Introducción y Final; con «Ninguna» solo quedan Introducción y Final. Cada tarjeta lleva un interruptor (`_cambiar_tarjeta`) que atenúa y bloquea su cuerpo. Prueba sin tocar tus archivos: `sfx_rules.CARPETA_USUARIO/ARCHIVO_MODO` a una carpeta temporal. Inicio: se quitó el chip «Idioma»; GO pone el idioma en «Detectar automáticamente» al empezar.

## emojis-posicion-free — Emojis en Resolve Free: posición, animación y orden

- **Pan/Tilt de un PNG con `Scaling=Fit`** (medido en Resolve Free 21.1, timeline 1080×1920): `Pan` se aplica ×1, `Tilt` solo ×`min(ancho,alto)/alto` (0,5625 en vertical) y NO depende del zoom. `colocar_emojis` (`.lua` y gemelo `.py`) lo compensa: Pan ×`ancho/min`, Tilt ×`alto/min`. En horizontal es hipótesis sin comprobar. El texto (Fusion) no tiene este factor.
- **Animación**: Free no tiene `io`; `emojis.comps_animacion` escribe las comps en `~/DaVinciSubtitles/emoji_comps/` y el manifiesto lleva `emoji_comps={carpeta, ids}`; `animar_emoji(…, comps)` importa la de largo más cercano (±3).
- **Orden**: en `place_guion` los emojis se colocan ANTES que los sonidos por palabra; al revés Resolve Free se cae («El puente no respondió en 90 s»).
- **Tema 4**: emoji ARRIBA del texto (`plantillas.EMOJI_ARRIBA`; `bloque_imagen` da `donde='arriba'`). Antes de tocar posiciones, medir con render real (`herramientas_dev/probar_emojis_temas.py`; diagnóstico `Vista.lua` `inspeccionar`/`ajustar_clip`).

## biblioteca-sonidos — Biblioteca de sonidos ampliada y sonido por tema (v5.5.3)

**Qué:** 323 sonidos más en `2_recursos/sfx_library` (de ~260 a ~585; 145 MB) elegidos de la biblioteca del autor (`E:\VFX-EDICION VIDEOS\DAVINCI RESOLVE\EFECTOS SONIDO`, `RECURSOS PREMIUN\BODAS & XV RECURSOS\SONIDOS` y el pack Check Marks de `PANTALLA DE VIDEO\ICONOS DE SI Y NO`) + 3 sintetizados (Pin drop y Deep pop en Pop, Closing tape en Papel), y 11 reglas «por tema» del modo Avanzado.

**Dónde:** `herramientas_dev/importar_sonidos.py` (`CATEGORIAS`: carpetas origen + patrón + cuántos + largo máximo; quita el silencio inicial para que el golpe caiga en la palabra, recorta con fundido, ≤3 s en WAV 16 bit y el resto en MP3 256k, no pisa lo que ya hay) → `DOCUMENTACION/sfx_origen.json` (de dónde salió cada audio). Categorías nuevas: Aplausos, Gritos y ovación, Pirotecnia, Dinero, Correcto, Error, Tiempo, Cámara, Latidos, Papel, Selección, Memes, Teclado y texto, Naturaleza, Ambientes, Fiesta, Cinemático, Transiciones, Idea, Explosiones, Pop, Intro y logos; ampliadas con prefijo «Pro »: Whoosh, Riser, Hit, Click, Glitch. `sfx_rules.REGLAS_PREDEFINIDAS` empieza por las `tema_*` (`texto_contiene` en español e inglés → Dinero, Tiempo, Aplausos, Correcto, Error, Cámara, Latidos, Idea, Explosiones, Fiesta, Pirotecnia): ENCENDIDAS y antes que las genéricas (lo concreto gana). Textos traducidos en `2_recursos/locales`.

**Licencias:** parte viene de packs comerciales (Artlist, Film Score/Multiply, Netflix Sounds, Envato Check Marks); el autor decidió incluirlos y responde por sus licencias (2026-10-13). Quedaron fuera TOP (música por tonalidades, 27 GB) y CANCIONES.

## emojis-coherentes — Cada emoji con SU palabra (v5.5.7)
**Qué:** el usuario vio emojis que no casaban: 💰 en «la entrada es 100 % gratuita», 💼 en «historias», 💬 en «un torneo con premios», 💡 en «emprendimientos de comida».
**Causas:**
- `ia_texto.emojis_de_ia` MOVÍA el emoji de una palabra a la destacada más cercana de su frase (el 💼 de «empresa» acababa en «historias»).
- Las claves CLDR del catálogo dan cosas raras: «festival» → pastel de luna, «comida» → taco, «haciendo» → cuernos con la mano.

**Ahora:**
- `emojis_conceptos.py` es un diccionario curado (es/en/pt, ~35 conceptos: gratis 🆓, premios/torneo 🏆, comida 🍽, festival 🎉, música/banda 🎵, empresa 💼, historias 📖, beca/maestría 🎓, fecha/sábado/octubre 🗓, guarda 🔖, envía 🔗, amigos 🫂…). Manda sobre la IA.
- Un emoji de la IA solo se acepta si `coherente(palabra, id, sugeridos)` lo confirma. Solo se mueve a otra palabra si también va con ella.
- Las palabras destacadas que el diccionario conoce reciben el suyo (como mucho uno cada ~6 palabras).
- `emojis_sin_ia` usa el diccionario y el catálogo solo si su sugerencia es la palabra misma.
- En el video de prueba: de 22 propuestos por la IA quedaron 12, todos con sentido.

**Con la Edición PRO (Temas 1–4):** donde la PRO enseña algo (acompañante, órbita, cifra, escena, tarjeta…) el emoji de GO se apaga (`edicion_pro.aplicar` → `sin_emoji`). Antes solo pasaba junto a un icono 3D. Gemelos: `colocar_pro._apagar_emojis` y `CineCaptions_EdicionPro.lua` `apagar_emojis`.

## sonido-pro — Sonido › Edición PRO: los sonidos de sus gráficos, con mando (v5.5.7)

Tercera pestaña de «Reglas automáticas» (`sfx_studio._pintar_reglas_pro`; la página abre en ella si la PRO está activa): interruptor
`pro_sonidos`, volumen `pro_sonidos_nivel` (suave −5 dB · normal · fuerte +3 dB, `edicion_pro.NIVEL_SONIDOS_DB`) y las tres familias
`pro_sonidos_familias` = movimiento (whoosh) · apariciones (toques/pop) · riser + golpe, cada una con «Oír un ejemplo» (uno distinto por clic, de
`edicion_pro_sonido._archivos`). `edicion_pro.aplicar` salta los sonidos de una familia apagada (`FAMILIA_DE_PISTA` por la pista PRO-*) y suma el
nivel antes de hornear la ganancia en el archivo. Dice el tema actual y que los sonidos de «Simple» siguen con los captions (la PRO no los pisa).

## nota — v5.5.7 · el emoji se separaba del caption al moverlo la regla de la cara

`colocar_pro._subir_captions` (y `subir_captions` del .lua) movía TODOS los clips del bloque con el mismo Tilt; el Tilt de un PNG «Fit» (los
emojis) solo se aplica ×min/alto (0,5625 en vertical), así que el emoji recorría ~56 %: con subidas de 500–760 px (medidas en un plan real)
quedaba 250–330 px lejos del texto, o encima al bajar. Ahora en las pistas EMOJI el desplazamiento va ×alto/min, y `_emojis_sin_cara` lee y escribe
la posición del emoji con ese mismo factor (Pan ×ancho/min, Tilt ×alto/min, como `colocar_emojis`).

## ai-sound-director — AI Sound Director (v5.34–5.35, fases 0–6: análisis, voz, AI SFX, música y ambiente, mezcla/QC/Sound Score y la página SONIDO)

**Qué:** el sound designer de GO, ENCIMA de los motores de siempre (`sfx_rules`, `sonidos_extra`, `edicion_pro_sonido`, `rectificador`, `musica_go`,
`ducking`, que quedan como motores internos). Interruptor `ai_sound_director` (pref, **apagado por defecto**; `CINECAPTIONS_AI_SOUND=1/0` lo fuerza en
las pruebas). **Apagado = GO exactamente como antes** (`al_colocar` devuelve el MISMO plan; probado contra el código de HEAD). Solo toca AUDIO: lee
captions, motions, cortes y planes para entenderlos, nunca los cambia. Cualquier excepción → `[AI SOUND] fallback: motor original` y GO sigue.
Plan completo y fases 3–8 (SFX y síntesis, música + ambiente, mezcla/QC/Sound Score, la NUEVA página Sonido = AI Sound Director, incremental,
regresión): `plan_ai_sound_director.md` (notas de la sesión).

**Flujo en GO:** tras `_planificar_pro`, `_director_sonido_arrancar` hace una FOTO en datos simples (`director_sonido.contexto`: palabras, tema,
recorte de pausas, bloques, planes de Efectos y PRO) y arranca `director_sonido.preparar(ctx, res=…)` en un hilo (`ai-sound-director`), que rellena
`res` según avanza: análisis → SONIDOS (fase 3, rápidos) → voz. En `_rectificar_planes`, `_director_sonido_al_colocar` lo recoge (espera ≤ 300 s; si
la voz no acabó, la original se queda pero los sonidos sí van) y `al_colocar(plan, res, video, plan_pro=…)` arma el plan de Efectos (abajo), o
—director apagado tras haberlo usado (`general.json: voz_ai_puesta` / `ai_puesto`)— un plan `solo_ai` que solo limpia. `_colocar_efectos` acepta ese plan.

**Fase 1 — análisis (no cambia nada audible):** `director_sonido_medir` (PyAV en streaming: `trozos`, `Grafo` de ffmpeg, `Sonometro` = ebur128 LUFS/LRA/
true peak, `Analizador` con marcos de 20 ms y finos de 171 ms, `EscritorWav` 24 bits) · `director_sonido_voz.analizar/diagnostico` (fondo medido en
silencios o, si casi no hay, en los HUECOS entre palabras; hum 50/60 Hz + armónicos, hiss, rumble y viento con marcos finos —en 20 ms los graves se
cuelan de la ventana—, resonancias sin la F0 de la voz, plosivas, sibilancia = eses p95 contra las vocales p90, aspereza/barro/aire contra el LTASS,
nivel desigual, clipping en muestras nativas, inteligibilidad 1–4 kHz, `noise_score`) · `director_sonido_musica` (música ya MEZCLADA: fondo cerca de la
voz, tonal, graves que no bajan sin voz y pulso en la envolvente de graves; estados NO_MUSIC_REQUIRED / KEEP_EXISTING / ADJUST_EXISTING / ADD_NEW /
REPLACE_ONLY_IF_ALLOWED sugeridos; Epidemic solo si existe `EPIDEMIC_API_KEY`, nunca leída para guardarla) · `director_sonido_ambiente` (por escena
entre los cortes que ya busca GO: metadata del proyecto → palabras → género PRO → audio del fondo; nunca añade sin coherencia) ·
`director_sonido_identidad` (perfil por tema DERIVADO de su configuración real + paleta del proyecto, cada rasgo con su porqué; las transiciones e
intro salen del plan de Efectos real: desde la 5.21 Efectos no aplica las de `recomendaciones`) · `director_sonido_eventos` (captions, motions con su
metadata real, narrativa HOOK…CTA) · `director_sonido_estado` (`sound_design_project` por huella del video, con `archivos_seguros`).

**Fuentes de audio (decisión del usuario):** la biblioteca local (`2_recursos/sfx_library`, la música vieja) NO alimenta los diseños nuevos:
`legacy_local_assets` = DISABLED_FOR_NEW_DESIGN (se conserva por los proyectos antiguos). Prioridad: procedural a la medida → Epidemic autorizado →
caché profesional aprobada (con metadata) → biblioteca curada → legacy solo tras el Quality Gate → silencio. Hoy (fases 0–2) solo afecta a la
música sugerida: sin proveedor autorizado, NO_MUSIC_REQUIRED con el aviso (`director_sonido_musica.LEGACY_LOCAL`, `proveedores`, `sugerir`).

**Fase 2 — voz:** `director_sonido_voz.restaurar` elige el backend (VoiceRestorationBackend: nivel 0 nada · 1 PyAV + `director_sonido_nr` · 2 RNNoise
solo con modelo validado en `RNNOISE_MODELOS` (hoy ninguno) · 3 externo registrado con `registrar_backend` (hoy ninguno)), prueba la cadena en
extractos (≤ 6 × 10 s; un video corto entero) con fuerza 1 → 0,6 → 0,3 y las GUARDAS antes/después con los MISMOS marcos (ruido musical = picos
espectrales sueltos que aparecen y desaparecen en el fondo, `UMBRAL_EFIMEROS` 3/marco: reducción del director +0,0–0,1, agresiva +4…+12; huecos
espectrales solo en bandas donde manda la voz; pérdida de agudos; inteligibilidad; envolvente de la voz r ≥ 0,9; sobrecompresión). Si DESPUÉS es
peor → menos proceso; si sigue peor → la original. Pasada A (mide), pasada B (copia con ganancia + limitador −2 dBFS; true peak ≤ −1 dBTP, si no se
recorta), comprobación final y misma duración exacta. Nivel = el del original dentro de −18…−12 LUFS (los SFX de siempre se nivelan con la voz
original). Audio con música mezclada: paso alto solo subsónico (35 Hz), sin reducción de ruido ni compresor; si no queda nada que se oiga → nivel 0.
El ambiente que se CONSERVA (calle, gente, naturaleza) limita la reducción a 6 dB; REDUCE, a 10. Copia: `~/DaVinciSubtitles/sound_director/<huella>/
AI_VOICE_<clave>.wav` (caché por huella + recorte + versión). Solo en timelines que armó GO con el video soltado (`_go_tl_listo`); con el audio del
timeline (la mezcla de sus pistas) la voz original se queda.

**`afftdn` NO sirve aquí:** en PyAV baja < 1 dB el ruido rosa a −38 dBFS (ni con perfil `bn` ni muestreando con `sn`/`asendcmd`). La reducción va en
`director_sonido_nr.ReductorEspectral` (numpy: STFT 1024/512 raíz de Hann, ruido por MÍNIMOS ~1,5 s ×2,5 —calibrado con ruido rosa—, Wiener con SNR a
priori «decision-directed», suavizado en frecuencia y caída lenta, TOPE de reducción 6–15 dB). Reconstrucción perfecta (error 0) y sin desfase.

**Resolve (gemelos `colocar_efectos.py` ↔ `CineCaptions_Efectos.lua`):** `_poner_voz_ai` / `poner_voz_ai`: pista «AI VOICE» (mono/stereo como el
original) con UN clip; A1 se apaga (`SetTrackEnable`) SOLO después de comprobar que el clip quedó entero y en su sitio; si algo falla (no entra, no
cuadra con A1, A1 no se deja apagar, hay otras pistas de audio del usuario con clips) la copia se quita y A1 queda encendida. Sin evento: AI VOICE fuera y
A1 vuelve. Pistas `AI MUSIC / AI AMBIENCE / AI SFX MOTION / AI SFX UI / AI SFX IMPACTS / AI SFX TONAL / AI SFX TEXTURE` por NOMBRE (eventos con
`pista`; vacías se quitan). `solo_ai` = solo lo del director. Re-aplicar no apila. `resolve_mcp._ASEGURAR_AUDIO` (final de GO en Studio) ya no
reactiva A1 si AI VOICE tiene su clip (sonarían las dos voces). La pequeña diferencia de fase (≤ 0,2 ms) es la del paso alto IIR, no un retraso.

**Epidemic Sound (`director_sonido_epidemic.py`, solo backend):** clave SOLO de `EPIDEMIC_API_KEY` (o del `.env` de la raíz en desarrollo; Git
ignora `.env`/`.env.*`, la plantilla es `.env.example`); al leerla —también al arrancar la app (`main`)— sale del entorno del proceso para que Resolve,
la IA local y node no la hereden; nunca se imprime, se anota, se guarda ni va a la interfaz (`_sin_clave` limpia cualquier eco del servidor).
API v0 (spec 0.1.17, base `https://api.epidemicsound.com`, `Authorization: Bearer`, `x-partner-user-id` = hash anónimo del equipo):
`/v0/collections`, `/v0/sound-effects/search` (term obligatorio), `/v0/sound-effects/{id}/preview` y `/download`, `/v0/tracks/search`,
`/v0/tracks/{id}/stream` (HLS) y `/download` (mp3 normal 128 kbps 24 h / high 320 kbps 1 h), `/v0/usage` (informar exportaciones de música: fase 4).
Plan gratuito: catálogo completo pero 50 descargas y 100 streams DE POR VIDA y sin licencia comercial. Errores: 401 no se reintenta, 403 = fuera del
plan (la función queda no disponible en la sesión), 406 del CDN ≥ 2 s, 429/502/503 con `Retry-After`, 500 una vez. `acceso()` = prueba segura del
nivel real (sin preview ni descarga salvo que se pidan). `materializar()` = UNA descarga del asset elegido a `sound_director/cache/epidemic/{music,
sfx,ambience}/` + `indice.json` (provider, asset_id, title, category, query, download_quality, local_path, file_hash, project_usage, date_downloaded);
copia válida → sin volver a llamar a la API (sirve sin conexión); duplicados por asset_id + file_hash; lo procesado va a `processed/` (el original
no se toca) y Resolve usa siempre el archivo LOCAL. Pruebas: `herramientas_dev/probar_epidemic.py` (servidor falso, 31) y `--real [--preview]
[--descarga]` contra la cuenta. Si la API falla: procedural, caché o silencio; nunca los legacy.

**Fase 3 — AI SFX (en GO; el director es el ÚNICO dueño del sound design):**
- `director_sonido_diseno.disenar(analisis, ctx)` lee la metadata REAL y decide evento a evento (casi todo LEAVE_SILENT). **Captions**: el instante que
  manda según el estilo (Kinetic: el héroe «pop» 10 f easeOutBack —el golpe cae en p≈0,37, cuando llega a su tamaño— + anillo que se dibuja + cinta que
  gira, `ANIM_KINETIC`; VIRAL: el clip de la palabra clave —shatter = golpe brillante, drag = whoosh corto, select = tic, negrita = pop—; «guion»
  (Temas 2, 4, 5, 6): la palabra clave con su zoom). CAPTION_SOUND_SCORE 0–1 (papel narrativo, importancia, tamaño/zoom/clip, cifra, anillo, distancia
  al último acento; nunca dos a < 2 s salvo una cifra; nada encima de la intro de Efectos) contra el umbral de la paleta (0,55 + 0,3·(0,4 − densidad)).
  El ACENTO de cada tema sale de su carácter (`caracter`): impacto ≥ 0,6 → golpe diseñado · PRO sobria / interfaz → tic · PRO editorial → trazo de pluma ·
  medio → pop (hoy: T1 golpe, T2 tic —su toque por palabra—, T3 por clip, T4 tic, T5 tic, T6 trazo). **Motions**: el MISMO «cuándo» que la PRO
  (`edicion_pro_sonido.momentos`, separado de `disenar` sin cambiar lo que hace: probado igual que HEAD) + eventos visuales de Efectos (corte, énfasis,
  B-roll, icono, pegatina, número); lo que ENTRA pesa más que lo que sale; un motion no suena a < 0,15 s de un acento de caption. **Encima**: riser en
  el gancho (una vez, no con intro de Efectos ni en temas sobrios), risers de la PRO como mucho uno cada 20 s y nunca a < 2,5 s de un golpe, MOTIVO
  tonal (la misma nota) en los datos y en el cierre (CTA), whoosh en cortes secos SOLO en temas enérgicos (transitorios ≥ 0,6: un corte seco en un tema
  sobrio no tiene movimiento que suene). **Densidad**: 2 + 4·densidad sonidos por ventana de 10 s compitiendo por importancia (solo gancho y cierre
  fijos); si un caption pierde su acento, se va entero (anillo, cinta, nota). Cada «Hit» de Simple → REPLACE / REMOVE con su porqué.
- `director_sonido_sfx.fabricar` (modo **híbrido**, el que eligió el usuario en la demo): el mejor archivo de la biblioteca curada que pasa el Quality
  Gate + ajuste semántico y una capa procedural a la medida (sub y clic bajo el golpe, aire bajo el whoosh); si nada pasa, procedural
  (`director_sonido_sintesis`); nunca la `sfx_library` legacy. Alineado al ANCLA (el pico en el fotograma que manda; el riser acaba 30 ms antes), nivel
  RELATIVO a la voz dentro del archivo (golpe −9 dB, whoosh −15, tic −22…; −2 dB más si cae sobre una palabra; la voz prevista = la medida + la
  ganancia de la fase 2; si queda > 1 dB distinta, se rehacen), pico ≤ −1 dBFS, microvariación (tono ±3 %, ±0,7 dB) cuando un archivo se repite (el
  motivo, no: es identidad), WAV 48 kHz/24 bits con nombre por contenido en `sound_director/<huella>/sfx/`. Quality Gate con caché en disco
  (`sound_director/cache/quality_gate.json`). PRUEBA ESPAÑOL (62 s): 16–25 sonidos según el tema en ~1 s (hoy GO pone ~75: 32 «Hit» + 43 de la PRO).
- `al_colocar`: en una COPIA del plan de Efectos, los sonidos de Efectos reciben `decidir_efectos` (los «extra» de la biblioteca de siempre → REPLACE;
  intro / outro / de un efecto visual → KEEP: van con su animación), los del director van con `pista` AI SFX …, `apagar_sfx` = pistas «SFX…» de Simple
  y la PRO queda marcada (`_ai_sound`) → `sonidos_pro` (final de `edicion_pro.aplicar`, tras el rectificador) quita los de los gráficos y deja los de
  «Motions completo» (`origen: motions`, solo marcados con el director al mando). La música sigue igual hasta la fase 4. Lo visual, idéntico.
- Resolve (gemelos): `_apagar_sfx` / `apagar_sfx` APAGAN (no borran: `SetClipEnabled(False)`) los clips de las pistas «SFX…» SOLO si los sonidos del
  director quedaron puestos (o su diseño era silencio a propósito); un GO con el director apagado los vuelve a poner.
- `herramientas_dev/demo_director_sonido.py` renderiza (render de «GO sin Resolve») el Tema 1 en A actual / B procedural / C biblioteca del autor /
  D híbrido / **E fase 3 tal cual la pone GO**, con LEEME de decisiones.
`director_sonido_fuentes` = Quality Gate técnico (clipping, ruido, muestreo, equilibrio, graves, transitorio, fase, bitrate, cresta) **+ ajuste
semántico por el nombre** (palabras ENTERAS; núcleo obligatorio por tipo; objetos concretos —plástico, acero, bate, mesa…— y tonos oscuros en un
video luminoso penalizan; nunca memes/fart/voces/música) + duration/spectral/energy fit + anti-repetición por familia. Lección: sin la parte
semántica la «calidad» técnica aprobaba «…Farts…» como golpe.

**Fase 4 — música y ambiente (`director_sonido_capas`):** `musica`: «Sin música» (control) → NO_MUSIC_REQUIRED · el video ya la trae → KEEP_EXISTING
(no se separa ni se pone otra encima) · hace falta y hay proveedor AUTORIZADO → ADD_NEW: consulta según energía/tono/paleta, VARIAS candidatas con
`music_fit` (BPM contra la energía, duración, mood; fuera solo-preview, explícitas y con voces), UNA descarga (`materializar`), copia procesada en
streaming: bucle con fundido cruzado, fundidos, hueco de EQ 2,5 kHz/350 Hz, nivel bajo la voz medido TRAS el EQ (Media −15 dB) y ducking por frases
(−6 dB al hablar, ataque 0,12 s, suelta 0,45 s) → pista «AI MUSIC» · sin proveedor → NO_MUSIC_REQUIRED + aviso. `ambiente`: lo del original ya lo
trató la voz; lo que se AÑADE (ADD_SUBTLE_AMBIENCE, o el control «Sutil/Inmersivo» con entorno claro) solo de grabaciones autorizadas: escenas seguidas
= un tramo, paso alto 120 Hz, −6 dB a 2,2 kHz, ~−28 dB bajo la voz y −4 dB al hablar → «AI AMBIENCE»; sin proveedor → LEAVE_SILENT. La música de
Efectos (si la hubiera) sale cuando el director pone la suya.

**Fase 5 — mezcla, QC y Sound Score (`director_sonido_mezcla`, `director_sonido.mezclar`):** tras la voz, la mezcla COMPLETA offline (la voz que va a
sonar —AI VOICE o el audio del timeline con Quitar pausas— + cada WAV en su sitio, a 0 dB como Resolve) medida en streaming (`Tira` = WAV por acceso
directo): LUFS/LRA/true peak, recortes, cada evento contra la voz mientras habla (umbral −40 dB bajo SU pico, invariante a su ganancia) y la música
contra la voz. Autocorrección: primero baja SOLO lo que queda a menos de 8 dB de la voz (hasta 2 vueltas), vuelve a medir y solo entonces, si los del
director empujan el true peak por encima de −1 dBTP, baja su bus (nunca la voz). Las bajadas quedan en `estado['mezcla_ajustes']` (como un fader: los
retoques de la página las conservan; cada GO empieza de cero). En los golpes el ancla se fija sobre el pico del sonido FINAL (archivo + capas).
SOUND SCORE = 25 voz + 15 ruido + 15 sincronía + 10 música + 10 consistencia + 15 protección de la voz + 10 mezcla, cada parte de su medida
(`FORMULA`). PRUEBA ESPAÑOL (Tema 1): 89/100, −14,1 LUFS, −3,7 dBTP, sincronía 3 ms.

**Fase 6 — la página SONIDO = AI Sound Director (`director_sonido_ui.PaginaDirector`, motor `director_sonido_sesion`):** `SubtitleApp._asegurar_sfx`
arma esta página (el SFX Lab de antes solo si la nueva no se pudiera construir: red técnica, no una página a elegir). Cabecera (interruptor, Tema, AI
Sonic Style, video, Sound Score en un anillo: un clic da el desglose), estado con ✓ (voz, ruido —«es música, no ruido» si la trae—, música, ambiente,
sonido de motions, mezcla, master), acciones (▶ Original / ▶ AI Sound = mezclas reales de 15 s desde el instante elegido, Deshacer todo, Aplicar a
Resolve —solo tras un GO con el director; plan `solo_ai` por `efectos_visuales.aplicar`—, Rediseñar sonido), controles (Estilo + intensidad,
densidad, prioridad de voz, música, ambiente; AUTO = sin clave en `ai_sound_controles`), la línea (VIDEO · VOZ · MÚSICA · AMBIENTE · SONIDOS IA; clic =
el sonido más cercano, otro clic en el mismo sitio pasa al siguiente solapado), el inspector (diseño IA, por qué, importancia; Oír, Menos…/Más… con
sus opciones, Regenerar, Silenciar, Bloquear) y «Dile a AI Sound Director…» (reglas en español: menos/más sonidos, la voz más clara, estilos, sin
música/ambiente, «quita el sonido de X», «rediseña el inicio/el final», «como estaba»). Los retoques van a `estado['ajustes']` por la `clave` del
evento (origen|caption|tipo|instante) y SOLO ese evento se rehace (los demás reutilizan su WAV: el nombre es su contenido); «Rediseñar» sube la ronda
(otras variaciones, lo bloqueado se queda). Si el video de Inicio no pasó por GO con el director, la página enseña el último que sí (lo dice). Sin
globos: todo en una línea de estado. Textos traducidos (5 idiomas).

**v5.37 — el director se encarga de TODO (el usuario: «en el Tema 1 aún suenan las reglas viejas y la página no hace nada»):** tres fallos
encontrados con el Registro, `contexto.json` y una lectura del timeline: (1) `efectos_visuales.aplicar` no pasaba `apagar_sfx` al plan de Resolve,
así que las pistas SFX/SFX 2 de las reglas quedaban encendidas — ahora va en `datos`; (2) `_preparar_sfx` mandaba los sonidos de `sfx_rules` a
Resolve aunque el director estuviera encendido — ahora devuelve `{}` (los `sfx_eventos` se quedan en los bloques para las decisiones del director);
(3) el Tema 1 neón llega sin los `runs` del tema (los arma el kit en la PRO): `director_sonido_diseno._momento_caption` usa la línea `main` (la
palabra principal entra con el «pop»). Los sonidos que la PRO arma AL APLICAR (kit neón, gráficos, Motions completo) ya no se borran sin más:
`director_sonido.sonidos_pro` → `redisenar_pro` los REHACE en su mismo instante (pico del WAV original + `ini`), tipo por pista (PRO-WHOOSH/RISER/HIT)
o por lo que describen (pop/tic), nada a < 0,15 s de un acento de caption ni encima de un motion que el director ya sonorizó, densidad por ventanas
de 10 s con lo del director, `fabricar` híbrido; quedan en `pro_sound_events`/`pro_sfx_plan` (si falla: fuera, salvo Motions completo). El
director viene ENCENDIDO por defecto (`activo`: sin preferencia = sí; «apagado» sigue siendo GO como antes).
**Biblioteca del autor entera (`director_sonido_biblioteca`):** índice de TODO su material (EFECTOS SONIDO + BODAS & XV SONIDOS + «Mis sonidos» =
`sound_director/biblioteca`, para lo que añada o descargue con licencia) por CARPETAS (IMPACTOS, Pads_Drones, Chord Hits, AMBIENTE…) y, si no,
por las palabras núcleo del nombre; fuera canciones, memes, gritos, aplausos, animales, melodías, bucles a tempo y el obturador de cámara.
3 105 archivos: 1 081 whooshes · 187 golpes · 634 risers · 392 tonales · 53 clics · 5 trazos · 676 camas de score · 77 ambientes. A disco
(`cache/indice_biblioteca.json`, se rehace si cambia una carpeta de primer nivel o a los 7 días). `director_sonido_fuentes.candidatos` añade 60 por
tipo (semántica primero, repartidos por packs) y `_palabras` lee también la carpeta (+ palabras en español: SELECCION, POSITIVO, risex, chord…).
**Música sin Epidemic:** `director_sonido_capas._musica_del_autor` = cama de score de sus colecciones de Film Score (modo mayor si el video es
luminoso, menor si es sobrio; nada oscuro en un video luminoso), Quality Gate, una por video (hash), mismo proceso (bucle, EQ, ducking por
frases) y 2 dB más baja (−17 bajo la voz, −23 cuando habla). También si nada de Epidemic encaja. **Ambiente:** `_ambiente_del_autor` = la
grabación del autor de ESE entorno (`AMBIENTE_DE`: calle, naturaleza, agua, gente, café, viento…; lluvia solo donde llueve); un entorno sin
grabación (interior) → silencio.
**La página hace de verdad:** cada cambio (control, retoque, Rediseñar, Deshacer, «Dile…») va SOLO a Resolve en el mismo hilo
(`director_sonido_sesion.aplicar_al_momento`: si el último GO fue con el director y Resolve está abierto; si no, queda pendiente). Cabecera con
«En Resolve y al día · hh:mm» o «Hay cambios que aún no están en Resolve» (y «Aplicar a Resolve» pasa a botón principal); secciones con título;
fila «Material» (cuánto material de las bibliotecas); carril MOTIONS PRO (los rehechos y los callados); el inspector dice qué archivo de la
biblioteca eligió o si se sintetizó; anillo del Sound Score más grande. Descargas CC0 (Kenney) o Sonniss: solo con el permiso del usuario, a «Mis
sonidos».

**Probar (sin el Resolve del usuario):** `python 1_codigo/herramientas_dev/probar_pagina_director.py` (la página: motor + Qt sin pantalla, capturas
PNG; 43) y `python 1_codigo/herramientas_dev/probar_director_sonido.py --fase 0|1|2|3|4|5|todo [--salida X] [--muestras Y]` (322; fase 4 con el
Epidemic FALSO de `probar_epidemic.py` sirviendo audio de verdad; fase 5 compara la mezcla medida con una suma independiente). También con Python 3.15.1
(`6_compilacion/venv315`).
(fase 3: los 6 temas con PRUEBA ESPAÑOL —silencio mayoritario, WAV, densidad, anti-repetición, golpe ±1 fotograma, identidad, «Hit» viejos—,
`al_colocar`/`sonidos_pro`, fallback, `colocar_efectos.py` y el `.lua` (con y sin io) apagando Simple, GO de punta a punta; 290 en total)
(Registro a una lista, prefs en memoria, estado en la salida; Resolve falso `herramientas_dev/resolve_falso.py` para el `.py`, LuaJIT/lupa para el
`.lua`, con y sin io; voz limpia de referencia con SAPI por COM `herramientas_dev/_voz_sapi.py` + fondos: ruido + hum, música sintética, ambientes de
`sfx_library/Ambientes`, aire acondicionado; regresión «apagado = HEAD» con `git show`; de punta a punta GO → `efectos_visuales.aplicar` → Resolve
falso). Deja VOICE_ORIGINAL_* / VOICE_AI_* para escuchar.

### Revisión de la página Sonido — 21 de octubre de 2026

Cambio limitado al contenido de Sonido y su lógica. La navegación, `isla_ui`, `qt_kit`, Inicio, los estilos globales y la versión quedan intactos.

`PaginaDirector` conserva los componentes Qt existentes. La línea, el tramo A/B, Aplicar y la lista de eventos aparecen antes de los controles y del diagnóstico. El inspector se coloca al lado a partir de 1000 px de ancho útil y debajo en ventanas menores. Los seis controles usan los Combo existentes; sus preferencias siguen siendo globales y se indica que también afectan a próximos GO. El diagnóstico conserva sus ocho estados, plegado de inicio. Las acciones se llaman «Crear otra versión» y «Restaurar diseño IA».

Los cambios de la página se guardan localmente y quedan pendientes: solo «Aplicar a Resolve» envía. La página bloquea los controles afectados durante un trabajo, conserva la frase si se rechaza o falla, mantiene los errores visibles y muestra «Medición pendiente» cuando el score quedó desactualizado. La lista permite elegir con las flechas y escuchar con Enter. La selección también mueve el tramo A/B.

`director_sonido_sesion.resumen` respeta el video elegido; no lo sustituye por el último diseñado. Los pedidos con negación no pueden caer en su regla positiva; los controles por tramo no compatibles piden aclaración sin ejecutar. Una orden combinada de capas y sección recalcula ambas partes.

El último GO guarda destino (proyecto, timeline e ID cuando existe) y sesión. Preparar el plan deja pendiente; `confirmar_colocacion` confirma solo tras éxito real y si la sesión sigue vigente. `Aplicar` compara el destino antes y después del envío. Los gemelos `colocar_efectos.py` y `CineCaptions_Efectos.lua` comprueban `destino_ai` antes de tocar bins o pistas; sin ese campo conservan el comportamiento previo. En Free, la comprobación autoritativa ocurre dentro del script. Un GO antiguo sin destino pide repetir GO para vincularlo.

`cerrar_preparacion` congela el resultado compartido mediante un candado: después del límite de espera, el trabajador puede terminar su cálculo pero no publicar ni sobrescribir el diseño colocado. Si GO reconstruye automáticamente un timeline tras un fallo, `revincular_colocacion` renueva solo su sesión/destino antes de repetir, conservando el audio. No se revincula ante un cambio manual de destino.

Pruebas aisladas: página/motor 48; fase 0, 32; sesión segura, 17; guardia Python/Lua con y sin io, 32; ciclo y resultados tardíos, 7. Todas pasan. Sin Resolve real ni preferencias del usuario. Capturas y mediciones en `4_diseno/propuesta_sonido/auditoria_2026_10_21/implementacion/`: a 1240×900 la línea empieza en y=298 del área útil (antes y=789), con inspector y acciones visibles.

**Página SONIDO = «elige una versión» (v5.42, diseño C elegido por el usuario: «la página de sonido me estresa»):** a la vista solo «Sonido», el video · Tema N, una pastilla de estado (En Resolve y al día / Cambios sin aplicar / Listo para aplicar / Haz GO…), el cuadro del video en su formato (`VistaVideo`, un cuadro a 1/4 leído con PyAV en un hilo) con ▶ y «Antes | Con sonido», y tres `TarjetaVersion`: Suave · Cinemática (la que diseñó la IA = controles en Auto, «Recomendada») · Con energía. Cada versión es un juego de los controles de siempre (`VERSIONES`, solo estilo/intensidad/densidad/música; voz y ambiente son del usuario): elegirla = `poner_control` + `_rehacer(capas=True)` en un hilo, queda pendiente; ▶ en otra la prepara, la elige y suena; `version_de(controles)` dice cuál está (None = ajustada a mano). Si el video ya trae música, las descripciones dicen «respeta la música del video». «Ajustar a mano» (plegado) guarda el interruptor del director, la línea con su inspector y los seis controles. Fuera de la página: el Sound Score, «Dile a AI Sound Director…» y el diagnóstico (el motor los sigue calculando). Pruebas: `herramientas_dev/probar_pagina_director.py` (53).

## sonido-biblioteca — Sonido con la biblioteca del autor (v5.43: reemplaza el diseño de SFX del AI Sound Director y su página)

**Qué:** el sonido de GO lo decide `sonido_skill` con la biblioteca del autor (`Desktop\SFX`, carpetas `01_SFX/NN_CATEGORIA`, prefijo `CATEGORIA - `) y las reglas de su `MAPA_SFX.md`. Es el MISMO motor que la skill de Claude «sonorizar-sfx» (`~/.claude/skills/sonorizar-sfx/scripts/proponer_timeline.py`): `REGLAS`, `POOLS` y `ESTILO` deben quedar iguales en los dos. Decisión del usuario (2026-10-23): esta lógica reemplaza al AI Sound Director.

**Eventos (sin mirar el video, de la metadata REAL de GO):** `etiquetas_de_go(ctx)` lee `director_sonido_eventos.captions` (palabra clave `main` → «Palabra clave» en el segundo donde Simple ponía su toque, `sfx_eventos`; clips `k ring/line trazo` → ARO = KINETIC; VIRAL shatter → acento, drag → swoosh, select → tic; `k hero` → golpe en p≈0,37 de 10 f; dinero en la clave o en una frase DATA → DINERO), `motions` (Efectos: corte, icono, número, pegatina, énfasis, B-roll; PRO por el nombre de la pieza: barra/mapa → carga, check, toggle, notificación, logo, calendario → página, glitch, neón…; kit neón: barrido → shine) y los `cortes` de GO (swoosh corto). La narrativa (`_rol_en`, `PESO_ROL`) da la fuerza para elegir los acentos.

**Decisión (`elegir`, `asignar`):** acento = el texto grande más fuerte de cada ventana de 4 s (no en ventanas seguidas); si dos chocan (< 0,25 s, o < 0,5–0,6 s entre pops) gana la prioridad mayor; máx. 2 impactos (logo + brillo); tope por ventana de 10 s según el estilo (v5.48: la densidad de los creadores, ver abajo; los subtítulos chicos solo suenan en cinética). Estilo: preferencia `sonido_estilo` o por el pack (VIRAL → cinética, Referencia/guion → elegante, el resto dinámico). Gancho (riser) solo si Efectos no puso ya una intro con sonido (`intro_con_sonido`). Variantes: `Elector` (v5.48, ver abajo), nunca la misma familia seguida.

**Archivos y nivel:** `catalogo()` usa `catalogo_sfx.json` de la biblioteca (lo escribe la skill: duración, PICO, fin audible) o mide con PyAV y guarda en `sound_director/cache/catalogo_biblioteca.json`. `hornear` escribe cada SFX recortado (whoosh = pico + 1 s; cola en silencio fuera), con fundido de 0,2 s y su nivel DENTRO del WAV (Resolve ignora el volumen de clip por script): pico objetivo por categoría −3 dB con voz, ≤ −1 dBFS, en `sound_director/<huella>/sfx_biblioteca/`. El PICO de cada sonido cae en el frame del evento (`ini = segundo − pico`).

**Enganche en GO:** `_director_sonido_arrancar` → si la preferencia `sonido_skill` (encendida por defecto) → `sonido_skill.preparar(ctx, res)` en vez de `director_sonido.preparar` (si el interruptor del director estaba apagado se enciende: su tubería es la que coloca). `res['sfx']` tiene la forma de `director_sonido_sfx.fabricar`, así que `al_colocar`, las pistas `AI SFX …`, `apagar_sfx` de Simple, `confirmar_colocacion` y `director_sonido_sesion.aplicar` siguen iguales. El diseño queda en el estado del video (`sfx_plan`, `sonido_skill`) y la foto de GO en `contexto.json` (para rehacer sin GO).

**Página SONIDO = editor visual A+B (`sonido_skill_ui.PaginaSonido`; el usuario eligió combinar dos propuestas):** la página del AI Sound Director ya NO se muestra (`director_sonido_ui.py` sigue en el código: lo usan pruebas y el MCP). Todo en un desplazable vertical: cabecera (logo, video · sonidos · estilo, «● cambios sin aplicar», «Rehacer», «Aplicar a Resolve»); (B) cinco `TarjetaEstilo` (Automático, Elegante, Dinámico, Lista, Cinética), `AroTipos` (cuántos de cada pista), Gancho al inicio / Fiesta o mar y la carpeta; (A) `CuadroVideo` (el fotograma del momento elegido con su etiqueta; clic = escuchar) e inspector (`IconoGrande`, tipo · segundo, archivo · pista, `Onda` del WAV horneado, POR QUÉ, ▶ Escuchar · Otra variante · ◀/▶ un fotograma · Quitar = `sonido_skill.editar`, y la revisión); (A) `LineaTiempo`: tira de fotogramas, onda de la voz, un carril por pista con bloques de color (ícono dibujado `pintar_icono` + onda), línea en el PICO, cabezal rojo en el momento elegido, zoom −/+ (elegir centra el editor ahí); (B) `TarjetaMomento` por sonido (fotograma, segundo, ícono, nombre, onda, porqué; clic = elegir). Datos: `resumen` + `visual(video, filas)` (miniaturas por segundo con PyAV solo de fotogramas clave —`skip_frame='NONKEY'`, rotación como `cuadro_del_video`—, voz en 1200 barras, ondas de cada WAV; caché `miniaturas/` + `visual.json` en la carpeta del video: ESPAÑOL 8,3 s la 1.ª vez, 0,5 s después). Pruebas (scratchpad, sin Resolve, aislado): Tema 1 real sobre ESPAÑOL.mov, PRUEBAS (7).mp4 y «3 things from beginner to pro.mp4»: palabras clave con sonido 34/35, 49/49, 35/35; aros → KINETIC 19/20, 23/24, 15/15; 50, 53 y 39 sonidos; miniaturas 63/85/77; TODO PASA.

**Lo aprendido de los creadores (v5.48):** la skill midió 70 videos de 5 creadores de Instagram y el usuario pidió llevarlo a la página. (1) **Solo sonidos curados** (`curado`): nunca `17_EXTRAIDOS_REFERENCIAS`, `_DE_REFERENCIAS` ni `solo_ejercicio` (los recortes sacados de los videos de creadores le sonaron «de primaria»). (2) **`Elector`** igual al de la skill (`apoyo_decision.Elector`): por pool 1 principal + `VARIANTES_POR_ROL` = 3 de otras familias (`familia` del catálogo), nunca la misma familia seguida, ningún archivo en más del `TOPE_REPETIR` = 40 % de su pool; si un pool se queda sin lugar, `RESPALDO` da el vecino (antes rotaba por TODO el pool: 19–23 archivos distintos en un video; los creadores usan 3–4 por tipo). (3) **Lo aprobado primero** (`usos_aprobados`, `pools_de`): las filas de los CSV de `_datos_catalogo/aprobados.json` pesan 5 y las réplicas de creadores (`00_REFERENCIAS_CREADORES/*/*/EJERCICIO - linea de tiempo.csv`) 1; el pool se ordena por ese peso. (4) **Densidad de los creadores** (`densidad_creadores` de `~/.sonorizar-sfx/datos/refs.json`, estilos con ≥ 5 videos; `max10`): elegante ~3, dinámico ~7, cinética ~16 por ventana de 10 s (antes 7/11/16); sin datos, `DENSIDAD_ESTILO`. (5) El brillo tras un impacto no entra si cae a < 0,25 s de otro sonido. Medido sobre el GO real de ESPAÑOL.mov (62 s, 60 eventos): elegante 30 → 11 SFX, dinámico 50 → 30, cinética 53 → 53; archivos distintos 19–23 → 7–10; 0 extraídos; revisión sin avisos.

**Música (v5.48, `sonido_musica`):** con `sonido_skill` encendido ahora SÍ hay música, de `02_MUSICA` de la biblioteca (mismo criterio que `musica.py` de la skill: `MOODS` y `puntuar` iguales). Carpetas: las del ánimo por las palabras del video y el pack (`carpetas_para`; «Fiesta o mar» suma fiesta y reggae chill) y, si nada encaja, las que más usan los creadores (`DE_CREADORES`: lo-fi, reggae chill, corporativa, house). En cada pista el mejor arranque EN UN COMPÁS (`puntuar`: cortes de GO y golpes whoosh/impacto/riser/glitch/flash en el beat 45 %, energía pareja 25 %, que no sea intro muda 20 %, cierre en compás 10 %); 3 opciones de carpetas distintas (`candidatos`). Medidas de cada pista: la caché de la skill (`~/.sonorizar-sfx/cache/musica`, librosa) o `bpm.py` + energía por pulso en `DaVinciSubtitles/musica_biblioteca_medidas.json`. `hornear`: tramo con fundidos 0,5 s / ~1,5 s, ducking suave (`ducking.curva_de_ganancia`, −4 dB al hablar) y −6 dB bajo la voz MEDIDO después del ducking (`sfx_rules.nivel_de_audio`; el usuario la quería así: a −20 y −11 no se oía), pico ≤ −1 dBFS; sin voz, −20 dB. Las 3 se hornean en `sound_director/<huella>/musica_biblioteca/`; la 1.ª queda elegida: `res['capas']['musica']['plan']` (GO la coloca en `AI MUSIC` con `al_colocar`, y la música de Efectos sale) y `estado['music_plan']` (lo que pone «Aplicar a Resolve»). Pistas de Kevin MacLeod: `credito` (bloque de `CREDITOS.txt` de su carpeta, CC BY 4.0 obligatorio). Preferencia `sonido_musica` (encendida por defecto). Página: tarjeta «Música» con las 3 opciones + «Sin música» (`sonido_musica.elegir` → pendiente), ▶ Escuchar, carpeta · BPM · nivel, crédito y su interruptor. Prueba (scratchpad, ESPAÑOL.mov): Fuego / Jamaican / Ocean, música 6,0 dB bajo la voz medida, cambiar de opción y «Sin música» cambian `music_plan`, `plan_para_resolve` lleva 31 SFX + 1 AI MUSIC; 6 s la primera vez.

**Pulido de la página (v5.48, el usuario eligió A + C entre 3 propuestas renderizadas con la página real):** (1) la `LineaTiempo` dibuja solo los carriles que suenan (`carriles`, `alto_total`; el alto del desplazable se ajusta en `_pintar`) y un carril **Música** (`COLOR_MUSICA`) con la onda de la pista elegida y su nombre (`_musica_linea`: la onda se lee una vez y queda en memoria); (2) el inspector ya no deja un hueco: cuadro del video 200 × 356 y **◀ Anterior · n / N · Siguiente ▶** para recorrer los sonidos; (3) textos: la música dice «Deporte · 144 BPM · debajo de tu voz, baja sola al hablar», la biblioteca solo el nombre de la carpeta, el estado no repite «cambios sin aplicar» (la pastilla de la cabecera ya lo dice; `_estado` oculta la línea vacía) y el crédito solo aparece si la pista lo pide; (4) **momentos compactos**: `TarjetaMomento` de 268 × 78 (miniatura, tipo · segundo, archivo, porqué) en vez de la foto grande de 330 px: la página queda ~250 px más corta. Los bloques de la página se arman en `bloques` y se añaden en un orden fijo. Arnés de captura con fuentes reales (no `offscreen`): ventana en x = −5000, `qt_kit.crear_app()`, la hoja de estilo del raíz con selector `#raiz` (un `background:` sin selector pisa los botones primarios).

**Pendiente:** con `sonido_skill` encendido NO se hacen la voz restaurada ni el ambiente del director (para tenerlos, apagar el interruptor de la página); los aros solo se ven si los bloques traen sus clips `k ring…`; el nivel de los SFX es fijo (−3 dB con voz), no relativo a la voz medida (la música sí lo es).
