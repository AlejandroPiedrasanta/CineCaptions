# CineCaptions · By Cinema Productions
# 1_codigo/director_sonido_sfx.py — «AI Sound Director», FASE 3: cada sonido del diseño hecho a la medida, en su WAV y listo para su pista AI.
"""
fabricar(diseno, carpeta, nivel_voz_db, modo='hibrido') → {'eventos': [eventos 'sonido' con 'pista' para el plan de Efectos], 'puestos', 'segundos'}

MODO (elegido por el usuario al comparar las 4 demos del Tema 1, 2026-10-21): 'hibrido' = para golpes, whooshes, risers, acentos y tics, el mejor
archivo de la biblioteca curada que pase el Quality Gate y el ajuste semántico (director_sonido_fuentes) + una capa procedural ajustada a ESE motion
(sub y clic bajo el golpe, aire que sigue el easing y la dirección bajo el whoosh); si ningún archivo pasa, procedural a la medida
(director_sonido_sintesis). 'procedural' = solo síntesis. Nunca la biblioteca legacy de la app (DISABLED_FOR_NEW_DESIGN).

Cada sonido: alineado a su ANCLA (el pico del golpe y del whoosh cae en el fotograma que manda; en pops, tics y acentos, v5.39, su ATAQUE —la
primera muestra a −20 dB del pico, medida en el sonido ya terminado—; el riser acaba 30 ms antes), con su nivel RELATIVO a la voz horneado dentro
del archivo (Resolve ignora el volumen de clip por script), WAV 48 kHz 24 bits con nombre por contenido (el mismo diseño = el mismo archivo:
re-aplicar no rehace nada) en ~/DaVinciSubtitles/sound_director/<huella>/sfx/. Con `fps` (Resolve), cada WAV empieza en un fotograma exacto con el
silencio justo delante: el redondeo a fotogramas de colocar_efectos (hasta ±16,7 ms) ya no mueve el golpe.

KIT «SOCIAL» (v5.39, params['kit']): UN pop y UN swipe para todo el video (`KIT_SOCIAL`, en 2_recursos), preparados una vez (`_preparar_kit`: sin DC,
paso alto, mono, sin silencio delante, entrada de 3 ms, corte a −50 dB) y con el tono por tipo de elemento (`_tono`, FFT; caché). Sin biblioteca,
sin elegir, sin anti-repetición, sin capa, sin paneo y sin azar: lo de CapCut, el mismo pop en cada palabra. Nivel por `_nivel_k100` («K100»: el
máximo de 100 ms con la ponderación K de BS.1770, lo que se OYE de un sonido corto y lo que mide el sonómetro; el RMS activo lo leía hasta 10 dB mal
y el máximo de 50 ms sin ponderar, hasta 2 dB según el tono y el brillo) y el swipe siempre ≥ 4 dB (K100) bajo el pop del héroe.
«Otro sonido» en cualquier evento del kit cambia ese sonido en TODO el video (`_kits`: `evitar` / `firma` de todos los eventos de ese tipo).
"""
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SR = 48000
MODO = 'hibrido'
VERSION = 4                                     # súbela si cambia la síntesis o la mezcla de capas: los WAV viejos no se reutilizan (2: golpe por su pico final;
                                                # 3: kit Social, ataque en el ancla, relleno al fotograma, archivos limpios; 4: kit a su nivel K100)
CATEGORIA = {'golpe': 'golpe', 'whoosh': 'whoosh', 'giro': 'whoosh', 'riser': 'riser', 'trazo': 'trazo', 'acento': 'tonal', 'tick': 'ui', 'pop': 'ui'}
POR_ATAQUE = ('pop', 'tick', 'acento')          # se alinean por su ataque (−20 dB), no por un máximo de 2 ms que llega tras un pre-roll o un 2.º golpe
KIT_SOCIAL = {'pop': ('sfx_emoji', 'burbuja.wav'),                                    # CC0, farfadet46 (sfx_emoji/LICENCIAS.txt): un pop de verdad
              'whoosh': ('kit_social', 'swish_single_4_393811.wav'),                  # CC0, Freesound 393811 (kit_social/LICENCIAS.txt): solo en cortes
              'tick': ('sfx_library', 'Interfaz (CC0)', 'click_interface_tick_002.wav')}   # CC0, Kenney: clic de 20 ms (si se pide un tic)
