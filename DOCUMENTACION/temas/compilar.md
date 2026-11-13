# Compilar, versiones, instaladores (Windows y Mac)

## instalador-cs — Instalador C#: banner, rutas, pasos

**Qué:** Instalador (C#): banner animado con el astrolabio girando, rutas de instalación, pasos con spinner

**Dónde:** `3_compilar/Instalador.cs` (`Banner`, `ListaPasos`, `ListaRutas`, `Instalacion.Rutas`); imágenes: `4_diseno/banner/crear_banner.py` (banner.jpg + `3_compilar/banner_capas/`)

## equipo-al-dia — El instalador pone el equipo al día («Tu equipo»)

**Qué (v5.72, pedido del usuario: «que el .exe actualice el PC: dependencias y drivers, sin ventanas de CMD ni interrumpir; dejar el entorno optimizado para evitar errores de compatibilidad»):** paso «Tu equipo» del instalador, justo después de copiar el programa y ANTES del motor y la autoprueba (Visual C++ lo necesitan sus DLL): `Instalador.cs` corre `--tarea equipo <estado> interactivo|silencioso` (`Tarea(..., extra)`; en `/prueba` se omite) → `tareas_instalador._tarea_equipo`: la ficha (tema `ficha-equipo`), `equipo_al_dia.poner_al_dia()` y la ficha guardada con `puesta_al_dia` {cuando, hecho, pendiente, fallos}. Nunca para la instalación (falla como Aviso). Su OK dice «GPU · driver · RAM · todo listo / puesto al día: … / revisa el Registro: …».

**Qué pone al día:** (1) sin administrador: la GPU de alto rendimiento (`HKCU\Software\Microsoft\DirectX\UserGpuPreferences`, `GpuPreference=2;`) para CineCaptions.exe y el Python de cada motor, solo con 2+ GPU y sin pisar una preferencia que ya exista (`gpu_preferida`); (2) con administrador, en UN proceso elevado `--tarea equipo_admin <estado> <plan.json> <salida.json>` (`ShellExecuteExW` «runas», ventana oculta, `hwnd` = la ventana de delante para que el permiso no salga parpadeando abajo): Visual C++ x64 si «falta» (winget `Microsoft.VCRedist.2015+.x64` → si no, `aka.ms/vs/17/release/vc_redist.x64.exe` con la firma comprobada por `WinVerifyTrust`, `/install /quiet /norestart`) y el driver de la GPU por Windows Update (`Microsoft.Update.Session` con comtypes dinámico: busca sin admin `IsInstalled=0 and Type='Driver'`, filtra clase Display + fabricante y solo uno MÁS nuevo que el instalado; descarga e instala con `ForceQuiet`, sin reiniciar) si el NVIDIA es < 595.

**Reglas:** la ventana de permiso de Windows (UAC) NO se puede esconder: sale una vez y solo si hay algo de sistema que hacer; cancelada → «pendiente». En `/silencioso` (actualizaciones automáticas) nada que pida permiso: queda en `pendiente`. El driver solo con DaVinci Resolve cerrado (se mira antes de buscar y otra vez dentro del proceso elevado). Nada de PowerShell ni cmd; de terceros solo Microsoft; nunca se actualizan otros programas del usuario; desde el código fuente no instala nada del sistema (`_elevar`). Lo que no se pudo lo ve el dueño en la ficha (app Ventas) y el usuario en el Registro (`vigilancia.avisar_equipo`).

**Motores al abrir:** `vigilancia.poner_motores_al_dia()` (desde `revisar_salud_al_arrancar`, solo el .exe de Windows): si el motor auxiliar no está `instalado()` (librerías distintas de las fijadas) → `motor_compat.instalar()` (incremental; ahora con `_LOCK_INSTALAR`, de uno en uno con el `_servidor()` que también lo llama); y `motor_voz.completar_requisitos()` (`--no-deps`, solo lo que falta) bajo `_LOCK_REQUISITOS`: mientras, `esperar_puesta_al_dia()` frena los arranques del motor de voz, `_lanzar_script` y el servidor de `ia_texto` (fuera del hilo de la interfaz; en él, `precargar()` no precarga).

**Probado (sin compilar, 06-11):** 40 comprobaciones sin tocar el sistema (plan simulado: driver más nuevo elegido, silencioso, Resolve abierto, UAC cancelado, sin VC++; GPU preferida con un winreg falso; tarea `equipo`/`equipo_admin`; telemetría con `_post` falso; candado del motor; `WinVerifyTrust` con Resolve.exe y un .exe sin firma), búsqueda REAL en Windows Update (solo buscar: 6-12 s, 0 drivers con el 621.14 del autor) y el C# compila. SIN probar: instalar de verdad Visual C++ o un driver (cambia el sistema), el proceso elevado con el .exe compilado.

## version — Versión del programa

**Desde la 5.20 (pedido del usuario: «en vez de tanto número»): DOS números** (5.20, 5.21…). `version.py` dice `5.20`; `3_compilar/sincronizar_version.py` acepta 2 o 3 números y `--subir` sube el ÚLTIMO (5.20 → 5.21); `actualizaciones._partes` lee «5.20» como 5.20.0 y `corta()` enseña «5.20» (lo que llega del manifiesto). **Compatibilidad:** los 5.5.x instalados solo entienden x.y.z: `Publicar_Version.ps1` escribe en version.json `5.20.0` (`$versionManifiesto`); los archivos se siguen llamando `_5.20`. El instalador rellena a 4 números (5.20.0.0).

**Qué:** Versión

**Dónde:** `version.py`

## mac — Instalador de Mac (.app/.pkg/.dmg)

**Qué:** Instalador de Mac (Apple Silicon): .app + .pkg + .dmg; no compila desde Windows (Mac o GitHub Actions)

**Voz dentro del programa (v5.58):** desde la 5.34 Whisper, Argos y ONNX corren en un Python 3.14 aparte que solo existe en Windows
(`motor_compat`), y el Mac salía SIN ellos: GO fallaba en «Transcribiendo» con «El motor auxiliar Python 3.14 está configurado para Windows
x64» (la autoprueba solo lo daba como aviso). Ahora `Construir_Instalador_Mac.sh` instala `2_recursos/motor_compat/requirements.txt` con
`--no-deps --only-binary` (onnxruntime 1.31.1 en Apple Silicon —2026-11-05; Windows sigue en onnxruntime-directml 1.24.4, la última con DirectML— y 1.23.2 en Intel, la última con rueda Intel, en vez de onnxruntime-directml) y
comprueba que se importan; `cinecaptions_mac.spec` las declara (worker.py viaja como dato y PyInstaller no lo analiza: hiddenimports,
collect_submodules, `copy_metadata`, obligatorio para httpx2/httpcore2, y `collect_dynamic_libs('ctranslate2')`) y corta la compilación si
falta alguna; la autoprueba del motor es CRÍTICA fuera de Windows (`tareas_instalador`, con VAD, int8, audio a 16 kHz y Argos sin red). En
el programa, `motor_compat.EN_PROCESO` corre `worker.atender` en el mismo proceso (ver `voz-ia`). macOS mínimo real: 14 (PySide6 6.12, av,
numpy y onnxruntime): desde la 5.58 lo piden el .pkg (`os-version min`), la app (`LSMinimumSystemVersion`) y la bienvenida; antes decía 12 y en
12-13 se instalaba y no abría. Si cambia la línea `onnxruntime-directml==` del requirements del motor, el `sed` del .sh lo detecta y corta.

**«No abre» tras instalar (v5.85; clientes de la 5.78 y la 5.84):** reproducido instalando el .dmg PUBLICADO en Macs de GitHub con pantalla
(macOS 15, 26 e Intel): la tarea `modelo` del postinstall baja Whisper con barras `tqdm`, que crean un candado de `multiprocessing`; en Mac eso
lanza el `resource_tracker` con el propio ejecutable y `-c from multiprocessing.resource_tracker import main;main(N)`. Sin `freeze_support` ese
hijo arrancaba CineCaptions ENTERO (offscreen, heredado del postinstall), se quedaba para siempre en la ventana de licencia invisible
(`QDialog::exec`, 30-60 % de CPU, padre 1) y con `~/.cinecaptions.lock`: cada clic en la app salía en silencio («ya se encuentra en
ejecución») hasta reiniciar la Mac. Arreglo (tema `arranque-seguro`): `arranque_seguro.atender_hijo()` lo primero del script principal
congelado (cualquier hijo `-c`/`-m` de una librería corre su código y sale), candado que se cura (una copia atascada se cierra), arranque con
tope (4 min sin ventana y sin latir → sale solo), el postinstall quita los huérfanos de versiones anteriores y pone tope a cada tarea, y la
autoprueba CRÍTICA «Procesos auxiliares» hace fallar la compilación si vuelve a pasar. Mientras tanto, al cliente le basta con reiniciar
la Mac o forzar la salida de «CineCaptions» en el Monitor de Actividad. Probar en Mac sin compilar: rama temporal del espejo con un
workflow que instala el .dmg publicado, lo abre con `open -a` y guarda capturas, ventanas (`CGWindowListCopyWindowInfo`), `sample`, el
candado y `~/DaVinciSubtitles` (bloquear `cinecaptions.shop` en `/etc/hosts` para no ensuciar los errores de Ventas); borrar la rama al acabar.

**Todos los estilos y funciones (v5.86; el usuario: «en Mac aún no están todos los estilos y funciones»):** el .app lleva los mismos
`2_recursos` y estilos que Windows (comprobado carpeta por carpeta contra el espejo); lo que faltaba eran dos motores: el recorte de persona
(«detrás de ti», persona delante de la PRO, cara de la placa del Kinetic, posiciones PRO), apagado en el Mac «por no estar probado», y el motor
de voz e IA Qwen3 (solo Windows). Ahora el recorte corre dentro del programa (ver `edicion-pro`) y el motor Qwen3 se instala en las Mac con
Apple Silicon (ver `voz-ia`); en las Intel no hay PyTorch nuevo: Whisper y reglas. Probar sin compilar: ramas temporales del espejo con un
workflow que monta el entorno como `Construir_Instalador_Mac.sh` y corre un script de prueba (el video de la vista del Kinetic para el
recorte; una voz de `say` para Qwen, porque las vistas no tienen audio). En las Macs de GitHub no hay tarjeta (`mps` no disponible): Qwen va en la CPU.

**La ventana del .dmg (v5.87; el usuario: «en Mac el instalador hazlo más intuitivo, se verá mejor», con la del de VirtualBox):**
fondo CLARO con la marca y dos tarjetas («1 Doble clic para instalar» sobre «Instalar CineCaptions», «2 Ábrelo desde Aplicaciones» sobre
el acceso «Aplicaciones»), y en el pie los consejos que antes iban en un LEEME.txt (clic derecho › Abrir si macOS lo bloquea; scripting externo
de Resolve en Local) junto a «Desinstalar»; textos en español y, debajo, en inglés; sin extensiones ni barras. Claro a propósito:
con imagen de fondo el Finder escribe los nombres de los iconos en negro también en modo oscuro (comprobado). Lo arma `dmgbuild` 1.6.7
(`7_mac/dmg/ajustes_dmg.py`: posiciones de los iconos = centro, en puntos; la ventana mide 660 × 548: 520 del fondo, con la franja 460-520 de reserva, + 28 de barra de título) escribiendo el
.DS_Store sin el Finder; el fondo, `7_mac/dmg/fondo.png` + `fondo@2x.png` (→ TIFF con `tiffutil`), sale de `4_diseno/instalador_mac/fondo_dmg.html`.
La actualización automática (`actualizaciones._pkg_de_dmg`) toma cualquier `*.pkg` de la raíz del disco: el nombre del .pkg da igual.

**Dónde:** `7_mac/` · `Construir_Instalador_Mac.sh`, `cinecaptions_mac.spec`, `pkg/scripts/postinstall` (corre `--tarea scripts`, `fuentes` y `modelo` como el usuario y quita los huérfanos de multiprocessing); leer `7_mac/0_LEEME.txt`. SIN PROBAR en una Mac real

## compilar-win — Compilar, versiones y desinstalador de Windows

**Qué:** Compilar / versiones / desinstalador de Windows (v5.3.2): `Actualizar_Windows.ps1` (huella del código → sube la versión +1 si cambió → `Construir_Instalador.ps1` → deja `INSTALADORES/Windows/Instalar_CineCaptions_<ver>.exe` y borra los viejos; `-Comprobar` dice si está al día; `-Registrar` da por bueno el instalador actual sin compilar, p. ej. tras tocar solo herramientas de desarrollo como `mapa_codigo.py`/`mcp_cinecaptions.py`, que no entran en la huella); `3_compilar/sincronizar_version.py` copia `APP_VERSION` a los scripts de Resolve y al Puente (antes se olvidaba: app 5.3.1 con scripts 5.3.0 = aviso «otra versión instalada»). Desinstalador en `3_compilar/Instalador.cs`: `Sitio` (carpetas/registro; env `CINECAPTIONS_PRUEBA_RAIZ` = sandbox de pruebas), `Borrado` (rutas largas, procesos por ruta, RunOnce, rastros del registro), `Instalacion.Desinstalar` (8 pasos), casillas «datos/licencia» y «modelos» (`/borrardatos /borrarmodelos /todo`; silencioso sin /todo conserva). Prueba: fixture en `C:\ccp*` + env de prueba + `Desinstalar.exe /desinstalar /silencioso /todo` (cuidado: la tarea `scripts` de Python sí escribe en `C:\ProgramData\Blackmagic Design`)

**Dónde:** 

## mac-actualizar — Mantener el instalador de Mac al día

Tras CUALQUIER mejora del programa (`1_codigo`, `2_recursos`, `3_compilar` o `7_mac`): `powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1` (sube a GitHub privado, compila Apple Silicon + Intel y deja `CineCaptions_Mac_*_<ver>.dmg` en `INSTALADORES/Mac`; ~15 min, correr en segundo plano). `-SoloDescargar` solo baja la última compilación buena. Detalles en `7_mac/0_LEEME.txt`. Sin probar en una Mac real.

**Espejo PÚBLICO otra vez (v5.57, 2026-10-31, pedido del usuario: «no quiero pagar GitHub… que pueda subir actualizaciones gratis»):** `CineCaptions-mac-build` volvió a público: Mac compila gratis en Actions, Windows en el PC y las actualizaciones salen del repositorio público `CineCaptions-releases` (sin coste). Precio aceptado: cualquiera puede leer el código del espejo (y la sal de `licencia.dat`); alternativa gratis sin hacer: el código CIFRADO en el espejo y la clave como secreto de Actions. `gh` tiene que estar con la cuenta AlejandroPiedrasanta (la otra cuenta del navegador, alejandropiedrasanta1-ui, no ve los repositorios).

**Espejo privado (v5.52):** `CineCaptions-mac-build` pasó a PRIVADO (siendo público, cualquiera leía todo el código y la sal de `licencia.dat`). Coste: los minutos de macOS cuentan ×10 contra los 2000 gratis del mes (unas 14 compilaciones de ~14 min); pasado el cupo GitHub no arranca la compilación («spending limit», ya pasó el 2026-10-09 en el repo privado) hasta el mes siguiente o hasta poner un pago. Volver a público es `gh repo edit … --visibility public`. El espejo sube SOLO lo que el repo privado no ignora: su `.gitignore` = el del privado + certificados y claves (`*.pfx *.p12 *.pem *.key firma.json .env*`, también excluidos en robocopy) y `git rm --cached` + `add` antes de cada commit (antes subía `desktop.ini` y habría subido `firma.json` o un `.pfx`).

## actualizaciones — Actualizaciones automáticas (cliente y publicación)

**Con el programa CERRADO (v5.87; el usuario: «que de verdad notifiquen si sale una versión nueva aunque esté cerrado, que auto lo descargue y
se instalen tanto en Mac como en Windows»; en Mac eligió «sin contraseña»):** `1_codigo/actualizar_fondo.py`, corrido como
`CineCaptions --tarea actualizar_fondo`. Consulta el version.json FIRMADO; si hay versión nueva y CineCaptions no está abierto (el candado
`~/.cinecaptions.lock` libre: `programa_abierto`), avisa con una notificación del sistema, descarga con el SHA-256 firmado e instala. Un fallo
no se reintenta solo antes de 6 h. Registro: `carpeta_estado()/actualizar_fondo.log`.
- **Windows:** tarea programada del USUARIO «CineCaptions Actualizaciones» (cada 4 h y «en cuanto se pueda» si el equipo estaba apagado; sin
  disparador de inicio de sesión ni carpeta propia: los dos piden administrador). La crea el programa al abrirse (`asegurar_programada`, desde
  `vigilancia.revisar_salud_al_arrancar`) y la quita el desinstalador (`Instalador.cs`). Instala con `/silencioso /noabrir /sinmodelo` (por
  usuario, sin UAC; los motores los pone al día el programa al abrirse). Notificación: el icono de la bandeja de Qt unos segundos.
- **Mac:** servicio del sistema `com.cinemaproductions.cinecaptions.actualizar` (`/Library/LaunchDaemons`, de root; lo pone el `postinstall`):
  al encender, cada 4 h y al momento con un pedido en `/Users/Shared/CineCaptions/pedidos` (QueueDirectories). Instala el .pkg SIN contraseña.
  Si ya estaba cargado, el postinstall no lo recarga (podría ser él quien instala). Seguridad: carpetas de root (la de pedidos 1777 con sticky
  bit; si alguien la cambió por un enlace se rehace), descargas en una carpeta solo de root (`actualizaciones.carpeta_descargas`), de un pedido
  solo «reabrir», el PID que esperar (nunca lo mata) y un .dmg que copia y comprueba con el SHA-256 firmado. Notificación: `osascript` como el
  usuario que está frente a la Mac. El desinstalador lo quita.
- **Con el programa abierto:** la versión nueva se descarga sola en cuanto sale (`_predescargar_actualizacion`) y se instala SIN ventanas al
  cerrarlo (`_instalar_al_cerrar`: Windows en silencio; Mac por el servicio). «Actualizar ahora» aprovecha esa descarga; en la Mac va por el
  servicio (sin contraseña) y, si no está, con la ventana de la contraseña de antes.

**Mac: se instala y se vuelve a abrir sola (v5.87; el usuario: «en Mac al actualizar no se actualiza bien, no se abre solo, tengo que
cerrarlo y volverlo a abrir»):** hasta la 5.86 la Mac solo abría el .dmg y pedía abrir el .pkg a mano CON EL PROGRAMA ABIERTO; nada lo cerraba ni
lo volvía a abrir. Ahora `actualizaciones._instalar_mac` (en el hilo de la descarga) saca el .pkg del .dmg (`hdiutil attach -nobrowse`, copia y
desmonta), deja en marcha `SCRIPT_MAC` aparte (`start_new_session`) y el programa se cierra como en Windows. El script espera a que se cierre
(60 s; si no, lo cierra), instala con `installer -pkg … -target /` (primero `sudo -n`, que en una Mac normal no vale; luego la ventana de la
contraseña de macOS por `osascript … with administrator privileges`; sin contraseña, el instalador de macOS de siempre con `open -W`) y abre
`/Applications/CineCaptions.app`. Registro: `~/DaVinciSubtitles/actualizacion_mac.log`. Caso `actualizar_en_mac_se_instala_y_vuelve_a_abrir`.
Probado en una Mac de GitHub con el .dmg publicado de la 5.86: «The install was successful» y se volvió a abrir solo.

**Previsiones (v5.87; pedido: «previene más errores o situaciones reales de futuros problemas»):** 1) quien actualiza desde la 5.86 (o instala
el .pkg a mano) tiene la versión VIEJA abierta mientras el .pkg la reemplaza: el `postinstall` la cierra con SIGTERM (solo la ventana: la orden
exacta, sin `--tarea` ni hijos) y al terminar abre la nueva; el programa, con SIGTERM, cierra la ventana como el botón y guarda
(`_cerrar_bien_al_terminar`). 2) El instalador descargado (hasta 1,2 GB en la Mac) ya no se queda en la carpeta temporal: al abrir se quita lo
de más de una hora (`limpiar_descargas_viejas`, desde `vigilancia.revisar_salud_al_arrancar`). Casos `instalar_a_mano_con_la_vieja_abierta_…`
y `descargas_viejas_de_actualizacion_se_quitan`.

