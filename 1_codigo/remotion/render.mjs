// CineCaptions · By Cinema Productions
// render.mjs — renderiza las animaciones Remotion de la Edición PRO en el PC del usuario (lo llama 1_codigo/edicion_pro_remotion.py).
//     node render.mjs <trabajos.json>
// trabajos.json = {"bundle": carpeta empaquetada, "navegador": chrome-headless-shell (opcional), "trabajos": [{"id": composición, "props": {...},
//                  "salida": .mov}]}. Cada trabajo sale en ProRes 4444 con alfa (Resolve lo pone encima del video tal cual). Una línea JSON por
// trabajo terminado: {"hecho": salida, "s": segundos} o {"error": ..., "salida": ...}. Un solo navegador para todos (más rápido).
import { openBrowser, renderMedia, selectComposition } from '@remotion/renderer';
import { readFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

const tareas = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const serveUrl = tareas.bundle;
const navegador = await openBrowser('chrome', tareas.navegador && existsSync(tareas.navegador) ? { browserExecutable: tareas.navegador } : {});
const hilos = Math.max(1, Math.min(8, Math.floor(os.cpus().length / 2)));
for (const t of tareas.trabajos || []) {
  const t0 = Date.now();
  try {
    mkdirSync(path.dirname(t.salida), { recursive: true });
    const composition = await selectComposition({ serveUrl, id: t.id, inputProps: t.props, puppeteerInstance: navegador });
    await renderMedia({ composition, serveUrl, codec: 'prores', proResProfile: '4444', imageFormat: 'png', pixelFormat: 'yuva444p10le',
                        outputLocation: t.salida, inputProps: t.props, puppeteerInstance: navegador, concurrency: hilos, overwrite: true,
                        chromiumOptions: { gl: 'angle' }, logLevel: 'error' });
    console.log(JSON.stringify({ hecho: t.salida, s: (Date.now() - t0) / 1000 }));
  } catch (e) {
    console.log(JSON.stringify({ error: String(e && e.message || e).slice(0, 400), salida: t.salida }));
  }
}
await navegador.close({ silent: true });
