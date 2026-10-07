# CineCaptions v5.3.0 — contexto para IA

> Léeme PRIMERO. Resume el programa para que NO tengas que leer `LEEME.txt` (208 KB, ~60k tokens) ni `REGISTRO_DE_CAMBIOS.txt`.
> Si necesitas más detalle de una parte, busca solo esa sección en `LEEME.txt` (los números entre paréntesis, p. ej. «LEEME §4.2»). No lo cargues entero.
> Tampoco abras la sección 14 del LEEME (mapa de funciones con líneas, ~150 KB): usa búsqueda de texto (Grep) en su lugar.

## 1. Qué es

Programa de escritorio (Windows 10/11, también corre en macOS) que **subtitula vídeos solo** y coloca los subtítulos ya diseñados en el timeline de **DaVinci Resolve**, con estilo de reels virales. Autor/marca: *CineCaptions · By Cinema Productions*.

Stack: **Python 3.14.8 + PySide6 (Qt)**. IA local (sin internet salvo la licencia): Qwen3-ASR (voz), Qwen3-4B-Instruct (texto), Whisper de respaldo, Argos Translate (traducción).

Cada subtítulo son hasta 4 bloques, uno encima del otro (v5.3, la estructura de los packs `.drb`):
- `arriba` (pequeña, máx. 2 palabras; antes «contexto»)
- `PRINCIPAL` (grande, UNA palabra, nunca un conector)
- `abajo` (mediana, máx. 2 palabras; antes «complemento»)
- `imagen` (el icono o la imagen/emoji; va DEBAJO del texto o donde lo ponga el bloque «imagen» del pack)
- `simple` (una sola línea para las palabras sueltas; antes «base»)

**Nombres de los clips de un pack** (lo único que lee el programa): `principal · arriba · abajo · imagen · simple`, con
variantes agregando 2 o 3 al final (MÁXIMO 3; la 1 va sin número). Un set necesita arriba + principal + abajo; `imagen` es
opcional. Los nombres viejos (`contexto`, `complemento`, `base`, hasta 10 sets) siguen valiendo. Internamente los roles
siguen siendo `context / main / complement / base` + `image`. Los TRES lectores de nombres (`packs_drt.parsear_nombre`,
`parsear_nombre_pack` de `CineCaptions.py` y del `.lua`) tienen que dar lo mismo (se probó con 36 casos). Regla del usuario
para la plantilla base: SOLO los efectos Luxe Slide y Luxe Shine (Joel Van Beek), nada de Text+ ni composiciones propias.

## 2. Flujo principal (botón GO)

`SubtitleApp._go` → `_go_generar` → `_run_pipeline` (hilo aparte):
1. Comprueba licencia (`_licencia_lista`).
2. Con el MCP de Resolve (`resolve_mcp.preparar_resolve`) abre Resolve si está cerrado (y solo entonces carga el proyecto más reciente).
3. `resolve_bridge.ejecutar('detectar')` renderiza el audio del timeline.
4. Transcribe → IA de texto corrige, elige palabra clave y emojis → arma bloques → añade SFX → escribe `.dynamic.json/.srt` + `subtitles_manifest.json`.
5. Vista previa REAL renderizada por Resolve → coloca en el timeline.

«Generar subtítulos» usa el MISMO `_run_pipeline`. «Regenerar» (`_on_update`) reusa las marcas guardadas sin transcribir otra vez.

## 3. Estructura de carpetas (numeradas por orden de uso)

```
CineCaptions/
  LEEME.txt, REGISTRO_DE_CAMBIOS.txt, Instalar_CineCaptions.exe
  1_codigo/      EL PROGRAMA (Python). Principal: "CineCaptions (script principal).py" (~9300 líneas)
  2_recursos/    Lo que viaja dentro del .exe: resolve_scripts/ (Lua=Free, Python=Studio, gemelos), guia_estilo/ (el .drt de «Crea tu estilo»),
                 motor_qwen/ (su propio Python 3.12), plantillas_incluidas/, locales/, fonts/,
                 sfx_library/, emojis/. NO renombrar sus subcarpetas (el código las busca por nombre).
  3_compilar/    Construir_Instalador.ps1, requirements.txt (versiones FIJAS), cinecaptions.spec,
                 Instalador.cs, encabezados.py, documentar.py, huellas.json
  4_diseno/      banner/, icono/, notas/ (nada va al .exe)
  5_licencias/   Administrador de licencias + kit cinema_licencias (no va al .exe)
  6_compilacion/ TEMPORAL (venv314, PyInstaller). Se puede borrar.
```

