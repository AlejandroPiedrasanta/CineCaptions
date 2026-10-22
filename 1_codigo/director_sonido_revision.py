# CineCaptions · By Cinema Productions
# 1_codigo/director_sonido_revision.py — la REVISIÓN del AI Sound Director: que todo lo que se ve tenga su decisión sonora.
"""
El diseño (director_sonido_diseno.disenar) decide qué suena; esta revisión lo vuelve a mirar ENTERO, en rondas, hasta que no queda nada que arreglar.
Solo DATOS: lee captions, motions, cortes y lo que ya suena; nunca cambia lo visual.

    1. inventario   cada cosa que se ve (caption, motion de la PRO o de Efectos, corte, sonido de la PRO ya puesto) y si tiene sonido o silencio con motivo
    2. rescate      lo importante que se quedó sin sonido y sin motivo de peso (quitado por densidad, caption justo bajo el umbral) vuelve si cabe
    3. coherencia   choques (< CHOQUE_S), ráfagas (más de RAFAGA_N en RAFAGA_S) y densidad por ventana de 10 s, contando lo de fuera (PRO)
    4. otra ronda   si algo cambió; para cuando una ronda no cambia nada o se acaban las rondas del razonamiento

Cuándo corre: en preparar_sfx (GO, al aplicar el tema, y cada rediseño de la página) y en la REVISIÓN FINAL de GO (director_sonido_sesion.revision_final),
con captions, Efectos y PRO ya en Resolve: ahí los sonidos de la PRO rehechos entran como `externos` (fijos: van pegados a su animación).

Razonamiento (control 'razonamiento' de la página; Auto = profundo): cuántas rondas, desde qué importancia se rescata, cuánto margen bajo el umbral
tiene un caption y cuántos sonidos más caben por ventana de 10 s. Lo bloqueado, lo retocado por el usuario, el gancho y el cierre no se tocan.
"""
import copy

import numpy as np

import director_sonido_diseno as D3
import director_sonido_eventos as EV

PROFUNDIDAD = {   # rondas · rescate (importancia mínima) · margen bajo el umbral de caption · sitio extra por ventana de 10 s · cortes (× su espaciado)
    'rapido': {'rondas': 1, 'rescate': 0.75, 'margen': 0.0, 'extra': 0, 'cortes_k': 1.0},
    'profundo': {'rondas': 2, 'rescate': 0.6, 'margen': 0.05, 'extra': 1, 'cortes_k': 1.0},
    'maximo': {'rondas': 4, 'rescate': 0.5, 'margen': 0.12, 'extra': 2, 'cortes_k': 0.6},
}
NOMBRE = {'rapido': 'Rápido', 'profundo': 'Profundo', 'maximo': 'Máximo'}
CUBRE_S = 0.25                         # un sonido «cubre» lo que se ve si su ancla cae a menos de esto
HUECO_CAPTION_S = 1.2                  # un caption rescatado necesita este aire con el sonido más cercano
RAFAGA_S, RAFAGA_N = 1.5, 3            # más de RAFAGA_N sonidos cortos en RAFAGA_S se amontonan
LARGOS = ('riser', 'acento')           # (un riser o una nota larga conviven con un golpe: no chocan)


def profundidad(controles=None):
    """La profundidad pedida en la página ('razonamiento'); Auto = profunda."""
    p = (controles or {}).get('razonamiento')
    return p if p in PROFUNDIDAD else 'profundo'


def _fijo(e):
    return bool(e.get('bloqueado') or e.get('ajustado')) or e.get('origen') in ('gancho', 'cierre')


def _suenan(eventos):
    return [e for e in eventos if e.get('decision') == 'GENERATE']


def _anclas(eventos, externos):
    return sorted([float(e['ancla']) for e in _suenan(eventos)] + [float(x['ancla']) for x in externos])


def _tope(car, p):
    return int(round(2 + 4 * float(car.get('densidad', 0.3)))) + PROFUNDIDAD[p]['extra']


