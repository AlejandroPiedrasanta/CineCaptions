# Auditoría del flujo real (v5.8)

Recorrido de una persona que quiere subtitular un video: **Inicio → Proyecto → Creativo → Generar → Resolve**.
Se revisó qué decide cada pantalla, si lo que se ve es lo que sale, y qué controles no aportaban nada.

## Lo que encontré (inconsistencias)

| # | Dónde | Problema | Causa real |
|---|---|---|---|
| 1 | Proyecto · «Composición del bloque» | Parecía no hacer nada | El estilo (pack) ya trae la posición exacta de las 3 líneas; la rejilla 3×3, AUTO, Altura y Horizontal solo son un **retoque** sobre eso, y estaban a la vista como si fueran obligatorios |
| 2 | Proyecto | Un desplazamiento olvidado movía todo | La preferencia guardaba `altura -5 %, horizontal +1 %` sin ningún aviso: **todos los bloques salían movidos** y Creativo no lo reflejaba |
| 3 | Proyecto | Un «Usar solo este estilo» se quedaba pegado | La pref `estilo_fijo` guardada (valor 1) forzaba el estilo 1 en TODOS los bloques sin que se notara (el pack tenía 3) |
| 4 | Creativo | No decía qué estilo del pack llevaba cada bloque | El reparto de los 3 estilos se sorteaba **dentro de Resolve** (semillas distintas en Studio y Free): ni la app ni tú podían saberlo, y el mismo video salía distinto en cada versión |
| 5 | Creativo · «Así se verá este bloque» | No reflejaba lo elegido en Proyecto | Dibujaba siempre la primera variante, sin posición y sin el ajuste fino |
| 6 | Creativo · «Ajustes del bloque» | Nombre confuso | Solo contiene «Palabras por línea» (máximo por línea) |

## Lo que cambié

1. **La app decide el estilo de cada bloque** (`estilos_bloque.py`): la rueda de siempre (sin repetir dos seguidos), el estilo fijo, o el que tú elijas a mano. Se escribe en el bloque (`estilo`) y los dos scripts de Resolve (`CineCaptions.py` y `CineCaptions_Subtitulos.lua`) lo respetan → Studio y Free dan lo mismo, y lo que ves es lo que sale.
2. **Creativo** (al pasar el cursor / tocar un texto): debajo de «Así se verá este bloque» aparece «Estilo 2 de 3 · Oro · automático» con botones para cambiarlo en ese bloque (o volver a Automático), y un cuadrito del video con **dónde cae** (arriba/centro/abajo), que ya incluye el ajuste fino de Proyecto. La vista previa usa el estilo asignado.
3. **Proyecto**: la tarjeta pasa a llamarse «Estilo del bloque» y deja a la vista solo lo que se usa de verdad (estilos, ‹ ›, miniaturas, vista previa, «Usar solo este / Alternando», icono arriba/abajo). Una línea de estado dice si los estilos **se alternan** o si **todos usan solo el estilo N**.
4. **Ajuste fino (avanzado)**: la rejilla 3×3, AUTO, Altura, Horizontal, Aplicar al timeline y Restablecer quedan plegados. Si hay algo distinto de la plantilla, el enlace se pone ámbar y dice qué (`con cambios: altura −5 %, horizontal +1 %`), así no se olvida.
5. «Ajustes del bloque» → «Tamaño del bloque» (solo es el máximo de palabras por línea).
6. Traducciones (en/de/fr/pt/it) y documentación actualizadas.

## Flujo resultante

1. **Inicio** – GO: hace todo con el pack elegido.
2. **Proyecto** – eliges el pack; los 3 estilos se alternan (o fijas uno). El «Ajuste fino» solo si quieres retocar posición.
3. **Creativo** – pintas roles (arriba/principal/abajo); al tocar un texto ves su estilo y su posición; lo cambias solo si no te gusta.
4. **Generar** – se escribe el manifiesto con el estilo de cada bloque → Resolve lo coloca tal cual.

## Pendiente / a tener en cuenta

- Los presets Gold/Matrix/Water de Amro aún no están convertidos a clips de Resolve.
- El Tilt del mini-cuadro es aproximado (usa el Tilt del pack, no renderiza).

## Prueba de punta a punta (GO real contra Resolve)

Voz sintética en español → GO (transcripción en GPU, roles, SFX, emojis, colocar en Resolve) en un timeline temporal que se borró después; dos pasadas seguidas con packs distintos (Viral · superior / inferior, Base títulos dinámicos), y el flujo Creativo (cambiar el estilo de un bloque → Generar → Resolve). Resultado: ~55 s por pasada, 0 errores en el registro, CTX/MAIN/CMP/EMOJI/SFX colocados, el estilo elegido a mano llega al JSON y al sidecar .lua.

| # | Hallazgo | Arreglo |
|---|---|---|
| 7 | **Volver a generar apilaba otra pista de emojis** (los animados `e_[0001-NNNN].png` no se reconocían como «nuestros», así que la pista se consideraba ajena) | `_es_clip_texto_nuestro` (py) / `es_clip_texto_nuestro` (lua) reconoce las secuencias de `emojis_secuencia` |
| 8 | El ajuste fino olvidado (−5 % altura, +1 % horizontal) y el «Usar solo este» se aplicaban en GO sin verse | Chips ámbar en Inicio «Posición ajustada ✕» y «Solo el estilo N ✕» (un clic los quita; se refrescan al tocarlos en Proyecto) |
| 9 | El log decía «Aviso: salió el mismo set dos bloques seguidos» aunque lo hubieras elegido tú o fuera estilo fijo | Con estilo decidido por la app (`cue.estilo`) ya no cuenta como aviso |
| 10 | Color de variante en lista RGB (packs antiguos) rompía el dibujo del cuadrito de posición | `_color_de_variante` acepta `#RRGGBB` y `[r,g,b]` |
| 11 | Subtítulo de Proyecto aún hablaba de «alinear las líneas» | «…y mira cómo queda cada estilo en tu bloque» |