## 4. Módulos clave (1_codigo)

| Archivo | Para qué |
|---|---|
| `CineCaptions (script principal).py` | Ventana (`SubtitleApp`), Editor de palabras (`WordTagWindow`, `LienzoPalabras`), packs (`PlantillasWindow`), `_run_pipeline`, `main()` |
| `dynamic_subtitles.py` | «Cerebro»: frases, roles, bloques (`puntuar_palabra`, `build_dynamic_cues`, `build_manual_cues`, `build_destacados_cues`) |
| `ia_texto.py` + `2_recursos/motor_qwen/motor_texto.py` | IA de texto local: correcciones, palabra principal/secundaria, emojis, quitar signos (`marcar_todo`) |
| `motor_voz.py` + `motor_qwen/motor_qwen.py` | Voz Qwen3-ASR + alineador, en Python 3.12 aparte, hablan por líneas `PROGRESO\|/ESTADO\|/LISTO\|` |
| `subtitle_transcriber.py` | Whisper (respaldo), traducción Argos, escritura de .srt/manifiestos |
| `resolve_mcp.py` | MCP oficial de Resolve 21.1+ (abrir Resolve, ejecutar scripts) |
| `resolve_bridge.py` | API externa (Studio) / Puente (Free) / modo manual |
| `plantillas.py`, `packs_drt.py`, `vistas_reales.py` | Packs de estilos `.drt/.drb` y vistas previas reales. `packs_drt.posiciones_de_drb` lee el Pan/Tilt/Zoom de cada clip del propio `.drb` (incluido el bloque `imagen`); `plantillas.bloque_imagen/estructura_de` alimentan las vistas |
| `mograf_ui.py`, `brillo_ui.py`, `efectos_ui.py` | Motion Graphics (barrido de pantalla, entrada de tarjetas, título cinético, traza de luz, formas del fondo, HUD de Inicio), barridos de luz de botones y fondo vivo |
| `emojis.py`, `sfx_rules.py`, `sfx_studio.py`, `sfx_audio.py` | Emojis y efectos de sonido |
| `licencia.py`, `ventana_licencia.py` | Licencia Lemon Squeezy |
| `qt_kit.py`, `tema.py`, `i18n.py`, `ajustes_ui.py`, `un_clic_ui.py`, `efectos_ui.py` | Interfaz, temas, idiomas, Ajustes, pantalla GO |
| `version.py` | `APP_VERSION`, `APP_NOMBRE`, `APP_AUTOR`, `APP_CREDITO` |

## 5. Cómo se comunica con Resolve

El programa corre FUERA de Resolve; sus scripts, DENTRO. Vías (mejor a peor): **A)** MCP oficial · **B)** API externa (solo Studio) · **C)** Puente Lua (Free, `CineCaptions_Puente.lua` vigila `~/DaVinciSubtitles/jobs/`) · **D)** manual.

Intercambio por **archivos** en `%USERPROFILE%\DaVinciSubtitles`: `subtitles_manifest.json`, `<vídeo>.dynamic.json/.srt`, `video_detectado.json`, `sfx_*_pendiente.json`, `vista_real_*.json`. Junto a cada `.json` va un `.lua` (sidecar) porque Resolve Free 21.1 quitó `io` y solo puede leer con `loadfile`.

**Colocación real:** `CineCaptions_Subtitulos.lua` (Free) y su gemelo `CineCaptions.py` (Studio). **MISMA lógica: un cambio va en los dos.**

