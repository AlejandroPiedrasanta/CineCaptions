# Estilo «VIRAL» (subtítulos virales: pila fina + negrita cursiva y tres efectos)

## viral-planificador — Planificador y geometría

**Qué:** Estilo nuevo e independiente (carpeta «ESTILO VIRAL» del usuario, 4 videos de referencia). Cada frase es una **pila de líneas**; cada palabra es su propio clip y entra cuando se dice:
`v fina` (palabra de enlace), `v negrita` (la palabra con peso, cursiva) —el «ESTILO VIRAL 3», «Hey / Did You Hear / About The / Bakery»— y, en un bloque de cada dos, la palabra clave sola y grande con un
**efecto** que rota (select → shatter → drag; si el que toca no cabe en el tiempo del bloque se prueba el siguiente): `v shatter` (azul cielo con barrido de luz que se rompe como un vidrio quebrado en 9 fragmentos, «ESTILO VIRAL 1»), `v select` (se escribe, un cursor la selecciona y se dibuja una caja roja punteada, «2») o `v drag` (una mano arrastra su contorno
punteado y se rellena de blanco con brillo, «4»). Con GO decide solo; en **Creativo**, las palabras pintadas «Principal» llevan efecto y, si hay alguna, SOLO ellas (el resto es pila). Lleva **sonidos** (un evento por palabra)
y **emojis** (con la palabra clave) como el estilo «guion». Mismo contrato de bloques que Kinetic: viral y kinetic comparten `_generar_con_kinetic` (`Pack.kinetic` es True también para VIRAL; `Pack.viral` los distingue).

**Dónde:** `1_codigo/viral_planificador.py` · `planificar(palabras, idioma, ancho_tl, alto_tl, ancla, mains, efectos, fin_video, cada)` → `{'cues','plan'}`; `armar_bloque` (líneas finas repartidas por igual, negritas, efecto),
`_bloques_con_tiempos` (tiempos y cierres: nunca solapa bloques; un efecto no se corta: antes se retrasa el siguiente ≤ 0,4 s), dos pasadas: un efecto que se queda sin su tiempo mínimo (`MINIMO`) baja a shatter o a pila;
`unir_fragmentos` (pega «$15» «000» → «$15,000» y «full» «-time» y recuerda los índices ORIGINALES: las marcas de Creativo cuentan sobre la lista original). Reutiliza `guion_planificador` (frases, puntajes) y
`kinetic_planificador._heroe`. Geometría `1_codigo/viral_captions.py` · `apilar` (filas centradas, palabras alineadas por la base; `SOBRESALE` deja sitio a la caja de select y a la mano de drag), `construir_cues`,
`K_PX = 691` (px del em por unidad de Size con Inter: ~8 % más que el 640 de Kinetic; medido con «HHHH»). JSON `{language, cues:[{start,end,plantilla,caja,lines,runs:[{k,texto,t,fin,x,y,size}]}]}` (el mismo que lee `place_kinetic_track`).

## viral-pack — El pack VIRAL y sus comps de Fusion

**Qué:** `2_recursos/plantillas_incluidas/VIRAL/` (`pack.json` con `"guion": "viral"`; `VIRAL vertical.drb` y `VIRAL horizontal.drb` con 5 clips cada uno —las mismas comps con las medidas de un cuadro 1080×1920 o 1920×1080—; `vista/` con 5 fotogramas reales sobre negro). Es pack «de fábrica» (`plantillas.FABRICA`: no se quita). Cada clip lleva un Text+ «Template» (la app le escribe
`StyledText` y `Size`) y su animación de entrada/salida dentro de la comp (salida por `comp.RenderEnd`). Tipografía: Inter 18pt Medium (fina), Inter 28pt ExtraBold con `ShearX` (negrita cursiva sintética: vale en cualquier equipo),
Inter 28pt Black (efectos); las trae `2_recursos/fonts`.