KIT_RESPALDO = {'pop': 'pop_sfx_neutral_776016'}  # si faltara el del kit: este pop (CC0, Freesound) en «Mis sonidos», con su silencio recortado
KIT_PASO_ALTO = {'pop': 150.0, 'tick': 150.0, 'whoosh': 200.0}
KIT_ACENTO_S = 0.2                              # el acento del gancho / CTA (pop + su octava baja) como mucho dura esto
SWIPE_BAJO_HEROE_DB = 4.0                       # el swipe de un corte, al menos esto (K100) bajo el pop del héroe (en CapCut manda el pop)
# ponderación K de ITU-R BS.1770 a 48 kHz (estante de cabeza + paso alto RLB): (b, a) de cada biquad
_K_BIQUADS = (((1.53512485958697, -2.69169618940638, 1.19839281085285), (1.0, -1.69065929318241, 0.73248077421585)),
              ((1.0, -2.0, 1.0), (1.0, -1.99004745483398, 0.99007225036621)))
_CANDIDATOS = {}
_KIT = {}


def _ganancia(x, objetivo_db):
    import director_sonido_sintesis as S
    return x * (10 ** ((objetivo_db - S.rms_activo_db(x)) / 20.0))


def _nivel_k100(x):
    """«K100»: la sonoridad máxima en 100 ms (LUFS de BS.1770: ponderación K, potencias de los canales sumadas, −0,691). Lo que se OYE de un pop
    o un swipe y lo MISMO que mide el sonómetro: el RMS activo (_ganancia) daba hasta 10,5 dB de diferencia entre dos pops que suenan igual, y el
    máximo de 50 ms sin ponderar se desviaba según el tono y el brillo (el swipe salía 2 dB más fuerte de lo pedido)."""
    import director_sonido_fuentes as F
    x = np.atleast_2d(np.asarray(x, np.float64))
    n = x.shape[1]
    if not n:
        return -120.0
    N = 1 << int(math.ceil(math.log2(n + SR)))                       # (con 1 s de silencio detrás: filtrado lineal, no circular)
    z = np.exp(-2j * np.pi * np.fft.rfftfreq(N))
    h = np.ones_like(z)
    for b, a in _K_BIQUADS:
        h *= (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)
    y = np.fft.irfft(np.fft.rfft(x, N, axis=1) * h, N, axis=1)[:, :n]
    return float(10 * np.log10(max(float(F._movil((y ** 2).sum(axis=0), int(0.1 * SR)).max()), 1e-20)) - 0.691)


