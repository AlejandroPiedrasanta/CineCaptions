# Bloques de subtítulos (cerebro, estilo por bloque, pausas)

## bloques — Cerebro de bloques

**Qué:** Cerebro de bloques

**Dónde:** `dynamic_subtitles.py`, `composicion.py`

## anim-cortos — Fix de animación de textos cortos

**Qué:** Fix de animación de textos cortos

**Dónde:** `dynamic_subtitles.py` · `proteger_animaciones` (marca `salto_anim`); lo leen `resolve_scripts/CineCaptions.py` y `CineCaptions_Subtitulos.lua` (mantener los dos gemelos iguales)

## estilo-bloque — Estilo (variante del pack) de cada bloque

**Qué:** Estilo (variante del pack) de CADA bloque: la app lo decide, Creativo lo enseña y se puede cambiar

**Dónde:** `estilos_bloque.py` · `asignar`, `orden_de_variantes` (gemela de la rueda de los scripts de Resolve); script principal · `_estilos_de_bloques`, `WordTagWindow._asignar_estilos/_pintar_estilo_bloque/_poner_estilo_de_bloque`; `editor_ui.MiniPosicion`; Proyecto: `ComposicionWindow` («Estilo del bloque», `fino_w` = Ajuste fino plegado, `modo_estilos_lbl`) **ya NO se muestra** (v5.11, a petición del usuario: `COMPOSICION_VISIBLE = False` en el script principal; el estilo de cada bloque se elige en Creativo; `estilo_fijo()` devuelve 0 sin la tarjeta, así un «Usar solo este» viejo no manda a escondidas; `emoji_posicion` guardado sigue valiendo). Auditoría en `DOCUMENTACION/historial/AUDITORIA_FLUJO.md`

## colgantes — Bloques que no acaban en artículo/preposición

**Qué:** Bloques que no acaban en artículo/preposición

**Dónde:** `dynamic_subtitles.py` · `COLGANTES`, `es_colgante`, `EVITAR_COLGANTES` (se recorta la cola del complemento en `grupos_estrictos`; esas palabras abren el bloque siguiente)

## nota — ESTRUCTURA POR PAUSAS

3b) ESTRUCTURA POR PAUSAS (v5.5)
   Una FRASE (lo que va entre dos pausas > 0,45 s o signos) se arma ENTERA en un solo bloque: arriba / principal / abajo,
   aunque pase de "Palabras por línea" (hasta el doble de arriba y abajo). El bloque se queda en pantalla hasta la
   pausa, y ahi se arma otro. Nada se borra a media frase. Las líneas entran una tras otra siguiendo el audio.
   Se apaga con la preferencia armar_por_pausas = false (vuelve a grupos exactos).

## nota — PALABRAS POR LINEA

PALABRAS POR LINEA (Creativo > Ajustes del bloque): Arriba/Principal/Abajo son topes ESTRICTOS en todo: la IA/sugerencia (dynamic_subtitles.grupos_estrictos ya no deja pasar el doble por «armar por pausas»), ✨ Completar (grupo_alrededor) y el armado final y la vista (build_manual_cues(tamanos=, peso_conector=): una linea no pasa del tope contando los conectores segun «Peso de conectores»; el resto de las palabras abre otro bloque, sin perder ninguna).

## nota — v5.8 · Auditoría del flujo

v5.8 · Auditoría del flujo (ver DOCUMENTACION/historial/AUDITORIA_FLUJO.md): el estilo (variante del pack) de cada bloque lo decide la APP con estilos_bloque.asignar (rueda sin repetir, estilo fijo o el que el usuario eligió en Creativo para ese bloque, guardado en palabras[primera palabra]['estilo']) y se escribe en b['estilo']; _estilos_de_bloques lo llama antes de st.write_dynamic (GO y Generar) y los dos scripts de Resolve (CineCaptions.py y CineCaptions_Subtitulos.lua) lo respetan en modo_plantillas; sin él (manifiestos viejos) usan su rueda. Creativo (WordTagWindow) llama a la misma asignar en _bloques_actuales, así que «Así se verá este bloque» enseña el estilo que saldrá, con su etiqueta, botones para cambiarlo y el cuadro editor_ui.MiniPosicion (dónde cae; incluye altura/horizontal/layout de la composición). En Proyecto, «Composición del bloque» pasó a «Estilo del bloque»: lo de alineación/altura/horizontal/aplicar quedó plegado en «Ajuste fino (avanzado)» (ámbar y con el detalle si hay cambios) y una línea dice si los estilos se alternan o si hay uno fijo (pref estilo_fijo).

## nota — v5.8 segunda pasada de la auditoría

dynamic_subtitles.grupos_estrictos recorta del complemento las palabras colgantes del final (es_colgante: conectores, preposiciones, demostrativos, numerales) sin cambiar qué grupos se eligen; la palabra recortada abre el bloque siguiente.
