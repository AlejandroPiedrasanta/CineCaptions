# CineCaptions · By Cinema Productions
# 1_codigo/herramientas_dev/probar_revision_sonido.py — prueba la REVISIÓN del AI Sound Director (director_sonido_revision) sin video ni Resolve.
"""
    python probar_revision_sonido.py

Diseños sintéticos (solo datos): rescate por densidad y de captions bajo el umbral según el razonamiento, silencios del usuario intocables,
choques, ráfagas, lo que ya suena en la PRO (externos), cortes en Máximo, estabilidad (una 2.ª revisión no cambia nada), que nunca lanza,
y que «Exígele más» entiende el razonamiento. Estilo «Social (CapCut)» (v5.39): el kit (un pop y un swipe, sin golpe ni swipe al entrar la
frase), el aterrizaje de cada cosa que entra (Resolve y MP4), su tono y su nivel, la revisión con el mismo kit, y director_sonido_sfx.fabricar
(identidad del kit, ataque en el ancla, al fotograma, determinista, «Otro sonido» para todo el video) + los archivos limpios y los vetos del
Quality Gate. Todo en una carpeta temporal (nada en ~/DaVinciSubtitles ni en las preferencias del usuario).
"""
import copy
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TMP = Path(tempfile.mkdtemp(prefix='cc_revision_sonido_'))
import director_sonido_estado as E
E.CARPETA = TMP / 'sound_director'                                   # (cachés del Quality Gate y «Mis sonidos»: aquí, no en las del usuario)
try:
    import ajustes_ui
    ajustes_ui.guardar_prefs = lambda *a, **k: None                   # (nunca las preferencias reales)
except Exception:
    pass
try:
    import registro
    registro.anotar = registro.excepcion = lambda *a, **k: None      # («nunca lanza» provoca un fallback a propósito: no va al Registro real)
except Exception:
    pass

import numpy as np

import director_sonido_diseno as D3
import director_sonido_eventos as EV
import director_sonido_fuentes as F
import director_sonido_medir as M
import director_sonido_revision as REV
import director_sonido_sfx as SFX

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

# 5b. estilo «Social (CapCut)»: todo lo que entra suena con el MISMO pop del kit, al aterrizar; swipe solo en los cortes; nunca un golpe
A_SOCIAL = dict(ANALISIS, narrativa={'frases': []}, voz={'duracion': 20.0})


def bloque(t, inicio=None):
    return {'start': t if inicio is None else inicio, 'runs': [{'rol': 'main', 't': t, 'zoom': 1.2, 'texto': f'P{t}'}]}


def suena(d):
    return [(round(e['ancla'], 2), e['tipo'], e['params'].get('social')) for e in sorted(d['eventos'], key=lambda e: e['ancla']) if e['decision'] == 'GENERATE']


cs = {'video': 'prueba.mp4', 'palabras': [], 'bloques': [bloque(0.5), bloque(1.5), bloque(1.6), bloque(3.0, 2.6), bloque(10.0)], 'cortes': [5.0]}
ds = D3.disenar(A_SOCIAL, cs, 30.0, controles={'estilo': 'social'})
suenan = suena(ds)
comprobar('social: acento del kit al abrir, pop en cada palabra y al entrar la frase, swipe solo en el corte (en su fotograma)',
          suenan == [(0.57, 'pop', 'acento'), (1.57, 'pop', 'heroe'), (2.67, 'pop', 'texto'), (3.07, 'pop', 'heroe'), (5.0, 'whoosh', 'corte'),
                     (10.07, 'pop', 'heroe')], str(suenan))
comprobar('social: nada a menos de 0,22 s del anterior (la palabra de 1,6 s calla)', ds['captions'][2]['decision'] == 'LEAVE_SILENT')
fu = ds['captions'][2].get('fusionados') or []
comprobar('social: lo que se funde queda dicho en su caption (con quién va)', len(fu) == 1 and fu[0]['texto'] == 'P1.6' and fu[0]['con'] == 'P1.5'
          and '«P1.6» → con el pop de «P1.5»' in ds['captions'][2]['por_que'], str(ds['captions'][2]))


def separados(d):
    """La distancia más corta entre dos sonidos (de inicio a inicio o de ancla a ancla, como _cerca_social)."""
    a = sorted((e for e in d['eventos'] if e['decision'] == 'GENERATE'), key=lambda e: e['t'])
    return min([min(abs(x['t'] - y['t']), abs(x['ancla'] - y['ancla'])) for i, x in enumerate(a) for y in a[i + 1:]] or [99.0])