**Qué:** v5.3.5. El programa lee un `version.json` público, avisa con el chip «Nueva versión X ↑» de Inicio, descarga el instalador de SU plataforma, comprueba el SHA-256 y lo lanza. Nunca instala sin que el usuario pulse y confirme.

**Cliente:** `actualizaciones.py` · `comprobar` (manifiesto → estado `nueva`/`al_dia`/`error` + `archivo` {url, sha256, tam}), `descargar` (a `%TEMP%/cinecaptions_actualizacion`, avance, **rechaza** sin huella o con huella distinta y borra el archivo), `instalar` (Windows: `Instalar_….exe /empezar` desprendido, él cierra el programa, reemplaza y reabre; Mac: `open` del .dmg), `clave_plataforma` (`windows`/`mac_arm64`/`mac_x86_64`). Script principal: `_revisar_actualizaciones_auto` (20 s tras abrir, como mucho cada 12 h; prefs `actualizaciones_auto`, `actualizacion_revisada`, `actualizacion_pendiente`, `actualizacion_avisada`, `canal_beta`, `url_actualizaciones`), `_ofrecer_actualizacion` (pregunta; no deja si GO/editor trabajan), `_descargar_actualizacion` (Dialogo 520×560 SIN marco y translúcido + `actualizar_ui.PanelActualizacion(sin_marco=True)` desde v5.49 —el panel pinta el fondo redondeado, lleva la ✕ dentro (`BotonCerrar`) y se arrastra; «Cancelar» es `BotonPildora`; iconos Phosphor pedidos con `QIcon.pixmap(lado)` (pedirlos × dpr los inflaba 1,5× a 150 %); para verla de verdad: `grab()` de la propia ventana, NUNCA capturar la pantalla (con escala 150 % la zona no coincide y sale el escritorio del usuario) —propuesta A + B del usuario: anillo con el %, «5.48 → 5.49», MB / velocidad de los últimos ~4 s / tiempo que falta, los tres pasos con su tiempo, «QUÉ TRAE LA x» con las notas del manifiesto partidas en frases y «Cancelar» (cierra el diálogo → `cancelado`)—; cierra la app 1,5 s después en Windows), chip en `_pintar_opciones_go`. Ajustes > Acerca de: interruptor «Avisarme de las actualizaciones», «Buscar actualizaciones» (`ajustes_ui.buscar_actualizaciones` → `_ofrecer_actualizacion`), «Recibir versiones beta».

