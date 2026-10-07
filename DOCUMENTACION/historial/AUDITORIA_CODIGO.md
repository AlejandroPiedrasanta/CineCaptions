# Auditoría de código · CineCaptions v5.7 (6 oct 2026)

Alcance: `1_codigo/` (54 módulos, ~43 000 líneas), el editor Creativo, el flujo Generar y los registros reales de tu equipo
(`cinecaptions.log`, `fallo_nativo.log`). Todo lo marcado **Corregido** ya está en el código y en el instalador.

## Cómo se hizo
| Técnica | Resultado |
|---|---|
| Análisis estático (pyflakes) | 0 nombres sin definir; 39 imports sin usar y 10 variables sin usar (cosmético) |
| Escáner AST propio (encoding, `shell=True`, `eval/exec/pickle`, red sin timeout, `zip.extract`, `open` sin `with`) | Limpio salvo 2 `subprocess.run` sin timeout (instalador del motor de voz) y 1 `read_text()` sin encoding (ruta solo-Linux) |
| Auditoría de hilos (qué widgets se tocan desde hilos de trabajo) | 0 infracciones reales |
| Fuzz de `build_manual_cues` (6 000 casos aleatorios) | Palabras conservadas y en orden, topes por rol respetados, sin solapes ni tiempos negativos: **0 violaciones** |
| Fuzz de `roles_inteligentes` (3 000 casos) | Sin excepciones; 0 violaciones tras A10 |
| Estrés de escritura de archivos (8 hilos + lector) | Antes: pérdida/corrupción posible. Ahora: 482/482 claves, 0 lecturas rotas |
| Geometría de la interfaz a 1100×700 y 1366×768 (5 páginas) | 0 widgets fuera de ventana, 0 textos cortados |
| Escala del editor (200 / 1 500 / 4 000 palabras) | Fluido tras A9 (0,085 s con 4 000 palabras) |
| Cobertura de traducciones (`tr()` vs `locales/*.json`) | Resuelto: A8 |
| Registros reales de tu app | Dos hallazgos (A1, B1) |

