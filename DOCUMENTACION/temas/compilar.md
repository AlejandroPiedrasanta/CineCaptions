# Compilar, versiones, instaladores (Windows y Mac)

## instalador-cs — Instalador C#: banner, rutas, pasos

**Qué:** Instalador (C#): banner animado con el astrolabio girando, rutas de instalación, pasos con spinner

**Dónde:** `3_compilar/Instalador.cs` (`Banner`, `ListaPasos`, `ListaRutas`, `Instalacion.Rutas`); imágenes: `4_diseno/banner/crear_banner.py` (banner.jpg + `3_compilar/banner_capas/`)

## version — Versión del programa

**Qué:** Versión

**Dónde:** `version.py`

## mac — Instalador de Mac (.app/.pkg/.dmg)

**Qué:** Instalador de Mac (Apple Silicon): .app + .pkg + .dmg; no compila desde Windows (Mac o GitHub Actions)

**Dónde:** `7_mac/` · `Construir_Instalador_Mac.sh`, `cinecaptions_mac.spec`, `pkg/scripts/postinstall` (corre `--tarea scripts` y `fuentes` como el usuario); leer `7_mac/0_LEEME.txt`. SIN PROBAR en una Mac real

## compilar-win — Compilar, versiones y desinstalador de Windows

**Qué:** Compilar / versiones / desinstalador de Windows (v5.3.2): `Actualizar_Windows.ps1` (huella del código → sube la versión +1 si cambió → `Construir_Instalador.ps1` → deja `INSTALADORES/Windows/Instalar_CineCaptions_<ver>.exe` y borra los viejos; `-Comprobar` dice si está al día; `-Registrar` da por bueno el instalador actual sin compilar, p. ej. tras tocar solo herramientas de desarrollo como `mapa_codigo.py`/`mcp_cinecaptions.py`, que no entran en la huella); `3_compilar/sincronizar_version.py` copia `APP_VERSION` a los scripts de Resolve y al Puente (antes se olvidaba: app 5.3.1 con scripts 5.3.0 = aviso «otra versión instalada»). Desinstalador en `3_compilar/Instalador.cs`: `Sitio` (carpetas/registro; env `CINECAPTIONS_PRUEBA_RAIZ` = sandbox de pruebas), `Borrado` (rutas largas, procesos por ruta, RunOnce, rastros del registro), `Instalacion.Desinstalar` (8 pasos), casillas «datos/licencia» y «modelos» (`/borrardatos /borrarmodelos /todo`; silencioso sin /todo conserva). Prueba: fixture en `C:\ccp*` + env de prueba + `Desinstalar.exe /desinstalar /silencioso /todo` (cuidado: la tarea `scripts` de Python sí escribe en `C:\ProgramData\Blackmagic Design`)

**Dónde:** 

## mac-actualizar — Mantener el instalador de Mac al día

Tras CUALQUIER mejora del programa (`1_codigo`, `2_recursos`, `3_compilar` o `7_mac`): `powershell -ExecutionPolicy Bypass -File Actualizar_Mac.ps1` (sube a GitHub privado, compila Apple Silicon + Intel y deja `CineCaptions_Mac_*_<ver>.dmg` en `INSTALADORES/Mac`; ~15 min, correr en segundo plano). `-SoloDescargar` solo baja la última compilación buena. Detalles en `7_mac/0_LEEME.txt`. Sin probar en una Mac real.

## actualizaciones — Actualizaciones automáticas (cliente y publicación)

**Qué:** v5.3.5. El programa lee un `version.json` público, avisa con el chip «Nueva versión X ↑» de Inicio, descarga el instalador de SU plataforma, comprueba el SHA-256 y lo lanza. Nunca instala sin que el usuario pulse y confirme.

**Cliente:** `actualizaciones.py` · `comprobar` (manifiesto → estado `nueva`/`al_dia`/`error` + `archivo` {url, sha256, tam}), `descargar` (a `%TEMP%/cinecaptions_actualizacion`, avance, **rechaza** sin huella o con huella distinta y borra el archivo), `instalar` (Windows: `Instalar_….exe /empezar` desprendido, él cierra el programa, reemplaza y reabre; Mac: `open` del .dmg), `clave_plataforma` (`windows`/`mac_arm64`/`mac_x86_64`). Script principal: `_revisar_actualizaciones_auto` (20 s tras abrir, como mucho cada 12 h; prefs `actualizaciones_auto`, `actualizacion_revisada`, `actualizacion_pendiente`, `actualizacion_avisada`, `canal_beta`, `url_actualizaciones`), `_ofrecer_actualizacion` (pregunta; no deja si GO/editor trabajan), `_descargar_actualizacion` (Dialogo + `PanelAsistencia`; cierra la app 1,5 s después en Windows), chip en `_pintar_opciones_go`. Ajustes > Acerca de: interruptor «Avisarme de las actualizaciones», «Buscar actualizaciones» (`ajustes_ui.buscar_actualizaciones` → `_ofrecer_actualizacion`), «Recibir versiones beta».

**Publicar:** `Publicar_Version.ps1 -Notas "…"` (tras `Actualizar_Windows.ps1` y `Actualizar_Mac.ps1`): arma `INSTALADORES/version.json` (sha256/tam por plataforma), crea la release `v<ver>` en el repositorio PÚBLICO `AlejandroPiedrasanta/CineCaptions-releases` (solo instaladores; el código sigue en el privado) y comprueba `releases/latest/download/version.json`. `-SinSubir` solo genera el manifiesto; `-CrearRepo` crea el repositorio la primera vez; `-Canal beta` guarda la versión en la clave `beta`. Se puede apuntar a otro sitio sin recompilar con `CINECAPTIONS_URL_ACTUALIZACIONES` o la pref `url_actualizaciones`.

**Trampa de la carpeta de trabajo (v5.3.9):** el instalador lanzado por el programa HEREDA su carpeta de trabajo, que es la carpeta de instalación (los accesos directos la fijan así); un proceso con su carpeta de trabajo dentro de una carpeta impide renombrarla → «No puedo reemplazar la versión instalada (algún archivo está en uso)». Arreglo en los dos lados: `Instalador.cs` · `Main` (tras leer las opciones, `/dir` pasa a ruta absoluta y se hace `SetCurrentDirectory(temp)`; así también arregla las actualizaciones lanzadas por versiones viejas del programa) y `CopiarPrograma` (12 reintentos de `Directory.Move`, recierra el programa en el 4.º y el 8.º); cliente: `actualizaciones.instalar` lanza con `cwd=` la carpeta del instalador. El instalador INSTALA SOLO al abrirse (solo el desinstalador espera el botón): probarlo exige sandbox + matarlo antes de las tareas (`scripts`, fuentes, modelos tocan el equipo real). Prueba válida: sandbox `C:\ccp_*` con una carpeta ya «instalada» (falsa), instalador con `WorkingDirectory` dentro y esperar a que aparezca `inst.anterior`; matar el instalador y los `CineCaptions.exe` del sandbox, borrar con `\\?\` y la clave `Software\CineCaptionsPrueba`.

**Pruebas:** servidor HTTP local + `version.json` falso (huella buena, mala, ausente, cancelar, 404, servidor caído) y la app `offscreen` con `USERPROFILE` falso para no ensuciar las prefs reales.

**Vigilancia de versiones (v5.4.2):** `actualizaciones.comprobar_ligero` (ETag + `If-None-Match`: casi siempre un 304 sin cuerpo) corre cada `INTERVALO_AUTO_S` = 10 s desde un `QTimer` del script principal (`_iniciar_vigia_actualizaciones` → `_revisar_actualizaciones_auto`); sin internet pasa a 60 s tras 3 fallos y lo anota una vez. Al detectar una versión nueva: chip de Inicio, `_avisar_actualizacion` (`ajustes_ui.pedir_actualizacion`: cuadro con las mejoras del manifiesto + «Actualizar ahora» / «Más tarde», una vez por versión y sesión, espera si GO/editor trabajan) y el botón de Ajustes. Ajustes > Acerca de usa `ajustes_ui.ControlActualizacion` (estado, «Leer notas», «Buscar actualizaciones» / «Actualizar a la X»). Tras instalar, `_mostrar_novedades_si_toca` compara la pref `version_vista` y enseña `ajustes_ui.mostrar_novedades` (todas las notas desde la versión anterior, `notas_desde`). `Publicar_Version.ps1` sin `-Notas` toma las mejoras de `ajustes_ui.NOTAS_VERSION` (`3_compilar/notas_de_version.py`), una por línea con viñeta: eso es lo que enseña el aviso. Una versión instalada ANTES de la 5.4.2 sigue mirando cada 12 h: se actualiza con «Buscar actualizaciones» o el chip.