def _remuestrear(x, factor):
    """x (canales, n) `factor` veces más agudo (y más corto) por FFT: limitado en banda, sin el apagado de agudos de np.interp (−2,3 a −4,6 dB
    en 12–20 kHz). Con silencio de relleno para que la cola no se enrosque al principio."""
    n = x.shape[1]
    m = max(8, int(round(n / factor)))
    if m == n:
        return np.array(x, np.float32)
    N = n + max(256, n // 2)
    M = max(8, int(round(N / factor)))
    X = np.fft.rfft(np.asarray(x, np.float64), N, axis=1)
    Y = np.zeros((x.shape[0], M // 2 + 1), np.complex128)
    k = min(X.shape[1], Y.shape[1])
    Y[:, :k] = X[:, :k]
    return (np.fft.irfft(Y, M, axis=1) * (M / N))[:, :m].astype(np.float32)


def _tono(x, semitonos):
    return _remuestrear(x, 2.0 ** (float(semitonos) / 12.0)) if semitonos else np.array(x, np.float32)


def _pico_idx(x):
    m = np.abs(x).max(axis=0)
    env = np.convolve(m, np.ones(96) / 96, 'same')
    return int(np.argmax(env))


def _balance(x, pos):
    if not pos:
        return x
    a = (np.clip(pos, -1, 1) + 1) * np.pi / 4
    return np.vstack((x[0] * np.cos(a) * 1.414, x[1] * np.sin(a) * 1.414)).astype(np.float32)


def sintetizar(e, rng):
    """El sonido procedural de un evento: (audio (2, n), segundos desde el inicio del archivo hasta el ancla)."""
    import director_sonido_sintesis as S
    p, t = e['params'], e['tipo']
    if t == 'golpe':
        return S.golpe(p.get('peso', 0.7), p.get('brillo', 0.5), p.get('cola', 0.4), p.get('pre', 0.09), rng), p.get('pre', 0.0)
    if t == 'whoosh':
        x = S.whoosh(max(0.12, e['dur'] - 0.12), p.get('direccion', 0.0), p.get('easing', 'easeInOutCubic'), p.get('brillo', 0.5), p.get('peso', 0.4), rng)
        return x, e['ancla'] - e['t']
    if t == 'giro':
        return S.giro(max(0.1, e['dur'] - 0.05), p.get('brillo', 0.5), rng), e['ancla'] - e['t']
    if t == 'trazo':
        return S.trazo(max(0.1, e['dur'] - 0.05), p.get('potencia', 2.4), p.get('brillo', 0.5), rng), 0.0
    if t == 'riser':
        return S.riser(e['dur'], p.get('brillo', 0.5), rng=rng), e['dur']
    if t == 'acento':
        return S.acento(p.get('nota', 523.25), e['dur'], p.get('brillo', 0.5)), 0.0
    if t == 'tick':
        return S.tick(p.get('brillo', 0.5), rng), 0.0
    if t == 'pop':
        return S.pop(p.get('brillo', 0.5), rng), 0.0
    return None, 0.0


def _recurso(*partes):
    """Un archivo de 2_recursos desde la fuente o desde la app instalada (PyInstaller deja cada carpeta de recursos en _MEIPASS, sin «2_recursos»;
    un despliegue portable, junto al ejecutable): la primera ruta que exista, o None."""
    bases = []
    if getattr(sys, '_MEIPASS', None):
        bases += [Path(sys._MEIPASS), Path(sys._MEIPASS) / '2_recursos']
    if getattr(sys, 'frozen', False):
        bases += [Path(sys.executable).parent / '2_recursos', Path(sys.executable).parent.parent / '2_recursos']
    bases.append(Path(__file__).resolve().parent.parent / '2_recursos')
    return next((b.joinpath(*partes) for b in bases if b.joinpath(*partes).is_file()), None)


def _respaldo(nombre):
    """El pop de respaldo del kit en «Mis sonidos» (sound_director/biblioteca), si el usuario lo tiene."""
    try:
        import director_sonido_estado as E
        import director_sonido_fuentes as F
        d = E.CARPETA / 'biblioteca'
        return next((p for p in sorted(d.rglob(f'{nombre}*')) if p.suffix.lower() in F.EXT and p.is_file()), None) if d.is_dir() else None
    except Exception:
        return None


def _preparar_kit(x, tipo):
    """Un sonido del kit, preparado UNA vez: mono, sin DC, paso alto (150 Hz el pop, 200 Hz el swipe), desde 5 ms antes de su ataque a −40 dB con
    3 ms de entrada en coseno, cortado donde su RMS de 10 ms cae a −50 dB + 20 ms de fundido, y con su pico a 1 (el nivel se pone por evento)."""
    import director_sonido_fuentes as F
    m = np.asarray(x, np.float64).mean(axis=0)
    m = F.paso_alto(m - m.mean(), KIT_PASO_ALTO.get(tipo, 150.0))
    a = np.abs(m)
    if not a.size or a.max() <= 0:
        return None
    m = m[max(0, int(np.argmax(a >= 0.01 * a.max())) - int(0.005 * SR)):]
    e = 10 * np.log10(np.maximum(F._movil(m ** 2, 480), 0.0) + 1e-20)
    m = m[:min(m.size, int(np.nonzero(e >= e.max() - 50.0)[0][-1]) + int(0.02 * SR))].copy()
    k = min(m.size, int(0.003 * SR))
    m[:k] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))
    k = min(m.size // 3, int(0.02 * SR))
    if k:
        m[-k:] *= np.linspace(1, 0, k)
    m /= np.abs(m).max() or 1.0
    return np.vstack((m, m)).astype(np.float32)


def _kit_variante(ruta, tipo, semitonos=0):
    """El sonido del kit preparado y con su tono (caché en memoria: cada tono se hace una vez por sesión)."""
    try:
        st = Path(ruta).stat()
    except OSError:
        return None
    k = (str(ruta), st.st_size, st.st_mtime_ns, tipo, int(semitonos))     # (si el archivo cambia en disco, se vuelve a preparar)
    if k not in _KIT:
        if k[-1]:
            base = _kit_variante(ruta, tipo, 0)
            _KIT[k] = None if base is None else _tono(base, k[-1])
        else:
            import director_sonido_fuentes as F
            d = F._leer(ruta, max_s=4.0)
            _KIT[k] = _preparar_kit(d[0], tipo) if d is not None else None
    return _KIT[k]


def _kit_de(tipo, evitar=(), firma=None):
    """(ruta, por qué) del sonido del kit de ese tipo: el que eligió el usuario (`firma`), el del kit, el de respaldo o, si los descartó todos,
    el mejor de su biblioteca que pase el Quality Gate ESTRICTO (una vez, para todo el video). Sin ninguno: el del kit (mejor eso que uno roto)."""
    evitar = {str(r) for r in evitar or ()}
    kit = _recurso(*KIT_SOCIAL[tipo]) if tipo in KIT_SOCIAL else None
    opciones = ((lambda: Path(str(firma)) if firma and Path(str(firma)).is_file() else None, 'el que elegiste para todo el video'),
                (lambda: kit, 'el del kit Social'),
                (lambda: _respaldo(KIT_RESPALDO[tipo]) if tipo in KIT_RESPALDO else None, 'el de respaldo del kit (en Mis sonidos)'))
    vistos = []
    for dar, por_que in opciones:                                     # (el respaldo solo se busca si hace falta)
        ruta = dar()
        if ruta is not None and str(ruta) not in evitar:
            return ruta, por_que
        if ruta is not None:
            vistos.append(ruta)
    if evitar:
        import director_sonido_fuentes as F
        cat = CATEGORIA.get(tipo, 'ui')
        cands = [c for c in _candidatos(cat) if str(c) not in evitar]
        ruta, _ranking = F.elegir(cands, {'tipo': cat, 'dur': 0.21 if tipo == 'whoosh' else 0.15, 'brillo': 0.5, 'energia': 0.4, 'estricto': True})
        if ruta:
            return Path(ruta), 'otro de tu biblioteca (pasa el Quality Gate estricto), para todo el video'
    defecto = kit or (vistos[0] if vistos else None)
    return (defecto, 'no hay otro que pase el Quality Gate estricto: sigue el del kit') if defecto is not None else (None, '')


def _kits(eventos):
    """El kit de ESTE video, resuelto una vez por tipo (pop / whoosh / tick) con lo que pidió el usuario en CUALQUIERA de sus eventos: «Otro
    sonido» cambia el sonido del kit en todo el video, nunca en uno solo. {tipo: {'tipo', 'ruta', 'sha1' (del preparado), 'por_que'}}."""
    pedidos = {}
    for e in eventos:
        p = e.get('params') or {}
        if not p.get('kit'):
            continue
        d = pedidos.setdefault(p['kit'], {'evitar': set(), 'firma': None})
        d['evitar'] |= {str(r) for r in p.get('evitar') or []}
        d['firma'] = p.get('firma') or d['firma']
    kits = {}
    for tipo, d in pedidos.items():
        ruta, por_que = _kit_de(tipo, d['evitar'], d['firma'])
        base = _kit_variante(ruta, tipo, 0) if ruta is not None else None
        if base is not None:
            kits[tipo] = {'tipo': tipo, 'ruta': str(ruta), 'sha1': hashlib.sha1(base.tobytes()).hexdigest()[:12], 'por_que': por_que}
    return kits


def _sonido_kit(kit, e, objetivo):
    """El sonido de un evento del kit a su nivel (`_nivel_k100` = objetivo): el kit con el tono de ese tipo de elemento y, en el acento del gancho /
    CTA (params['capa_kit'] = [semitonos, dB]), el mismo pop una octava abajo debajo, alineados por su ataque; como mucho KIT_ACENTO_S. (audio, elección)."""
    import director_sonido_fuentes as F
    p = e['params']
    st = int(p.get('semitonos') or 0)
    x = _kit_variante(kit['ruta'], kit['tipo'], st)
    if x is None:
        return None, None
    x = x * (10 ** ((objetivo - _nivel_k100(x)) / 20.0))
    capa = p.get('capa_kit')
    if capa:
        y = _kit_variante(kit['ruta'], kit['tipo'], int(capa[0]))
        if y is not None:
            y = y * (10 ** ((objetivo + float(capa[1]) - _nivel_k100(y)) / 20.0))
            x, _ = _sumar(x, F.indice_ataque(x) / SR, y, F.indice_ataque(y) / SR)
            x = x[:, max(0, F.indice_ataque(x, -40.0) - int(0.005 * SR)):].copy()      # (la octava baja estira su pre-roll: otra vez 5 ms
            k = min(x.shape[1], int(0.003 * SR))                                        # antes del ataque y 3 ms de entrada)
            x[:, :k] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))).astype(np.float32)
            n = int(KIT_ACENTO_S * SR)
            if x.shape[1] > n:
                x = x[:, :n].copy()
                k = int(0.02 * SR)
                x[:, -k:] *= np.linspace(1, 0, k, dtype=np.float32)
    eleccion = {'candidatos': 1, 'elegido': Path(kit['ruta']).name, 'archivo': kit['ruta'], 'kit': kit['tipo'], 'sha1': kit['sha1'],
                'semitonos': st, 'por_que': kit['por_que']}
    return np.asarray(x, np.float32), eleccion


