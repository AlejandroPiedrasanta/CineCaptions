# Auditoría de Sonido y propuesta de interfaz

**CineCaptions 5.37 · 21 de octubre de 2026**

## Conclusión

La página actual tiene un motor de sonido amplio y controles útiles, pero su organización da prioridad a explicar el análisis y configurar la IA antes de permitir trabajar con el resultado. En una ventana de 1240 × 900, la línea temporal apenas empieza a verse al final del área útil; el inspector queda debajo. Hay además problemas funcionales que deben corregirse junto al diseño: identidad del destino en Resolve, confirmación de sincronización, errores que desaparecen y órdenes interpretadas fuera de su alcance esperado.

La propuesta convierte Sonido en un espacio para **escuchar, seleccionar un momento y ajustar**. Conserva la dirección automática, las explicaciones y los bloqueos; coloca línea e inspector juntos y presenta el diagnóstico como información desplegable.

## Alcance y evidencia

- Lectura de `director_sonido_ui.py`, `director_sonido_sesion.py`, `director_sonido.py`, estado, diseño y conexiones con GO/Resolve. Referencias de línea válidas para la copia auditada.
- **48/48 comprobaciones del arnés existente**, con preferencias, directorios personales, cachés y estado aislados. Video local existente y transcripción de 182 palabras. **Cero intentos de uso de Resolve real registrados.**
- Widgets reales de Qt, sin pantalla, dentro del contenedor de scroll utilizado por producción; capturas a 1240 × 900 y 1000 × 720.
- Reproducciones adicionales con mocks en memoria para comprobar casos no cubiertos por el arnés habitual. El script entregado reproduce **5/5 casos**: sustitución de video, marcado prematuro de sincronización, negación, alcance temporal y orden combinada. Se distinguen de la ejecución integrada y de la mera lectura estática. Ver [detalle del motor](auditoria-motor.md) y [reproducción aislada](reproducir_hallazgos_motor.py).
- Propuesta interactiva con datos ilustrativos: no reproduce audio ni envía a Resolve. No se modificó el código del programa ni se compilaron instaladores.

Que el arnés pase confirma los recorridos que comprueba; no descarta las fallas de destino, concurrencia, interpretación y disposición descritas aquí. No se realizó una sesión de escucha ni una colocación real en Resolve, por lo que esta auditoría no califica perceptualmente la calidad sonora.

## Cómo funciona realmente

1. **GO prepara el contexto:** palabras, bloques, cortes, tema y planes de efectos/motions. El director analiza el material y produce efectos, música/ambiente cuando corresponde, tratamiento de voz y medición de mezcla. Viene encendido por defecto en el código actual.
2. **Sonido carga un diseño existente.** No analiza de forma independiente un video nuevo desde esta página. Si el seleccionado en Inicio carece de diseño, puede mostrar el último video que sí lo tiene.
3. **La cabecera y ocho estados** resumen voz, ruido, música, ambiente, motions, mezcla, master y material disponible. El Sound Score es una medida interna de varios componentes; no sustituye la escucha.
4. **La comparación A/B** genera WAV reales de un fragmento de hasta 15 s, empezando dos segundos antes del cursor. “Oír” un evento reproduce su contexto durante 4,5 s; no equivale a escuchar solo el archivo aislado.
5. **Seis controles** permiten dirigir estilo, intensidad, cantidad de sonidos, prioridad de voz, música y ambiente. Auto quita la elección manual. Aunque los eventos se guardan por video, estos controles son preferencias globales.
6. **La línea muestra seis carriles.** Video, voz, música y ambiente sirven de contexto. Los eventos de SONIDOS IA son seleccionables; el carril MOTIONS PRO se muestra, pero no permite seleccionarlos para editarlos en esta vista.
7. **El inspector** explica el evento y su material, ofrece menos/más, otra variación, silencio y bloqueo. Los retoques se guardan por clave; el bloqueo conserva un evento ante nuevas variaciones.
8. **Los cambios intentan aplicarse automáticamente a Resolve** si existe un GO previo con director y Resolve está abierto. En otro caso quedan pendientes. “Aplicar a Resolve” también permite enviar/reintentar. Los audios procesados se guardan aparte del original.
9. **“Rediseñar” cambia variaciones**, conservando las decisiones de fondo. **“Deshacer todo” restaura Auto y elimina retoques y bloqueos**; no recupera el paso anterior. El campo de frases usa patrones, no comprensión libre de instrucciones.

