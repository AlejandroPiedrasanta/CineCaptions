# CineCaptions · By Cinema Productions
# 1_codigo/director_sonido_diseno.py — «AI Sound Director», FASE 3: qué suena y qué se queda en silencio, evento por evento, en los 6 temas.
"""
disenar(analisis, ctx) → {'eventos', 'captions', 'motions', 'viejos', 'resumen'}

Lee lo que GO ya decidió —los cues del tema con sus clips de animación REALES (Kinetic: héroe / anillo / cinta; VIRAL: shatter / select / drag /
negrita; «guion»: la palabra clave con su zoom), las piezas de la PRO con sus tiempos (`edicion_pro_sonido.momentos`, el mismo «cuándo» que usa la
PRO), los eventos visuales de Efectos y los cortes— y la PALETA del proyecto (fase 1).

    captions   CAPTION_SOUND_SCORE 0–1 por caption (papel narrativo, importancia de la frase, tamaño / zoom / clip de la palabra clave, cifra, anillo,
               distancia al último acento). Por debajo del umbral de la paleta: LEAVE_SILENT (la mayoría). El acento de cada tema sale de su carácter:
               golpe diseñado (impacto alto), pop (medio), tic de interfaz (sobrio) o trazo de pluma (editorial); en VIRAL, el de su clip.
    motions    cada movimiento con su importancia (escena entera > tarjeta > icono > tic) y su sitio libre (no pisa un acento de caption).
    encima     un riser en el gancho (una vez), el MOTIVO tonal del video en los datos y en el cierre, whooshes en los cortes que respiran.
    densidad   como mucho 2 + 4·densidad sonidos por ventana de 10 s (se quitan los de menos importancia; golpes y risers mandan).

Cada evento: tipo (golpe, whoosh, giro, riser, trazo, acento, tick, pop), instante, ancla (el fotograma que manda), duración EXACTA de su
animación, pista AI, nivel bajo la voz, parámetros de síntesis (easing, dirección, peso, brillo, semilla), decisión GENERATE y su porqué.
Los sonidos de Simple en cada caption reciben REPLACE / REMOVE con su motivo (los de Efectos y la PRO, en director_sonido.al_colocar / sonidos_pro).

Estilo «Social (CapCut)» (v5.39, `controles['estilo'] == 'social'`): TODO lo que se ve entrar suena con el MISMO pop del kit (director_sonido_sfx.
KIT_SOCIAL), con el tono y el nivel de su tamaño (`SOCIAL_MAPA`, director_sonido_eventos.SOCIAL_NIVEL: héroe > cinta > texto > etiqueta), en el
fotograma en que ATERRIZA (`_aterrizaje`: el MP4 sin Resolve —ctx['render'] == 'mp4'— o el clip de Resolve); el primer héroe y UNA llamada a la
acción, con el acento del kit (el pop +3 dB con su octava baja), nunca un golpe ni un riser; los anillos que se dibujan justo tras su héroe callan;
el swipe del kit solo en los cortes de escena (centrado, sin paneo). Nada a < SOCIAL_HUECO_S de otro sonido (`_cerca_social`: de inicio a inicio
o de ancla a ancla; manda el de más prioridad: héroe > cinta > texto > etiqueta > trazo > corte); lo que se funde queda en su caption
('fusionados' y su porqué: «LOS» → con el pop de «SUBTÍTULOS»), nunca se pierde en silencio.

Lo que pide el usuario en la página (fase 6, el 5 % humano) entra aquí:
    controles   {'estilo': auto|limpio|cinematico|energico|minimo, 'intensidad' / 'densidad' / 'voz': auto|poco|medio|mucho} (música y ambiente:
                fase 4). AUTO = lo que decidió la IA. El estilo mueve la paleta; la intensidad, el nivel y el peso (no cambia el carácter del tema);
                la densidad, el umbral y el tope por ventana; la voz, cuánto se apartan los sonidos cuando ella habla.
    ajustes     {clave_de_evento: {'silenciar', 'bloqueado' + 'plan' (el evento ya hecho, no se rehace), 'params' (MENOS / MÁS), 'dur_k', 'semilla'}}
    ronda       sube con «Rediseñar sonido»: otras variaciones de todo lo que no esté bloqueado.
"""
import hashlib
import math

import numpy as np

import director_sonido_eventos as EV

TIPOS = ('golpe', 'whoosh', 'giro', 'riser', 'trazo', 'acento', 'tick', 'pop')
IMPORTANCIA_MOTION = {'escena': 0.7, 'whoosh_grande': 0.65, 'whoosh': 0.5, 'pop': 0.42, 'tick': 0.35, 'golpe': 0.6}
CLAVE_PRO = {'whoosh': 'whoosh', 'pop': 'pop', 'pin': 'pop', 'click': 'tick', 'ui': 'tick', 'corte': 'tick', 'hit': 'golpe', 'tecla': 'tick',
             'cash': 'acento', 'error': None, 'riser': None}          # error: el modo gris ya se ve; un zumbido sobra · riser: lo decide el director
CLIP_VIRAL = {'v shatter': ('golpe', 0.2), 'v drag': ('whoosh', 0.12), 'v select': ('tick', 0.1), 'v negrita': ('pop', 0.05)}
VISUAL_FX = {'corte': ('whoosh', 0.55), 'enfasis': ('whoosh', 0.4), 'broll': ('whoosh', 0.45), 'icono': ('pop', 0.4), 'pegatina': ('pop', 0.4),
             'numero': ('tick', 0.42)}
CHOQUE_S = 0.15                       # un motion menor no suena a menos de esto de un acento de caption
ESTILOS = {'limpio': {'impacto': -0.25, 'densidad': -0.1, 'ui': 0.2, 'reverb': -0.1},
           'cinematico': {'impacto': 0.2, 'reverb': 0.2, 'transitorios': 0.1, 'densidad': -0.05},
           'energico': {'densidad': 0.2, 'transitorios': 0.2, 'motion': 0.2, 'impacto': 0.1},
           'minimo': {'densidad': -0.3, 'impacto': -0.1, 'motion': -0.2},
           'social': {'impacto': -0.2, 'densidad': 0.3, 'ui': 0.3, 'reverb': -0.2}}          # «Social (CapCut)»: ver disenar