cc = {'video': 'prueba.mp4', 'palabras': [], 'bloques': [bloque(1.0), bloque(4.0), bloque(6.0)], 'cortes': [4.2, 5.9, 8.0]}
dc = D3.disenar(A_SOCIAL, cc, 30.0, controles={'estilo': 'social'})
sc = suena(dc)
comprobar('social: un corte a 0,13–0,17 s de un pop calla (nada a menos de 0,22 s, tampoco el swipe); el corte libre suena',
          sc == [(1.07, 'pop', 'acento'), (4.07, 'pop', 'heroe'), (6.07, 'pop', 'heroe'), (8.0, 'whoosh', 'corte')] and separados(dc) >= 0.22, str(sc))
rc, _ = REV.revisar(dc, cc, A_SOCIAL, 'maximo')
comprobar('social: la revisión tampoco deja dos sonidos a menos de 0,22 s', separados(rc) >= 0.22 and suena(rc) == sc, str(suena(rc)))
activos = [e for e in ds['eventos'] if e['decision'] == 'GENERATE']
comprobar('social: ni golpe, ni riser, ni nota; el swipe solo en cortes', not any(e['tipo'] in ('golpe', 'riser', 'acento') for e in ds['eventos'])
          and all(e['origen'] == 'corte' for e in activos if e['tipo'] == 'whoosh'))
comprobar('social: todo del kit, limpio, centrado y sin azar de tono', all(e['params'].get('kit') in ('pop', 'whoosh') and e['params'].get('sin_capa')
                                                                       and e['params'].get('direccion') == 0.0 for e in activos))
comprobar('social: el nivel de cada uno es el de su tamaño (sin apartarse distinto sobre la voz)',
          all(e['nivel_rel_voz_db'] == EV.SOCIAL_NIVEL[e['params']['social']] for e in activos), str([(e['id'], e['nivel_rel_voz_db']) for e in activos]))
comprobar('social: el anclaje cae en la rejilla de fotogramas', all(abs(e['ancla'] * 30 - round(e['ancla'] * 30)) < 0.02 for e in activos))
r, inf = REV.revisar(ds, cs, A_SOCIAL, 'profundo')
comprobar('social: la revisión no le quita el ritmo ni mete golpes', suena(r) == suenan and not any(e['tipo'] == 'golpe' for e in r['eventos']), str(inf['notas']))

# el Tema 1 (clips 'k …'): cada cosa que entra con su tono; el anillo pegado a su héroe calla; MP4 y Resolve aterrizan con su propia curva
k1 = {'start': 0.2, 'runs': [{'k': 'k hero lima', 't': 0.2, 'texto': 'ABRE', 'size': 0.38}]}
k2 = {'start': 1.0, 'runs': [{'k': 'k label', 't': 1.0, 'texto': 'SI', 'size': 0.056}, {'k': 'k hero blanco', 't': 1.5, 'texto': 'MUNDO', 'size': 0.4},
                             {'k': 'k ring trazo lima', 't': 1.6}, {'k': 'k tape magenta', 't': 2.1, 'texto': 'YA', 'size': 0.19},
                             {'k': 'k sup', 't': 2.6, 'texto': '90', 'size': 0.096}, {'k': 'k line trazo lima', 't': 3.4}]}
ck = {'video': 'prueba.mp4', 'palabras': [], 'bloques': [k1, k2], 'cortes': []}
dk = D3.disenar(A_SOCIAL, ck, 30.0, controles={'estilo': 'social'})
sk = [(round(e['ancla'], 3), e['params']['social'], e['params']['semitonos']) for e in sorted(dk['eventos'], key=lambda e: e['ancla']) if e['decision'] == 'GENERATE']
comprobar('Tema 1 en Resolve: héroe + 2 f, etiqueta + 1 f, cinta + 2 f, el anillo junto al héroe calla, el subrayado tardío suena; tonos del kit',
          sk == [(0.267, 'acento', -2), (1.033, 'etiqueta', 4), (1.567, 'heroe', 0), (2.167, 'cinta', -3), (2.633, 'texto', 2), (3.433, 'trazo', 2)], str(sk))
acento = next(e for e in dk['eventos'] if e['params'].get('social') == 'acento')
comprobar('el gancho: el acento del kit (pop +3 dB con su octava baja), nunca un golpe',
          acento['tipo'] == 'pop' and acento['params'].get('capa_kit') == [-12, -8.0] and acento['nivel_rel_voz_db'] == EV.SOCIAL_NIVEL['heroe'] + 3.0)
