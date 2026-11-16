# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/diseno.py — el diseño de «Plantillas virales cinema»: tamaños, colores, posiciones y sets de los 6 packs → diseno.json.
"""El diseño de «Plantillas virales cinema»: 6 packs (Luxe / Amro × superior / centro / inferior), cada uno
en vertical (1080x1920) y horizontal (1920x1080), con 6 sets + base. Tamaños y separaciones salen de la
calibración (cal_v.json: lo que mide cada preset a un tamaño conocido). Escribe diseno.json."""
import json
import pathlib

AQUI = pathlib.Path(__file__).resolve().parent
CAL = json.loads((AQUI / 'cal_v.json').read_text(encoding='utf-8'))

# lo medido en vertical: (tamaño de la prueba, alto sobre el centro, alto bajo el centro) en píxeles
MEDIDA = {
    'Luxe Shine': (0.15, CAL['cal_v_00.png']),
    'Luxe Slide': (0.15, CAL['cal_v_01.png']),
    'Highlight_Captions': (0.122, CAL['cal_v_02.png']),
    'Strike_Captions': (0.2, CAL['cal_v_03.png']),
    'Underline_Captions': (0.126, CAL['cal_v_04.png']),
    'Underline_sin_barra': (0.126, CAL['cal_v_05.png']),
    # Fire se escala con Transform1.Size (su Text Size no cuenta): medido a escala 1 con 'VIRAL'
    'Fire_Captions': (1.0, {'arriba': 119, 'abajo': 123}),
}
FACTOR_H = 0.5            # en horizontal el Text+ mide 1,77 veces más (se escala con el ancho): se reduce
def fh(preset):
    """Escala horizontal respecto del vertical: Luxe se ve más chico a lo ancho, así que sube."""
    return 0.75 if preset.startswith('Luxe') else FACTOR_H


GAP = {'v': 16, 'h': 10}  # aire entre líneas, en píxeles del cuadro
ALTO = {'v': 1920, 'h': 1080}
ZONAS = {'v': {'superior': 520, 'centro': 0, 'inferior': -360},
         'h': {'superior': 250, 'centro': 0, 'inferior': -250}}
# aire extra (px del cuadro vertical) entre el principal y sus vecinos: la barra, el fuego o el tachado se salen del texto
EXTRA = {'Highlight_Captions': 30, 'Underline_Captions': 34, 'Fire_Captions': 80, 'Strike_Captions': 34}
BLANCO = (1.0, 1.0, 1.0)
ORO = (1.0, 0.82, 0.40)
CHAMPAN = (0.96, 0.88, 0.74)
CHAMPAN_SUAVE = (0.93, 0.88, 0.80)
ROSA_ORO = (0.98, 0.72, 0.63)
HIELO = (0.66, 0.84, 1.0)


def rol(preset, size, color=None, barra=None, tono=None, texto=''):
    return {'preset': preset, 'size': size, 'color': color, 'barra': barra, 'tono': tono, 'texto': texto}


def slide(color=BLANCO, size=0.12, texto=''):
    return rol('Luxe Slide', size, color, texto=texto)


def limpio(texto='', size=0.058):
    """Amro: el Underline SIN su barra (texto Inter Black limpio) para contexto y complemento."""
    return rol('Underline_Captions', size, BLANCO, barra=False, texto=texto)