**Publicar:** `Publicar_Version.ps1 -Notas "…"` (tras `Actualizar_Windows.ps1` y `Actualizar_Mac.ps1`): arma `INSTALADORES/version.json` (sha256/tam por plataforma), crea la release `v<ver>` en el repositorio PÚBLICO `AlejandroPiedrasanta/CineCaptions-releases` (solo instaladores; el código sigue en el privado) y comprueba `releases/latest/download/version.json`. `-SinSubir` solo genera el manifiesto; `-CrearRepo` crea el repositorio la primera vez; `-Canal beta` guarda la versión en la clave `beta`. Se puede apuntar a otro sitio sin recompilar con `CINECAPTIONS_URL_ACTUALIZACIONES` o la pref `url_actualizaciones`.

**Firma del manifiesto (v5.52):** `version.json` lleva `"firma": {"alg": "ed25519", "clave": "<id>", "valor": "<base64>"}` sobre el JSON canónico sin la firma (`actualizaciones.bytes_firmados`). `Publicar_Version.ps1` llama a `3_compilar/firmar_manifiesto.py` (comprueba la firma con `CLAVES_FIRMA` antes de escribir; sin clave no publica). El cliente (`firma_valida` dentro de `_interpretar`, para `comprobar` y `comprobar_ligero`) da `error` «manifiesto sin firma válida» y no ofrece nada: ni con la cuenta de GitHub robada ni cambiando `url_actualizaciones` se cuela un instalador (su SHA-256 va dentro de lo firmado). Ed25519 en Python puro (`firma_ed25519.py`, vectores del RFC 8032; ~3 ms; nada de `cryptography`, otro .pyd sin firma). Claves privadas FUERA del repo en `~/CineCaptions_claves/actualizaciones_{principal,reserva}.key` (la de reserva, copiada a USB/nube); perder las dos = los programas instalados ya no se actualizan. `--claves-nuevas` crea las que falten e imprime las públicas.

