# CineCaptions · By Cinema Productions
# 1_codigo/herramientas_dev/probar_revision_sonido.py — prueba la REVISIÓN del AI Sound Director (director_sonido_revision) sin video ni Resolve.
"""
    python probar_revision_sonido.py

Diseños sintéticos (solo datos): rescate por densidad y de captions bajo el umbral según el razonamiento, silencios del usuario intocables,
choques, ráfagas, lo que ya suena en la PRO (externos), cortes en Máximo, estabilidad (una 2.ª revisión no cambia nada), que nunca lanza,
y que «Exígele más» entiende el razonamiento.
"""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import director_sonido_diseno as D3
import director_sonido_revision as REV

RESULTADOS = []


def comprobar(nombre, ok, detalle=''):
    RESULTADOS.append((nombre, bool(ok)))
    print(('OK   ' if ok else 'FALLA') + f' {nombre}' + (f' — {detalle}' if detalle and not ok else ''))


ANALISIS = {'paleta': {'valores': {'impacto': 0.7, 'ui': 0.4, 'densidad': 0.3, 'brillo': 0.5, 'reverb': 0.4, 'motion': 0.6, 'transitorios': 0.7}},
            'rasgos': {'estilo': 'guion', 'modo_pro': None}}
CAR = D3.caracter(ANALISIS)                                           # golpe · densidad 0,3 → tope 3 (+1 profundo, +2 máximo)


def ev(i, tipo, ancla, decision='GENERATE', imp=0.5, origen='motion', ref=None, **extra):
    e = {'id': f'{tipo}-{i:02d}', 'tipo': tipo, 't': round(ancla - 0.05, 3), 'ancla': ancla, 'dur': 0.3, 'pista': 'AI SFX MOTION', 'nivel_rel_voz_db': -15.0,
         'params': {'semilla': i}, 'decision': decision, 'por_que': 'prueba', 'importancia': imp, 'origen': origen, 'ref': ref}
    e.update(extra)
    e['clave'] = D3.clave(e)
    return e


def diseno(eventos, captions=None):
    return {'eventos': eventos, 'captions': captions or [], 'motions': [], 'viejos': [], 'caracter': CAR, 'resumen': {'umbral': 0.6}}


def ctx(bloques=None, cortes=None):
    return {'video': 'prueba.mp4', 'palabras': [], 'bloques': bloques or [], 'cortes': cortes or []}


def decision(d, id_):
    return next(e['decision'] for e in d['eventos'] if e['id'] == id_)


# 1. rescate por densidad: en 0–10 s suenan 3 (= tope) y uno importante quedó fuera
base = diseno([ev(1, 'tick', 1.0), ev(2, 'tick', 3.0), ev(3, 'tick', 5.0), ev(4, 'whoosh', 7.0, 'REMOVE', 0.7)])
r, inf = REV.revisar(base, ctx(), ANALISIS, 'rapido')
comprobar('rápido no rescata con la ventana llena', decision(r, 'whoosh-04') == 'REMOVE')
r, inf = REV.revisar(base, ctx(), ANALISIS, 'profundo')
comprobar('profundo rescata lo importante si cabe (+1 por ventana)', decision(r, 'whoosh-04') == 'GENERATE' and inf['rescatados'] == 1, str(inf))
comprobar('el diseño de entrada no se toca', decision(base, 'whoosh-04') == 'REMOVE')
bajo = diseno([ev(1, 'tick', 1.0), ev(2, 'tick', 3.0), ev(3, 'tick', 5.0), ev(4, 'whoosh', 7.0, 'REMOVE', 0.55)])
r, _ = REV.revisar(bajo, ctx(), ANALISIS, 'profundo')
comprobar('profundo no rescata lo de poca importancia (0,55 < 0,6)', decision(r, 'whoosh-04') == 'REMOVE')
r, _ = REV.revisar(bajo, ctx(), ANALISIS, 'maximo')
comprobar('máximo sí (0,55 ≥ 0,5)', decision(r, 'whoosh-04') == 'GENERATE')

