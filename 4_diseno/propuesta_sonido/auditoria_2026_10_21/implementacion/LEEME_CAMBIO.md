# Sonido: implementación acotada

21 de octubre de 2026. Cambios aplicados al código fuente, sin compilar ni publicar instaladores.

## Alcance

Solo se reorganiza el contenido de la página Sonido y se corrige su lógica. `isla_ui.py`, `qt_kit.py`, `ajustes_ui.py`, `un_clic_ui.py`, `version.py`, la navegación, el menú y los estilos globales no tienen cambios. En el script principal únicamente se modificaron los hooks de colocación y recuperación del audio de GO.

La interfaz conserva las tarjetas, botones, Combo, fuentes y colores del proyecto. La línea, la comparación A/B y la lista de eventos aparecen primero; el inspector va al lado cuando hay ancho y debajo en ventanas menores. El diagnóstico queda plegado. La lista permite elegir con las flechas y escuchar con Enter. Los seis controles conservan su alcance global, indicado en pantalla.

Los retoques quedan pendientes hasta pulsar Aplicar a Resolve. Los errores permanecen visibles, las frases se conservan si fallan y los controles no aceptan cambios durante un trabajo. Un score desactualizado se marca como medición pendiente.

La lógica conserva el video elegido y valida proyecto/timeline antes de enviar. Los scripts Python y Lua repiten la comprobación antes de tocar pistas. Se confirma sincronización tras el resultado exitoso de Resolve; los resultados de sesiones anteriores y de trabajadores que terminaron después del límite de espera no sobrescriben el estado confirmado. La recuperación automática de GO renueva su destino si reconstruye un timeline. Los diseños antiguos sin destino vinculado requieren repetir GO antes de aplicar desde Sonido.

## Verificación

| Grupo | Resultado |
|---|---:|
| Página y motor, arnés integrado con muestra local | 48/48 |
| Contratos básicos de GO y compatibilidad visual (fase 0) | 32/32 |
| Sesión, instrucciones y sincronización | 17/17 |
| Destino Python y Lua, con y sin io | 32/32 |
| Confirmación, rearme y resultado tardío | 7/7 |

Estado, preferencias y cachés aislados; cero llamadas a Resolve real. La verificación no incluye escucha perceptiva ni una colocación sobre un proyecto del usuario.

A 1240×900, la línea comienza en y=298 del área útil, frente a y=789 en la versión auditada. Se ven la línea, el inspector, A/B y Aplicar. A 1000×720 se ven línea y acciones; el inspector pasa debajo. No hay desplazamiento horizontal en esos tamaños.

Capturas y resultados:

- [Página a 1240×900](pagina_actual_1240x900_arriba.png).
- [Página a 1000×720](pagina_actual_1000x720_arriba.png).
- [Resultados y geometrías](resultado_verificacion.json).
- [Fase 0](fase0/informe.json).

La auditoría de la carpeta superior documenta la situación anterior; este archivo describe lo que se implementó después. La regeneración de documentación se limitó al índice de código: se conservó `4_diseno/0_LEEME.txt`, protegido contra escritura.
