# Resolve (API, MCP, scripts, vistas reales)

## resolve-api — Resolve (API, puente, MCP, scripts)

**Qué:** Resolve (API/puente/MCP)

**Dónde:** `resolve_bridge.py`, `resolve_mcp.py`, `instalador_scripts.py`

## vista-real-previo — Vista real cortada a medias

**Qué:** Vista real cortada a medias (el timeline temporal «· vista …» quedaba como el actual)

**Dónde:** `vistas_reales.py` · `anotar_previo`, `reparar_pendiente`, `PREVIO` (`~/DaVinciSubtitles/vista_previo.json`); se llama desde `resolve_mcp.ejecutar_py` / `preparar_resolve` (`_reparar_vistas`)

## nota — v5.8 segunda pasada de la auditoría

Los gemelos de Resolve son IGUALES también en emojis animados: el .lua (Free) ya importa la secuencia e_[0001-NNNN].png, la repite en bucle y le pone la comp de Fusion de entrada/salida (sin io, en Free 21.1, va en bucle pero sin rebote). Se comprobó ítem por ítem contra el .py en Resolve Studio (fuscript -l lua): pistas, tiempos, Tilt/Pan/Zoom, SFX y la expresión de la comp, idénticos.

## nota — v5.8 segunda pasada de la auditoría

vistas_reales.anotar_previo guarda en vista_previo.json el timeline en que estabas antes de la vista real; si el programa o Resolve se cortan a medias, resolve_mcp (ejecutar_py/preparar_resolve) llama a vistas_reales.reparar_pendiente: vuelve a ese timeline y borra los temporales (con 3 s de margen). Con una vista real en curso en este programa (_ACTIVOS) no repara.