def _candidatos(tipo):
    import director_sonido_fuentes as F
    if tipo not in _CANDIDATOS:
        _CANDIDATOS[tipo] = F.candidatos(tipo)
    return _CANDIDATOS[tipo]


def de_biblioteca(e, usados):
    """El mejor archivo de la biblioteca curada que pasa el Quality Gate y el ajuste semántico, recortado y alineado. (audio, offset, elección).
    `params['evitar']` = archivos que el usuario ya no quiere para ESTE evento («otro SFX» / «otra textura»)."""
    import director_sonido_fuentes as F
    tipo = CATEGORIA.get(e['tipo'])
    evitar = {str(x) for x in (e['params'].get('evitar') or [])}
    cands = [c for c in _candidatos(tipo) if str(c) not in evitar]
    if not cands:
        return None, 0.0, {'candidatos': 0}
    objetivo = {'tipo': tipo, 'dur': e['dur'], 'brillo': e['params'].get('brillo', 0.5), 'energia': 0.8 if e['tipo'] == 'golpe' else 0.4}
    ruta, ranking = F.elegir(cands, objetivo, usados)
    eleccion = {'candidatos': len(ranking), 'rechazados_quality_gate': sum(1 for r in ranking if r[0] < 0), 'elegido': Path(ruta).name if ruta else None,
                'top3': [(r[0], Path(r[1]).name) for r in ranking[:3]]}
    if not ruta:
        return None, 0.0, eleccion
    usados[ruta] = usados.get(ruta, 0) + 1
    largo = e['dur'] + (0.6 if e['tipo'] in ('golpe', 'acento') else 0.2)
    x = F.leer_para_mezcla(ruta, None if e['tipo'] == 'riser' else largo, 0.25 if e['tipo'] in ('golpe', 'acento') else 0.04)
    if x is None:
        return None, 0.0, eleccion
    eleccion['archivo'] = str(ruta)
    if e['tipo'] == 'riser':
        x = x[:, -int(e['dur'] * SR):] if x.shape[1] > e['dur'] * SR else x
        return x, x.shape[1] / SR, eleccion
    return _balance(x, e['params'].get('direccion', 0.0)), _pico_idx(x) / SR, eleccion