La página vigente es `PaginaDirector`. SFX Lab queda como respaldo si falla su construcción (`CineCaptions (script principal).py:10636`). Las propuestas PNG del 4 de octubre en la carpeta superior corresponden al diseño anterior y no son una captura de la página actual.

## Hallazgos de funcionamiento

| Prioridad | Situación actual | Cambio propuesto | Motivo y evidencia |
|---|---|---|---|
| Alta | Se permite aplicar un diseño sin verificar la identidad del proyecto/timeline actual. Además, puede mostrarse el último video diseñado en lugar del elegido en Inicio. | Vincular diseño a sesión de GO y destino; mostrar archivo, proyecto y timeline; exigir coincidencia antes de colocar. | La sustitución de A por B y `puede_aplicar=True` se reprodujeron con mocks. La falta de validación de destino se verificó por lectura. `director_sonido_sesion.py:152`, `:531`; `efectos_visuales.py:1178`. No se provocó una colocación incorrecta real. |
| Alta | El plan marca “en Resolve” antes de confirmar su colocación. | Separar plan preparado, envío iniciado y sincronización confirmada. Marcar al día solo tras respuesta válida del destino. | Reproducido con mocks sin invocar Resolve. `director_sonido.py:542`; la UI confía en esa marca en `director_sonido_ui.py:505`. |
| Alta | Un procesamiento que termina tarde puede sobrescribir estado registrado por la colocación. | Identificador de sesión, revisión del estado y actualización coordinada; descartar resultados obsoletos. | Reproducido con concurrencia controlada en memoria. GO puede continuar tras una espera de 300 s sin detener el hilo: principal `:11926`; snapshots en `director_sonido.py:173`, `:211`, `:237`. No se observó el caso en una sesión real del usuario. |
| Alta | Algunos errores se escriben y se borran inmediatamente al repintar. | Estado de operación independiente y persistente, con detalle expandible y reintento. | Lectura directa: `_trabajar` muestra error en `director_sonido_ui.py:610` y llama a `_pintar` en `:611`, que reemplaza el mensaje en `:493`. |
| Alta | Segmentados, entrada y Enviar siguen disponibles durante un trabajo que rechaza nuevas acciones por ocupado. | Deshabilitar los controles afectados o conservar explícitamente la última intención; limpiar la frase solo al aceptarla. | Lectura directa: lista parcial de acciones en `director_sonido_ui.py:437`, rechazo en `:588`, borrado de entrada en `:740`. |
| Media | Los pedidos por texto pueden invertir intención o ampliar el alcance. | Mostrar la interpretación y el tramo antes de ejecutar; ofrecer pedidos compatibles como acciones visibles. | Reproducido: “No quiero más sonidos” produce densidad alta; “Sin música al final” produce música desactivada para todo el video. `director_sonido_sesion.py:575`. |
| Media | Una orden combinada de música/ambiente y rediseño temporal puede guardar el control sin recalcular la capa. | Separar el cambio de capas y la variación de eventos, aplicando ambos cuando corresponda. | Reproducido con mocks: el camino combinado llega a `_rehacer` sin `capas=True`. `director_sonido_sesion.py:392`, `:625`. |
| Media | El score de videos de más de diez minutos puede conservar una medición anterior tras un retoque. | Mostrar “Medición pendiente” y momento/revisión de la última medición. | Lectura: `sound_score_viejo=True` en `director_sonido_sesion.py:299`, no expuesto por `resumen` en `:216`; UI muestra el número en `director_sonido_ui.py:494`. |
| Por verificar | Inicio puede indicar Efectos apagados mientras el director, activado por separado, añade SFX. | Definir y mostrar un único dueño del sonido, con ajustes coherentes entre Inicio y Sonido. | Hipótesis sustentada por lectura; requiere prueba de GO dedicada. Principal `:8680`, `:8695`, `:11892`; director activo por defecto en `director_sonido.py:31`. No se presenta como fallo observado en Resolve. |

