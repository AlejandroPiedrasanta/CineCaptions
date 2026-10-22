# Auditoria funcional del motor de Sonido

Fecha de auditoria: 21 de octubre de 2026. Alcance: pagina Sonido de CineCaptions, sus servicios de sesion, estado, motor e integracion con GO/Resolve.

Se leyeron primero `CLAUDE.md` y `DOCUMENTACION/RESUMEN.md`. No se localizaron archivos `AGENTS.md` en la busqueda del repositorio. Esta auditoria no cambia codigo del programa, preferencias, audio ni timelines de Resolve.

## Niveles de evidencia

- **Reproducido con mocks:** se ejecuto la funcion real del programa, sustituyendo estado, preferencias y dependencias externas por funciones en memoria. Demuestra la decision de codigo; no demuestra su efecto en un Resolve real.
- **Lectura estatica:** la conclusion procede de las ramas y llamadas verificadas en el codigo. Se indica cuando falta una prueba completa de GO/Resolve.
- **Exploratorio:** hubo un arnes puntual adicional con dependencias simuladas, no incluido entre los cinco casos de reproduccion persistidos.

Las referencias de lineas corresponden al codigo consultado durante esta auditoria. Las rutas siguientes son relativas a la raiz del repositorio; `principal` abrevia `1_codigo/CineCaptions (script principal).py`.

## Flujo que existe actualmente

1. La pagina Sonido se construye como `PaginaDirector`. Si esa construccion falla, el script principal intenta abrir el antiguo SFX Lab. No son dos modos elegibles por el usuario. Referencia: principal:10636-10683.
2. El director esta **encendido por defecto** si no existe una preferencia. La variable de entorno de pruebas puede forzarlo. Referencia: `1_codigo/director_sonido.py:31-43`.
3. GO captura video, palabras, bloques, tema, recorte, planes visuales y PRO; inicia un hilo independiente. Referencias: principal:11887-11916 y 14176-14177; `1_codigo/director_sonido.py:65-87`.
4. El motor ejecuta analisis, SFX, musica/ambiente, voz y mezcla/QC, guardando resultados intermedios. Cada fase captura sus excepciones y escribe el fallo en Registro. Referencia: `1_codigo/director_sonido.py:162-242`.
5. Antes de colocar, GO espera hasta 300 segundos y recoge lo preparado. Si el hilo sigue vivo, omite la voz en esa colocacion y conserva los resultados disponibles. Referencia: principal:11919-11934.
6. El director agrega sus eventos a las pistas AI, apaga SFX anteriores y puede reemplazar la voz original por una copia procesada. El flujo de colocacion acepta un plan `solo_ai`. Referencias: `1_codigo/director_sonido.py:502-566`; `1_codigo/director_sonido_sesion.py:519-545`.
7. Una vez existe contexto de GO, la pagina puede retocar o redisenar sin repetir transcripcion. Los cambios se guardan y la UI intenta aplicarlos automaticamente a Resolve. Referencias: `1_codigo/director_sonido_sesion.py:269-302, 548-566`; `1_codigo/director_sonido_ui.py:585-623, 633-685`.

### Precondiciones y alcance de los ajustes

- Para redisenar hacen falta un contexto guardado y un analisis anterior de GO. Si faltan, `_rehacer` lanza un mensaje que pide GO. Referencia: `1_codigo/director_sonido_sesion.py:272-275`.
- Para aplicar desde Sonido se exige `ultimo_go.con_director`, pero no se comprueba la identidad del timeline actual. Referencia: `1_codigo/director_sonido_sesion.py:531-538`.
- Los retoques, bloqueos y ronda se guardan por archivo de video. Los seis controles son preferencias globales. Referencias: `1_codigo/director_sonido_sesion.py:248-258, 309-417`; `1_codigo/director_sonido.py:259-271`.
- El estado depende de ruta, tamano y fecha del archivo; un archivo modificado cambia su huella. Las copias procesadas viven bajo `~/DaVinciSubtitles/sound_director/`. Referencia: `1_codigo/director_sonido_estado.py:22-55, 85-114`.
- La sustitucion de voz esta habilitada solo en timelines que GO armo desde un video. Si la fuente es el audio de un timeline existente, conserva esa mezcla. Referencia: `1_codigo/director_sonido.py:435-464`.
- El control de prioridad de voz modifica el nivel relativo de efectos, no vuelve a ejecutar la restauracion de voz. Referencias: `1_codigo/director_sonido_diseno.py:99-101`; `1_codigo/director_sonido_sesion.py:269-302`.

## Hallazgos priorizados

### H1. P1: el video mostrado y el timeline destino pueden no corresponder