dm = D3.disenar(A_SOCIAL, dict(ck, render='mp4'), 30.0, controles={'estilo': 'social'})
sm = [(round(e['ancla'], 3), e['params']['social']) for e in sorted(dm['eventos'], key=lambda e: e['ancla']) if e['decision'] == 'GENERATE']
comprobar('MP4 sin Resolve: el primer fotograma con ≥ 50 % del fundido (ceil((t + 0,06)·fps))',
          sm == [(0.267, 'acento'), (1.067, 'etiqueta'), (1.567, 'heroe'), (2.167, 'cinta'), (2.667, 'texto'), (3.433, 'trazo')], str(sm))
try:
    import render_temas
    comprobar('MP4_ENTRADA_S = el fundido de render_temas', D3.MP4_ENTRADA_S == render_temas.ENTRADA_S)
except ImportError:
    pass

# la revisión rescata con el kit (nunca un golpe ni un archivo de la biblioteca)
solo = D3.disenar(A_SOCIAL, dict(cs, bloques=[bloque(10.0)], cortes=[]), 30.0, controles={'estilo': 'social'})
solo['eventos'] = []
solo['captions'][0].update(decision='LEAVE_SILENT', por_que='prueba')
r, inf = REV.revisar(solo, dict(cs, bloques=[bloque(10.0)], cortes=[]), A_SOCIAL, 'profundo')
nuevo = [e for e in r['eventos'] if e['decision'] == 'GENERATE']
comprobar('social: lo rescatado es el pop del kit en su aterrizaje', len(nuevo) == 1 and nuevo[0]['tipo'] == 'pop' and nuevo[0]['params'].get('kit') == 'pop'
          and abs(nuevo[0]['ancla'] - 302 / 30) < 1e-3 and nuevo[0]['nivel_rel_voz_db'] == EV.SOCIAL_NIVEL['heroe'], str(nuevo))

# director_sonido_sfx.fabricar con el kit: una fuente por tipo, ataque en el ancla, al fotograma, nivel exacto, determinista
NV = -18.0


def wavs(hecho):
    return [np.concatenate(list(M.leer_wav(x['archivo'])), axis=1).astype(np.float64) for x in hecho['eventos']]


h1 = SFX.fabricar(dk, TMP / 'sfx1', NV, fps=30.0)
h2 = SFX.fabricar(dk, TMP / 'sfx2', NV, fps=30.0)
ok_kit = all(p.get('fuente') == 'kit social' for p in h1['puestos'])
fuentes = {(p['kit']['tipo'], p['kit']['sha1']) for p in h1['puestos'] if p.get('kit')}
comprobar('kit: todos los pops salen del MISMO sonido preparado (burbuja.wav)', ok_kit and len(fuentes) == 1 and h1['kit']['pop']['archivo'] == 'burbuja.wav',
          str(h1.get('kit')))
ys = wavs(h1)
err = []
for x, p, y in zip(h1['eventos'], h1['puestos'], ys):
    e = next(e for e in dk['eventos'] if e['id'] == p['id'])
    err.append(abs(x['ini'] + F.indice_ataque(y) / 48000.0 - e['ancla']))
comprobar('kit: el ataque (−20 dB) cae en el ancla (< 1 ms) y cada WAV empieza en un fotograma exacto',
          max(err) < 0.001 and all(abs(x['ini'] * 30 - round(x['ini'] * 30)) < 1e-3 for x in h1['eventos']), str(err))
niv = {p['kit']['social']: round(SFX._nivel_k100(y) - NV, 2) for p, y in zip(h1['puestos'], ys)}
SN = EV.SOCIAL_NIVEL
comprobar('kit: nivel K100 (BS.1770, 100 ms) = el de su tamaño; héroe > cinta > texto > etiqueta, cada paso de 2 a 3 dB',
          all(abs(niv.get(k, 99) - SN[k]) <= 0.02 for k in ('heroe', 'cinta', 'texto', 'etiqueta')) and niv.get('acento', -99) > SN['acento'] - 0.01
          and all(2.0 <= SN[a] - SN[b] <= 3.0 for a, b in (('heroe', 'cinta'), ('cinta', 'texto'), ('texto', 'etiqueta'))), str(niv))
comprobar('kit: mono, limpio al empezar (≤ −35 dB) y al acabar (≤ −45 dB)', all(np.abs(y[0] - y[1]).max() < 1e-6 for y in ys) and all(
    20 * np.log10(np.abs(y.mean(0)[:96]).max() / np.abs(y).max() + 1e-12) <= -35 and 20 * np.log10(np.abs(y.mean(0)[-240:]).max() / np.abs(y).max() + 1e-12) <= -45
    for y in ys))
comprobar('kit: determinista (dos veces = los mismos bytes)', [hashlib.sha1(Path(x['archivo']).read_bytes()).hexdigest() for x in h1['eventos']]
          == [hashlib.sha1(Path(x['archivo']).read_bytes()).hexdigest() for x in h2['eventos']])