def _capa(e, rng):
    """La capa procedural del modo híbrido, a la medida de ESE motion: (audio, segundos desde el inicio hasta el ancla, dB bajo el archivo) o None."""
    import director_sonido_sintesis as S
    p = e['params']
    if e['tipo'] == 'golpe':
        return S.golpe(p.get('peso', 0.7), p.get('brillo', 0.5), 0.15, 0.0, rng), 0.0, 6.0
    if e['tipo'] == 'whoosh':
        return S.whoosh(max(0.12, e['dur'] - 0.12), p.get('direccion', 0.0), p.get('easing', 'easeInOutCubic'), 0.8, 0.2, rng), e['ancla'] - e['t'], 8.0
    return None


def _menos_graves(x, corte_hz=180.0):
    """Paso alto suave (por FFT, rampa de una octava): «menos graves»."""
    n = x.shape[1]
    X = np.fft.rfft(x, axis=1)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = np.clip(np.log2(np.maximum(f, 1.0) / (corte_hz / 2.0)), 0.0, 1.0)
    return np.fft.irfft(X * g, n, axis=1).astype(np.float32)


def _transitorio_suave(x, off, ms=22.0):
    """El ataque en el ancla, redondeado (de 0,45 a 1 en `ms`): «menos transitorio»."""
    i0 = max(0, int(round(off * SR)) - int(0.002 * SR))
    k = int(ms / 1000.0 * SR)
    y = x.copy()
    y[:, :i0] *= 0.45
    y[:, i0:i0 + k] *= np.linspace(0.45, 1.0, min(k, max(0, y.shape[1] - i0)))
    return y