## 6. Dónde cambiar qué

| Quiero cambiar… | Archivo |
|---|---|
| versión | `1_codigo/version.py` + línea `VERSION` de `2_recursos/resolve_scripts` (+ `PAQUETE` en `CineCaptions_Puente.lua`) + `ajustes_ui.NOTAS_VERSION` |
| lo que hace GO / su orden | script principal, `_go`, `_go_generar`, `_run_pipeline` |
| qué palabra es PRINCIPAL | `dynamic_subtitles.py` (`puntuar_palabra`) e `ia_texto.py` (`_roles_por_ia`) |
| prompt de la IA | `2_recursos/motor_qwen/motor_texto.py` (`SISTEMA`, `PALETA`) |
| qué signos se quitan | `ia_texto.py` (`SIGNOS`, `sin_signos`) |
| cuándo suena cada efecto | `2_recursos/resolve_scripts/sfx_rules.json` (sin código) |
| cómo se coloca en Resolve | `CineCaptions_Subtitulos.lua` **y** `CineCaptions.py` |
| nombres de roles de un pack / bloque «imagen» / emoji en el slot | `packs_drt.py` (`ALIAS`) **y** los dos `parsear_nombre_pack` y `colocar_emojis` de los gemelos (+ los dos «Importar Estilos») |
| la plantilla base y la guía «Crea tu estilo» | `4_diseno/plantilla_base_cinema/` (ver «PLANTILLA BASE - como se hizo.txt»); la guía va a `2_recursos/guia_estilo/` |
| animaciones y Motion Graphics | `mograf_ui.py` (todas las pantallas e Inicio), `brillo_ui.py` (botones), `efectos_ui.py` (fondo) |
| licencia (tienda, producto, pruebas) | constantes `LIC_*` de `licencia.py` |
| colores, tipografía, controles | `qt_kit.py` |
| textos traducidos | `2_recursos/locales/<idioma>.json` (clave = texto en español) |
| qué entra en el .exe | `3_compilar/cinecaptions.spec` |
| pasos/textos del instalador | `3_compilar/Instalador.cs` |

## 7. Reglas obligatorias (no romper nada)

1. **Encabezado:** todo archivo de código empieza con
   `# CineCaptions · By Cinema Productions` y `# <ruta> — <qué es>`.
   Archivo nuevo → añadir su descripción en `3_compilar/encabezados.py` y correr `python 3_compilar/encabezados.py`.
2. **Todo texto visible** va en `tr("texto en español")` y su traducción en `2_recursos/locales` (en, pt, fr, de, it).
3. **Lo pesado** (red, IA, Resolve, disco) en un hilo. La interfaz SOLO se toca desde su hilo (`qt_kit.correr_en_hilo`, `despues`, o la cola `msg_queue`).
4. **Gemelos Lua/Python:** un cambio de comportamiento va en los dos.
5. **Librerías con versión FIJA** en `3_compilar/requirements.txt`. Cuidados: `av` se queda en 18.1.0; `huggingface_hub` 1.33.0; `sacremoses` 0.1.1; `argostranslate` se instala SIN dependencias; el motor Qwen3 va aparte (Python 3.12.10, torch 2.10.0).
6. **Los IDs de licencia** van en constantes `LIC_*` de `licencia.py`, nunca en un archivo editable por el cliente.
7. **Probar en un proyecto de prueba** de Resolve, nunca en los reales.
8. **Atajos que no se pierden:** 1–6 (pinceles), Ctrl+Z, Ctrl+Y, Esc.
9. **Nombres internos que se conservan:** carpetas `RCS · <pack> · <formato>` del Media Pool, emojis `rcs_emoji_*.png`, timeline `RCS · temporal` y la carpeta de datos `%USERPROFILE%\DaVinciSubtitles`. Renombrarlos duplica packs o deja el programa vacío.
10. **No leas ni edites** `6_compilacion/`, `__pycache__/` ni archivos `.lock`.

## 8. Datos del usuario (fuera del programa)