**Trampa de la carpeta de trabajo (v5.3.9):** el instalador lanzado por el programa HEREDA su carpeta de trabajo, que es la carpeta de instalación (los accesos directos la fijan así); un proceso con su carpeta de trabajo dentro de una carpeta impide renombrarla → «No puedo reemplazar la versión instalada (algún archivo está en uso)». Arreglo en los dos lados: `Instalador.cs` · `Main` (tras leer las opciones, `/dir` pasa a ruta absoluta y se hace `SetCurrentDirectory(temp)`; así también arregla las actualizaciones lanzadas por versiones viejas del programa) y `CopiarPrograma` (12 reintentos de `Directory.Move`, recierra el programa en el 4.º y el 8.º); cliente: `actualizaciones.instalar` lanza con `cwd=` la carpeta del instalador. El instalador INSTALA SOLO al abrirse (solo el desinstalador espera el botón): probarlo exige sandbox + matarlo antes de las tareas (`scripts`, fuentes, modelos tocan el equipo real). Prueba válida: sandbox `C:\ccp_*` con una carpeta ya «instalada» (falsa), instalador con `WorkingDirectory` dentro y esperar a que aparezca `inst.anterior`; matar el instalador y los `CineCaptions.exe` del sandbox, borrar con `\\?\` y la clave `Software\CineCaptionsPrueba`.

**Pruebas:** servidor HTTP local + `version.json` falso (huella buena, mala, ausente, cancelar, 404, servidor caído) y la app `offscreen` con `USERPROFILE` falso para no ensuciar las prefs reales. Desde la 5.52 el falso tiene que ir firmado: clave de prueba con `firma_ed25519.nueva_privada()` metida en `actualizaciones.CLAVES_FIRMA` solo dentro de la prueba (o `firmar_manifiesto.py` sobre una copia en el scratchpad); también vale `CINECAPTIONS_URL_ACTUALIZACIONES=file:///…`.