def _variar(x, off, rng, tono=0.03, nivel_db=0.7):
    """Microvariación de un archivo que ya sonó en este video (tono ±3 %, nivel ±0,7 dB): dos toques seguidos nunca son el mismo clon. El ancla se
    corre con el cambio de tono. (El MOTIVO tonal y el kit Social no pasan por aquí: se repiten igual a propósito.) v5.39: por FFT, sin np.interp."""
    f = 1.0 + float(rng.uniform(-tono, tono))
    y = _remuestrear(np.asarray(x, np.float32), f)
    return y * (10 ** (float(rng.uniform(-nivel_db, nivel_db)) / 20.0)), off / f


def _sumar(a, off_a, b, off_b):
    """Dos sonidos alineados por su ancla en uno solo: (audio, offset)."""
    off = max(off_a, off_b)
    ia, ib = int(round((off - off_a) * SR)), int(round((off - off_b) * SR))
    n = max(ia + a.shape[1], ib + b.shape[1])
    y = np.zeros((2, n), np.float32)
    y[:, ia:ia + a.shape[1]] += a
    y[:, ib:ib + b.shape[1]] += b
    return y, off


def _nombre(e, nivel_db, modo, relleno=0, kit=None):
    p = {k: v for k, v in e['params'].items() if not (e['tipo'] == 'acento' and k == 'semilla')}    # el motivo: la misma nota = el mismo archivo
    clave = json.dumps({'v': VERSION, 'modo': modo, 'tipo': e['tipo'], 'dur': e['dur'], 'ancla_rel': round(e['ancla'] - e['t'], 3), 'p': p,
                        'nivel': round(nivel_db, 1), 'relleno': int(relleno), 'kit': kit}, sort_keys=True, default=str)
    return f"{e['id'].split('-')[0]}_{hashlib.sha1(clave.encode('utf-8')).hexdigest()[:12]}.wav"


def _escribir(destino, x):
    import director_sonido_medir as M
    tmp = destino.with_suffix('.tmp.wav')
    w = M.EscritorWav(tmp, 2)
    try:
        w.escribir(x)
    finally:
        w.cerrar()
    tmp.replace(destino)


