# Compilar, versiones, instaladores (Windows y Mac)

## instalador-cs — Instalador C#: banner, rutas, pasos

**Qué:** Instalador (C#): banner animado con el astrolabio girando, rutas de instalación, pasos con spinner

**Dónde:** `3_compilar/Instalador.cs` (`Banner`, `ListaPasos`, `ListaRutas`, `Instalacion.Rutas`); imágenes: `4_diseno/banner/crear_banner.py` (banner.jpg + `3_compilar/banner_capas/`)

## version — Versión del programa

**Desde la 5.20 (pedido del usuario: «en vez de tanto número»): DOS números** (5.20, 5.21…). `version.py` dice `5.20`; `3_compilar/sincronizar_version.py` acepta 2 o 3 números y `--subir` sube el ÚLTIMO (5.20 → 5.21); `actualizaciones._partes` lee «5.20» como 5.20.0 y `corta()` enseña «5.20» (lo que llega del manifiesto). **Compatibilidad:** los 5.5.x instalados solo entienden x.y.z: `Publicar_Version.ps1` escribe en version.json `5.20.0` (`$versionManifiesto`); los archivos se siguen llamando `_5.20`. El instalador rellena a 4 números (5.20.0.0).

**Qué:** Versión

**Dónde:** `version.py`

## mac — Instalador de Mac (.app/.pkg/.dmg)

**Qué:** Instalador de Mac (Apple Silicon): .app + .pkg + .dmg; no compila desde Windows (Mac o GitHub Actions)

**Voz dentro del programa (v5.58):** desde la 5.34 Whisper, Argos y ONNX corren en un Python 3.14 aparte que solo existe en Windows
(`motor_compat`), y el Mac salía SIN ellos: GO fallaba en «Transcribiendo» con «El motor auxiliar Python 3.14 está configurado para Windows
x64» (la autoprueba solo lo daba como aviso). Ahora `Construir_Instalador_Mac.sh` instala `2_recursos/motor_compat/requirements.txt` con
`--no-deps --only-binary` (onnxruntime 1.24.4 en Apple Silicon y 1.23.2 en Intel, la última con rueda Intel, en vez de onnxruntime-directml) y
comprueba que se importan; `cinecaptions_mac.spec` las declara (worker.py viaja como dato y PyInstaller no lo analiza: hiddenimports,
collect_submodules, `copy_metadata`, obligatorio para httpx2/httpcore2, y `collect_dynamic_libs('ctranslate2')`) y corta la compilación si
falta alguna; la autoprueba del motor es CRÍTICA fuera de Windows (`tareas_instalador`, con VAD, int8, audio a 16 kHz y Argos sin red). En
el programa, `motor_compat.EN_PROCESO` corre `worker.atender` en el mismo proceso (ver `voz-ia`). macOS mínimo real: 14 (PySide6 6.12, av,
numpy y onnxruntime): desde la 5.58 lo piden el .pkg (`os-version min`), la app (`LSMinimumSystemVersion`) y la bienvenida; antes decía 12 y en
12-13 se instalaba y no abría. Si cambia la línea `onnxruntime-directml==` del requirements del motor, el `sed` del .sh lo detecta y corta.

**Dónde:** `7_mac/` · `Construir_Instalador_Mac.sh`, `cinecaptions_mac.spec`, `pkg/scripts/postinstall` (corre `--tarea scripts` y `fuentes` como el usuario); leer `7_mac/0_LEEME.txt`. SIN PROBAR en una Mac real

## compilar-win — Compilar, versiones y desinstalador de Windows

**Qué:** Compilar / versiones / desinstalador de Windows (v5.3.2): `Actualizar_Windows.ps1` (huella del código → sube la versión +1 si cambió → `Construir_Instalador.ps1` → deja `INSTALADORES/Windows/Instalar_CineCaptions_<ver>.exe` y borra los viejos; `-Comprobar` dice si está al día; `-Registrar` da por bueno el instalador actual sin compilar, p. ej. tras tocar solo herramientas de desarrollo como `mapa_codigo.py`/`mcp_cinecaptions.py`, que no entran en la huella); `3_compilar/sincronizar_version.py` copia `APP_VERSION` a los scripts de Resolve y al Puente (antes se olvidaba: app 5.3.1 con scripts 5.3.0 = aviso «otra versión instalada»). Desinstalador en `3_compilar/Instalador.cs`: `Sitio` (carpetas/registro; env `CINECAPTIONS_PRUEBA_RAIZ` = sandbox de pruebas), `Borrado` (rutas largas, procesos por ruta, RunOnce, rastros del registro), `Instalacion.Desinstalar` (8 pasos), casillas «datos/licencia» y «modelos» (`/borrardatos /borrarmodelos /todo`; silencioso sin /todo conserva). Prueba: fixture en `C:\ccp*` + env de prueba + `Desinstalar.exe /desinstalar /silencioso /todo` (cuidado: la tarea `scripts` de Python sí escribe en `C:\ProgramData\Blackmagic Design`)

**Dónde:** 

## mac-actualizar — Mantener el instalador de Mac al día

Tras CUALQUIER mejora del programa (`1_codigo`, `2_recursos`, `3_compilar` o `7_mac`): `powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1` (sube a GitHub privado, compila Apple Silicon + Intel y deja `CineCaptions_Mac_*_<ver>.dmg` en `INSTALADORES/Mac`; ~15 min, correr en segundo plano). `-SoloDescargar` solo baja la última compilación buena. Detalles en `7_mac/0_LEEME.txt`. Sin probar en una Mac real.

**Espejo PÚBLICO otra vez (v5.57, 2026-10-31, pedido del usuario: «no quiero pagar GitHub… que pueda subir actualizaciones gratis»):** `CineCaptions-mac-build` volvió a público: Mac compila gratis en Actions, Windows en el PC y las actualizaciones salen del repositorio público `CineCaptions-releases` (sin coste). Precio aceptado: cualquiera puede leer el código del espejo (y la sal de `licencia.dat`); alternativa gratis sin hacer: el código CIFRADO en el espejo y la clave como secreto de Actions. `gh` tiene que estar con la cuenta AlejandroPiedrasanta (la otra cuenta del navegador, alejandropiedrasanta1-ui, no ve los repositorios).

**Espejo privado (v5.52):** `CineCaptions-mac-build` pasó a PRIVADO (siendo público, cualquiera leía todo el código y la sal de `licencia.dat`). Coste: los minutos de macOS cuentan ×10 contra los 2000 gratis del mes (unas 14 compilaciones de ~14 min); pasado el cupo GitHub no arranca la compilación («spending limit», ya pasó el 2026-10-09 en el repo privado) hasta el mes siguiente o hasta poner un pago. Volver a público es `gh repo edit … --visibility public`. El espejo sube SOLO lo que el repo privado no ignora: su `.gitignore` = el del privado + certificados y claves (`*.pfx *.p12 *.pem *.key firma.json .env*`, también excluidos en robocopy) y `git rm --cached` + `add` antes de cada commit (antes subía `desktop.ini` y habría subido `firma.json` o un `.pfx`).

## actualizaciones — Actualizaciones automáticas (cliente y publicación)

**Qué:** v5.3.5. El programa lee un `version.json` público, avisa con el chip «Nueva versión X ↑» de Inicio, descarga el instalador de SU plataforma, comprueba el SHA-256 y lo lanza. Nunca instala sin que el usuario pulse y confirme.

**Cliente:** `actualizaciones.py` · `comprobar` (manifiesto → estado `nueva`/`al_dia`/`error` + `archivo` {url, sha256, tam}), `descargar` (a `%TEMP%/cinecaptions_actualizacion`, avance, **rechaza** sin huella o con huella distinta y borra el archivo), `instalar` (Windows: `Instalar_….exe /empezar` desprendido, él cierra el programa, reemplaza y reabre; Mac: `open` del .dmg), `clave_plataforma` (`windows`/`mac_arm64`/`mac_x86_64`). Script principal: `_revisar_actualizaciones_auto` (20 s tras abrir, como mucho cada 12 h; prefs `actualizaciones_auto`, `actualizacion_revisada`, `actualizacion_pendiente`, `actualizacion_avisada`, `canal_beta`, `url_actualizaciones`), `_ofrecer_actualizacion` (pregunta; no deja si GO/editor trabajan), `_descargar_actualizacion` (Dialogo 520×560 SIN marco y translúcido + `actualizar_ui.PanelActualizacion(sin_marco=True)` desde v5.49 —el panel pinta el fondo redondeado, lleva la ✕ dentro (`BotonCerrar`) y se arrastra; «Cancelar» es `BotonPildora`; iconos Phosphor pedidos con `QIcon.pixmap(lado)` (pedirlos × dpr los inflaba 1,5× a 150 %); para verla de verdad: `grab()` de la propia ventana, NUNCA capturar la pantalla (con escala 150 % la zona no coincide y sale el escritorio del usuario) —propuesta A + B del usuario: anillo con el %, «5.48 → 5.49», MB / velocidad de los últimos ~4 s / tiempo que falta, los tres pasos con su tiempo, «QUÉ TRAE LA x» con las notas del manifiesto partidas en frases y «Cancelar» (cierra el diálogo → `cancelado`)—; cierra la app 1,5 s después en Windows), chip en `_pintar_opciones_go`. Ajustes > Acerca de: interruptor «Avisarme de las actualizaciones», «Buscar actualizaciones» (`ajustes_ui.buscar_actualizaciones` → `_ofrecer_actualizacion`), «Recibir versiones beta».

**Publicar:** `Publicar_Version.ps1 -Notas "…"` (tras `Actualizar_Windows.ps1` y `Actualizar_Mac.ps1`): arma `INSTALADORES/version.json` (sha256/tam por plataforma), crea la release `v<ver>` en el repositorio PÚBLICO `AlejandroPiedrasanta/CineCaptions-releases` (solo instaladores; el código sigue en el privado) y comprueba `releases/latest/download/version.json`. `-SinSubir` solo genera el manifiesto; `-CrearRepo` crea el repositorio la primera vez; `-Canal beta` guarda la versión en la clave `beta`. Se puede apuntar a otro sitio sin recompilar con `CINECAPTIONS_URL_ACTUALIZACIONES` o la pref `url_actualizaciones`.

**Firma del manifiesto (v5.52):** `version.json` lleva `"firma": {"alg": "ed25519", "clave": "<id>", "valor": "<base64>"}` sobre el JSON canónico sin la firma (`actualizaciones.bytes_firmados`). `Publicar_Version.ps1` llama a `3_compilar/firmar_manifiesto.py` (comprueba la firma con `CLAVES_FIRMA` antes de escribir; sin clave no publica). El cliente (`firma_valida` dentro de `_interpretar`, para `comprobar` y `comprobar_ligero`) da `error` «manifiesto sin firma válida» y no ofrece nada: ni con la cuenta de GitHub robada ni cambiando `url_actualizaciones` se cuela un instalador (su SHA-256 va dentro de lo firmado). Ed25519 en Python puro (`firma_ed25519.py`, vectores del RFC 8032; ~3 ms; nada de `cryptography`, otro .pyd sin firma). Claves privadas FUERA del repo en `~/CineCaptions_claves/actualizaciones_{principal,reserva}.key` (la de reserva, copiada a USB/nube); perder las dos = los programas instalados ya no se actualizan. `--claves-nuevas` crea las que falten e imprime las públicas.

**Trampa de la carpeta de trabajo (v5.3.9):** el instalador lanzado por el programa HEREDA su carpeta de trabajo, que es la carpeta de instalación (los accesos directos la fijan así); un proceso con su carpeta de trabajo dentro de una carpeta impide renombrarla → «No puedo reemplazar la versión instalada (algún archivo está en uso)». Arreglo en los dos lados: `Instalador.cs` · `Main` (tras leer las opciones, `/dir` pasa a ruta absoluta y se hace `SetCurrentDirectory(temp)`; así también arregla las actualizaciones lanzadas por versiones viejas del programa) y `CopiarPrograma` (12 reintentos de `Directory.Move`, recierra el programa en el 4.º y el 8.º); cliente: `actualizaciones.instalar` lanza con `cwd=` la carpeta del instalador. El instalador INSTALA SOLO al abrirse (solo el desinstalador espera el botón): probarlo exige sandbox + matarlo antes de las tareas (`scripts`, fuentes, modelos tocan el equipo real). Prueba válida: sandbox `C:\ccp_*` con una carpeta ya «instalada» (falsa), instalador con `WorkingDirectory` dentro y esperar a que aparezca `inst.anterior`; matar el instalador y los `CineCaptions.exe` del sandbox, borrar con `\\?\` y la clave `Software\CineCaptionsPrueba`.

**Pruebas:** servidor HTTP local + `version.json` falso (huella buena, mala, ausente, cancelar, 404, servidor caído) y la app `offscreen` con `USERPROFILE` falso para no ensuciar las prefs reales. Desde la 5.52 el falso tiene que ir firmado: clave de prueba con `firma_ed25519.nueva_privada()` metida en `actualizaciones.CLAVES_FIRMA` solo dentro de la prueba (o `firmar_manifiesto.py` sobre una copia en el scratchpad); también vale `CINECAPTIONS_URL_ACTUALIZACIONES=file:///…`.

**Vigilancia de versiones (v5.4.2):** `actualizaciones.comprobar_ligero` (ETag + `If-None-Match`: casi siempre un 304 sin cuerpo) corre cada `INTERVALO_AUTO_S` = 10 s desde un `QTimer` del script principal (`_iniciar_vigia_actualizaciones` → `_revisar_actualizaciones_auto`); sin internet pasa a 60 s tras 3 fallos y lo anota una vez. Al detectar una versión nueva: chip de Inicio, `_avisar_actualizacion` (`ajustes_ui.pedir_actualizacion`: cuadro con las mejoras del manifiesto + «Actualizar ahora» / «Más tarde», una vez por versión y sesión, espera si GO/editor trabajan) y el botón de Ajustes. Ajustes > Acerca de usa `ajustes_ui.ControlActualizacion` (estado, «Leer notas», «Buscar actualizaciones» / «Actualizar a la X»). Tras instalar, `_mostrar_novedades_si_toca` compara la pref `version_vista` y enseña `ajustes_ui.mostrar_novedades` (todas las notas desde la versión anterior, `notas_desde`). `Publicar_Version.ps1` sin `-Notas` toma las mejoras de `ajustes_ui.NOTAS_VERSION` (`3_compilar/notas_de_version.py`), una por línea con viñeta: eso es lo que enseña el aviso. Una versión instalada ANTES de la 5.4.2 sigue mirando cada 12 h: se actualiza con «Buscar actualizaciones» o el chip.

## nota — Compilar: carpetas de solo lectura (BorrarCarpeta)

Si `Actualizar_Windows.ps1` falla con «Acceso denegado» al borrar `6_compilacion/fuentes|dist|instalador`: `desktop.ini` y `.cf/` (Explorador/sincronización) marcan las carpetas como solo lectura y `[IO.Directory]::Delete` no las borra. `3_compilar/Construir_Instalador.ps1` ya usa `BorrarCarpeta` (quita atributos de hijos Y de la carpeta raíz, luego borra). Si PyInstaller da PermissionError en `6_compilacion/dist`, quitar atributos de `dist` y repetir.