- `%USERPROFILE%\DaVinciSubtitles\` → preferencias, licencia firmada (`licencia\licencia.dat`), marcas por vídeo (`<vídeo>.marcas.json`), plantillas del usuario, jobs, logs, `diagnostico.txt`.
- `%LOCALAPPDATA%\Programs\CineCaptions\` → programa instalado.
- `%LOCALAPPDATA%\CineCaptions\motor_qwen\` → motor de voz/IA (Python 3.12).
- `%USERPROFILE%\.cache\huggingface\` → modelos.

## 9. Compilar

```powershell
powershell -ExecutionPolicy Bypass -File 3_compilar\Construir_Instalador.ps1
```
Hace: venv → documentación automática → copia y valida sintaxis → PyInstaller (3–6 min) → **autoprueba** (si algo no carga, NO arma el .exe) → compila instalador C# → deja `Instalar_CineCaptions.exe`. `-SoloInstalador` reusa lo ya compilado.

## 10. Licencias

Lemon Squeezy (tienda `LIC_TIENDA_LS = 488116`, producto por nombre «CineCaptions» hasta tener ID). Estado firmado por equipo, 7 días sin internet, verificación cada 12 h. Se exige al abrir, en GO, al generar y al regenerar; el motor se niega sin licencia.
**`LIC_ACEPTAR_PRUEBA = True` (modo pruebas): ponerlo en `False` ANTES de vender.**

## 11. Registro de cambios

Cada compilación anota los cambios sola. Para dejar el porqué:
```powershell
6_compilacion\venv314\Scripts\python.exe 3_compilar\documentar.py --nota "qué cambié y por qué"
```

## 12. Cómo trabajar con este proyecto sin gastar tokens

- Lee este archivo; para el detalle de una parte, abre solo esa sección del LEEME.
- **Busca antes de leer:** Grep por nombre de función/clase en vez de abrir archivos completos. El script principal tiene ~9300 líneas, `CineCaptions_Subtitulos.lua` ~6500 y `CineCaptions.py` (Resolve) ~6200.
- Lee con rango de líneas (`view_range`) solo la función que vas a tocar.
- Cambios mínimos: muestra solo el diff, sin reescribir archivos enteros.
- Si tocas algo de Resolve, recuerda el gemelo Lua/Python y la tabla de la sección 6.
- No regeneres ni pegues el índice/mapa del LEEME (secciones 13 y 14): los rehace `documentar.py` solo.

---
## Rendimiento (v5.3)

- **GO**: `_precargar_motores()` (script principal) carga y calienta en segundo plano la voz y la IA de texto mientras Resolve da el audio. `motor_voz` y `ia_texto` mantienen servidores persistentes (`motor_qwen.py --servidor`, `motor_texto.py`, línea `TIPO|texto`); `motor_voz.modo_gpu()` decide residente (≥22 GB) / solapado (≥14,5 GB) / secuencial. Con la RTX 5070 Ti (15,9 GB): voz 9,8 s + IA de texto 5,7 s tras precarga (antes ~118 s en frío).
- **Whisper**: modelo en caché, `BatchedInferencePipeline` si el audio dura más de 45 s en CUDA; `_CUDA_FALLO` evita el segundo intento con CUDA tras un fallo de cuBLAS (se colgaba para siempre).
- **Interfaz**: `ritmo_ui.ritmo` mide el retraso real de un temporizador de 250 ms y alarga el intervalo de FondoVivo y de la esfera (x1,5 / x2,2) si el bucle va saturado; baja despacio y con retroceso anti-oscilación. Nunca pausa. Inicio es la pantalla cara (≈55–70 % de un núcleo, pinta a mano con QPainter); el resto de pantallas ≈7–16 %.
- **Colocación en Resolve**: 46 bloques ≈ 16 s (≈0,35 s por bloque y llamada a la API); no se optimizó más porque cada `SetProperty`/`AppendToTimeline` es una llamada a Resolve.

*CineCaptions · By Cinema Productions · © 2026 — versión del contexto: v5.3.0 (2026-10-05)*
