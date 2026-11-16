# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/diseno_base.py — el diseño de la plantilla BASE nueva (arriba · principal · abajo · imagen × 3 variantes + simple), solo con Luxe Slide y Luxe Shine → diseno.json.
"""La plantilla base nueva, con la estructura de v5.3 y SOLO los efectos de texto de Joel Van Beek (VBF · Luxe Title Pack):
nada de Text+ sueltos ni composiciones de Fusion propias, solo «Luxe Slide» y «Luxe Shine» puestos y configurados.

    arriba N · principal N · abajo N · imagen N      (N = 1, 2, 3: «agregando al final 1, 2 o 3»)
    simple                                           (una sola línea, para las palabras sueltas)

Cada variante apila los cuatro bloques uno encima del otro:  arriba / PRINCIPAL / abajo / imagen.

    arriba, abajo, simple, imagen  → Luxe Slide  (Poppins Regular, o Poppins Bold para resaltar con negrita)
    principal                      → Luxe Shine  (la palabra clave: grande, con brillo y de color)

El estilo sale del video de referencia (reels con una línea pequeña Regular + una palabra Bold y una palabra grande
de color con brillo): variante 1 cian, 2 rosa, 3 fuego. «imagen» es un Luxe Slide con un círculo de muestra (●): su
Pan/Tilt/Zoom dice dónde y de qué tamaño va el icono o la imagen (zoom 1 = tamaño normal del emoji).

Las alturas salen de la calibración de «Plantillas virales cinema» (cal_v.json: lo que mide cada preset a un tamaño
conocido); en horizontal el Text+ mide 1,77 veces más a igual tamaño y Luxe se escala ×0,75.
"""
import json
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'plantillas_virales'))
import diseno as D       # noqa: E402  (la calibración y la función medida() de las plantillas virales)

PACK = 'Base títulos dinámicos'
ARCHIVOS = {'v': 'Base titulos dinamicos vertical', 'h': 'Base titulos dinamicos Horizontal'}

BLANCO = (1.0, 1.0, 1.0)
CIAN = (0.30, 0.86, 1.0)
ROSA = (1.0, 0.45, 0.72)
FUEGO = (1.0, 0.27, 0.10)

# variante -> estilo de cada bloque: (preset, fuente, estilo, color)
SLIDE, SHINE = 'Luxe Slide', 'Luxe Shine'
VARIANTES = {
    1: dict(nombre='Cian', arriba=('Regular', BLANCO), principal=CIAN, abajo=('Regular', BLANCO), simbolo=CIAN, zoom=1.0),
    2: dict(nombre='Rosa', arriba=('Regular', BLANCO), principal=ROSA, abajo=('Bold', BLANCO), simbolo=ROSA, zoom=1.25),
    3: dict(nombre='Fuego', arriba=('Bold', BLANCO), principal=FUEGO, abajo=('Regular', BLANCO), simbolo=FUEGO, zoom=0.85),
}
TEXTOS = {'arriba': 'Esto es', 'principal': 'Increíble', 'abajo': 'de verdad', 'simple': 'Palabras sueltas'}

# tamaños en vertical (los del pack Luxe de las plantillas virales: Slide 0.12, Shine 0.30); el símbolo mide ~320 px por
# unidad de tamaño en Arial, así que 0.5 → ● de ~165 px (el emoji normal mide 0.085 del alto = 163 px en vertical)
TAM = {'arriba': 0.12, 'abajo': 0.12, 'simple': 0.14, 'principal': 0.30, 'simbolo': 0.50}
# dónde queda el centro del principal (px desde el centro del cuadro, Y arriba): el grupo cae en el tercio bajo
ZONA = {'v': -150, 'h': 0}
ALTO = {'v': 1920, 'h': 1080}
GAP = {'v': 16, 'h': 10}
# aire extra: el principal (Luxe Shine, cursiva con tildes y descendentes) se sale de lo medido; sobre todo por abajo
EXTRA_ARRIBA = {'v': 14, 'h': 10}
EXTRA_ABAJO = {'v': 38, 'h': 26}
LADO_EMOJI = {'v': 0.085, 'h': 0.13}        # fracción del alto: lo mismo que EMOJI_ALTO de los scripts de Resolve


def _cfg(preset, size, color, texto, formato, estilo=None, fuente=None):
    c = D.rol(preset, round(size * (D.fh(preset) if formato == 'h' else 1.0), 4), tuple(color), texto=texto)
    c['color'] = list(color)
    if estilo:
        c['font'] = fuente or 'Poppins'
        c['style'] = estilo
    return c


def clips(formato):
    H, gap = ALTO[formato], GAP[formato]
    P = ZONA[formato]
    lista = []
    for n, v in VARIANTES.items():
        sufijo = '' if n == 1 else f' {n}'          # el 1 va sin número, como siempre ('principal', 'principal 2'…)
        est_a, col_a = v['arriba']
        est_b, col_b = v['abajo']
        arriba = _cfg(SLIDE, TAM['arriba'], col_a, TEXTOS['arriba'], formato, est_a)
        principal = _cfg(SHINE, TAM['principal'], v['principal'], TEXTOS['principal'], formato)
        abajo = _cfg(SLIDE, TAM['abajo'], col_b, TEXTOS['abajo'], formato, est_b)
        p_arr, p_abj = D.medida(principal, formato)
        a_arr, a_abj = D.medida(arriba, formato)
        b_arr, b_abj = D.medida(abajo, formato)
        y_arriba = P + p_arr + gap + EXTRA_ARRIBA[formato] + a_abj
        y_abajo = P - p_abj - gap - EXTRA_ABAJO[formato] - b_arr
        lado = LADO_EMOJI[formato] * H * v['zoom']
        y_imagen = y_abajo - b_abj - gap - lado / 2
        simbolo = _cfg(SLIDE, TAM['simbolo'], v['simbolo'], '●', formato, 'Regular', 'Arial')
        if formato == 'h':           # en horizontal el círculo mide 140 px (el emoji normal), no 163: 0.32 en vez de 0.375
            simbolo['size'] = 0.32
        lista += [
            dict(nombre='arriba' + sufijo, set=n, cfg=arriba, pos=[0.0, round(y_arriba / H, 4), 1.0, 1.0]),
            dict(nombre='principal' + sufijo, set=n, cfg=principal, pos=[0.0, round(P / H, 4), 1.0, 1.0]),
            dict(nombre='abajo' + sufijo, set=n, cfg=abajo, pos=[0.0, round(y_abajo / H, 4), 1.0, 1.0]),
            dict(nombre='imagen' + sufijo, set=n, cfg=simbolo, pos=[0.0, round(y_imagen / H, 4), v['zoom'], v['zoom']]),
        ]
    simple = _cfg(SLIDE, TAM['simple'], BLANCO, TEXTOS['simple'], formato, 'Bold')
    lista.append(dict(nombre='simple', set=0, cfg=simple, pos=[0.0, round(P / H, 4), 1.0, 1.0]))
    return lista


def diseno():
    return [dict(archivo=ARCHIVOS[f], formato=f, pack=PACK, clips=clips(f)) for f in ('h', 'v')]


if __name__ == '__main__':
    d = diseno()
    (AQUI / 'diseno.json').write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    for pk in d:
        print(pk['archivo'], len(pk['clips']), 'clips')
        for c in pk['clips']:
            print('   %-12s %-11s tam %.3f  y %+.3f  zoom %.2f' % (c['nombre'], c['cfg']['preset'], c['cfg']['size'],
                                                              c['pos'][1], c['pos'][2]))