SOCIAL_HUECO_S = 0.22                  # Social: nada a menos de esto de otro sonido, pops, swipes de corte y motions (el ritmo, sin amontonar)
SOCIAL_TOPE = 24                       # Social: sonidos por ventana de 10 s (el Tema 1 llega a 18 en 10 s: con 14 se perdían palabras que se ven)
SOCIAL_TRAZO_S = 0.25                  # Social: un anillo / subrayado que empieza a menos de esto tras su héroe calla (ya suena el pop del héroe)
MP4_ENTRADA_S = 0.12                   # el fundido de entrada de cada elemento en el MP4 sin Resolve (render_temas.ENTRADA_S, smoothstep)
# Social: lo que suena en cada cosa que se ve —el MISMO sonido del kit— (sonido del kit, semitonos, prioridad al fusionar dos a < SOCIAL_HUECO_S,
# importancia para la densidad, duración del archivo). El nivel, en director_sonido_eventos.SOCIAL_NIVEL.
SOCIAL_MAPA = {'acento': ('pop', -2, 6, 0.95, 0.2), 'heroe': ('pop', 0, 5, 0.9, 0.15), 'cinta': ('pop', -3, 4, 0.8, 0.15),
               'texto': ('pop', 2, 3, 0.7, 0.15), 'etiqueta': ('pop', 4, 2, 0.6, 0.15), 'trazo': ('pop', 2, 1, 0.5, 0.15),
               'corte': ('whoosh', 0, 0, 0.45, 0.21)}
SOCIAL_CAPA_ACENTO = (-12, -8.0)       # el acento: el mismo pop una octava abajo y 8 dB bajo él, para darle cuerpo (sin boom)
DENSIDAD = {'poco': 0.1, 'medio': 0.35, 'mucho': 0.7}
INTENSIDAD = {'poco': (-4.0, 0.8), 'medio': (0.0, 1.0), 'mucho': (3.0, 1.15)}        # (dB para todos, factor de peso del golpe)
VOZ = {'poco': (1.0, 1.0), 'medio': (0.0, 2.0), 'mucho': (-3.0, 5.0)}              # (dB para todos, dB más si cae sobre una palabra)


def _semilla(*partes):
    return int(hashlib.sha1('|'.join(str(p) for p in partes).encode('utf-8')).hexdigest()[:8], 16)


def clave(e):
    """La identidad de un evento entre un diseño y el siguiente (para sus ajustes): origen, caption, tipo e instante (a 0,1 s)."""
    return f"{e.get('origen')}|{e.get('ref')}|{e.get('tipo')}|{round(float(e.get('ancla') or 0.0), 1)}"


def con_controles(analisis, controles):
    """La PALETA con el estilo que pidió el usuario encima (AUTO = la de la IA). No toca el análisis original."""
    c = controles or {}
    estilo = ESTILOS.get(c.get('estilo') or 'auto')
    if not estilo and c.get('densidad') not in DENSIDAD:
        return analisis
    a = dict(analisis)
    v = dict(((analisis.get('paleta') or {}).get('valores') or {}))
    for k, d in (estilo or {}).items():
        v[k] = round(float(np.clip(float(v.get(k, 0.5)) + d, 0, 1)), 3)
    if c.get('densidad') in DENSIDAD:
        v['densidad'] = DENSIDAD[c['densidad']]
    a['paleta'] = dict(analisis.get('paleta') or {}, valores=v)
    return a


def caracter(analisis, controles=None):
    """Cómo suena el ACENTO de caption de ESTE tema (de su identidad, nada fijo por número de tema) y cuánto se permite."""
    analisis = con_controles(analisis, controles)
    c = controles or {}
    r = analisis.get('rasgos') or {}
    v = (analisis.get('paleta') or {}).get('valores') or {}
    impacto, ui = float(v.get('impacto', 0.5)), float(v.get('ui', 0.5))
    if r.get('modo_pro') == 'editorial':
        acento, motivo = 'trazo', 'PRO editorial: cálido y acústico, una pluma en vez de un golpe'
    elif impacto >= 0.6:
        acento, motivo = 'golpe', f'impacto {impacto:.2f}: la palabra grande pega'
    elif r.get('modo_pro') == 'sobria' or (ui >= 0.6 and impacto < 0.45):
        acento, motivo = 'tick', f'sobrio / interfaz (ui {ui:.2f}): un toque nítido, nada de golpes'
    elif impacto >= 0.42:
        acento, motivo = 'pop', f'impacto medio ({impacto:.2f}): la palabra aparece con cuerpo, sin golpe'
    else:
        acento, motivo = 'tick', f'impacto bajo ({impacto:.2f}): solo un toque'
    return {'acento': acento, 'por_que': motivo, 'estilo': r.get('estilo'), 'modo_pro': r.get('modo_pro'),
            'riser': impacto >= 0.45 and r.get('modo_pro') not in ('sobria', 'editorial'),
            'cortes_cada_s': 6.0 if float(v.get('motion', 0.5)) >= 0.45 else 10.0,
            'cortes_whoosh': float(v.get('transitorios', 0.5)) >= 0.6 and r.get('modo_pro') not in ('sobria', 'editorial'),
            'sobrio': r.get('modo_pro') in ('sobria', 'editorial'),
            'densidad': float(v.get('densidad', 0.3)), 'impacto': impacto, 'brillo': float(v.get('brillo', 0.5)), 'reverb': float(v.get('reverb', 0.5)),
            'nivel_extra_db': INTENSIDAD.get(c.get('intensidad'), (0.0, 1.0))[0] + VOZ.get(c.get('voz'), (0.0, 2.0))[0],
            'peso_k': INTENSIDAD.get(c.get('intensidad'), (0.0, 1.0))[1], 'sobre_voz_db': VOZ.get(c.get('voz'), (0.0, 2.0))[1],
            'controles': {k: c.get(k) for k in ('estilo', 'intensidad', 'densidad', 'voz') if c.get(k) not in (None, 'auto')}}