**Dónde:** `2_recursos/generador_packs/` · `pack_viral.py` (construye los dos .drb clonando un clip de `Referencia vertical.drb`, como Kinetic), `viral_elementos.py` (los 5 elementos; `todos('v'|'h')`, `configurar`), `viral_comps.py` (polígonos),
`viral_lab.py` (comps de laboratorio; `pack_viral.py --lab` las añade como «v lab …»). Al cambiar una comp: `python 2_recursos/generador_packs/pack_viral.py`, subir `plantillas.REVISION_BIN['VIRAL']` y rehacer la vista
(`python 1_codigo/hacer_vista_viral.py`).

**Hallazgos de Fusion (Resolve 21.1.1), medidos con renders reales:**
- Una **expresión que falla NO avisa: el clip sale NEGRO y opaco.** `string.len(...)` y `#...` fallan (GetInput da None); valen `math.*`, `time`, `comp.RenderEnd`, `Nodo.Size`, `Nodo.Output.DataWindow`, `comp:GetPrefs(...)`.
  Para comprobarlas sin renderizar: `item.ImportFusionComp(ruta)` + `herramienta.GetInput('Entrada', fotograma)` (None = error).
- **Write On** del Text+ = `Start`/`End` (0-1). El nº de letras se estima por el ancho de un Text+ «Medida» (sin Write On) dividido por el ancho medio de una letra (`0.62 em`).
- **Contorno y caja punteados son nativos:** `ElementShape` 0 relleno · 1 contorno de letra · 2 relleno del borde · 3 contorno del borde; `LineStyle` 0 sólido · 1 guion · 2 punto; `Level` 0 texto · 1 línea · 2 palabra · 3 carácter;
  `ExtendHorizontal/Vertical` = margen del borde (en unidades del cuadro, no del texto). `Shear{n}` (ShearX) inclina un elemento.
- **Polígonos:** `PolylineMask` cuya entrada `Polyline` sale de un `BezierSpline` con `KeyFrames[0].Value = Polyline { Closed = true, Points = {…} }` (un `PolylineStroke` a mano carga pero renderiza negro). Coordenadas de la máscara: X en
  fracción del ancho, **Y en fracción del alto**, centro = (0, 0): para no deformar, y × (ancho/alto).
- `Transform`: `Center` es una traslación (déjalo en 0,5/0,5) y `Pivot` solo ancla el escalado/giro: para crecer desde una esquina basta `Pivot` = esquina. `EffectMask` de un Transform reemplaza solo dentro de la máscara (franjas del glitch).
- `Rectangle/EllipseMask`: Height es fracción del ALTO, Width del ANCHO. `Text+.Output.DataWindow` = {izq, abajo, der, arriba} en píxeles, y hacia arriba.
- Una animación larga se COMPRIME en el tiempo si el clip dura poco (`tt()`: hasta ×2), así el efecto llega a su estado final aunque la palabra se diga deprisa.

## viral-app-resolve — Enganche en la app y en Resolve

**Qué:** GO y Generar usan el estilo si el pack elegido es VIRAL (chip «Estilo» de Inicio: «VIRAL · subtítulos virales»; tarjeta en Proyecto con su vista incluida).

**Dónde:** app: `_generar_con_kinetic` (rama `es_viral`: `viral_planificador` / `viral_captions`, pref `viral_ancla` alto|medio|bajo, por defecto bajo, `track['clip_prueba'] = 'v fina'`, y emojis + sonido de emojis),
`plantillas.Pack.viral`, `estructura_de` (`viral: True`), `REVISION_BIN['VIRAL']`. Resolve: `place_kinetic_track` (py) = `place_kinetic` (lua) — el MISMO colocador que Kinetic, ya generalizado: `preparar_pack_kinetic(…, clip_prueba)`
(el clip que prueba que el bin está completo; por defecto «k hero blanco»), `_grupo_kinetic` (prefijo «v »), y emojis si el cue trae `emoji` (como `place_guion_track`). Pistas `ES-K1…`.

## viral-pruebas — Cómo probarlo

**Qué:** Prueba de punta a punta sin tocar el video del usuario: palabras con tiempos → plan → Resolve (timeline temporal `zz_BANCO`) → render → hoja de cuadros; y la misma generación DENTRO de la app, sin Resolve.

