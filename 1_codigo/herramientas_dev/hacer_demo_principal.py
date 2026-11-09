# CineCaptions · By Cinema Productions
# 1_codigo/herramientas_dev/hacer_demo_principal.py — los dos videos de la demo «Principal» del Corrector sin audio (2_recursos/creativo).
"""
v5.78 (el usuario eligió la propuesta B: «la preview cuando no hay audio que sea un video de que si cambia una palabra por principal lo
cambia en video, pero un ejemplo real»). Con el MISMO planificador y dibujo que el móvil del Corrector (vista_tema, Estilo 2 = pack
Referencia) y la foto de muestra del móvil, renderiza el bloque de «nadie» de la frase
«Así ganamos 10.000 euros en un mes con este truco que nadie te cuenta»:

    demo_principal_antes.mp4 / .jpg     sin marcas: el programa elige «cuenta» («que nadie te CUENTA»)
    demo_principal_despues.mp4 / .jpg   «nadie» como Principal («con este truco que NADIE te cuenta»)

Cada MP4 es la pantalla del móvil (360×780, la proporción de movil.json) con el bloque animado de principio a fin, sin audio; el .jpg es el
bloque quieto con todo dentro (lo que se ve con «Reducir animaciones»). editor_ui.DemoPrincipal los reproduce con vistas_slider.Reproductor.

    python hacer_demo_principal.py [--salida CARPETA]        (de fábrica: 2_recursos/creativo)
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent                       # 1_codigo
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(AQUI))

FRASE = 'Así ganamos 10.000 euros en un mes con este truco que nadie te cuenta'.split()
OBJETIVO = 'nadie'
PACK = 'Referencia'
ANCHO, ALTO, FPS = 360, 780, 30


def _ffmpeg():
    ff = shutil.which('ffmpeg')
    if ff:
        return ff
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        raise SystemExit('No encuentro ffmpeg')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--salida', default=str(AQUI.parent / '2_recursos' / 'creativo'))
    salida = Path(ap.parse_args().salida)
    salida.mkdir(parents=True, exist_ok=True)
    import ajustes_ui
    ajustes_ui.guardar_prefs = lambda *a, **k: None
    import edicion_pro
    edicion_pro.emojis_permitidos = lambda *a, **k: False                 # (la demo, sin emojis: como GO sin la Edición PRO)
    from PySide6.QtCore import QRectF
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    app = QGuiApplication.instance() or QGuiApplication([])               # noqa: F841
    import vista_tema as VT

    palabras = [{'word': t, 'start': round(0.4 + i * 0.36, 3), 'end': round(0.4 + i * 0.36 + 0.32, 3)} for i, t in enumerate(FRASE)]
    idx = FRASE.index(OBJETIVO)
    estilo = VT.estilo_de_pack(PACK)
    ff = _ffmpeg()
    for nombre, roles in (('antes', [None] * len(palabras)), ('despues', [('main' if i == idx else None) for i in range(len(palabras))])):
        cues = VT.planificar(palabras, roles, PACK, estilo, idioma='es', fin_video=palabras[-1]['end'] + 1.0)
        cu = VT.Cuadros(cues, estilo, ANCHO, ALTO)
        k = cu.cue_de_palabra(OBJETIVO, palabras[idx]['start'])
        a, b = cu.tramo(k)
        cu.cuadro(cu.instante_quieto(k)).save(str(salida / f'demo_principal_{nombre}.jpg'), quality=90)
        tmp = Path(tempfile.mkdtemp(prefix='cc_demo_principal_'))
        try:
            n, t = 0, a
            while t <= b - 0.02:
                img = QImage(ANCHO, ALTO, QImage.Format.Format_RGB888)
                p = QPainter(img)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                cu.pintar(p, QRectF(0, 0, ANCHO, ALTO), t)
                p.end()
                img.save(str(tmp / f'{n:04d}.png'))
                n, t = n + 1, t + 1.0 / FPS
            subprocess.run([ff, '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', str(tmp / '%04d.png'), '-an', '-c:v', 'libx264',
                            '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', str(salida / f'demo_principal_{nombre}.mp4')], check=True)
            print(f'{nombre}: bloque {k} ({a:.2f}–{b:.2f} s), {n} cuadros', flush=True)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