def _sitio(eventos, externos, t, tope):
    k0 = 10.0 * int(max(0.0, t) // 10.0)
    return sum(1 for a in _anclas(eventos, externos) if k0 <= a < k0 + 10.0) < tope


def _nuevo(eventos, car, ctx, tipo, t, ancla, d, motivo, imp, origen, ref=None, **params):
    """Un evento con las MISMAS reglas que disenar (semilla, peso, nivel bajo la voz)."""
    params.setdefault('brillo', car['brillo'])
    params['semilla'] = D3._semilla('revision', tipo, round(ancla, 3), ref, ctx.get('video'))
    if 'peso' in params:
        params['peso'] = round(float(np.clip(params['peso'] * car['peso_k'], 0.2, 1.0)), 3)
    sobre = D3._en_voz(ctx.get('palabras') or [], ancla)
    rel = EV.NIVEL_REL_VOZ[tipo] + car['nivel_extra_db'] - (car['sobre_voz_db'] if tipo not in ('golpe', 'riser') and sobre else 0.0)
    e = {'id': f'{tipo}-r{len(eventos) + 1:02d}', 'tipo': tipo, 't': round(max(0.0, t), 3), 'ancla': round(ancla, 3), 'dur': round(d, 3),
         'pista': EV.PISTA[tipo], 'nivel_rel_voz_db': round(rel, 1), 'params': params, 'decision': 'GENERATE', 'por_que': motivo,
         'importancia': round(float(imp), 2), 'origen': origen, 'ref': ref, 'revision': 'rescatado'}
    e['clave'] = D3.clave(e)
    eventos.append(e)
    return e


def _sonido_de_caption(eventos, car, ctx, info, fps):
    """El sonido de un caption que se quedó justo bajo el umbral: el mismo momento que le daría disenar, pero ligero (pop, o el tic / trazo de un
    tema sobrio): es una palabra de menos peso y un golpe en ella pisaría a los acentos de verdad."""
    bloques = ctx.get('bloques') or []
    cue = info.get('cue')
    if not isinstance(cue, int) or cue >= len(bloques) or not isinstance(bloques[cue], dict):
        return None
    m = D3._momento_caption(bloques[cue], car, fps)
    if m is None:
        return None
    a = float(m['ancla'])
    tipo = 'pop' if m['tipo'] in ('golpe', 'whoosh') or m['tipo'] not in EV.NIVEL_REL_VOZ else m['tipo']   # lo rescatado ACOMPAÑA: nunca un golpe
    motivo = f"«{m['texto']}»: se veía sin sonido; la revisión lo acompaña ({info.get('rol', '').lower()}, score {info.get('caption_sound_score')})"
    imp = float(info.get('caption_sound_score') or 0.5)
    if tipo == 'golpe':
        return _nuevo(eventos, car, ctx, 'golpe', a - 0.09, a, 0.6, motivo, imp, 'caption', cue, peso=0.4, cola=0.35 + 0.3 * car['reverb'], pre=0.09)
    if tipo == 'whoosh':
        return _nuevo(eventos, car, ctx, 'whoosh', a - 0.165, a, 0.42, motivo, imp, 'caption', cue, direccion=0.6, easing='easeOutCubic', peso=0.35)
    if tipo == 'trazo':
        return _nuevo(eventos, car, ctx, 'trazo', a - 0.02, a, 0.32, motivo, imp, 'caption', cue, potencia=2.0, brillo=min(car['brillo'], 0.45))
    return _nuevo(eventos, car, ctx, tipo, a, a, 0.25 if tipo == 'tick' else 0.3, motivo, imp, 'caption', cue)


def _rescatar(d, car, ctx, p, externos, fps, notas):
    """Lo importante sin sonido y sin motivo de peso vuelve, si cabe en su ventana y no pisa a nadie."""
    cfg, tope, cambios = PROFUNDIDAD[p], _tope(car, p), 0
    eventos = d['eventos']
    for e in sorted((e for e in eventos if e.get('decision') == 'REMOVE' and not _fijo(e)), key=lambda e: -float(e.get('importancia') or 0)):
        a = float(e['ancla'])
        if float(e.get('importancia') or 0) < cfg['rescate'] or not _sitio(eventos, externos, a, tope):
            continue
        if e.get('tipo') not in LARGOS and any(abs(a - x) < D3.CHOQUE_S for x in _anclas(eventos, externos)):
            continue
        e['decision'] = 'GENERATE'
        e['revision'] = 'rescatado'
        e['por_que'] = str(e.get('por_que') or '') + ' — RESCATADO por la revisión: importa y ya cabe en su ventana'
        cambios += 1
        notas.append(f"{a:.1f} s: rescaté «{e.get('tipo')}» ({e.get('origen')})")
        for info in d.get('captions') or []:             # su caption vuelve a sonar (y lo que le acompañaba)
            if e.get('origen') in ('caption', 'dato') and info.get('cue') == e.get('ref') and info.get('decision') == 'LEAVE_SILENT':
                info['decision'] = 'GENERATE'
                info['por_que'] = str(info.get('por_que') or '') + ' → la revisión le devolvió su acento'
    umbral = float((d.get('resumen') or {}).get('umbral') or 0.6) - cfg['margen']
    for info in d.get('captions') or []:
        if info.get('decision') != 'LEAVE_SILENT' or cfg['margen'] <= 0:
            continue
        s, t = float(info.get('caption_sound_score') or 0.0), float(info.get('t') or 0.0)
        porque = str(info.get('por_que') or '')
        if s < umbral or 'intro' in porque or 'SILENCIADO' in porque or not _sitio(eventos, externos, t, tope):
            continue
        if any(abs(t - x) < HUECO_CAPTION_S for x in _anclas(eventos, externos)):
            continue
        if any(e.get('ref') == info.get('cue') and e.get('origen') in ('caption', 'dato') and _fijo(e) for e in eventos):
            continue                                                   # (el usuario lo silenció)
        if _sonido_de_caption(eventos, car, ctx, info, fps) is None:
            continue
        info['decision'] = 'GENERATE'
        info['por_que'] = porque + f' → la revisión ({NOMBRE[p].lower()}) le dio sonido: score {s:.2f} a {umbral + cfg["margen"] - s:.2f} del umbral'
        cambios += 1
        notas.append(f"{t:.1f} s: «{info.get('texto')}» tenía score {s:.2f} y estaba solo: ahora suena")
    if car.get('cortes_whoosh') and cfg['cortes_k'] < 1.0:          # (máximo) cortes de escena que respiran, más juntos
        cada = float(car.get('cortes_cada_s') or 8.0) * cfg['cortes_k']
        for tc in sorted(float(x) for x in ctx.get('cortes') or []):
            anclas = _anclas(eventos, externos)
            if tc < 1.0 or any(abs(tc - x) < 0.6 for x in anclas) or not _sitio(eventos, externos, tc, tope):
                continue
            if any(e['tipo'] == 'whoosh' and abs(tc - float(e['ancla'])) < cada for e in _suenan(eventos)):
                continue
            _nuevo(eventos, car, ctx, 'whoosh', tc - 0.42 * 0.55, tc, 0.54, f'corte de escena a {tc:.2f} s: la revisión máxima le da su aire', 0.5, 'corte',
                   direccion=0.8 if len(eventos) % 2 else -0.8, easing='easeInOutCubic', peso=0.4)
            cambios += 1
            notas.append(f'{tc:.1f} s: corte sin aire → whoosh')
    return cambios


def _quitar(e, motivo):
    e['decision'] = 'REMOVE'
    e['revision'] = 'corregido'
    e['por_que'] = str(e.get('por_que') or '') + f' — REVISIÓN: {motivo}'


def _coherencia(d, car, p, externos, notas):
    """Choques, ráfagas y densidad, con lo de fuera contado. Quita siempre el que menos pesa (nunca lo fijo)."""
    eventos, cambios = d['eventos'], 0
    cortos = sorted((e for e in _suenan(eventos) if e.get('tipo') not in LARGOS), key=lambda e: float(e['ancla']))
    for i, e in enumerate(cortos):                                    # choques entre los del director
        if e.get('decision') != 'GENERATE':
            continue
        for o in cortos[i + 1:]:
            if float(o['ancla']) - float(e['ancla']) >= D3.CHOQUE_S:
                break
            if o.get('decision') != 'GENERATE':
                continue
            debil = min((e, o), key=lambda x: (_fijo(x), float(x.get('importancia') or 0)))
            if _fijo(debil):
                continue
            _quitar(debil, f"chocaba a {abs(float(o['ancla']) - float(e['ancla'])) * 1000:.0f} ms con otro sonido")
            cambios += 1
            notas.append(f"{float(debil['ancla']):.1f} s: dos sonidos a la vez → queda uno")
            if debil is e:
                break
    for x in externos:                                                # contra lo que ya suena fuera (la PRO, pegado a su animación)
        for e in _suenan(eventos):
            if e.get('tipo') not in LARGOS and not _fijo(e) and x.get('tipo') not in LARGOS and abs(float(e['ancla']) - float(x['ancla'])) < D3.CHOQUE_S:
                _quitar(e, 'la PRO ya suena aquí con su animación')
                cambios += 1
                notas.append(f"{float(e['ancla']):.1f} s: la PRO ya sonaba → quito el mío")
    cortos = sorted((e for e in _suenan(eventos) if e.get('tipo') not in LARGOS), key=lambda e: float(e['ancla']))
    for i in range(len(cortos)):                                      # ráfagas
        grupo = [e for e in cortos[i:] if e.get('decision') == 'GENERATE' and float(e['ancla']) - float(cortos[i]['ancla']) < RAFAGA_S]
        while len(grupo) > RAFAGA_N:
            libres = [e for e in grupo if not _fijo(e)]
            if not libres:
                break
            debil = min(libres, key=lambda e: float(e.get('importancia') or 0))
            _quitar(debil, f'más de {RAFAGA_N} sonidos en {RAFAGA_S} s se amontonan')
            grupo.remove(debil)
            cambios += 1
            notas.append(f"{float(debil['ancla']):.1f} s: ráfaga → uno menos")
    tope = _tope(car, p)
    fin = max([float(e['ancla']) for e in eventos] + [float(x['ancla']) for x in externos] + [0.0])
    for k0 in np.arange(0.0, fin + 10.0, 10.0):                      # densidad por ventana de 10 s
        dentro = [e for e in _suenan(eventos) if k0 <= float(e['ancla']) < k0 + 10.0]
        fuera = sum(1 for x in externos if k0 <= float(x['ancla']) < k0 + 10.0)
        sobran = len(dentro) + fuera - tope
        for e in sorted((e for e in dentro if not _fijo(e)), key=lambda e: float(e.get('importancia') or 0))[:max(0, sobran)]:
            _quitar(e, f'más de {tope} sonidos en {int(k0)}–{int(k0) + 10} s')
            cambios += 1
            notas.append(f"{float(e['ancla']):.1f} s: ventana llena → fuera")
    return cambios


def _inventario(d, ctx, externos):
    """Cada cosa que se ve y qué le pasa: 'suena' | 'silencio' (decidido, con motivo) | 'rescatado' | 'corregido'. → (marcas, cuentas)."""
    anclas = _anclas(d['eventos'], externos)
    rescatados = [float(e['ancla']) for e in _suenan(d['eventos']) if e.get('revision') == 'rescatado']

    def cubierto(t):
        return any(abs(t - a) < CUBRE_S for a in anclas)

    marcas = []
    for info in d.get('captions') or []:
        t = float(info.get('t') or 0.0)
        if any(abs(t - a) < HUECO_CAPTION_S for a in rescatados) and info.get('decision') != 'LEAVE_SILENT':
            marcas.append((round(t, 2), 'rescatado', f"«{info.get('texto') or ''}»"))
        else:
            marcas.append((round(t, 2), 'suena' if info.get('decision') != 'LEAVE_SILENT' else 'silencio', f"«{info.get('texto') or ''}»"))
    for m in d.get('motions') or []:
        t = float(m.get('t') or 0.0)
        marcas.append((round(t, 2), 'suena' if cubierto(t) else 'silencio', str(m.get('que') or 'motion')))
    for tc in ctx.get('cortes') or []:
        tc = float(tc)
        marcas.append((round(tc, 2), 'suena' if any(abs(tc - a) < 0.6 for a in anclas) else 'silencio', 'corte'))
    for x in externos:
        marcas.append((round(float(x['ancla']), 2), 'suena', 'PRO'))
    for e in d['eventos']:
        if e.get('revision') == 'corregido':
            marcas.append((round(float(e['ancla']), 2), 'corregido', str(e.get('tipo'))))
        elif e.get('revision') == 'rescatado' and e.get('decision') == 'GENERATE' and e.get('origen') not in ('caption',):
            marcas.append((round(float(e['ancla']), 2), 'rescatado', str(e.get('tipo'))))
    marcas.sort()
    cuentas = {k: sum(1 for m in marcas if m[1] == k) for k in ('suena', 'silencio', 'rescatado', 'corregido')}
    return marcas, cuentas


def revisar(diseno, ctx, analisis=None, p='profundo', externos=None, fps=30.0, fase='diseno'):
    """La revisión completa sobre una COPIA del diseño. Devuelve (diseño revisado, informe). `externos`: [{'ancla', 'tipo'}] que ya suenan fuera
    (los sonidos de la PRO rehechos) y no se tocan. Nunca lanza: si algo falla, el diseño de entrada y un informe vacío."""
    p = p if p in PROFUNDIDAD else 'profundo'
    externos = [x for x in (externos or []) if isinstance(x, dict) and x.get('ancla') is not None]
    try:
        d = copy.deepcopy(diseno)
        car = d.get('caracter') or D3.caracter(analisis or {})
        notas, rondas, rescatados, corregidos = [], 0, 0, 0
        for _ in range(PROFUNDIDAD[p]['rondas']):
            rondas += 1
            r = _rescatar(d, car, ctx or {}, p, externos, fps, notas)
            c = _coherencia(d, car, p, externos, notas)
            rescatados, corregidos = rescatados + r, corregidos + c
            if not (r or c):
                break
        for info in d.get('captions') or []:                         # un caption sin ninguno de sus acentos sonando, en silencio (y dicho)
            suyos = [e for e in d['eventos'] if e.get('ref') == info.get('cue') and e.get('origen') == 'caption']
            if info.get('decision') != 'LEAVE_SILENT' and suyos and not any(e.get('decision') == 'GENERATE' for e in suyos):
                info['decision'] = 'LEAVE_SILENT'
                info['por_que'] = str(info.get('por_que') or '') + ' → la revisión lo dejó en silencio: no cabía sin amontonar'
        d['eventos'].sort(key=lambda e: float(e['t']))
        for e in d['eventos']:
            e.setdefault('clave', D3.clave(e))
        marcas, cuentas = _inventario(d, ctx or {}, externos)
        activos = _suenan(d['eventos'])
        res = dict(d.get('resumen') or {})
        res.update({'eventos': len(activos), 'con_sonido': sum(1 for c in d.get('captions') or [] if c.get('decision') != 'LEAVE_SILENT'),
                    'en_silencio': sum(1 for c in d.get('captions') or [] if c.get('decision') == 'LEAVE_SILENT'),
                    'por_tipo': {t: sum(1 for e in activos if e['tipo'] == t) for t in sorted({e['tipo'] for e in activos})}})
        d['resumen'] = res
        informe = {'fase': fase, 'profundidad': p, 'rondas': rondas, 'rescatados': rescatados, 'corregidos': corregidos, 'cambios': rescatados + corregidos,
                   'visuales': len(marcas), 'cuentas': cuentas, 'externos': len(externos), 'notas': notas[:40], 'marcas': marcas}
        d['revision'] = informe
        return d, informe
    except Exception:
        try:
            import director_sonido
            director_sonido.fallback('revisión')
        except Exception:
            pass
        return diseno, {'fase': fase, 'profundidad': p, 'rondas': 0, 'rescatados': 0, 'corregidos': 0, 'cambios': 0, 'visuales': 0, 'cuentas': {},
                        'externos': 0, 'notas': [], 'marcas': []}


def frase(informe):
    """Una línea para la página: qué miró y qué hizo."""
    if not informe or not informe.get('visuales'):
        return ''
    c = informe.get('cuentas') or {}
    partes = [f"{informe['visuales']} cosas en pantalla", f"{c.get('suena', 0) + c.get('rescatado', 0)} con sonido",
              f"{c.get('silencio', 0)} en silencio a propósito"]
    if informe.get('rescatados'):
        partes.append(f"{informe['rescatados']} rescatados")
    if informe.get('corregidos'):
        partes.append(f"{informe['corregidos']} corregidos")
    fase = 'con todo ya colocado' if informe.get('fase') == 'final' else 'del diseño'
    return f"Revisión {fase} · {NOMBRE.get(informe.get('profundidad'), '')} · {informe.get('rondas', 0)} rondas: " + ' · '.join(partes)