## A · Corregidos
| # | Gravedad | Hallazgo | Arreglo |
|---|---|---|---|
| A1 | **Alta** | **7 congelaciones de 2,5–2,9 s** en tu uso real (siempre el mismo sitio en el registro): al pulsar «Obtener»/detectar, la interfaz llamaba a `resolve_bridge.modo_actual()` → MCP → esperaba a Resolve **en el hilo de la interfaz**. | `_detectar_desde_resolve` y `_forzar_deteccion_nueva` preguntan el modo en un hilo (`correr_en_hilo`). Probado: bloqueo de la interfaz 0,000 s con un Resolve que tarda 1,5 s. |
| A2 | **Alta** | `preferencias.json`, marcas, proyectos y manifiestos se escribían con `write_text()` (vacía el archivo y luego lo llena) y con lectura-modificación-escritura sin cerrojo. Un cierre brusco, o un hilo que leyera a mitad, devolvía «sin preferencias» y al guardar **borraba todas las demás claves** (tema, motor, packs…) o dejaba las marcas a medias. | Módulo nuevo `archivos_seguros.py`: escritura en temporal + `os.replace` atómico, cerrojo para mezclar claves, reintentos ante bloqueos de Windows, copia `.bak` de las marcas (y `cargar_marcas` la usa si la principal está rota), archivo roto apartado como `.roto` en vez de pisarse. Aplicado a preferencias (2 rutas), marcas, proyectos, manifiestos y sidecars `.lua`. |
| A3 | Media | «Editar marcas y regenerar» armaba los bloques, elegía efectos y emojis **en el hilo de la interfaz** (podía congelar la ventana en vídeos largos). | `_regenerar_marcas` corre en un hilo; la ventana sigue viva y el popup avanza. |
| A4 | Media | `correr_en_hilo` solo capturaba `Exception`: el transcriptor usa `SystemExit` para avisar errores y el callback **nunca se ejecutaba** (pantalla esperando para siempre). | Captura `BaseException`. |
| A5 | Media | `ejecutar_en_ui` lanzaba `RuntimeError: Signal source has been deleted` si un hilo terminaba al cerrar la app (excepción sin atrapar en el hilo). | Se ignora si la app ya se cierra. |
| A6 | Baja | Código muerto tras quitar botones del Creativo (`_completar_grupos`, `_abrir_proyectos_guardados`, `_elegir_version`, `_reajustar_ahora`, `_mostrar_aviso_manual`, ~90 líneas) y 2 variables sin usar. | Eliminado. |
| A7 | Baja | Texto sin traducir en el popup de Asistencia («Revisando la ortografía…»). | `tr()` + 5 idiomas. |
| A8 | Media | **261 de 1 603 textos de la interfaz (16 %) no tenían traducción** a en/de/fr/pt/it (script principal 74, `sfx_studio` 72, `registro_ui` 23, `estilos_inicio` 20, `sfx_editor` 20, `un_clic_ui` 17…). | Traducidos los 261 a los 5 idiomas (1 305 textos) y validados: mismos `{marcadores}`, mismas «comillas» y mismos espacios que el original. Cobertura ahora 100 % (1 603/1 603 en cada idioma). |
| A9 | Baja | `_actualizar_contador` tardaba 0,43 s con 4 000 palabras (vídeo de ~20 min). Causa: `sfx_rules._dueno_de` recorría todos los bloques por cada palabra (4 000 × 1 500 = más de 1 s también al generar) y `emojis.catalogo()` volvía a mirar la carpeta de emojis del usuario en cada llamada (con 400 emojis, ~4 s de redibujado). | Búsqueda binaria de bloques y la carpeta de emojis se vuelve a mirar como mucho cada 0,75 s (`_invalidar()` la refresca al instante cuando la interfaz cambia algo). Resultado: 0,085 s con 4 000 palabras y 0,078 s con 400 emojis. |
| A10 | Baja | Con la IA, ~1,6 % de los guiones pintaban dos grupos «Principal» pegados o una principal de más palabras que el tope. Causa real: `grupo_alrededor` no contaba los conectores («de», «que»…) al formar la principal, justo lo que pediste que contaran como palabra. | La principal son ahora exactamente N palabras seguidas (los conectores cuentan). Además `grupos_estrictos` ya no deja un grupo sin complemento pegado a otro sin contexto. Fuzz de 3 000 casos: 0 violaciones (antes 49). |
| A11 | Baja | `motor_voz.py`: la instalación con pip (PyTorch ~2,5 GB) y `get-pip` podían quedarse colgadas sin límite. | Timeout de 60 min y 10 min con mensaje claro y traducido. |

## B · Pendientes / recomendaciones
| # | Gravedad | Hallazgo | Recomendación |
|---|---|---|---|
| B1 | Info | `fallo_nativo.log` registra `0x8001010d` (RPC_E_CANTCALLBACKDURINGINTERNALCALL) **en 30 de 30 sesiones**, siempre dentro de `app.exec()`. Solo 1 sesión se marcó como cierre anómalo, así que parece una excepción COM benigna de Windows/Qt que `faulthandler` vuelca igualmente. Efecto: ensucia el log y puede esconder un fallo real. | Usar `sesion_abierta.flag` (ya existe) para decidir si un volcado importa; si algún día hay un cierre real, capturar un minidump con WER `LocalDumps`. |
| B2 | Info | Licencia: el estado local va firmado con HMAC cuya sal viaja en el programa, y la ventana de 7 días sin conexión depende del reloj local. Es el límite normal de una licencia en el cliente. | Si preocupa la piratería, validar siempre contra el servidor al abrir (más estricto). |
| B3 | Info | Una línea «base» puede llevar 3 palabras aunque «palabras por básico» sea 2 (evita dejar una palabra huérfana). | Documentarlo o hacerlo configurable. |

## Lo que está bien
Sin secretos en el código · sin `shell=True`, `eval`, `exec` ni `pickle` · toda la red con timeout · todo texto con `encoding` explícito ·
disciplina de hilos correcta (los hilos solo llegan a la interfaz por `ejecutar_en_ui` o la cola) · licencia con escritura atómica ·
interfaz sin desbordes a 1100×700 · conservación de palabras y topes por rol verificados con 6 000 casos aleatorios.

## Regla nueva (en `CLAUDE.md`)
Nunca llamar a `resolve_mcp`/`resolve_bridge` que esperen a Resolve (`modo_actual()` sin `pasivo`, `disponible()`, `estado()`) en el hilo de la interfaz, y
nunca `write_text` directo para estado del usuario: usar `archivos_seguros`.