`resumen(video)` sustituye un video sin diseno por `general.ultimo_video`. Devuelve el video anterior y puede dejar `puede_aplicar=True`. La UI avisa con un texto que es el ultimo video que paso por GO, pero no exige elegirlo explicitamente. `aplicar` comprueba solamente el GO anterior del video; el backend escribe en el timeline **actual**.

La combinacion permite retocar B cuando Inicio apunta a A, e intentar enviar el resultado al timeline que el usuario tenga abierto. El problema incluye la aplicacion automatica despues de cambios.

- Evidencia: **reproducido con mocks** el reemplazo A -> B y `puede_aplicar=True`; **lectura estatica** el destino actual y la ausencia de comprobacion de identidad.
- Referencias: `1_codigo/director_sonido_sesion.py:152-168, 222-223, 531-544, 548-566`; `1_codigo/director_sonido_ui.py:491-498, 595-603`; `1_codigo/efectos_visuales.py:1178-1190`; `2_recursos/efectos/colocar_efectos.py:318`.
- Implicacion para UI: identificar permanentemente video editado y proyecto/timeline destino; mostrar la recuperacion del ultimo diseno como una eleccion explicita; bloquear la aplicacion si el destino no coincide con la sesion.

### H2. P1: se marca sincronizado antes de colocar el audio

`al_colocar` establece `pendiente_resolve=False`, fecha `en_resolve` y `ultimo_go.con_director=True` al construir el plan. En ese momento no se ha confirmado su ejecucion. `_pintar_resolve` utiliza esos datos para mostrar «En Resolve y al dia».

Una colocacion posterior fallida puede dejar un estado de exito en la pagina. El nombre `sound_events_placed` tambien se utiliza para audios materializados localmente, sin constituir por si solo evidencia de clips colocados en Resolve.

- Evidencia: **reproducido con mocks** el registro de sincronizacion llamando solo a `al_colocar`, sin invocar Resolve.
- Referencias: `1_codigo/director_sonido.py:406-412, 542-550`; `1_codigo/director_sonido_ui.py:505-518`.
- Implicacion para UI: diferenciar diseno listo, cambios pendientes, aplicando y sincronizado confirmado. La confirmacion debe depender del resultado real del backend.

### H3. P1: un hilo tardio puede sobrescribir el registro de colocacion

`preparar` carga una copia del estado y la guarda al terminar distintas fases. GO puede continuar tras el limite de espera dejando vivo ese hilo. Entre ambas cosas, `al_colocar` actualiza el estado con `ultimo_go` y `en_resolve`. Un guardado posterior del estado antiguo puede perder esas claves.

El usuario podria ver perderse la capacidad de aplicar o quedar asociado a resultados de voz/QC que no entraron en la colocacion terminada.

- Evidencia: **lectura estatica**, apoyada por un **arnes exploratorio** de dos hilos y estado simulado que reprodujo la desaparicion de `ultimo_go`. No se probo con archivos de estado reales ni Resolve.
- Referencias: principal:11926-11930; `1_codigo/director_sonido.py:173, 184, 195, 205, 211-237, 542-547`; `1_codigo/director_sonido_estado.py:95-102`.
- Implicacion tecnica y de UI: identificar sesion y revision; evitar que un trabajo anterior confirme o sobrescriba una sesion posterior; mantener visible si una fase quedo pendiente.

### H4. P1/P2: el interruptor de Inicio y el del director pueden contradecirse

Inicio pasa `con_sfx=False` cuando «Efectos» esta apagado. El arranque del director depende solamente de su propia preferencia, encendida por defecto. El contexto del director no lleva `con_sfx`, y el diseno puede generar acentos aun cuando el caption no tenga eventos de sonido anteriores.

- Evidencia: **lectura estatica**. La ruta permite volver a anadir SFX; falta comprobar el resultado completo de GO en un entorno de prueba dedicado.
- Referencias: principal:8680, 8695-8696, 11892-11899; `1_codigo/director_sonido.py:31-43, 65-72`; `1_codigo/director_sonido_diseno.py:189-235`.
- Implicacion para UI: definir un solo propietario del estado de sonido y sincronizar Inicio con Sonido. Separar claramente activar el motor de las decisiones sobre SFX, musica, ambiente y voz.

### H5. P2: las instrucciones no comprenden negacion ni alcance temporal general

`interpretar` aplica expresiones regulares. «No quiero mas sonidos» produce `densidad=mucho`; «Sin musica al final» se convierte en un control global de musica. La pagina no deberia sugerir comprension libre que el servicio no implementa.