def fabricar(diseno, carpeta, nivel_voz_db, modo=MODO, fps=None):
    """Los sonidos del diseño (solo los GENERATE) hechos y escritos. Devuelve {'eventos', 'puestos', 'segundos', 'modo', 'kit'} (ver el docstring
    del módulo). `fps` (Resolve): cada WAV empieza en un fotograma exacto, con el silencio que falte delante."""
    import director_sonido_fuentes as F
    t0 = time.time()
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    usados, salida, puestos = {}, [], []
    eventos = sorted(diseno.get('eventos') or [], key=lambda e: e['t'])
    kits = _kits(eventos)
    heroes = [float(nivel_voz_db) + float(e['nivel_rel_voz_db']) + float(e['params'].get('nivel_extra_db') or 0.0) for e in eventos
              if e.get('decision') == 'GENERATE' and e['params'].get('kit') == 'pop' and e['params'].get('social') in ('heroe', 'acento')]
    tope_swipe = min(heroes) - SWIPE_BAJO_HEROE_DB if heroes else None
    n_kit = {}
    for e in eventos:
        if e.get('decision') != 'GENERATE':
            continue
        fijo = e.get('plan_fijo') or {}
        if e.get('bloqueado') and fijo.get('archivo') and Path(str(fijo['archivo'])).is_file():      # BLOQUEADO: el mismo archivo y el mismo sitio
            salida.append(dict(fijo, ai=dict(fijo.get('ai') or {}, id=e['id'], tipo=e['tipo'], origen=e.get('origen'))))
            puestos.append({'id': e['id'], 'tipo': e['tipo'], 'origen': e.get('origen'), 'decision': e['decision'], 'por_que': e['por_que'],
                            'importancia': e['importancia'], 'fuente': (fijo.get('ai') or {}).get('fuente') or 'bloqueado', 'bloqueado': True,
                            'clave': e.get('clave')})
            continue
        p = e['params']
        rng = np.random.default_rng(int(p.get('semilla') or 0))
        objetivo = float(nivel_voz_db) + float(e['nivel_rel_voz_db']) + float(p.get('nivel_extra_db') or 0.0)
        if p.get('kit') == 'whoosh' and tope_swipe is not None:
            objetivo = min(objetivo, tope_swipe)                      # (el swipe nunca tapa al pop: CapCut suena a pop)
        x, off, fuente, eleccion = None, 0.0, 'procedural', None
        kit = kits.get(p.get('kit')) if p.get('kit') and not p.get('solo_procedural') else None
        if kit is not None:                                           # Social: el kit, tal cual (sin biblioteca, capa, paneo ni azar)
            x, eleccion = _sonido_kit(kit, e, objetivo)
            if x is not None:
                fuente = 'kit social'
                off = (_pico_idx(x) if p['kit'] == 'whoosh' else F.indice_ataque(x)) / SR
                n_kit[p['kit']] = n_kit.get(p['kit'], 0) + 1
        if x is None and modo == 'hibrido' and not p.get('solo_procedural'):
            x, off, eleccion = de_biblioteca(e, usados)
            if x is None and p.get('sin_sintesis') and (eleccion or {}).get('candidatos'):     # (Social: con librería, nunca sintético: se repite
                x, off, eleccion = de_biblioteca(e, {})                                         # el mejor archivo antes que sonar a falso)
            if x is not None:
                fuente = 'biblioteca curada'
        if x is None:
            x, off = sintetizar(e, rng)
            fuente = ('procedural' if modo == 'procedural' or p.get('solo_procedural') or not (eleccion or {}).get('candidatos')
                      else 'procedural (ningún archivo pasó el Quality Gate)')
        if x is None or not x.size:
            puestos.append({'id': e['id'], 'tipo': e['tipo'], 'fuente': 'LEAVE_SILENT', 'por_que': 'no se pudo hacer: mejor silencio'})
            continue
        if fuente != 'kit social':
            x = _ganancia(np.asarray(x, np.float32), objetivo)
            if fuente == 'biblioteca curada' and e['tipo'] != 'acento' and usados.get((eleccion or {}).get('archivo'), 0) > 1:
                x, off = _variar(x, off, rng)
            if (fuente == 'biblioteca curada' and not p.get('sin_capa')) or p.get('otra_capa'):
                capa = _capa(e, rng)
                if capa is not None:
                    y, off_y, menos_db = capa
                    x, off = _sumar(x, off, _ganancia(y, objetivo - menos_db), off_y)
                    fuente += ' + capa procedural'
        if p.get('clic'):                                             # «mejor transitorio»: un clic nítido justo en el ancla
            import director_sonido_sintesis as S
            x, off = _sumar(x, off, _ganancia(S.tick(0.85, rng), objetivo - 6.0), 0.0)
            fuente += ' + clic'
        if p.get('graves_menos'):
            x = _menos_graves(x)
        if p.get('transitorio_menos'):
            x = _transitorio_suave(x, off)
        if e['tipo'] == 'golpe' or p.get('kit') == 'whoosh':          # el golpe se sincroniza por su PICO: el del sonido FINAL (archivo + capas),
            off = _pico_idx(x) / SR                                   # no el del archivo solo (una cola más fuerte lo corría +80 ms); el swipe, igual
        elif e['tipo'] in POR_ATAQUE:                                 # pops, tics y acentos: por su ATAQUE en la suma mono, medido al final
            off = F.indice_ataque(x) / SR
        pico = float(np.abs(x).max()) if x.size else 0.0
        if pico > 0.89:                                               # −1 dBFS de muestra como mucho (los true peaks los mira la fase 5)
            x = x * (0.89 / pico)
        inicio = e['ancla'] - off - (0.03 if e['tipo'] == 'riser' else 0.0)
        if inicio < 0:
            x, inicio = x[:, int(round(-inicio * SR)):], 0.0
            k = min(x.shape[1], 144)
            x[:, :k] *= np.linspace(0, 1, k)
        if x.shape[1] < 96:
            continue
        relleno = 0
        if fps and inicio > 0:                                        # Resolve coloca por fotogramas: el WAV empieza en uno exacto y el silencio
            base = math.floor(inicio * float(fps) + 1e-6) / float(fps)     # de delante deja el golpe en su sitio (no ±16,7 ms del redondeo)
            relleno = int(round((inicio - base) * SR))
            if relleno:
                x = np.pad(np.asarray(x, np.float32), ((0, 0), (relleno, 0)))
            inicio = base
        destino = carpeta / _nombre(e, objetivo, modo, relleno, (kit or {}).get('sha1') if fuente == 'kit social' else None)
        if not destino.is_file():
            _escribir(destino, x)
        info = {'id': e['id'], 'tipo': e['tipo'], 'origen': e.get('origen'), 'decision': e['decision'], 'por_que': e['por_que'],
                'importancia': e['importancia'], 'fuente': fuente, 'nivel_db': round(objetivo, 1), 'clave': e.get('clave'), 'archivo': str(destino)}
        if eleccion and eleccion.get('elegido'):
            info['eleccion'] = eleccion
        if fuente == 'kit social':
            info['kit'] = {'tipo': p['kit'], 'sha1': kit['sha1'], 'archivo': Path(kit['ruta']).name, 'semitonos': int(p.get('semitonos') or 0),
                           'social': p.get('social')}
        salida.append({'tipo': 'sonido', 'pista': e['pista'], 'ini': round(inicio, 6), 'dur': round(x.shape[1] / SR, 3), 'archivo': str(destino),
                       'asset': f"{e['id']} · {fuente}", 'ai': {k: info[k] for k in ('id', 'tipo', 'origen', 'fuente', 'clave')}})
        puestos.append(info)
    try:
        F.guardar_cache()
    except Exception:
        pass
    resumen_kit = {t: {'archivo': Path(k['ruta']).name, 'ruta': k['ruta'], 'sha1': k['sha1'], 'por_que': k['por_que'], 'eventos': n_kit.get(t, 0)}
                   for t, k in kits.items()}
    return {'eventos': salida, 'puestos': puestos, 'segundos': round(time.time() - t0, 2), 'modo': modo, 'kit': resumen_kit}