def _momento_caption(c, car, fps):
    """El instante que manda en un caption, su clip y su energía visual: {'t', 'ancla', 'tipo', 'bono', 'texto', 'anillo', 'cinta', 'que'} o None."""
    runs = [r for r in (c.get('runs') or []) if isinstance(r, dict)]
    estilo = car['estilo']
    if estilo in ('kinetic', 'viral') and not any(r.get('k') for r in runs):   # v5.37: los bloques de GO aún sin los clips del tema (Tema 1 neón: los
        linea = next((l for l in (c.get('lines') or []) if isinstance(l, dict) and l.get('role') == 'main'), None)    # captions los arma el kit
        if linea is not None:                                                 # en la PRO): la palabra principal entra con el «pop» del héroe
            t = float(linea.get('start') or c.get('start') or 0.0)
            a = EV.ANIM_KINETIC['pop']
            return {'t': t, 'ancla': t + (0.37 * a['f'] / fps if estilo == 'kinetic' else 0.05), 'tipo': car['acento'] if estilo == 'kinetic' else 'pop',
                    'bono': 0.1, 'size': 0.25, 'texto': str(linea.get('text') or ''), 'que': 'entra la palabra principal', 'anillo': None, 'cinta': None}
    if estilo == 'kinetic':
        con_k = [r for r in runs if r.get('k')]
        heroe = next((r for r in con_k if str(r['k']).startswith('k hero')), None) or max(con_k, key=lambda r: float(r.get('size') or 0), default=None)
        if heroe is None:
            return None
        t = float(heroe.get('t') or c.get('start') or 0.0)
        size = float(heroe.get('size') or 0.2)
        a = EV.ANIM_KINETIC['pop']
        return {'t': t, 'ancla': t + 0.37 * a['f'] / fps, 'tipo': car['acento'], 'bono': float(np.clip((size - 0.2) * 0.8, 0, 0.2)), 'size': size,
                'texto': str(heroe.get('texto') or ''), 'que': f"el héroe entra con «pop» {a['f']} f easeOutBack (×2,6, giro −4°)",
                'anillo': next((r for r in con_k if EV.anim_de_clip(r['k']) == 'trazo'), None),
                'cinta': next((r for r in con_k if EV.anim_de_clip(r['k']) == 'giro'), None)}
    if estilo == 'viral':
        mejor = None
        for r in runs:
            clip = ' '.join(str(r.get('k') or '').split()[:2])
            if clip in CLIP_VIRAL and (mejor is None or CLIP_VIRAL[clip][1] > CLIP_VIRAL[mejor[0]][1]):
                mejor = (clip, r)
        if mejor is None:
            return None                                                   # solo la pila fina: no hay palabra protagonista
        clip, r = mejor
        tipo, bono = CLIP_VIRAL[clip]
        t = float(r.get('t') or c.get('start') or 0.0)
        return {'t': t, 'ancla': t + (0.1 if tipo == 'whoosh' else 0.05), 'tipo': tipo, 'bono': bono, 'size': float(r.get('size') or 0.1),
                'texto': str(r.get('texto') or ''), 'que': f'la palabra clave entra con «{clip[2:]}»', 'anillo': None, 'cinta': None}
    main = next((r for r in runs if r.get('rol') == 'main'), None)
    if main is not None:                                                  # «guion» (Temas 2, 4, 5, 6): la palabra clave con su zoom
        zoom = float(main.get('zoom') or 1.0)
        t = float(main.get('t') or c.get('start') or 0.0)
        return {'t': t, 'ancla': t + 0.05, 'tipo': car['acento'], 'bono': float(np.clip((zoom - 1.0) * 0.5, 0, 0.2)), 'size': zoom,
                'texto': str(main.get('texto') or ''), 'que': f'la palabra clave aparece a ×{zoom:.2f}', 'anillo': None, 'cinta': None}
    lineas = [l for l in (c.get('lines') or []) if isinstance(l, dict) and l.get('role') == 'main']
    if lineas:                                                            # 3 líneas: la principal
        t = float(lineas[0].get('start') or c.get('start') or 0.0)
        return {'t': t, 'ancla': t + 0.04, 'tipo': car['acento'], 'bono': 0.0, 'size': 1.0, 'texto': str(lineas[0].get('text') or ''),
                'que': 'entra la línea principal', 'anillo': None, 'cinta': None}
    return None


def _en_voz(palabras, t):
    return any(float(p.get('start') or 0) <= t <= float(p.get('end') or 0) for p in palabras or [])


def _ease_out_back(p, c1=1.70158):
    return 1.0 + (c1 + 1.0) * (p - 1.0) ** 3 + c1 * (p - 1.0) ** 2


def _fotogramas_hasta(anim):
    """Fotogramas desde el inicio de un clip del Tema 1 (ANIM_KINETIC, easeOutBack) hasta el primero con ≥ 50 %: en el héroe («pop», de 0,38× a
    1×), el 50 % de su ÁREA final (escala ≥ 0,71: + 2 f, ya a 0,82); en los demás, de su entrada; un anillo que se dibuja, su primer fotograma."""
    a = EV.ANIM_KINETIC.get(anim) or EV.ANIM_KINETIC['abre']
    if anim == 'trazo' or not a.get('f'):
        return 1
    umbral = (math.sqrt(0.5) - 0.38) / 0.62 if anim == 'pop' else 0.5
    return next((k for k in range(1, int(a['f']) + 1) if _ease_out_back(k / float(a['f'])) >= umbral), 1)


def _aterrizaje(t, clase, render, fps, anim=None, ancla=None):
    """El instante (en la rejilla de fotogramas) en que lo que entra ATERRIZA, donde va su sonido en Social:
        MP4 sin Resolve (ctx['render'] == 'mp4'; render_temas: fundido smoothstep de MP4_ENTRADA_S) → el primer fotograma con ≥ 50 % de opacidad,
            ceil((t0 + MP4_ENTRADA_S / 2)·fps)/fps; un anillo / subrayado, su primer fotograma visible.
        Resolve → el fotograma del clip + los suyos hasta el 50 % (`_fotogramas_hasta`; héroe «pop»: + 2 f). Sin clip del Tema 1 (guion, VIRAL,
            líneas): el instante de siempre (`ancla`), llevado al fotograma siguiente."""
    fps = float(fps or 30.0)
    if render == 'mp4':
        if clase == 'trazo':
            return math.ceil(t * fps + 1e-6) / fps
        return math.ceil((t + 0.5 * MP4_ENTRADA_S) * fps - 1e-6) / fps
    if anim:
        return (int(round(t * fps)) + _fotogramas_hasta(anim)) / fps
    return math.ceil((t if ancla is None else ancla) * fps - 1e-6) / fps