- Evidencia: ambos casos **reproducidos con mocks** usando la funcion real `interpretar`.
- Referencias: `1_codigo/director_sonido_sesion.py:575-622`.
- Implicacion para UI: presentar acciones compatibles y una interpretacion visible antes de cambios ambiguos; seleccionar el tramo de forma explicita.

### H6. P2: musica/ambiente y redisenado de tramo pueden no combinarse

`ejecutar` detecta que debe recalcular capas cuando cambia musica o ambiente. Si tambien hay una accion de redisenado de seccion, retorna mediante `redisenar`, que no transmite esa bandera a `_rehacer`. El control se guarda, pero las capas actuales no se regeneran por ese camino.

- Evidencia: **reproducido con mocks** interceptando `_rehacer`: musica=nada + seccion ejecuta el recalculo sin `capas=True`.
- Referencias: `1_codigo/director_sonido_sesion.py:392-407, 625-657`.
- Implicacion para UI: cada instruccion debe anunciar que partes del diseno se cambiaran y confirmar sus resultados; el backend debe aplicar todas sus acciones de forma coherente.

### H7. P2: «Deshacer todo» es restablecer y afecta ajustes globales

La accion elimina ajustes y bloqueos del video, vuelve ronda a cero y deja vacios los controles globales. No recupera el estado inmediatamente anterior y no ofrece historial de pasos.

- Evidencia: **lectura estatica**.
- Referencia: `1_codigo/director_sonido_sesion.py:410-417`.
- Implicacion para UI: llamar a esta accion «Restablecer diseno» y separarla de un verdadero Deshacer. Hacer visible su alcance por video y sobre valores globales.

### H8. P2: el Sound Score puede ser antiguo sin indicacion visible

Tras un retoque de un video mayor de 600 segundos, `_rehacer` omite medir de nuevo y guarda `sound_score_viejo=True`. El resumen no expone esa marca y la UI sigue pintando el numero existente.

- Evidencia: **lectura estatica**.
- Referencias: `1_codigo/director_sonido_sesion.py:286-300, 216-223`; `1_codigo/director_sonido_ui.py:494`.
- Implicacion para UI: mostrar fecha/revision de medicion y «Pendiente de medir» si cambio el diseno. El numero no debe implicar validacion actual del timeline.

## Persistencia y documentacion

La escritura del estado utiliza `archivos_seguros`, con JSON por huella y carpeta para archivos procesados. Esta es una base util para una interfaz que conserve decisiones por video. La atomicidad del archivo no evita la sobrescritura logica entre snapshots concurrentes descrita en H3.

Existe documentacion desactualizada: `DOCUMENTACION/temas/sonido.md:182-188` describe el director apagado por defecto; `1_codigo/director_sonido.py:31-43` lo enciende. `DOCUMENTACION/RESUMEN.md` tambien describe Sonido como el antiguo SFX Lab. Se documenta la divergencia; no se modificaron esos archivos.

## Reproduccion persistida

Archivo: `reproducir_hallazgos_motor.py`, en esta misma carpeta.

Desde la raiz del repositorio, en PowerShell:

```powershell
& '6_compilacion\venv315\Scripts\python.exe' -B '4_diseno\propuesta_sonido\auditoria_2026_10_21\reproducir_hallazgos_motor.py'
```

El script importa los tres modulos auditados y sustituye la lectura/escritura del estado, preferencias, log y material por funciones en memoria. Simula la existencia de A.mp4/B.mp4. No importa el conector de Resolve ni ejecuta audio. Desactiva la escritura de bytecode. Sus cinco comprobaciones son:

1. Recuperacion automatica de B al pedir el resumen de A.
2. Registro de sincronizacion prematuro al armar el plan.
3. Interpretacion invertida de una negacion.
4. Perdida del alcance «al final» de una instruccion de musica.
5. Omision de regeneracion de capas en comando musica + seccion.

**Importante:** que estos casos pasen significa que el comportamiento observado continua reproducible; no son pruebas de aceptacion del comportamiento deseado.

### Que se ejecuto y limites

Se ejecutaron arneses puntuales con mocks para los casos anteriores, la aceptacion de un plan sin identidad de destino y una intercalacion de hilos con estado simulado. Se ejecuto ademas el script persistido de cinco casos. No se ejecutaron pruebas mas amplias.

No se abrio ni controlo Resolve, no se generaron WAV, no se midio sonido real, no se probaron proveedores de audio y no se ejecuto GO completo. Los hallazgos de audio percibido, compatibilidad Free/Studio, desempeno real y comportamiento final de pistas requieren una sesion de prueba separada. Este informe no afirma haberlos validado.