# 2. caption justo bajo el umbral y solo: profundo le da un sonido ligero en el momento de disenar
bloques = [{'start': 4.0, 'runs': [{'rol': 'main', 't': 4.0, 'zoom': 1.3, 'texto': 'DINERO'}]}]
caps = [{'cue': 0, 't': 4.0, 'texto': 'DINERO', 'rol': 'DATA', 'caption_sound_score': 0.57, 'decision': 'LEAVE_SILENT', 'por_que': 'score 0.57 < 0.60'}]
r, inf = REV.revisar(diseno([ev(1, 'tick', 12.0)], caps), ctx(bloques), ANALISIS, 'profundo')
nuevo = [e for e in r['eventos'] if e.get('origen') == 'caption' and e.get('ref') == 0]
comprobar('caption bajo el umbral → suena, ligero (pop, no el golpe del tema)', len(nuevo) == 1 and CAR['acento'] == 'golpe' and nuevo[0]['tipo'] == 'pop'
          and abs(nuevo[0]['ancla'] - 4.05) < 1e-6 and r['captions'][0]['decision'] == 'GENERATE', str(nuevo))
comprobar('el nuevo evento sale con pista, nivel y clave', bool(nuevo and nuevo[0]['pista'] and nuevo[0]['clave'] and 'nivel_rel_voz_db' in nuevo[0]))
r, _ = REV.revisar(diseno([ev(1, 'tick', 12.0)], caps), ctx(bloques), ANALISIS, 'rapido')
comprobar('rápido no toca los captions en silencio', r['captions'][0]['decision'] == 'LEAVE_SILENT')
cerca = diseno([ev(1, 'tick', 4.6)], copy.deepcopy(caps))
r, _ = REV.revisar(cerca, ctx(bloques), ANALISIS, 'maximo')
comprobar('sin aire (otro sonido a < 1,2 s) no se rescata', r['captions'][0]['decision'] == 'LEAVE_SILENT')
silenciado = copy.deepcopy(caps)
silenciado[0]['por_que'] += ' — SILENCIADO por ti'
r, _ = REV.revisar(diseno([], silenciado), ctx(bloques), ANALISIS, 'maximo')
comprobar('lo que el usuario silenció no vuelve', r['captions'][0]['decision'] == 'LEAVE_SILENT')

# 3. coherencia: choques, lo fijo manda, ráfagas
r, inf = REV.revisar(diseno([ev(1, 'tick', 2.0, imp=0.4), ev(2, 'pop', 2.08, imp=0.6)]), ctx(), ANALISIS, 'profundo')
comprobar('choque: queda el que más pesa', decision(r, 'tick-01') == 'REMOVE' and decision(r, 'pop-02') == 'GENERATE', str(inf['notas']))
r, _ = REV.revisar(diseno([ev(1, 'tick', 2.0, imp=0.4, bloqueado=True), ev(2, 'pop', 2.08, imp=0.6)]), ctx(), ANALISIS, 'profundo')
comprobar('choque: lo bloqueado nunca se quita', decision(r, 'tick-01') == 'GENERATE' and decision(r, 'pop-02') == 'REMOVE')
r, _ = REV.revisar(diseno([ev(1, 'golpe', 2.0, imp=0.7), ev(2, 'riser', 2.02, imp=0.5)]), ctx(), ANALISIS, 'profundo')
comprobar('un riser que acaba en el golpe no choca', decision(r, 'riser-02') == 'GENERATE')
rafaga = diseno([ev(i, 'pop', 20.0 + 0.3 * i, imp=0.4 + 0.05 * i) for i in range(1, 6)])
r, _ = REV.revisar(rafaga, ctx(), ANALISIS, 'maximo')
comprobar('ráfaga: como mucho 3 en 1,5 s (quedan los que más pesan)', sum(1 for e in r['eventos'] if e['decision'] == 'GENERATE') == 3
          and decision(r, 'pop-01') == 'REMOVE')

# 4. lo que ya suena en la PRO (revisión final)
r, inf = REV.revisar(diseno([ev(1, 'tick', 5.0, imp=0.6), ev(2, 'tick', 8.0)]), ctx(), ANALISIS, 'profundo',
                     externos=[{'ancla': 5.05, 'tipo': 'whoosh'}], fase='final')
comprobar('la PRO ya suena ahí → quito el mío', decision(r, 'tick-01') == 'REMOVE' and inf['fase'] == 'final')
lleno = diseno([ev(1, 'tick', 1.0, imp=0.3), ev(2, 'tick', 3.0, imp=0.5), ev(3, 'tick', 5.0, imp=0.6)])
r, _ = REV.revisar(lleno, ctx(), ANALISIS, 'rapido', externos=[{'ancla': 7.0, 'tipo': 'whoosh'}, {'ancla': 8.5, 'tipo': 'whoosh'}])
comprobar('densidad contando la PRO: sale el más débil', decision(r, 'tick-01') == 'REMOVE' and decision(r, 'tick-03') == 'GENERATE')

