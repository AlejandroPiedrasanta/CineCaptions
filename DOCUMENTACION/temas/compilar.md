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