## Hallazgos de interfaz

| Antes | Después propuesto | Por qué |
|---|---|---|
| Cabecera, ocho estados y seis filas de controles antes de la línea. | Cabecera compacta, A/B y línea primero; inspector lateral. | La selección, la escucha y el ajuste necesitan compartir el área visible. |
| A/B y Aplicar desaparecen al bajar hasta los eventos. | Escucha y estado próximos al espacio de trabajo; acciones principales persistentes en la aplicación nativa. | Mantener el contexto entre seleccionar un momento y escuchar o enviar. El prototipo ilustra la ubicación, no implementa barras fijas. |
| Varias filas de mensajes compiten por expresar actividad, errores y sincronización. | Mensaje de operación separado del estado de destino y de la identificación del video. | Cada mensaje conserva su significado y los fallos no se tapan. |
| “Rediseñar sonido” y “Deshacer todo”. | “Crear otra versión” y “Restaurar diseño IA”. | Son nombres ajustados a su comportamiento. Un deshacer por pasos necesitaría historial nuevo. |
| Envío automático implícito junto a un botón Aplicar. | Revisar localmente y enviar mediante Aplicar como política propuesta; envío automático solo si se elige explícitamente. | Es un cambio de comportamiento deliberado que requiere separar edición y aplicación en el motor. |
| Globales mostrados dentro del video sin aclarar alcance. | “Solo este video” y valores para próximos GO diferenciados. | La propuesta requiere persistencia por video; la etiqueta del prototipo todavía no describe el motor actual. |
| Eventos diminutos y selección oculta de solapados mediante clic repetido. | Lista de eventos vinculada al inspector; selección explícita y posterior zoom por tramo. | Permite trabajar sin acertar en una marca de pocos píxeles. Zoom y solapamientos quedan como trabajo de implementación. |
| Carriles de contexto y editables parecen equivalentes. | Sonidos IA seleccionables; demás carriles de contexto; edición PRO separada hasta disponer del soporte real. | No prometer que cualquier bloque es editable. |
| Textos truncados dependen de tooltips que están desactivados globalmente. | Detalle expandible mediante clic, sin globos. | Recuperar la información completa y respetar la preferencia existente. |
| Score grande y ocho estados siempre expandidos. | Score secundario y análisis desplegable. | El diagnóstico apoya la tarea, sin desplazar la línea. |
| Widgets de score, línea y segmentados operables principalmente con ratón. | Controles nativos accesibles, foco visible y lista textual operable con teclado. | La implementación Qt debe añadir foco, teclas y nombres accesibles. La demostración usa botones y selectores nativos del navegador. |
| Campo de texto parece aceptar cualquier pedido. | Pedidos compatibles visibles; interpretación verificable antes de instrucciones libres. | Ajustar la expectativa a lo que el parser realmente entiende. |

## Medición de la página actual

Capturas Qt con contenedor y márgenes equivalentes a producción; no incluyen la ventana completa del programa.

| Ventana | Área útil vertical | Altura de página | Recorrido de scroll | Línea desde el inicio del área útil |
|---|---:|---:|---:|---:|
| 1240 × 900 | 792 px | 1299 px | 519 px | y = 789 px: solo 3 px visibles |
| 1000 × 720 | 612 px | 1314 px | 714 px | y = 789 px: no visible inicialmente |

Existe scroll vertical funcional: no es pérdida permanente de controles. El problema es que el inspector y la línea quedan separados de las acciones de escucha y envío. Ver [captura superior](verificacion/pagina_actual_1240x900_arriba.png), [captura inferior](verificacion/pagina_actual_1240x900_abajo.png), [mediciones](verificacion/resultado_verificacion.json) y [metodología de verificación](verificacion/LEEME_VERIFICACION.md).

## Nueva interfaz propuesta

