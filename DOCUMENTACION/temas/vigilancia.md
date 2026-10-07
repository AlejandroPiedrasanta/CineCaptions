# Vigilancia, logs y respaldo de modelos

## vigilancia — Vigilancia, logs y respaldo de modelos

**Qué:** Vigilancia / logs / respaldo de modelos (v5.11): GO y Generar vigilados, motores que no responden se matan y el flujo sigue con el respaldo, arranque atascado, disco/memoria, errores.log, informe de soporte Windows/Mac

**Dónde:** `vigilancia.py` · `iniciar/latido/terminar/pausar`, `UMBRALES` (aviso, atasco por paso), `iniciar_monitor`, `vigilar_arranque/arranque_listo`, `revisar_salud_al_arrancar`; app: `_vigilar_tarea`, `_fin_tarea`, `_destrabar`, `_esperando_al_usuario` (editor abierto = pausa), `_chequeo_de_arranque`, kind `'vigia'` en `_poll_queue`; motores: `motor_voz.abortar/pedir(sin_senal)/_FALLOS` (Qwen 1.7B→0.6B→CPU→Whisper; 2 fallos seguidos = Whisper directo), `ia_texto.abortar/analizar` (4B→1.7B→reglas); `registro.py` · `errores.log` (avisos+errores, 3×2 MB), `entorno_detallado`, `reporte_soporte` (lo copia «Copiar informe» del Registro), marca de sesión `hora|abriendo/listo` y `tarea_en_curso.json`. Un paso nuevo de GO con espera larga: darle su umbral en `UMBRALES` y mandar mensajes `status` mientras trabaja