**Vigilancia de versiones (v5.4.2):** `actualizaciones.comprobar_ligero` (ETag + `If-None-Match`: casi siempre un 304 sin cuerpo) corre cada `INTERVALO_AUTO_S` = 10 s desde un `QTimer` del script principal (`_iniciar_vigia_actualizaciones` → `_revisar_actualizaciones_auto`); sin internet pasa a 60 s tras 3 fallos y lo anota una vez. Al detectar una versión nueva: chip de Inicio, `_avisar_actualizacion` (`ajustes_ui.pedir_actualizacion`: cuadro con las mejoras del manifiesto + «Actualizar ahora» / «Más tarde», una vez por versión y sesión, espera si GO/editor trabajan) y el botón de Ajustes. Ajustes > Acerca de usa `ajustes_ui.ControlActualizacion` (estado, «Leer notas», «Buscar actualizaciones» / «Actualizar a la X»). Tras instalar, `_mostrar_novedades_si_toca` compara la pref `version_vista` y enseña `ajustes_ui.mostrar_novedades` (todas las notas desde la versión anterior, `notas_desde`). `Publicar_Version.ps1` sin `-Notas` toma las mejoras de `ajustes_ui.NOTAS_VERSION` (`3_compilar/notas_de_version.py`), una por línea con viñeta: eso es lo que enseña el aviso. Una versión instalada ANTES de la 5.4.2 sigue mirando cada 12 h: se actualiza con «Buscar actualizaciones» o el chip.