dsw = D3.disenar(A_SOCIAL, cs, 30.0, controles={'estilo': 'social'})
hs = SFX.fabricar(dsw, TMP / 'sfx3', NV)
sw = [(p, y) for p, y in zip(hs['puestos'], wavs(hs)) if (p.get('kit') or {}).get('tipo') == 'whoosh']
x_sw = next(x for x, p in zip(hs['eventos'], hs['puestos']) if p['id'] == sw[0][0]['id'])
comprobar('swipe: el del kit, su pico en el corte y ≥ 4 dB (K100) bajo el pop del héroe', len(sw) == 1
          and abs(x_sw['ini'] + SFX._pico_idx(sw[0][1]) / 48000 - 5.0) < 0.002 and SFX._nivel_k100(sw[0][1]) - NV <= EV.SOCIAL_NIVEL['heroe'] - 4.0 + 0.01,
          str(SFX._nivel_k100(sw[0][1]) - NV))


def wav_prueba(nombre, x):
    ruta = TMP / 'biblio' / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    w = M.EscritorWav(ruta, 2)
    w.escribir(np.vstack((x, x)).astype(np.float32))
    w.cerrar()
    return ruta


tt = np.arange(int(0.12 * 48000)) / 48000.0
pop_limpio = wav_prueba('pop_prueba.wav', np.concatenate((np.zeros(480), 0.6 * np.sin(2 * np.pi * 1100 * tt) * np.exp(-tt / 0.012), np.zeros(4800))))
golpe1 = 0.6 * np.sin(2 * np.pi * 1100 * tt) * np.exp(-tt / 0.006)
pop_flam = wav_prueba('pop_flam.wav', np.concatenate((np.zeros(480), golpe1[:2400], golpe1, np.zeros(4800))))
bloque_ruido = wav_prueba('whoosh_bloque.wav', 0.4 * np.random.default_rng(1).standard_normal(int(0.3 * 48000)) * np.linspace(1, 0.9, int(0.3 * 48000)))
ajustado = copy.deepcopy(dsw)
uno = next(e for e in ajustado['eventos'] if e['params'].get('social') == 'heroe' and e['decision'] == 'GENERATE')
uno['params']['evitar'] = [h1['kit']['pop']['ruta']]                  # «Otro sonido» en UN pop…
SFX._CANDIDATOS['ui'] = [pop_flam, pop_limpio]
hx = SFX.fabricar(ajustado, TMP / 'sfx4', NV)
SFX._CANDIDATOS.pop('ui', None)
elegidos = {(p.get('eleccion') or {}).get('elegido') for p in hx['puestos'] if (p.get('kit') or {}).get('tipo') == 'pop'}
comprobar('«Otro sonido» en un pop cambia el kit en TODO el video (al mejor que pasa el Quality Gate estricto)', elegidos == {'pop_prueba.wav'}, str(elegidos))
q_flam, q_bloque, q_limpio = F.calidad(pop_flam, 'ui'), F.calidad(bloque_ruido, 'whoosh'), F.calidad(pop_limpio, 'ui')
comprobar('Quality Gate: un flam y un bloque de ruido son VETO; el pop limpio pasa', q_flam['score'] == 0 and q_flam['vetos'] and q_bloque['score'] == 0
          and q_bloque['vetos'] and q_limpio['score'] >= F.UMBRAL, f"{q_flam['vetos']} · {q_bloque['vetos']} · {q_limpio['motivos']}")
sucio = wav_prueba('sucio_whoosh.wav', np.concatenate((np.full(9600, 0.05), 0.05 + 0.5 * np.random.default_rng(2).standard_normal(14400), np.full(9600, 0.05))))
y = F.leer_para_mezcla(sucio, 0.2, 0.04)
m = y.mean(0)
comprobar('leer_para_mezcla: sin DC ni silencio delante, entrada y salida limpias (todos los estilos)',
          np.argmax(np.abs(m) >= 0.01 * np.abs(m).max()) <= int(0.006 * 48000) and 20 * np.log10(np.abs(m[:96]).max() / np.abs(m).max()) <= -35
          and 20 * np.log10(np.abs(m[-240:]).max() / np.abs(m).max() + 1e-12) <= -45 and abs(float(m.mean())) < 0.01)

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

shutil.rmtree(TMP, ignore_errors=True)
fallos = [n for n, ok in RESULTADOS if not ok]
print(f'\n{len(RESULTADOS) - len(fallos)}/{len(RESULTADOS)} correctas' + (f' · fallan: {", ".join(fallos)}' if fallos else ''))
sys.exit(1 if fallos else 0)