## Segunda pasada: lo que había quedado pendiente, corregido

| # | Pendiente | Corrección |
|---|---|---|
| 12 | Con «Palabras por línea 1·1·1» el bloque acababa en un artículo («cómo multiplicamos las \| ventas») | `dynamic_subtitles.grupos_estrictos` recorta del complemento las palabras colgantes del final (conectores, preposiciones, demostrativos, numerales); abren el bloque siguiente («cómo / multiplicamos \| las ventas»). Mismos grupos, mismo número de bloques con apoyo; 0 complementos colgantes en las pruebas (1·1·1, 2·1·2, 3·1·3, 1·1·2) y 3 000 casos de fuzz sin violaciones |
| 13 | Un timeline temporal de «vista real» podía quedar como el actual si el programa/Resolve se cortaban a medias | Se anota el timeline previo (`vista_previo.json`); el siguiente trabajo (GO, generar, vistas) lo restaura y borra el temporal. Probado en Resolve real |
| 14 | El script `.lua` (Resolve Free) no se había podido ejecutar | Se ejecutó en Resolve Studio con `fuscript -l lua` sobre el mismo manifiesto y se comparó ítem por ítem con el `.py`: texto, SFX, composición idénticos. **Hallazgo:** el `.lua` no traía los emojis animados (ponía PNG fijos); portado (importar secuencia, bucle, entrada/salida). Ahora las 9 pistas coinciden exactamente, incluida la expresión de la animación. En Free 21.1 (sin `io`) las secuencias van en bucle pero sin rebote |
| 15 | No había guía para quien abre el programa por primera vez | **Recorrido visual** de 14 pasos por toda la interfaz (ver abajo) |

## Estilo «guion» (REFERENCIA.mp4), planificador, banco de pruebas y MCP (v5.9)

**Qué pasaba:** con el flujo de 3 líneas (contexto / principal / complemento por bloque) salía texto antes y después de la palabra grande y nada cuadraba con la referencia, porque la referencia es OTRA estructura: cada palabra es su propio clip, con su estilo, su sitio y su momento.

**Qué se hizo:**
- Pack «Referencia» (8 estilos: Impacto cian, Editorial rosa/azul, Moderno blanco y los presets de Amro Highlight/Fire/Strike/Underline) incorporado al programa; sus clips van centrados y es el script quien los coloca.
- Estilo «guion» en los dos scripts de Resolve (py y lua idénticos: 50 clips, 0 diferencias de inicio, duración, Pan, Tilt, zoom, texto y pista).
- Replica EXACTA de la referencia (`guion_referencia.cues_de_la_referencia`): posiciones ±0,5 %, anchos ±1 %.
- Planificador automático para cualquier video (`guion_planificador`), validado contra la referencia: 12/13 palabras grandes, 13/15 cortes de bloque.
- GO: ya usa los packs del usuario y los de estilo «guion» (antes `_plantilla_un_clic` llamaba a `plantillas.packs_usuario`, que no existe, y los ignoraba).
- Banco de pruebas (`banco_pruebas.py`) y servidor MCP (`mcp_cinecaptions.py`, `.mcp.json`): transcribir, planificar, colocar, renderizar, comparar y medir sin tocar tu timeline.

**Trampas encontradas:** (1) el macro oculta el texto si entrada + salida > duración del clip: se fijan en 0,14 / 0,10 s; (2) una palabra más ancha que el comp se recorta antes del zoom: el planificador solo usa estilos donde cabe; (3) «Luxe Shine» refracta lo que tiene debajo: grandes en pistas inferiores; (4) el render borra lo que empiece por su nombre.

**Pendiente / a tener en cuenta:** solo vertical (el pack es vertical); sin SFX ni emojis en este estilo todavía; los degradados, brillos y destellos de la referencia son del macro y no son idénticos; el planificador acierta la mayoría de las palabras grandes pero no todas (se corrigen pintándolas en el editor o con `mains=` por MCP).

## Recorrido visual

Capa sobre toda la ventana: oscurece el resto, ilumina la zona del paso con un halo que late (el foco sigue a la zona si se desplaza o cambia de tamaño) y pone al lado una tarjeta con el título, la explicación y Atrás / Siguiente. Pasos: bienvenida · barra de navegación · GO · opciones bajo GO · audio · pack de estilos · Crea tu estilo · Vista real · Estilo del bloque · Creativo · Sonido · estado · Ajustes · fin. Teclado: → / Intro / Espacio siguiente, ← atrás, Esc salir.

- Sale solo la primera vez que se abre el programa (cuando no hay licencia pendiente, trabajo en curso ni diálogos).
- **Ajustes → Recorrido guiado** (panel rápido del engranaje y pestaña Interfaz): interruptor para desactivarlo (al reactivarlo vuelve a salir la próxima vez) y «Ver el recorrido ahora». Dentro del recorrido, «No volver a mostrar este recorrido» también lo desactiva.
- Traducido a en / de / fr / pt / it (se comprobó que ninguna tarjeta se corta ni sale de la ventana).

## Pendiente / a tener en cuenta

- Los presets Gold/Matrix/Water de Amro aún no están convertidos a clips de Resolve.
- El Tilt del mini-cuadro es aproximado (usa el Tilt del pack, no renderiza).
- Abrir «Proyecto» con Resolve conectado renderiza solas las vistas reales que falten (crea un timeline temporal); durante el recorrido se aplaza hasta que termina.