FAMILIAS = {
    'Luxe': {
        'nombre': 'Luxe',
        'sets': [
            ('Blanco y brillo', slide(), rol('Luxe Shine', 0.30, BLANCO), slide()),
            ('Oro', slide(), rol('Luxe Shine', 0.30, ORO), slide()),
            ('Champán', slide(CHAMPAN_SUAVE), rol('Luxe Shine', 0.30, CHAMPAN), slide(CHAMPAN_SUAVE)),
            ('Rosa oro', slide(), rol('Luxe Shine', 0.30, ROSA_ORO), slide()),
            ('Hielo', slide(), rol('Luxe Shine', 0.30, HIELO), slide()),
            ('Grande dorado', slide(ORO), rol('Luxe Shine', 0.34, BLANCO), slide(ORO)),
        ],
        'base': slide(size=0.14),
        'textos': ('Así se hace', 'Viral', 'en segundos', 'Cinema'),
    },
    'Amro': {
        'nombre': 'Amro',
        'sets': [
            ('Highlight naranja', limpio(), rol('Highlight_Captions', 0.125, BLANCO, tono=0.0), limpio()),
            ('Highlight rosa', limpio(), rol('Highlight_Captions', 0.125, BLANCO, tono=0.75), limpio()),
            ('Underline verde', limpio(), rol('Underline_Captions', 0.125, BLANCO, tono=0.0), limpio()),
            ('Underline amarillo', limpio(), rol('Underline_Captions', 0.125, BLANCO, tono=0.85), limpio()),
            ('Fire', limpio(), rol('Fire_Captions', 0.66), limpio()),
            ('Strike rojo', limpio(), rol('Strike_Captions', 0.15, BLANCO), limpio()),
        ],
        'base': limpio(size=0.07),
        'textos': ('ASÍ SE HACE', 'VIRAL', 'EN SEGUNDOS', 'CINEMA'),
    },
}
NOMBRE_ROL = ('contexto', 'principal', 'complemento')


def medida(cfg, formato):
    """(alto sobre el centro, alto bajo el centro) en px para ese preset y tamaño."""
    clave = 'Underline_sin_barra' if (cfg['preset'] == 'Underline_Captions' and cfg.get('barra') is False) else cfg['preset']
    t0, m = MEDIDA[clave]
    k = cfg['size'] / t0
    if formato == 'h':
        k *= 1.77 * fh(cfg['preset'])
    return m['arriba'] * k, m['abajo'] * k


def nombre_clip(r, n):
    return NOMBRE_ROL[r] if n == 1 else f'{NOMBRE_ROL[r]} {n}'


def pack(familia, zona, formato):
    f = FAMILIAS[familia]
    P = ZONAS[formato][zona]
    H = ALTO[formato]
    gap = GAP[formato]
    clips = []
    for n, (nombre_set, ctx, prin, comp) in enumerate(f['sets'], 1):
        p_arr, p_abj = medida(prin, formato)
        c_arr, c_abj = medida(ctx, formato)
        k_arr, k_abj = medida(comp, formato)
        extra = EXTRA.get(prin['preset'], 0) * (1.0 if formato == 'v' else 0.75)
        y = {0: P + p_arr + gap + extra + c_abj, 1: P, 2: P - p_abj - gap - extra - k_arr}
        for r, cfg in enumerate((ctx, prin, comp)):
            c = dict(cfg, size=round(cfg['size'] * (fh(cfg['preset']) if formato == 'h' else 1.0), 4), texto=f['textos'][r])
            clips.append({'nombre': nombre_clip(r, n), 'set': n, 'estilo': nombre_set, 'rol': NOMBRE_ROL[r],
                          'cfg': c, 'pos': [0.0, round(y[r] / H, 6), 1.0, 1.0]})
    base = dict(f['base'], size=round(f['base']['size'] * (fh(f['base']['preset']) if formato == 'h' else 1.0), 4), texto=f['textos'][3])
    clips.append({'nombre': 'base', 'set': 0, 'estilo': 'base', 'rol': 'base', 'cfg': base,
                  'pos': [0.0, round(P / H, 6), 1.0, 1.0]})
    nombre = f'Plantillas virales cinema · {f["nombre"]} · {zona}'
    archivo = f'Plantillas virales cinema {f["nombre"]} {zona} {"vertical" if formato == "v" else "horizontal"}'
    return {'pack': nombre, 'carpeta': f'Plantillas virales cinema {f["nombre"]} {zona}', 'archivo': archivo,
            'familia': familia, 'zona': zona, 'formato': formato, 'clips': clips}


def main():
    packs = [pack(fam, zona, fmt) for fam in FAMILIAS for zona in ('superior', 'centro', 'inferior') for fmt in ('v', 'h')]
    (AQUI / 'diseno.json').write_text(json.dumps(packs, ensure_ascii=False, indent=1), encoding='utf-8')
    for p in packs:
        ys = [c['pos'][1] for c in p['clips']]
        print(f'{p["archivo"]:52} {len(p["clips"])} clips  y de {min(ys):+.3f} a {max(ys):+.3f}')


if __name__ == '__main__':
    main()