def _clase_social(r):
    """Qué es lo que entra, para su sonido en Social: 'heroe' | 'cinta' | 'texto' | 'etiqueta' | 'trazo' | None."""
    k = str(r.get('k') or '')
    if k.startswith('k hero'):
        return 'heroe'
    if k.startswith(('k tape', 'k tapes')):
        return 'cinta'
    if k.startswith('k ') and EV.anim_de_clip(k) == 'trazo':
        return 'trazo'
    if k.startswith('k label') or (k.startswith('k sup') and float(r.get('size') or 0.1) < 0.07):
        return 'etiqueta'                                             # (el «sup» pequeño hace de etiqueta; el normal y las cifras, de texto)
    if ' '.join(k.split()[:2]) in CLIP_VIRAL:
        return 'heroe'
    return 'texto' if str(r.get('texto') or '').strip() else None


def entradas_social(c, car, fps, render):
    """Lo que se ve entrar en un caption, para Social: [{'ancla', 'clase', 'texto', 't'}]. Con los clips del tema (Kinetic, VIRAL): cada run con 'k'
    y 't', en su aterrizaje; un anillo / subrayado a < SOCIAL_TRAZO_S tras su héroe, fuera (ya suena el héroe). Sin ellos (guion, líneas): la
    palabra principal y, si el bloque aparece ≥ 0,25 s antes, su entrada (texto)."""
    runs = [r for r in (c.get('runs') or []) if isinstance(r, dict) and r.get('k') and r.get('t') is not None]
    salida = []
    if runs:
        heroes = [float(r['t']) for r in runs if _clase_social(r) == 'heroe']
        for r in runs:
            clase, t = _clase_social(r), float(r['t'])
            if clase is None or (clase == 'trazo' and any(0.0 <= t - th < SOCIAL_TRAZO_S for th in heroes)):
                continue
            anim = EV.anim_de_clip(r['k']) if str(r['k']).startswith('k ') else None
            salida.append({'ancla': _aterrizaje(t, clase, render, fps, anim, t + 0.05), 'clase': clase, 'texto': str(r.get('texto') or ''), 't': t})
        return salida
    m = _momento_caption(c, car, fps)
    if m is None:
        return []
    salida.append({'ancla': _aterrizaje(m['t'], 'heroe', render, fps, None, m['ancla']), 'clase': 'heroe', 'texto': m['texto'], 't': m['t']})
    inicio = float(c.get('start') if c.get('start') is not None else m['t'])
    if m['t'] - inicio >= 0.25:
        salida.append({'ancla': _aterrizaje(inicio, 'texto', render, fps, None, inicio + 0.04), 'clase': 'texto', 'texto': '', 't': inicio})
    return salida


def _cerca_social(eventos, inicio, ancla):
    """Social: los sonidos que se oirían a < SOCIAL_HUECO_S de uno que empieza en `inicio` con su ancla en `ancla` (de inicio a inicio o de ancla
    a ancla: el swipe empieza 45 ms antes de su pico)."""
    return [e for e in eventos if e.get('decision') == 'GENERATE'
            and min(abs(float(e['t']) - inicio), abs(float(e['ancla']) - ancla)) < SOCIAL_HUECO_S]


def params_social(clase):
    """(tipo, duración, params) de un sonido del kit Social para esa clase (`SOCIAL_MAPA`): sin capa, sin síntesis, sin paneo."""
    kit, st, _prio, _imp, d = SOCIAL_MAPA[clase]
    p = {'kit': kit, 'social': clase, 'semitonos': st, 'direccion': 0.0, 'sin_capa': True, 'sin_sintesis': True}
    if clase == 'acento':
        p['capa_kit'] = list(SOCIAL_CAPA_ACENTO)
    return ('whoosh' if kit == 'whoosh' else 'pop'), d, p


def _captions_social(ctx, car, fps, render, frases, fin_intro, ev):
    """Social: cada cosa que entra en cada caption (`entradas_social`) con su sonido del kit; el primer héroe del video y el de UNA llamada a la
    acción, con el acento; dos a < SOCIAL_HUECO_S se funden quedándose el de más prioridad (héroe > cinta > texto > etiqueta > trazo); nada encima
    de la intro de Efectos. Crea los eventos con `ev` y devuelve (captions, viejos) como el resto de disenar."""
    captions, viejos, todos = [], [], []
    for i, c in enumerate(ctx.get('bloques') or []):
        if not isinstance(c, dict):
            continue
        entradas = entradas_social(c, car, fps, render)
        th = next((x['t'] for x in entradas if x['clase'] == 'heroe'), entradas[0]['t'] if entradas else float(c.get('start') or 0.0))
        rol, imp, _frase = EV._rol_en(frases, th)
        rol = 'HOOK' if i == 0 else rol
        captions.append({'cue': i, 't': round(th, 3), 'texto': next((x['texto'] for x in entradas if x['clase'] == 'heroe'), ''), 'rol': rol,
                         'caption_sound_score': 1.0, '_viejos': [e for e in (c.get('sfx_eventos') or []) if isinstance(e, dict)]})
        todos += [dict(x, cue=i, rol=rol, imp=float(imp)) for x in entradas]
    todos.sort(key=lambda x: x['ancla'])
    gancho = next((x for x in todos if x['clase'] == 'heroe'), None)
    cierre = next((x for x in todos if x['clase'] == 'heroe' and x['rol'] == 'CTA' and x is not gancho), None)
    for x in (gancho, cierre):
        if x is not None:
            x['clase'] = 'acento'
    puestos, fundidos = [], []
    for x in sorted(todos, key=lambda x: (-SOCIAL_MAPA[x['clase']][2], x['ancla'])):
        cerca = [y for y in puestos if abs(x['ancla'] - y['ancla']) < SOCIAL_HUECO_S]
        if x['ancla'] < fin_intro or cerca:                           # (lo que calla queda dicho en su caption: con quién va, o la intro)
            fundidos.append((x, min(cerca, key=lambda y: abs(x['ancla'] - y['ancla'])) if cerca and x['ancla'] >= fin_intro else None))
        else:
            puestos.append(x)
    for x in sorted(puestos, key=lambda x: x['ancla']):
        tipo, d, pk = params_social(x['clase'])
        que = {'acento': 'el acento del kit (pop +3 dB con su octava baja): la palabra que abre / cierra, sin golpe', 'heroe': 'el pop del kit',
               'cinta': 'el pop del kit, 3 semitonos abajo', 'texto': 'el pop del kit, 2 semitonos arriba y 4 dB menos',
               'etiqueta': 'el pop del kit, agudo y suave', 'trazo': 'el pop del kit, suave, al empezar a dibujarse'}[x['clase']]
        motivo = f"«{x['texto'] or x['clase']}» ({x['rol'].lower()}, {x['clase']}): {que}, cuando aterriza"
        ev(tipo, x['ancla'], x['ancla'], d, motivo, SOCIAL_MAPA[x['clase']][3] + 0.05 * x['imp'], 'caption', x['cue'],
           rel_db=EV.SOCIAL_NIVEL[x['clase']], **pk)
    for info in captions:
        suyos = [x for x in puestos if x['cue'] == info['cue']]
        info['decision'] = 'GENERATE' if suyos else 'LEAVE_SILENT'
        info['por_que'] = ('Social (CapCut): ' + ', '.join(f"{x['clase']} «{x['texto']}»" if x['texto'] else x['clase'] for x in suyos) +
                           ' con el kit, al aterrizar' if suyos else 'Social: lo suyo ya suena con otro sonido')
        info['fusionados'] = [{'texto': x['texto'], 'clase': x['clase'], 'ancla': round(x['ancla'], 3),
                               'con': (y['texto'] or y['clase']) if y else None, 'a_s': round(abs(x['ancla'] - y['ancla']), 3) if y else None}
                              for x, y in fundidos if x['cue'] == info['cue']]
        if info['fusionados']:
            info['por_que'] += ' · ' + '; '.join(
                f"«{f['texto'] or f['clase']}» → con el pop de «{f['con']}» (a {f['a_s']:.2f} s: nada a menos de {SOCIAL_HUECO_S:.2f} s)" if f['con']
                else f"«{f['texto'] or f['clase']}» calla: suena la intro de Efectos" for f in info['fusionados'])
        for e in info.pop('_viejos'):
            viejos.append({'cue': info['cue'], 'viejo': e.get('sfx_nombre') or e.get('sfx'), 't': e.get('t'), 'decision': 'REPLACE' if suyos else 'REMOVE',
                           'por_que': 'Social: el genérico se cambia por el pop del kit al aterrizar'})
    return captions, viejos