**Dónde:** `1_codigo/probar_viral.py` (`elementos`, `calibrar`, `video <media>`, `lab`, `cues`; siempre limpia el banco al acabar), `probar_viral_app.py <palabras.json> [--marcar 8,24] [--sin-sfx]` (SubtitleApp sin pantalla y sin Resolve:
GO/Creativo, sonidos y emojis), `hacer_vista_viral.py`. Las palabras de un video salen del MCP `transcribir` (`~/DaVinciSubtitles/mcp/palabras_<video>.json`). **No usar `go_real` mientras el usuario trabaja en Resolve:** el GO real cierra su proyecto
y crea «CineCaptions N» (el 2026-10-08 hubo que restaurar el proyecto y borrar el de prueba). `banco_pruebas.renderizar` solo borra los trabajos de render de SU carpeta.

## Medidas y trampas de tamaño

- `Size` de Text+ es relativo al ANCHO del cuadro: em = `Size × 0,6397 × ancho` px (691 px a 1080 de ancho) con Inter, tanto en vertical como en horizontal (comprobado con «HHHH» en 1080×1920 y 1920×1080).
- Las alturas de mayúsculas de `viral_planificador.CAP` son fracciones del «lado de referencia» (`lado corto × 16/9`): el texto mide los mismos píxeles en vertical y horizontal (47 px de mayúsculas la palabra fina, 78 la negrita, 138 el efecto a 1080 de lado corto).
- El log de Resolve no se puede leer (regla de permisos): para saber por qué una comp sale negra, bisecta con clips mínimos (`viral_lab.py`) y `GetInput`.
- `ImportFusionComp` sobre un clip que YA tiene una comp la SOBRESCRIBE (no crea otra) y `DeleteFusionCompByName` no borra la comp activa: los laboratorios solo se hacen sobre clips del banco `zz_BANCO`.

## El Shatter (vidrio quebrado) — cómo está hecho

Azul cielo (degradado + brillo fijo en la mitad de arriba) → fundido → **barrido de luz** (RectangleMask inclinada de borde suave, rellena de blanco y compuesta con `Operator = Atop` solo sobre las letras) → a los 12 fotogramas
la palabra se rompe en 9 fragmentos. Los cortes son un ÁRBOL (`ARBOL` en `comp_shatter`): cada corte es un semiplano (una RectangleMask enorme girada unos grados: bordes de esquirla) y cada hoja es la intersección de los
semiplanos de su camino; cada fragmento se RECORTA antes de moverse (un Transform con EffectMask dejaría colarse las letras vecinas) y se desliza, gira un poco y cambia de tono (facetas). El ancho de la palabra sale de un Text+ «Medida».
Probado y descartado: un «filo claro» con `ErodeDilate` + `Held Out` (lavaba todo el color). El tiempo se comprime (`tt(28)`) en clips cortos.

## viral-colores — Colores de los efectos (v5.4.13, sin compilar)

Cada efecto del pack VIRAL tiene 4 colores (`viral_captions.COLORES`): **Shatter** azul cielo (el de siempre) / `rosa` / `lima` / `oro` (`viral_elementos.PALETAS_SHATTER`: degradado, base, bisel, halo, brillo y luz del barrido), **Select** caja roja / `azul` / `verde` / `naranja` (`CAJAS_SELECT`), **Drag** blanco / `amarillo` / `cian` / `rosa` (`TINTES_DRAG`: relleno y contorno punteado; la mano sigue blanca). Los clips se llaman «v shatter rosa»… (14 clips por formato); la geometría es la del efecto base (`base_de`). `viral_planificador.planificar` rota por aparición de cada efecto (la 1.ª vez el de siempre) y `REVISION_BIN['VIRAL'] = 'Vir 2'`. Las 5 comps de antes salen IDÉNTICAS (comprobado byte a byte contra el .drb anterior). Pendiente: verificarlas en Resolve con `probar_viral.py video <palabras.json>` en un video con ≥ 5 efectos (sólo se probó el planificador y que las comps se generen bien formadas).
