# CineCaptions · By Cinema Productions
# 4_diseno/propuesta_sonido/100 MEJORAS - rendimiento e interfaz.md — propuesta de la pantalla Sonido sin el pad XY y 100 mejoras (rendimiento e interfaz, por pestaña).

Prioridad: **(A)** alta · **(M)** media · **(B)** baja. Todo sale de lo que hay hoy en el código y de lo que se vio al probar.

## Imágenes de la propuesta «Sonido» (sin el deslizador visual)

| Archivo | Qué muestra |
|---|---|
| `A_sonido_nuevo_modo_simple.png` | Vista normal (1900 px): biblioteca · estudio · reglas en **modo simple** + marcadores con realce |
| `B_sonido_nuevo_modo_avanzado.png` | Igual, con las **reglas avanzadas** a la vista |
| `C_sonido_nuevo_pantalla_pequena_1600.png` | Pantalla pequeña: la biblioteca pasa a una barra de categorías arriba y el estudio queda junto a las reglas |

Qué cambia respecto a la pantalla actual:
- Fuera el **pad XY** (el deslizador visual del centro) y fuera la onda. En su lugar, tres tarjetas grandes **Tono / Velocidad / Volumen**, cada una con su valor en grande, botones − y +, un deslizador fino, un reset propio y los extremos (grave–agudo, lento–rápido).
- **Ajustes rápidos** con un clic: Normal, Grave, Agudo, Rápido, Lento, Radio, Épico.
- **Reproducir** grande, y destino de envío en dos selectores claros (Insertar/Reemplazar · En el cabezal/En marcadores).
- **Favoritos** y **usados recientemente** como chips con ▶ (aprovechan el hueco que dejaba el pad).
- Columna derecha: **Reglas automáticas** (Simple/Avanzado) y **Efectos en los marcadores** con borde y color de acento.

---

## Los 10 que haría primero
1. (A) Modo de subtítulos como chip en GO (hoy el selector de modo ya no tiene dónde estar) — n.º 45.
2. (A) Arreglar el desborde de «Estilos y composición» a 1500 px — n.º 30.
3. (A) No dejar timelines temporales en el proyecto del cliente — n.º 100.
4. (A) Caché en disco de la lectura de packs `.drb` — n.º 4.
5. (A) «Instalar todas las tipografías» en un clic — n.º 51.
6. (A) Pantalla de carga inmediata al abrir — n.º 2.
7. (A) Rediseño de Sonido sin pad (estas imágenes) — n.º 73.
8. (A) Resumen previo y cancelación limpia de GO — n.º 41–42.
9. (A) Guardado de preferencias con debounce — n.º 21.
10. (A) Auditor de textos sin traducir por idioma — n.º 40.

---

## Rendimiento (1–25)
1. (A) Importar bajo demanda `numpy`, `av`, `pynput`, Argos y la IA: que solo carguen cuando se usan (el SFX Lab ya lo hace; extenderlo).
2. (A) Mostrar la ventana con el logo al instante y cargar módulos en un hilo, en vez de esperar al final de los `import`.
3. (M) Comprobar que el programa instalado arranca desde su carpeta sin re-extraerse en cada arranque; si no, pasar a modo carpeta.
4. (A) Guardar en disco (hash + fecha) lo leído de cada `.drb`: hoy leer los packs cuesta ≈1 s por consulta y ahora hay 20 `.drb`.
5. (M) Leer los packs en un hilo y mostrar tarjetas «esqueleto» mientras tanto.
6. (A) Guardar las vistas reales ya renderizadas por Resolve por hash del `.drb`; no volver a renderizar si no cambió.
7. (M) Renderizar vistas reales solo de las tarjetas visibles (perezoso al hacer scroll).
8. (M) Debounce de 150 ms en `_refrescar_vista_estilo` y `_refrescar_receta` al mover controles.
9. (M) Fondo vivo: dibujarlo a un pixmap reutilizable, limitarlo a 30 fps y ofrecer modo «Ahorro» que lo apaga.
10. (B) Omitir la entrada escalonada de tarjetas si el equipo baja de cierto fps (medirlo una vez).
11. (M) Revisar sombras y desenfoques: son lo más caro de Qt; cambiarlos por bordes y degradados pintados.
12. (M) Árbol de sonidos: cargar cada categoría solo al expandirla y contar archivos con caché.
13. (A) Cachear los últimos sonidos decodificados y procesados (`sfx_audio.cargar` decodifica en cada selección y además reproduce solo).
14. (M) Procesar tono/velocidad en un hilo, por trozos y cancelable.
15. (M) Precargar el modelo de voz en segundo plano al abrir (el usuario suele soltar un video enseguida), con un indicador.
16. (B) Motor Qwen3 en modo servidor con apagado por inactividad configurable.
17. (B) Reutilizar la sesión de `onnxruntime` de la detección de voz y usar GPU si existe.
18. (A) Todas las llamadas largas a Resolve en un hilo con avance en un archivo de estado (el patrón del taller); evita los cortes de 10 s que llegaron a colgarlo.
19. (A) Renderizar las vistas previas en lote con un solo timeline temporal y borrarlo SIEMPRE al terminar.
20. (B) Escribir los JSON de bloques sin sangría en proyectos largos.
21. (A) `_guardar_preferencias` se llama en cada clic: agrupar con debounce de 500 ms y escritura atómica.
22. (B) Proyectos recientes: leer solo la cabecera de cada archivo y paginar.
23. (M) Indexar las tipografías una vez y guardar el índice (cada consulta vuelve a leer los `.ttf`).
24. (M) El chequeo de librerías y el diagnóstico, en hilo y solo al abrir «Detalles».
25. (M) Modo `--perfil` que registre arranque, cambio de pestaña y render, para decidir con datos.