**Cabecera:** Sonido, nombre del archivo, tema, alcance del ajuste, director para el próximo GO y destino de Resolve. Si se muestra un diseño anterior, aviso explícito y acción para volver al video de Inicio. En vacío: acción para ir a Inicio y generar el primer diseño.

**Área principal:** comparación Original / Mezcla IA del mismo tramo, inicio y final visibles, línea de seis carriles e inspector contiguo. En anchos pequeños el inspector pasa debajo. El transporte real deberá reflejar preparando, reproduciendo, detenido y finalizado.

**Inspector:** nombre, tiempo, duración, motivo y material del evento; escuchar en contexto, otra versión, bloquear, silenciar y ajustar duración. “Menos…” y “Más…” podrán conservarse en un menú de ajustes. Los eventos bloqueados deben mostrar por qué algunas acciones están inactivas.

**Dirección:** seis controles compactos con Auto y su decisión actual, evitando seis filas largas. La propuesta de valor Auto resuelto requiere exponer consistentemente la elección actual del motor. La prioridad de voz debe describirse como protección frente a las otras capas, sin prometer una nueva restauración de voz.

**Pedidos:** botones para acciones admitidas. Si se mantiene texto libre, conservar el pedido y explicar la interpretación, especialmente su alcance temporal, antes de ejecutarlo.

**Diagnóstico:** análisis completo, material y desglose de score desplegables, con estado de medición y detalle legible. No mostrar un éxito técnico como garantía de que el diseño resulta agradable al oído.

**Estado:** Preparando → Listo para escuchar → Cambios pendientes → Aplicando → Sincronizado confirmado. Error y resultado obsoleto son estados propios, sin ocultarlos con el mensaje genérico del director.

## Qué se puede explorar en la propuesta

Seleccionar cualquiera de cinco sonidos de ejemplo, abrir su lista, consultar el inspector, silenciar y reactivar, bloquear, generar variaciones simuladas, acortar, cambiar los seis controles, usar pedidos compatibles y simular Aplicar. Cambiar Original/Mezcla IA demuestra la selección del modo y avisa que no hay reproducción de audio.

La apariencia sigue el tema del visor con colores y estructura propios de CineCaptions. Se verificó distribución en seis anchos de navegador, desde 320 a 1440 px, y el tema claro/oscuro. Pasan **11/11 comprobaciones de la propuesta**, incluyendo selección con ratón, selección mediante teclado conservando foco, silencio, bloqueo, pedido de música, restauración y aplicación simulada; no se registraron errores JavaScript. Son comprobaciones del prototipo, no una validación de DPI o dispositivos de la aplicación Qt. Ver [resultado de la propuesta](resultado_propuesta.json).

Los bloques, formas de onda, tiempos, decisiones Auto y score del prototipo son datos ilustrativos, aunque el nombre del video coincide con la muestra usada para comprobar la página real. No deben compararse numéricamente con el resultado de ese arnés.

## Orden recomendado para implementar

1. **Corregir consistencia:** validar destino y sesión, confirmar sincronización tras éxito, conservar errores, evitar sobrescrituras tardías y acciones perdidas. Aclarar el contrato de los interruptores de Inicio y Sonido.
2. **Reorganizar Qt:** conservar el motor, trasladar línea e inspector al área principal, compactar dirección y plegar diagnóstico. Renombrar acciones y añadir carga/vacío/errores claros.
3. **Definir alcance y envío:** controles por video, valores para futuros GO y política de aplicación explícita. No basta con cambiar las etiquetas.
4. **Completar interacción:** transporte A/B real, selección accesible por lista y teclado, detalle expandible y zoom por tramo. Añadir historial solo si se decide desarrollar deshacer por pasos.
5. **Validar:** repetir pruebas aisladas y comprobar portátil, escalado de Windows, textos largos e idioma; después ejecutar una sesión dedicada de Resolve verificando proyecto/timeline, reintentos y ausencia de audio duplicado.

Criterio de aceptación principal: en 1240 × 900 se deben ver comparación, línea y controles esenciales del evento sin bajar por los diagnósticos; cada envío debe identificar el destino y solo anunciar sincronización tras confirmación real.
