# CineCaptions · By Cinema Productions
# 1_codigo/herramientas_dev/vista_tema5.py — el Tema 5 SIN Resolve, para revisarlo y para la tarjeta del slider (2_recursos/vistas_slider/Tema5.mp4
# + .jpg): los mismos bloques que pondría GO (tema4_planificador), las mismas piezas (edicion_pro_tema5.planificar) y la misma regla de la cara
# (edicion_pro._ajustar_posiciones), renderizadas con Remotion y compuestas en el orden de las pistas de Resolve: video (bajado en la pantalla
# dividida) · escenas · captions «detrás» · la persona recortada con la IA local (MODNet, como el Magic Mask) · elementos en pantalla · captions.
#     python 1_codigo/herramientas_dev/vista_tema5.py <video> [--palabras p.json] [--salida …/Tema5.mp4] [--ancho 486] [--segundos 24] [--crf 27]
# Las palabras: --palabras ({"words": [{word, start, end}]}) o ~/DaVinciSubtitles/<video>.marcas.json (las deja un GO o «Generar»).
import argparse
import json
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI.parent))
import av  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import edicion_pro as EP  # noqa: E402
import edicion_pro_persona as PE  # noqa: E402
import edicion_pro_remotion as RM  # noqa: E402
import edicion_pro_tema5 as T5  # noqa: E402
import tema4_planificador as T4  # noqa: E402

ORDEN = ('fondo', 'detras', 'delante', 'subs')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--palabras', default='')
    ap.add_argument('--salida', default=str(RAIZ / '2_recursos' / 'vistas_slider' / 'Tema5.mp4'))
    ap.add_argument('--ancho', type=int, default=486)
    ap.add_argument('--segundos', type=float, default=24.0)
    ap.add_argument('--crf', type=int, default=27)
    ap.add_argument('--idioma', default='es')
    a = ap.parse_args()
    video = Path(a.video)
    fuente = Path(a.palabras) if a.palabras else Path.home() / 'DaVinciSubtitles' / f'{video.stem}.marcas.json'
    palabras = json.loads(fuente.read_text(encoding='utf-8'))['words']
    with av.open(str(video)) as c:
        s = c.streams.video[0]
        W, H, fps = s.width, s.height, float(s.average_rate or 30)
    vertical = H > W
    cues, _ = T4.cues_de(palabras, 'es', 'Tema5', 1080)
    tmp = Path(tempfile.mkdtemp(prefix='vista_t5_'))
    (tmp / 'g.json').write_text(json.dumps({'cues': cues}, ensure_ascii=False), encoding='utf-8')
    (tmp / 'm.json').write_text(json.dumps({'tracks': [{'style': 'guion', 'data_path': str(tmp / 'g.json')}]}), encoding='utf-8')
    T5.MANIFIESTO = tmp / 'm.json'
    det_de = lambda t: PE.personas(str(video), t)                                       # noqa: E731  (aquí la fuente ES el timeline)
    piezas, divididas = T5.planificar({'piezas': []}, vertical, 'media', str(video), det_de=det_de, foto_de=lambda t: T5.foto(video, t),
                                      idioma=a.idioma, estado=print)
    for p in sorted(piezas, key=lambda x: x['ini']):
        if p['pieza'] in ('skill', 'acomp'):
            print(f"  {p['ini']:6.2f}-{p['fin']:6.2f} {p['remotion']:12s} {p.get('motivo', '')}")
    piezas = [p for p in piezas if p['ini'] < a.segundos]
    for p in piezas:                                                                     # la regla de la cara (como aplicar)
        p['_valores0'] = dict(p['valores'])
        if not p.get('ajustar'):
            continue
        det = det_de((p['ini'] + p['fin']) / 2.0)
        EP._ajustar_posiciones(p, det, vertical)
        T5.subir_detras(p)
        if p['pieza'] == 'subtitulo' and p.pop('quitar', False):
            p['valores'].update(y=84.0 if vertical else 86.0, escala=0.8)
        if p['capa'] == 'detras' and not (det and det.get('personas')):
            p['valores'] = dict(p['_valores0'], modo='normal', y=T5.Y_NORMAL[vertical])
            p['capa'] = 'subs'
    T5.coordinar(piezas)
    piezas = [p for p in piezas if not p.get('quitar')]
    trab = []
    for p in piezas:
        props = dict(p['valores'], _ancho=W, _alto=H, _fps=fps, _dur=round(max(0.6, p['fin'] - p['ini']), 3))
        trab.append({'id': p['remotion'], 'props': props, 'salida': RM.salida_para(p['remotion'], props, tmp)})
        p['_salida'] = str(trab[-1]['salida'])
    hechos = RM.renderizar(trab)
    print('clips', sum(hechos.values()), '/', len(trab))
    capas = {k: [] for k in ORDEN}
    for p in piezas:
        if hechos.get(p['_salida']):
            capas[p['capa']].append([int(round(p['ini'] * fps)), int(round(p['fin'] * fps)), p['_salida'], None])
    div = [(int(round(d['ini'] * fps)), int(round(d['fin'] * fps)), int(round(d['bajar'] * H))) for d in divididas]
    alto = int(round(a.ancho * H / W / 2)) * 2
    salida = Path(a.salida)
    poster, mejor = None, -1
    with av.open(str(video)) as src, av.open(str(salida), 'w', options={'movflags': '+faststart'}) as out:
        vs = out.add_stream('libx264', rate=round(fps))
        vs.width, vs.height, vs.pix_fmt = a.ancho, alto, 'yuv420p'
        vs.options = {'crf': str(a.crf), 'preset': 'slow'}
        for n, fr in enumerate(src.decode(src.streams.video[0])):
            if n >= a.segundos * fps:
                break
            rgb = fr.to_ndarray(format='rgb24')
            baja = next((b for f0, f1, b in div if f0 <= n < f1), 0)
            if baja:                                                                     # pantalla dividida: la persona, a la mitad de abajo
                rgb = np.concatenate([np.zeros((baja, W, 3), np.uint8), rgb[: H - baja]], axis=0)
            img = Image.fromarray(rgb).convert('RGBA')

            def capa(lista):
                puestos = 0
                for c in lista:
                    if c[0] <= n < c[1]:
                        if c[3] is None:
                            c[3] = av.open(c[2]).decode(video=0)
                        try:
                            img.alpha_composite(Image.fromarray(next(c[3]).to_ndarray(format='rgba'), 'RGBA'))
                            puestos += 1
                        except StopIteration:
                            pass
                return puestos

            usados = capa(capas['fondo'])
            d = capa(capas['detras'])
            if d:                                                                        # la persona, ENCIMA de lo que va detrás
                m = Image.fromarray((PE.mate(rgb) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
                persona = Image.fromarray(rgb).convert('RGBA')
                persona.putalpha(m)
                img.alpha_composite(persona)
            usados += d + capa(capas['delante']) + capa(capas['subs'])
            if usados > mejor and n > fps * 1.2:
                mejor, poster = usados, img.convert('RGB').copy()
            for pk in vs.encode(av.VideoFrame.from_image(img.convert('RGB').resize((a.ancho, alto), Image.LANCZOS))):
                out.mux(pk)
        for pk in vs.encode():
            out.mux(pk)
    if poster is not None:
        poster.resize((a.ancho, alto), Image.LANCZOS).save(salida.with_suffix('.jpg'), quality=88)
    print(salida, salida.stat().st_size // 1024, 'KB')


if __name__ == '__main__':
    main()