## Interfaz general (26–40)
26. (M) Barra de título numerada también en Inicio y en Ajustes, para que todo hable el mismo idioma.
27. (A) Atajos Ctrl+1…4 para cambiar de pestaña, visibles en el menú.
28. (M) Progreso global de GO en la barra lateral, visible desde cualquier pestaña.
29. (A) Modo compacto automático por debajo de 1366 px: iconos sin texto y tarjetas a una columna.
30. (A) Arreglar el desborde horizontal de «Estilos y composición» (el panel Composición queda cortado a 1500 px): ancho mínimo de la rejilla y Composición debajo cuando no cabe.
31. (B) Estados vacíos con ilustración y una acción («Suelta un video aquí»).
32. (M) Tooltips con atajo en todos los botones de icono (↺ ▶ ? ＋).
33. (B) El «?» de la barra de título abre un mini-tutorial de esa pestaña.
34. (M) Avisos tipo «toast» abajo a la derecha en vez de texto de estado en cada pantalla.
35. (M) Deshacer (Ctrl+Z) para cambios de estilo y de sonido.
36. (B) Previsualizar el tema al pasar el ratón en Ajustes › Interfaz.
37. (M) Escala de la interfaz (90–130 %) para 4K y portátiles.
38. (M) Subir el contraste de los textos grises pequeños (#8D9BB5 en 12 px no pasa AA).
39. (B) Foco visible por teclado en chips y botones, con un orden de tabulación lógico.
40. (A) Auditor que liste los textos `tr()` sin traducir en cada idioma, para que ninguna pantalla salga a medias.

## Inicio y GO (41–48)
41. (A) Resumen antes de empezar («Voy a: transcribir 2:31 · estilo X · efectos sí») con «Cambiar».
42. (A) Cancelación limpia y reanudación (guardar la transcripción por tramos).
43. (M) Pasos de GO con tiempo estimado que aprende de ejecuciones anteriores.
44. (M) Soltar varios videos = cola de proyectos.
45. (A) Chip «Modo» en GO (Normal · Dinámico · Hormozi…), porque el selector de modo ya no está en Proyecto.
46. (B) Recetas rápidas con icono, atajos 1–9, duplicar y renombrar.
47. (M) Estado de Resolve y del timeline activo siempre visible, con reconexión automática y botón «Abrir Resolve».
48. (M) Pantalla de resultado tras GO: n.º de bloques, efectos puestos, tiempo y botones «Abrir en Resolve / Ver en Creativo / Rehacer».

## Proyecto · Estilos y composición (49–60)
49. (A) Filtros por familia (Luxe, Amro, Títulos II…) y por posición (arriba/centro/abajo) en «Packs de estilos».
50. (M) Packs favoritos (estrella) y «usados recientemente».
51. (A) Un solo aviso «Faltan N tipografías» con «Instalar todas» y progreso (hoy es un aviso por tarjeta).
52. (M) Vista previa con tu propia frase en todas las tarjetas.
53. (B) Comparar dos packs lado a lado.
54. (M) Composición: restablecer por línea y presets Izquierda / Centro / Derecha con miniaturas.
55. (M) Importar `.drb`/`.drt` arrastrando, con informe previo (sets, fuentes, posiciones).
56. (B) Editor de pack: renombrar, reordenar y ocultar sets.
57. (M) Tarjeta «Fuente»: duración, fps, resolución y formato H/V detectado; la onda a una línea o fuera.
58. (A) Autodetectar H/V y preseleccionar la versión del pack, avisando si no coincide.
59. (B) La etiqueta «H·V» con tooltip: qué formatos y posiciones trae el pack.
60. (M) «Probar en Resolve»: inserta un bloque de ejemplo en el timeline y lo borra al salir.

## Creativo (61–72)
61. (A) Atajos 1/2/3 para contexto/principal/complemento y flechas para ir palabra a palabra.
62. (M) Vista del bloque en vivo con la vista real del pack elegido (no aproximada).
63. (M) Reproducir con audio y la palabra iluminándose (karaoke) para revisar de oído.
64. (M) Corrector ortográfico en línea: subrayado y clic para corregir.
65. (B) Buscar y reemplazar en todas las palabras.
66. (M) «Marcar con IA»: mostrar por qué se eligió cada palabra clave y pedir otra.
67. (B) Buscador de emojis con recientes y sugerencia por sentimiento.
68. (M) Selección múltiple y arrastre para pintar rangos.
69. (A) Autoguardado continuo de la sesión y restauración tras un cierre inesperado.
70. (B) Dividir y unir bloques con un clic.
71. (M) Mapa de bloques por rol (franja con zoom) en lugar de una onda.
72. (B) Comparar «antes / después» de la IA.

## Sonido (73–90)
73. (A) Quitar el pad XY y usar tarjetas con pasos ± y reset por control (imágenes A, B y C).
74. (M) Ajustes rápidos editables y guardables por el usuario.
75. (M) Favoritos y recientes dentro del estudio.
76. (A) Barra espaciadora = reproducir/parar; flechas ↑↓ recorren la lista con vista previa.
77. (M) Normalizar el volumen de la biblioteca (LUFS) para que el modo simple suene parejo, y un medidor numérico.
78. (M) Etiquetas por sonido (corto/largo, grave/agudo, «UI», «impacto») con filtros en chips.
79. (A) Modo simple: de 1 a 4 sonidos, orden secuencial o aleatorio y «cada N bloques».
80. (M) Modo simple: sacar a la pantalla la separación mínima entre efectos (hoy 0,25 s en el JSON).
81. (M) Simulador «así sonaría» con 5 bloques de ejemplo.
82. (M) Modo avanzado: editor visual de reglas (activar, ordenar, probar) en vez de abrir `sfx_rules.json`.
83. (M) Marcadores: leer los colores reales del timeline de Resolve y mostrar el conteo («3 azules») antes de colocar.
84. (B) Marcadores: botón «Escuchar» por color.
85. (A) Colocar con vista previa (qué se pondrá y dónde) y deshacer.
86. (B) Elegir número y nombre de la pista de audio SFX y el volumen por categoría.
87. (M) Bajar unos dB la música bajo cada efecto (opcional).
88. (B) Importar paquetes `.zip` de sonidos y detectar duplicados por hash.
89. (B) Recortar y fundir el sonido con dos números (sin onda).
90. (B) Exportar/importar el «perfil de sonido» (modo, sonidos, mapa de marcadores).

## Ajustes, instalador y mantenimiento (91–100)
91. (M) Instalador: tamaño y espacio necesario, y casilla «motor de IA (opcional)» para aligerar el peso.
92. (M) Actualizaciones diferenciales en lugar de reinstalar 185 MB.
93. (M) Comprobar la integridad (hash) de packs, fuentes y sonidos al arrancar, con botón «Reparar».
94. (B) Copia de seguridad semanal automática y restauración con vista de contenido.
95. (M) Licencia: días restantes y botón «Gestionar»; aviso 7 días antes de que caduque la verificación sin conexión.
96. (M) «Enviar reporte» con el log y el diagnóstico (sin datos personales) y vista previa de lo que se envía.
97. (B) Modo portátil opcional (carpeta, sin instalar).
98. (B) Mac: probar el puente y el atajo global (⌘↩) y empaquetar notarizado.
99. (M) Pruebas de regresión visual: capturas comparadas por pestaña y un script único que lance todas las comprobaciones antes de compilar.
100. (A) Que ningún proceso deje timelines o bins temporales en el proyecto del cliente: prefijo común y limpieza al cerrar (hoy queda «RCS · temporal…» en el proyecto «6»).