# 5. máximo: cortes que respiran (tema enérgico)
r, inf = REV.revisar(diseno([ev(1, 'tick', 1.0)]), ctx(cortes=[12.0, 25.0]), ANALISIS, 'maximo')
comprobar('máximo da aire a los cortes sin sonido', sum(1 for e in r['eventos'] if e.get('origen') == 'corte') == 2, str(inf['notas']))
r, _ = REV.revisar(diseno([ev(1, 'tick', 1.0)]), ctx(cortes=[12.0, 25.0]), ANALISIS, 'profundo')
comprobar('profundo deja los cortes como los decidió el diseño', not any(e.get('origen') == 'corte' for e in r['eventos']))

# 5b. estilo «Social (CapCut)»: cada palabra que entra suena, limpia (sin capa sintética) y al aparecer
A_SOCIAL = dict(ANALISIS, narrativa={'frases': []}, voz={'duracion': 20.0})


def bloque(t, inicio=None):
    return {'start': t if inicio is None else inicio, 'runs': [{'rol': 'main', 't': t, 'zoom': 1.2, 'texto': f'P{t}'}]}


cs = {'video': 'prueba.mp4', 'palabras': [], 'bloques': [bloque(0.5), bloque(1.5), bloque(1.6), bloque(3.0, 2.6), bloque(10.0)], 'cortes': [5.0]}
ds = D3.disenar(A_SOCIAL, cs, 30.0, controles={'estilo': 'social'})
suenan = [(round(e['ancla'], 2), e['tipo']) for e in ds['eventos'] if e['decision'] == 'GENERATE']
comprobar('social: golpe solo al abrir, pop en cada palabra, swipe al entrar la frase y en el corte',
          suenan == [(0.52, 'golpe'), (1.52, 'pop'), (2.64, 'whoosh'), (3.02, 'pop'), (5.0, 'whoosh'), (10.02, 'pop')], str(suenan))
comprobar('social: nada a menos de 0,22 s del anterior (la palabra de 1,6 s calla)', ds['captions'][2]['decision'] == 'LEAVE_SILENT')
comprobar('social: todo limpio, sin la capa sintética', all(e['params'].get('sin_capa') for e in ds['eventos'] if e['decision'] == 'GENERATE'))
comprobar('social: sin riser de gancho ni nota de cierre', not any(e['tipo'] in ('riser', 'acento') for e in ds['eventos']))
r, inf = REV.revisar(ds, cs, A_SOCIAL, 'profundo')
comprobar('social: la revisión no le quita el ritmo', sum(1 for e in r['eventos'] if e['decision'] == 'GENERATE') == len(suenan), str(inf['notas']))

# 6. estable, informe y nunca lanza
d1, i1 = REV.revisar(base, ctx(), ANALISIS, 'maximo')
d2, i2 = REV.revisar(d1, ctx(), ANALISIS, 'maximo')
comprobar('una 2.ª revisión no cambia nada', i2['cambios'] == 0, str(i2['notas']))
comprobar('informe con marcas y frase', bool(i1['marcas']) and REV.frase(i1).startswith('Revisión'))
roto, informe = REV.revisar({'eventos': None}, None)
comprobar('nunca lanza: devuelve lo de entrada', roto == {'eventos': None} and informe['cambios'] == 0)
comprobar('razonamiento: Auto = profundo', REV.profundidad({}) == 'profundo' and REV.profundidad({'razonamiento': 'maximo'}) == 'maximo')

# 7. «Exígele más»
try:
    import director_sonido_sesion as S
    a = S.interpretar('piensa más y revisa todo')['acciones']
    comprobar('«piensa más y revisa todo» → razonamiento máximo', ('control', 'razonamiento', 'maximo') in a, str(a))
    a = S.interpretar('más sonidos')['acciones']
    comprobar('«más sonidos» sigue siendo densidad', a == [('control', 'densidad', 'mucho')], str(a))
    a = S.interpretar('quiero sonidos tipo CapCut')['acciones']
    comprobar('«tipo CapCut» → estilo social', ('control', 'estilo', 'social') in a, str(a))
except Exception as err:                                              # (sin las dependencias del motor)
    comprobar('interpretar', False, f'{type(err).__name__}: {err}')

fallos = [n for n, ok in RESULTADOS if not ok]
print(f'\n{len(RESULTADOS) - len(fallos)}/{len(RESULTADOS)} correctas' + (f' · fallan: {", ".join(fallos)}' if fallos else ''))
sys.exit(1 if fallos else 0)
