# Editor Creativo (palabras, Asistencia, Generar)

## editor-palabras — Editor de palabras (pintar roles)

**Qué:** Editor de palabras (pintar roles)

**Dónde:** script principal · `class WordTagWindow`, `_poner_rol`, `_actualizar_contador_pronto`, `_bloques_actuales`; lienzo: `class LienzoPalabras`

## creativo-ui — Editor Creativo: barra, tarjeta, play, Asistencia, Generar

**Qué:** Editor Creativo: barra, tarjeta del párrafo, play, panel de avance (Asistencia / Generar)

**Dónde:** `editor_ui.py` · `BarraHerramientas`, `MarcoPapel`, `ControlTamano`, `BotonPlay`, `PanelAsistencia`; flujo Generar: script principal · `_receta_generar`, `_gen_abrir`, `_gen_fase`, `_gen_fin`, `_regenerar_marcas`

## nota — CREATIVO v5.7b

CREATIVO v5.7b: se quitó «Peso de conectores»: dyn.normalizar_peso_conector() devuelve SIEMPRE 1.0 (palabra por palabra). Los máximos Arriba/Principal/Abajo se reajustan EN VIVO (WordTagWindow._on_tamanos_change -> _reajustar_en_vivo, debounce 90 ms) si los roles son de la IA (_roles_auto; cualquier marca a mano lo apaga: aparece «Reajustar con IA»). _calcular_alternativas = las 4 versiones de la IA con los máximos actuales (usa el análisis cacheado _ia_cache: instantáneo); selector «Versión de la IA» 1-4. Todo con deshacer (un solo Ctrl+Z por tanda de clics).

## nota — v5.7 · Creativo

v5.7 · Creativo (párrafo): el lienzo (LienzoPalabras) es transparente y vive en editor_ui.MarcoPapel (tarjeta de esquinas redondeadas); cada frase se dibuja en su panel redondeado con la hora en pastilla (_paneles/_pastillas en dibujar). editor_ui.PistaPincel dice qué hace el pincel elegido (_actualizar_pista_pincel). «Capitalizar palabras de contenido» está en la barra de herramientas, junto a ✕ Emojis.

## nota — v5.7 · «Marcar con IA» ahora se llama «Asistencia»

v5.7 · «Marcar con IA» ahora se llama «Asistencia» (chip del editor, diálogo, avisos y traducciones en 2_recursos/locales). Su diálogo es editor_ui.PanelAsistencia: orbe animado + 4 pasos reales (estado['fase'] lo pone el hilo de _sugerir_con_ia) + barra; al acabar muestra «Listo» 650 ms. El deslizador de tamaño del párrafo (editor_ui.ControlTamano, junto a «Capitalizar») llama a WordTagWindow._poner_tam_letra (aplica con 45 ms de debounce y guarda a los 700 ms).

## nota — v5.7 · «Generar» del editor

v5.7 · «Generar» del editor (WordTagWindow._continuar -> SubtitleApp._sesion_editor -> _receta_generar): aplica la receta de GO (efectos según el
interruptor «Efectos» de Inicio = pref go_sfx; los emojis son los de las palabras) y abre un popup (editor_ui.PanelAsistencia con los pasos armar /
sfx / emojis / colocar). El avance es REAL: el hilo manda ('gen_fase', clave) por msg_queue; _colocar_en_resolve marca «colocar»; 'colocado_en_resolve',
'error' o un fallo lo cierran (_gen_fin). «Editar marcas y regenerar» (_on_update) ya no genera en el hilo de la interfaz: _regenerar_marcas corre en un hilo.
Archivos: archivos_seguros.py (escritura atómica + cerrojo; preferencias, marcas con .bak, proyectos, manifiestos). Nada de write_text() directo para estado del usuario.
Regla: ninguna llamada a resolve_mcp/resolve_bridge que espere a Resolve (modo_actual() sin pasivo, disponible(), estado()) en el hilo de la interfaz: usar correr_en_hilo.