**Actualización obligatoria (v5.72, pedido del usuario: «force_update» + versión mínima, eligió «aviso fijo; la ✕ cierra la app»):** `"force_update": true` y `"version_minima": "5.72.0"` en la RAÍZ de `version.json`, dentro de lo firmado (sin la clave nadie obliga a nada). `actualizaciones._obligatoria` marca `obligatoria` solo si `force_update` es `true` de verdad (no un texto), la instalada es MENOR que la mínima y hay instalador de ESTA plataforma (sin él quedaría bloqueado para nada). `_avisar_actualizacion` → `_exigir_actualizacion` → `ajustes_ui.exigir_actualizacion` («Actualización obligatoria», «Cerrar CineCaptions» / «Actualizar ahora», sin «Más tarde»); la ✕, Esc o «Cerrar» cierran el programa. Solo tras una consulta que SÍ llegó (sin internet no bloquea: la pref `actualizacion_pendiente` no basta), espera a que terminen GO o el editor, la descarga va modal y, si se cancela o falla, el aviso vuelve a los 300 ms; en Mac se cierra tras abrir el .dmg. Publicar: `Publicar_Version.ps1 -Minima 5.72` (se conserva en las siguientes hasta `-SinObligatoria`), `-SoloMinima -Minima x.y` cambia solo la mínima de lo ya publicado (reescribe y firma `version.json` de la última release) y rechaza una mínima mayor que la estable. Las versiones anteriores a la 5.72 ignoran estos campos. Pruebas: grupo «Actualización obligatoria» de `simular_equipos.py`.

## nota — Compilar: carpetas de solo lectura (BorrarCarpeta)

Si `Actualizar_Windows.ps1` falla con «Acceso denegado» al borrar `6_compilacion/fuentes|dist|instalador`: `desktop.ini` y `.cf/` (Explorador/sincronización) marcan las carpetas como solo lectura y `[IO.Directory]::Delete` no las borra. `3_compilar/Construir_Instalador.ps1` ya usa `BorrarCarpeta` (quita atributos de hijos Y de la carpeta raíz, luego borra). Si PyInstaller da PermissionError en `6_compilacion/dist`, quitar atributos de `dist` y repetir.
