# Verificación aislada de la página Sonido — 21 de octubre de 2026

Se ejecutó el arnés existente `1_codigo/herramientas_dev/probar_pagina_director.py` con `6_compilacion/venv315/Scripts/python.exe` mediante `verificar_aislado.py`, que llama a su `main()` con `--salida` y el video de muestra existente. Resultado: **48/48 comprobaciones pasan**, salida 0, 62,5 segundos para el arnés.

El video fue `PRUEBA ESPAÑOL.mp4`, disponible en Desktop/VIDEOS EN ESPAÑOL. Se reutilizaron las 182 palabras de su transcripción ya existente, leídas una vez en memoria. No se generó una nueva transcripción.

## Aislamiento

`probar_director_sonido.entorno()` ya desvía preferencias a memoria, Registro a una lista y estado del director a la salida. No desvía por sí mismo la caché de `efectos_visuales`. El wrapper añade un home virtual y TEMP/TMP/APPDATA/LOCALAPPDATA dentro de esta carpeta antes de importar los módulos de negocio. De esa manera, efectos_cache, efectos_plan y otras rutas derivadas del home no apuntan a los datos reales del usuario. No se modificó código de producción. Se desactivó la escritura de bytecode.

Los métodos de ejecución de Resolve se bloquearon antes de importar el arnés. Su aplicación en la página se simula como establece el propio arnés. Se registraron **0 intentos de ejecución real en los métodos vigilados**. La salida «en Resolve» de estas pruebas es simulada; no es evidencia de una escritura en la aplicación.

## Qué cubren las 48 comprobaciones

Resumen y notas de estado; retocar un evento sin cambiar los demás; silenciar y restaurar; acortar y regenerar; bloqueo preservado al rediseñar; rediseñar una sección; controles de densidad y prioridad de voz; restaurar valores Auto; órdenes reconocidas y frases no reconocidas; dos mezclas A/B de igual duración y con diferencia de señal; plan para Resolve y rechazo sin un GO compatible; carga de la página en hilo; selección de sonidos solapados; inspector; estados simulados de sincronización y aplicación; estado vacío; apertura de la nueva página desde `_asegurar_sfx`.

No comprueban la calidad perceptiva del sonido, reproducción audible, un Resolve real ni toda la ventana de la aplicación.

## Capturas con el contenedor real de desplazamiento

Además de las capturas nativas de 1240×1500 del arnés, el wrapper monta `PaginaDirector` con `Desplazable`, los márgenes 40/86/28/22 de `_nueva_pagina('sfx', con_barra=False)` y el resumen ya calculado. Selecciona un evento sin invocar acciones de audio ni Resolve. Se excluyen la navegación y otras capas externas de la ventana completa.

| Marco | Página de contenido | Viewport del scroll | Recorrido vertical |
|---|---:|---:|---:|
| 1240×900 | 1150×1299 | 1162×792 | 519 px |
| 1000×720 | 910×1314 | 922×612 | 714 px |

El mínimo indicado por Qt para la página con un evento seleccionado es 778×1299. A 1000×720, el contenido termina usando 1314 px de alto por el ajuste del texto. No hay desplazamiento horizontal en estas dos anchuras.

Al inicio, la línea de sonido empieza en y=789 dentro del viewport. A 1240×900 apenas intersecta los 3 px inferiores del área desplazable; a 1000×720 queda completamente debajo del área visible. El título del evento seleccionado empieza en y=1051. El campo para pedir cambios está en y=1251 o y=1266. La página permite llegar a estos elementos bajando: es un problema de jerarquía y acceso al trabajo principal, no una pérdida definitiva de contenido por falta de scroll.

Los botones Original/AI Sound, Aplicar a Resolve y Rediseñar sonido sí están visibles al inicio, en y=387 dentro del viewport. Como pertenecen al mismo documento desplazable, desaparecen al bajar al inspector y la línea.

Archivos útiles:

- `pagina_actual_1240x900_arriba.png` y `pagina_actual_1240x900_abajo.png`.
- `pagina_actual_1000x720_arriba.png` y `pagina_actual_1000x720_abajo.png`.
- `pagina_actual_contenido_1240.png` y `pagina_actual_contenido_1000.png`: contenido completo.
- `pagina_director_1.png` y `pagina_director_2.png`: capturas originales del arnés.
- `resultado_verificacion.json`: geometrías y resultados estructurados.
- `ejecucion.log`: salida de las 48 comprobaciones.

## Límite de la conclusión

Las comprobaciones existentes pasan para este video y estas rutas simuladas. Esto respalda que el flujo básico funciona; no prueba ausencia general de errores. La observación visual está limitada a Qt offscreen, un caso de contenido, dos tamaños y escala de interfaz por defecto con preferencias en memoria.