def disenar(analisis, ctx, fps=30.0, controles=None, ajustes=None, ronda=0):
    """El diseño de sonido de ESTE video (ver el docstring del módulo). Nunca cambia lo visual: solo lee."""
    car = caracter(analisis, controles)
    social = (controles or {}).get('estilo') == 'social'              # «Social (CapCut)»: todo lo que entra suena con el MISMO pop, al aterrizar
    render = 'mp4' if ctx.get('render') == 'mp4' else 'resolve'
    if social:
        car = dict(car, social=True, riser=False, render=render, acento='pop',
                   por_que='Social (CapCut): el mismo pop del kit en todo lo que entra, al aterrizar; swipe solo en los cortes')
    analisis = con_controles(analisis, controles)
    narr = analisis.get('narrativa') or {}
    frases = narr.get('frases') or []
    dur = float((analisis.get('voz') or {}).get('duracion') or 0.0) or float((ctx.get('palabras') or [{}])[-1].get('end') or 0.0)
    densidad, impacto, brillo, reverb = car['densidad'], car['impacto'], car['brillo'], car['reverb']
    umbral = 0.55 + 0.3 * (0.4 - densidad)
    palabras = ctx.get('palabras') or []
    eventos, viejos, captions, motions = [], [], [], []
    nota = (523.25 if brillo >= 0.5 else 392.0) * (0.75 if car['modo_pro'] == 'editorial' else 1.0)   # el MOTIVO del video: siempre la misma nota

    def ev(tipo, t, ancla, d, motivo, imp, origen, ref=None, rel_db=None, **params):
        params.setdefault('brillo', brillo)
        params['semilla'] = _semilla(tipo, round(ancla, 3), ref, ctx.get('video'), *((ronda,) if ronda else ()))
        if 'peso' in params:
            params['peso'] = round(float(np.clip(params['peso'] * car['peso_k'], 0.2, 1.0)), 3)
        sobre = _en_voz(palabras, ancla)
        rel = EV.NIVEL_REL_VOZ[tipo] + car['nivel_extra_db'] - (car['sobre_voz_db'] if tipo not in ('golpe', 'riser') and sobre else 0.0)
        rel -= max(0.0, car['sobre_voz_db'] - 2.0) * 0.3 if tipo == 'golpe' and sobre else 0.0     # (voz «máxima»: hasta el golpe se aparta un poco)
        if rel_db is not None:                                        # Social: el nivel de su tamaño, igual sobre la voz o no (el mismo pop)
            rel = rel_db + car['nivel_extra_db']
        eventos.append({'id': f'{tipo}-{len(eventos) + 1:02d}', 'tipo': tipo, 't': round(max(0.0, t), 3), 'ancla': round(ancla, 3), 'dur': round(d, 3),
                        'pista': EV.PISTA[tipo], 'nivel_rel_voz_db': round(rel, 1),
                        'params': params, 'decision': 'GENERATE', 'por_que': motivo, 'importancia': round(float(imp), 2), 'origen': origen, 'ref': ref})
        return eventos[-1]

    # --- intro / outro de Efectos con su sonido propio: se respetan (van pegados a su animación)
    fx_ev = [e for e in ((ctx.get('plan_efectos') or {}).get('eventos') or []) if isinstance(e, dict)]
    intro_sonido = next((e for e in fx_ev if e.get('tipo') == 'sonido' and not e.get('extra') and float(e.get('ini') or 0) < 1.0), None)
    fin_intro = float(intro_sonido.get('pico') or intro_sonido.get('dur') or 0.8) + 0.25 if intro_sonido else 0.0

    # --- captions. Social: todo lo que entra, con el kit (sin umbral, sin capa sintética, sin golpes); se funde por prioridad
    if social:
        captions, viejos = _captions_social(ctx, car, fps, render, frases, fin_intro, ev)
    ultimo, n_datos, gancho_usado = -99.0, 0, False
    for i, c in enumerate(ctx.get('bloques') or []):
        if not isinstance(c, dict) or social:
            continue
        viejos_c = [e for e in (c.get('sfx_eventos') or []) if isinstance(e, dict)]
        m = _momento_caption(c, car, fps)
        if m is None:
            for e in viejos_c:
                viejos.append({'cue': i, 'viejo': e.get('sfx_nombre') or e.get('sfx'), 't': e.get('t'), 'decision': 'REMOVE',
                               'por_que': 'el caption no tiene palabra protagonista: el sonido de Simple sobra'})
            continue
        t = m['t']
        rol, imp, _frase = EV._rol_en(frases, t)
        if i == 0:
            rol = 'HOOK'
        cifra = any(ch.isdigit() for ch in m['texto'])
        peso_rol = EV.PESO_ROL.get(rol, 0.0)
        if rol == 'HOOK' and gancho_usado:
            peso_rol = 0.15                                           # el gancho se marca UNA vez; los que siguen, como uno más
        s = 0.15 + peso_rol + 0.25 * float(imp) + m['bono'] + (0.1 if m['anillo'] else 0.0) + (0.15 if cifra else 0.0)
        hueco = t - ultimo
        s -= 0.35 if hueco < 3.0 else (0.15 if hueco < 5.0 else 0.0)
        if hueco < 2.0 and not cifra:
            s = min(s, umbral - 0.01)                                 # dos acentos a menos de 2 s se pisan (salvo una cifra)
        if t < fin_intro:
            s = min(s, umbral - 0.01)                                 # la intro de Efectos ya suena aquí
        s = float(np.clip(s, 0, 1))
        info = {'cue': i, 't': round(t, 3), 'texto': m['texto'], 'rol': rol, 'caption_sound_score': round(s, 2)}
        if s < umbral:
            info['decision'] = 'LEAVE_SILENT'
            info['por_que'] = (f'score {s:.2f} < {umbral:.2f}' + (f' (otro acento hace {hueco:.1f} s)' if hueco < 5 else '') +
                               (' (suena la intro)' if t < fin_intro else '') + f': {rol.lower()}, lo dice la voz y el tema ya lo anima')
            for e in viejos_c:
                viejos.append({'cue': i, 'viejo': e.get('sfx_nombre') or e.get('sfx'), 't': e.get('t'), 'decision': 'REMOVE',
                               'por_que': 'un sonido en casi cada caption cansa y tapa la voz: este caption va en silencio'})
            captions.append(info)
            continue
        tipo = m['tipo']
        info['decision'] = 'REPLACE' if viejos_c else 'GENERATE'
        info['por_que'] = f'score {s:.2f} ≥ {umbral:.2f}: {rol.lower()}' + (' con cifra' if cifra else '') + (' y anillo' if m['anillo'] else '')
        if tipo == 'golpe':
            pre = 0.09
            peso = float(np.clip(0.35 + 1.4 * float(m['size'] if car['estilo'] == 'kinetic' else 0.25) * impacto, 0.3, 1.0))
            ev('golpe', m['ancla'] - pre, m['ancla'], 0.6, f"«{m['texto']}» ({rol.lower()}): {m['que']}; el golpe cae cuando llega a su tamaño, "
               f"con {int(pre * 1000)} ms de aire antes; peso {peso:.2f}", s, 'caption', i, peso=peso, cola=0.35 + 0.3 * reverb, pre=pre,
               brillo=float(np.clip(brillo + (0.25 if car['estilo'] == 'viral' else 0.0), 0, 1)))
        elif tipo == 'whoosh':
            d = 0.3
            ev('whoosh', m['ancla'] - 0.55 * d, m['ancla'], d + 0.12, f"«{m['texto']}» ({rol.lower()}): {m['que']}: aire corto que arrastra la palabra",
               s, 'caption', i, direccion=0.6, easing='easeOutCubic', peso=0.35)
        elif tipo == 'trazo':
            ev('trazo', m['ancla'] - 0.02, m['ancla'], 0.32, f"«{m['texto']}» ({rol.lower()}): {m['que']}: una pluma sobre papel, no un golpe", s,
               'caption', i, potencia=2.0, brillo=min(brillo, 0.45))
        else:
            ev(tipo, m['ancla'], m['ancla'], 0.25 if tipo == 'tick' else 0.3, f"«{m['texto']}» ({rol.lower()}): {m['que']}: {car['por_que']}", s, 'caption', i)
        for e in viejos_c:
            viejos.append({'cue': i, 'viejo': e.get('sfx_nombre') or e.get('sfx'), 't': e.get('t'), 'decision': 'REPLACE',
                           'por_que': f'el sonido genérico se cambia por un {tipo} diseñado para ESTE momento (tiempo, tamaño y paleta)'})
        ultimo = t
        gancho_usado = gancho_usado or rol == 'HOOK'
        if m['anillo'] is not None and rol in ('HOOK', 'DATA', 'REVEAL', 'CTA'):
            ta = float(m['anillo'].get('t') or t)
            ev('trazo', ta, ta, EV.ANIM_KINETIC['trazo']['s'] + 0.05, 'el anillo se dibuja en 0,45 s frenando (1 − (1 − p)^2,4): rotulador con esa energía',
               s * 0.8, 'caption', i, potencia=2.4)
        if m['cinta'] is not None and rol in ('HOOK', 'REVEAL', 'CTA'):
            tc = float(m['cinta'].get('t') or t)
            f = EV.ANIM_KINETIC['giro']['f']
            ev('giro', tc, tc + 0.6 * f / fps, f / fps + 0.05, f'la cinta entra girada −9° en {f} f: whoosh que da la vuelta y el slap al pegarse',
               s * 0.7, 'caption', i)
        if rol == 'DATA' and n_datos < 3:
            ev('acento', m['ancla'] + 0.02, m['ancla'], 1.1, 'motivo de los datos: la misma nota en cada cifra (identidad del video)', s * 0.7, 'dato', i, nota=nota)
            n_datos += 1
        captions.append(info)
    acentos = [e for e in eventos if e['origen'] == 'caption' and e['tipo'] in ('golpe', 'pop', 'tick', 'trazo', 'whoosh')]

    # --- el gancho: un riser corto que acaba en el primer acento fuerte (si llega pronto y el tema lo pide)
    golpes = [e for e in acentos if e['tipo'] == 'golpe']
    if car['riser'] and not social and not intro_sonido and golpes and 0.9 < golpes[0]['ancla'] <= 4.0:
        g = golpes[0]
        d = min(1.6, g['ancla'] - 0.05)
        ev('riser', g['ancla'] - d, g['ancla'], d, f'gancho: sube {d:.1f} s y se corta 30 ms antes del primer golpe (payoff)', 0.9, 'gancho')
    # --- el cierre: el motivo, más largo, en la última llamada a la acción con sonido
    cta = [c for c in captions if c['rol'] == 'CTA' and c.get('decision') != 'LEAVE_SILENT' and not social]   # (Social: sin firma tonal)
    if cta:
        tf = cta[-1]['t'] + 0.15
        ev('acento', tf, tf, 1.6, 'cierre (CTA): el motivo del video, más largo — firma sonora del final', 0.8, 'cierre', cta[-1]['cue'], nota=nota * 0.75)

    # --- motions de la PRO (el mismo «cuándo» que usa la PRO) y de Efectos
    pro = ctx.get('plan_pro') or {}
    candidatos = []                                                       # (tipo, t_ancla, dur, importancia, motivo, params)
    transiciones = []
    if pro.get('piezas'):
        try:
            import edicion_pro_sonido as PS
            momentos, transiciones = PS.momentos({'piezas': pro['piezas'], 'tema5': pro.get('tema5')}, ())
        except Exception:
            momentos = []
        for k_pro, t, nivel, largo, _ancla, que in momentos:
            tipo = CLAVE_PRO.get(k_pro, 'tick')
            if tipo is None:
                motions.append({'t': round(float(t), 3), 'que': que, 'decision': 'LEAVE_SILENT', 'por_que': 'se ve solo; un sonido aquí sobra'})
                continue
            if car['sobrio'] and tipo == 'whoosh' and str(que).startswith('sale'):
                motions.append({'t': round(float(t), 3), 'que': que, 'decision': 'LEAVE_SILENT', 'por_que': 'tema sobrio: solo suena lo que entra'})
                continue
            grande = k_pro == 'whoosh' and nivel >= -10.5
            imp = IMPORTANCIA_MOTION['whoosh_grande' if grande else tipo]
            if tipo == 'whoosh' and str(que).startswith('entra'):
                imp += 0.1                                            # lo que ENTRA manda (la escena que llega se oye; la que se va, menos)
            elif tipo == 'whoosh' and str(que).startswith('sale'):
                imp -= 0.1
            d = float(largo or 0.5) if tipo == 'whoosh' else 0.3
            candidatos.append((tipo, float(t), d, imp, f'PRO: {que}', {'peso': 0.55 if grande else 0.35, 'direccion': 0.0}))
    for e in fx_ev:
        tp = e.get('tipo')
        if tp not in VISUAL_FX:
            continue
        tipo, imp = VISUAL_FX[tp]
        a, d = float(e.get('ini') or 0.0), float(e.get('dur') or 0.5)
        ancla = a + (min(d, 0.6) / 2 if tp == 'corte' else 0.1)
        claro = str(e.get('asset') or '') in ('destello', 'glitch')
        candidatos.append((tipo, ancla, min(0.6, max(0.25, d)) if tipo == 'whoosh' else 0.25, imp, f"Efectos: {tp} «{e.get('asset') or ''}»",
                           {'peso': 0.4, 'brillo': float(np.clip(brillo + (0.2 if claro else 0.0), 0, 1)), 'direccion': 0.0}))
    lado = 1.0
    for tipo, t, d, imp, motivo, params in sorted(candidatos, key=lambda x: x[1]):
        cerca = (_cerca_social(eventos, t - (0.045 if tipo == 'whoosh' else 0.0), t) if social
                 else [e for e in eventos if abs(e['ancla'] - t) < CHOQUE_S])
        if cerca:
            motions.append({'t': round(t, 3), 'que': motivo, 'decision': 'LEAVE_SILENT',
                            'por_que': f"pisaría «{cerca[0]['id']}» (a menos de {SOCIAL_HUECO_S if social else CHOQUE_S:.2f} s)"})
            continue
        if social:                                                    # (Social: el mismo kit también en lo que mueve la PRO / Efectos)
            clase = 'corte' if tipo == 'whoosh' else ('heroe' if tipo == 'golpe' else 'texto')
            tp, d_k, pk = params_social(clase)
            ev(tp, t - (0.045 if tp == 'whoosh' else 0.0), t, d_k, f'{motivo}: el {pk["kit"]} del kit Social', imp, 'motion', None,
               rel_db=EV.SOCIAL_NIVEL[clase], brillo=params.get('brillo', brillo), **pk)
        elif tipo == 'whoosh':
            params['direccion'] = lado * 0.7
            lado = -lado
            ev('whoosh', t - 0.55 * d, t, d + 0.12, f'{motivo}: aire con el pico en el movimiento ({d:.2f} s)', imp, 'motion', None, easing='easeInOutCubic', **params)
        elif tipo == 'golpe':
            ev('golpe', t - 0.05, t, 0.5, f'{motivo}: un golpe suave', imp, 'motion', None, pre=0.05, cola=0.25, **{k: v for k, v in params.items() if k != 'direccion'})
        else:
            ev(tipo, t, t, 0.25, f'{motivo}: toque de interfaz a la medida', imp, 'motion', None, **{k: v for k, v in params.items() if k not in ('peso', 'direccion')})
        motions.append({'t': round(t, 3), 'que': motivo, 'decision': 'GENERATE', 'id': eventos[-1]['id']})
    # risers antes de las escenas grandes de la PRO: como mucho uno cada 20 s, nunca encima de un golpe de caption (no en temas sobrios)
    if car['riser']:
        ultimo_r = -99.0
        for t, que in sorted(transiciones):
            t = float(t)
            if (t < 2.0 or t - ultimo_r < 20.0 or any(e['tipo'] == 'riser' and abs(e['ancla'] - t) < 8.0 for e in eventos)
                    or any(e['tipo'] == 'golpe' and e['origen'] == 'caption' and abs(e['ancla'] - t) < 2.5 for e in eventos)):
                continue
            ev('riser', t - 1.2, t, 1.2, f'transición grande de la PRO ({que}): la tensión sube y se corta justo al entrar', 0.55, 'motion')
            ultimo_r = t
    # --- cortes de escena que respiran (sin otra transición): aire, de lado alterno — solo en temas enérgicos (en uno sobrio, un corte seco no
    #     tiene movimiento que suene: sería un sonido sin causa)
    ultimo_w = -99.0
    for tc in sorted(float(x) for x in (ctx.get('cortes') or []) if car['cortes_whoosh'] or social):
        if social:                                                    # Social: el swipe del kit en cada corte, centrado y con su pico en el corte,
            if (tc < 1.0 or _cerca_social(eventos, tc - 0.045, tc)    # salvo que otro sonido caiga a < SOCIAL_HUECO_S (el corte es lo último:
                    or any(e['origen'] == 'motion' and e['tipo'] in ('whoosh', 'riser', 'golpe') and abs(tc - e['ancla']) < 1.5 for e in eventos)):
                continue                                              # un pop a 0,13 s ya lo marca y los dos juntos se amontonan)
            tp, d_k, pk = params_social('corte')
            ev(tp, tc - 0.045, tc, d_k, f'corte de escena a {tc:.2f} s: el swipe del kit, centrado, con su pico en el corte', SOCIAL_MAPA['corte'][3],
               'corte', None, rel_db=EV.SOCIAL_NIVEL['corte'], **pk)
            continue
        if (tc - ultimo_w < car['cortes_cada_s'] or tc < 1.0 or any(abs(tc - e['ancla']) < 0.6 for e in eventos)
                or any(e['origen'] == 'motion' and e['tipo'] in ('whoosh', 'riser', 'golpe') and abs(tc - e['ancla']) < 1.5 for e in eventos)):
            continue
        d = 0.42
        ev('whoosh', tc - d * 0.55, tc, d + 0.12, f'corte de escena a {tc:.2f} s: aire que pasa con easeInOutCubic (pico en el corte), de lado alterno', 0.5,
           'corte', None, direccion=lado * 0.8, easing='easeInOutCubic', peso=0.4)
        lado, ultimo_w = -lado, tc

    # --- lo que el usuario pidió para cada evento (página AI Sound Director): silenciar, bloquear, MENOS / MÁS, regenerar
    for e in eventos:
        aj = (ajustes or {}).get(clave(e)) or {}
        if not aj:
            continue
        e['clave'] = clave(e)
        if aj.get('silenciar'):
            e['decision'] = 'LEAVE_SILENT'
            e['por_que'] += ' — SILENCIADO por ti'
            e['ajustado'] = True
            continue
        if aj.get('params'):
            e['params'].update(aj['params'])
            e['ajustado'] = True
        if aj.get('dur_k'):
            e['dur'] = round(max(0.08, e['dur'] * float(aj['dur_k'])), 3)
        if aj.get('semilla') is not None:
            e['params']['semilla'] = int(aj['semilla'])
        if aj.get('bloqueado'):
            e['bloqueado'] = True
            if isinstance(aj.get('plan'), dict):
                e['plan_fijo'] = dict(aj['plan'])
    # --- densidad: como mucho 2 + 4·densidad sonidos por ventana de 10 s; compiten por importancia (solo el gancho, el cierre y lo bloqueado van fijos)
    tope = SOCIAL_TOPE if social else int(round(2 + 4 * densidad))
    eventos.sort(key=lambda e: e['t'])
    fijos = {e['id'] for e in eventos if e['origen'] in ('gancho', 'cierre') or e.get('bloqueado') or e.get('ajustado')}   # (lo retocado por el usuario se queda)
    if golpes and any(e['origen'] == 'gancho' for e in eventos):
        fijos.add(golpes[0]['id'])                                    # el golpe que remata el riser del gancho
    for k0 in np.arange(0, max(dur, 1.0), 10.0):
        dentro = [e for e in eventos if k0 <= e['ancla'] < k0 + 10 and e['decision'] == 'GENERATE']
        sobran = max(0, len(dentro) - tope)
        for e in sorted((e for e in dentro if e['id'] not in fijos), key=lambda e: (e['importancia'], -e['t']))[:sobran]:
            e['decision'] = 'REMOVE'
            e['por_que'] += f' — QUITADO: más de {tope} sonidos en {int(k0)}–{int(k0) + 10} s (pesa menos que los que quedan)'
    for info in captions:                                             # sin su acento, el caption entero va en silencio (anillo, cinta y nota también)
        if info.get('decision') == 'LEAVE_SILENT':
            continue
        suyos = [e for e in eventos if e.get('ref') == info['cue'] and e['origen'] in ('caption', 'dato')]
        if social and suyos and any(e['decision'] == 'GENERATE' for e in suyos):
            continue                                                  # (Social: un caption tiene varios pops; calla solo si se quedó sin todos)
        if suyos and suyos[0]['decision'] == 'REMOVE':
            for e in suyos:
                if e['decision'] == 'GENERATE':
                    e['decision'] = 'REMOVE'
                    e['por_que'] += ' — QUITADO: su caption se quedó sin acento'
            info['decision'] = 'LEAVE_SILENT'
            info['por_que'] += ' → LEAVE_SILENT: no cupo en su ventana de 10 s'
            for v in viejos:
                if v['cue'] == info['cue'] and v['decision'] == 'REPLACE':
                    v['decision'] = 'REMOVE'
    activos = [e for e in eventos if e['decision'] == 'GENERATE']
    resumen = {'captions': len(captions), 'con_sonido': sum(1 for c in captions if c['decision'] != 'LEAVE_SILENT'),
               'en_silencio': sum(1 for c in captions if c['decision'] == 'LEAVE_SILENT'), 'eventos': len(activos),
               'motions': len(motions), 'motions_con_sonido': sum(1 for m in motions if m['decision'] == 'GENERATE' and
                                                                   any(e['id'] == m.get('id') and e['decision'] == 'GENERATE' for e in eventos)),
               'por_tipo': {t: sum(1 for e in activos if e['tipo'] == t) for t in sorted({e['tipo'] for e in activos})},
               'por_origen': {o: sum(1 for e in activos if e['origen'] == o) for o in sorted({e['origen'] for e in activos})},
               'viejos': {d: sum(1 for x in viejos if x['decision'] == d) for d in ('REPLACE', 'REMOVE', 'KEEP')}, 'umbral': round(umbral, 2),
               'acento': car['acento'], 'por_que_acento': car['por_que'], 'intro_de_efectos': bool(intro_sonido), 'controles': car['controles'],
               'ronda': int(ronda or 0), 'ajustados': sum(1 for e in eventos if e.get('ajustado') or e.get('bloqueado'))}
    for e in eventos:
        e.setdefault('clave', clave(e))
    return {'eventos': eventos, 'captions': captions, 'motions': motions, 'viejos': viejos, 'caracter': car, 'resumen': resumen}
