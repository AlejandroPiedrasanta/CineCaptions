# Pruebas y MCP del programa

## banco-mcp — Banco de pruebas y MCP del programa

**Qué:** Banco de pruebas y MCP del programa

**Dónde:** `banco_pruebas.py` (timeline temporal `zz_BANCO` con fondo gris + audio, `colocar_guion`, `renderizar`, `hoja`, `lado_a_lado`, `medir_texto`, `limpiar`); servidor MCP `mcp_cinecaptions.py` (stdio, sin dependencias; registrado en `.mcp.json`): `estado`, `packs`, `transcribir`, `planificar`, `banco_preparar`, `colocar`, `renderizar`, `cuadros`, `comparar`, `medir`, `limpiar_banco`, `probar_video` (todo el ciclo → hoja de cuadros), `go_real` (el botón GO de la app SIN pantalla vía `probar_go.py`: el flujo real del usuario → render → hoja), `probar_referencia` (los 15 bloques EXACTOS de la referencia → render → al lado del video: regresión del pack), `evaluar` (palabras grandes, cortes y estilos vs la referencia), `registro`. El servidor recarga solo los `guion_*`/`banco_pruebas` al cambiar en disco (`_recargar`); tras tocar `mcp_cinecaptions.py` hay que reconectar el MCP. `probar_go.py` necesita `w.show()` (offscreen): la animación final de GO es la que dispara la colocación, sin ella GO se cuelga tras «Armando los bloques…»

## pruebas-sin-pantalla — Probar la app sin pantalla (arneses Qt)

Python con dependencias: `6_compilacion/venv314/Scripts/python.exe`. Con `QT_QPA_PLATFORM=offscreen`; importar el script principal con `importlib`, parchear `licencia.vigente=lambda:True` y `SubtitleApp._revisar_licencia_al_arrancar=lambda s:None`. Los errores de pruebas se escriben en `~/DaVinciSubtitles/cinecaptions.log`.
- **Prefs reales:** `_poner_go_pack`, `_plantilla_elegida`, `poner_estilo_fijo`, `_alternar_*_go` escriben `~/DaVinciSubtitles/preferencias.json` de verdad: parchea `ajustes_ui.leer_prefs/guardar_prefs` en memoria (como `probar_go.py`) o haz copia antes.
- **GO sin Resolve:** `resolve_mcp.ruta_exe = lambda: None` (con solo `CINECAPTIONS_SIN_MCP` GO se detiene tras transcribir por `_abortar_si_fallo_el_timeline`) y anular `ui.error_con_acciones` (el diálogo modal bloquea el hilo UI). `w.show()` es obligatorio (la animación final de GO dispara la colocación).
- Este venv no trae las DLL de CUDA para Whisper: cae a CPU.
- Para fuentes reales NO `offscreen`: ventana en x=-5000 (`test_paridad.py`/`test_creativo.py` necesitan `qt_kit.crear_app()`).
