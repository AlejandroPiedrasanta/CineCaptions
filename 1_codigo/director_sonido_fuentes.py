# CineCaptions · By Cinema Productions
# 1_codigo/director_sonido_fuentes.py — «AI Sound Director»: de dónde sale cada sonido (SOUND ASSET STRATEGY) y el QUALITY GATE de cada archivo.
"""
Prioridad para diseños NUEVOS (decisión del usuario, 2026-10-21):
    1 procedural / a la medida (director_sonido_sintesis) · 2 Epidemic autorizado (director_sonido_epidemic) · 3 caché profesional aprobada ·
    4 biblioteca curada (la del autor, la que el usuario apruebe) · 5 LEGACY local (2_recursos/sfx_library) = DISABLED_FOR_NEW_DESIGN, solo si un
    asset pasa el Quality Gate y el usuario lo aprueba · 6 SILENCIO. Un silencio profesional es mejor que un SFX malo.

`calidad(ruta)` → QUALITY SCORE 0–100 con sus motivos (cada penalización explicada): clipping, ruido de fondo, frecuencia de muestreo, equilibrio
espectral (apagado / áspero), graves (DC, rumble por debajo de 30 Hz), transitorio (ataque), duración útil, estéreo (fase), formato con pérdida
(bitrate y, v5.39, el corte de agudos de un MP3 aunque venga en .wav) y cresta (producción). Con caché por huella del archivo. Por debajo de
UMBRAL: REJECT aunque el archivo exista. v5.39: los DEFECTOS claros son VETO (score 0, `vetos`), no −10 que un archivo malo aguanta: un «pop» con
dos golpes (flam), ataque lento, graves o apagado; un «whoosh» sin aire (rumble), rectangular (ruido plano) o cortado a nivel alto. Los más finos
(`VETO_ESTRICTO`: cola de un pop > 200 ms, bordes de un whoosh > −35 dB, su pico pasado el corte, nada de IMPACTOS) solo con objetivo['estricto']
(el kit «Social»), para que los demás estilos sigan encontrando archivos en una biblioteca normal.
`candidatos(tipo)` → archivos de la biblioteca del autor por carpeta (whoosh, golpe, riser, ui, tonal); `elegir(candidatos, objetivo)` → nunca el
primero: puntúa quality, duration_fit, spectral_fit (contra el brillo de la paleta), energy_fit y recent_similarity, y devuelve el mejor + el ranking.
`leer_para_mezcla(ruta, dur)` → el archivo LIMPIO: sin DC ni subgraves, sin silencio delante, entrada de 3 ms y cola adaptativa con fundido.
"""
import hashlib
import re
from pathlib import Path

import numpy as np

UMBRAL = 70
CALIDAD_VERSION = 2                  # súbela si cambian las medidas o los vetos: la caché en disco de antes no se reutiliza (2: vetos v5.39)
SR = 48000
LEGACY_LOCAL = 'DISABLED_FOR_NEW_DESIGN'
BIBLIOTECA_AUTOR = Path(r'E:\VFX-EDICION VIDEOS\DAVINCI RESOLVE\EFECTOS SONIDO\UTILES')      # licencias: el autor responde (memoria recursos-del-autor)
CARPETAS = {   # tipo → subcarpetas de la biblioteca del autor (por nombre; se ignora lo que no exista)
    'whoosh': ('Artlist - 200+ Sound Effects/Whooshes', 'Artlist - 200+ Sound Effects/Transitions', 'Whooshes', '1_Sfx - Varios/WHOOSH', 'Cinematic SFX/WHOOSH'),
    'golpe': ('Cinematic SFX/IMPACTOS', '2_Sfx - Cinematic', 'Artlist - 200+ Sound Effects/Impact', 'Artlist - 200+ Sound Effects/Hits', '1_Sfx - Varios/IMPACTOS'),
    'riser': ('Artlist - 200+ Sound Effects/Risers', '2_Sfx - Cinematic', '1_Sfx - Varios/RISERS Y TENSION', 'Cinematic SFX/RISERS Y TENSION', 'SFX RISEX'),
    'ui': ('Artlist - 200+ Sound Effects/Menus', '1_Sfx - Varios/CLICKS Y UI'),
    'tonal': ('Artlist - 200+ Sound Effects/Pulses', 'Artlist - 200+ Sound Effects/Mysterious'),
}
EXT = ('.wav', '.mp3', '.aif', '.aiff', '.flac', '.ogg', '.m4a')
CARPETAS['trazo'] = CARPETAS['ui'] + ('Cinematic SFX/OBJETOS Y FOLEY', '1_Sfx - Varios/OTROS')
# SEMANTIC FIT por el nombre del archivo: lo que encaja con cada diseño, lo que es un OBJETO concreto (suena a eso, no a un gráfico) y lo que nunca va
SEMANTICA = {
    'golpe': ('impact', 'hit', 'slam', 'boom', 'cinematic', 'sub', 'drop', 'braam', 'thud', 'designed', 'trailer', 'bass', 'deep', 'titanic', 'epic'),
    'whoosh': ('whoosh', 'swoosh', 'swish', 'swipe', 'transition', 'air', 'woosh', 'pass', 'swing', 'zip', 'sweep'),
    'riser': ('riser', 'rise', 'swell', 'build', 'uplift', 'tension', 'sweep', 'reverse', 'risex'),
    'ui': ('click', 'tap', 'ui', 'button', 'select', 'pop', 'tick', 'interface', 'menu', 'blip', 'beep', 'notification', 'seleccion', 'taping', 'tapping'),
    'tonal': ('chime', 'bell', 'ping', 'sparkle', 'shimmer', 'notification', 'tone', 'glass', 'twinkle', 'positive', 'magic', 'success', 'chord',
              'note', 'positivo', 'tonal'),
    'trazo': ('marker', 'pen', 'pencil', 'scribble', 'draw', 'write', 'writing', 'chalk', 'brush', 'sketch'),
}
OBJETOS = ('plastic', 'pottery', 'metal', 'metallic', 'steel', 'armor', 'sword', 'wood', 'wooden', 'table', 'rock', 'stone', 'glass', 'debris', 'breaking',
           'door', 'car', 'gun', 'weapon', 'military', 'target', 'punch', 'combat', 'fight', 'bat', 'baseball', 'whack', 'smack', 'wet', 'body',
           'kitchen', 'bottle', 'paper', 'thunder', 'fire', 'steam', 'anime', 'wobbly')
NUCLEO = {   # sin al menos una de estas palabras, el archivo no es de ese tipo (un «Reverse Wind Riser» no es un golpe aunque diga «Cinematics»)
    'golpe': ('impact', 'hit', 'slam', 'boom', 'braam', 'thud', 'drop', 'bass'),
    'whoosh': ('whoosh', 'swoosh', 'swish', 'swipe', 'transition', 'woosh', 'pass'),
    'riser': ('riser', 'rise', 'swell', 'build', 'uplift', 'reverse', 'risex'),
    'ui': ('click', 'tap', 'ui', 'button', 'select', 'pop', 'tick', 'blip', 'beep', 'interface', 'seleccion', 'taping', 'tapping'),
    'tonal': ('chime', 'bell', 'ping', 'sparkle', 'shimmer', 'shimmering', 'tone', 'twinkle', 'notification', 'chord', 'note', 'positivo'),
    'trazo': ('marker', 'pen', 'pencil', 'scribble', 'draw', 'write', 'writing', 'chalk', 'sketch'),
}
OSCURO = ('dark', 'ominous', 'sinister', 'evil', 'mysterious', 'creepy', 'suspense', 'horror')     # no van con un video luminoso (brillo ≥ 0,5)
NUNCA = ('fart', 'burp', 'meme', 'cartoon', 'scream', 'laugh', 'baby', 'vomit', 'toilet', 'moan', 'vocal', 'voice', 'song', 'guitar', 'piano',
         'arpeggio', 'creepy', 'horror', 'ghost', 'scary', 'zombie', 'monster', 'funny', 'comedy', 'cry')
_CACHE = {}
_DISCO = {'cargado': False, 'cambios': 0}                 # v5.34: las medidas también en disco (sound_director/cache/quality_gate.json)


def _ruta_cache():
    import director_sonido_estado as E
    return E.CARPETA / 'cache' / 'quality_gate.json'


def _cargar_disco():
    if _DISCO['cargado']:
        return
    _DISCO['cargado'] = True
    try:
        import archivos_seguros
        datos = archivos_seguros.leer_json(_ruta_cache(), {}) or {}
        if datos.get('version') != CALIDAD_VERSION:                   # (medidas de otra versión del Quality Gate: se vuelven a medir)
            return
        for k, v in (datos.get('entradas') or {}).items():
            clave, _, tipo = str(k).partition('|')
            _CACHE.setdefault((clave, tipo or None), v)
    except Exception:
        pass


def guardar_cache():
    """Las medidas nuevas del Quality Gate, a disco (el mismo archivo con la misma huella no se vuelve a medir en el próximo GO)."""
    if not _DISCO['cambios']:
        return
    try:
        import archivos_seguros
        archivos_seguros.escribir_json(_ruta_cache(), {'version': CALIDAD_VERSION, 'entradas': {f'{k[0]}|{k[1] or ""}': v for k, v in _CACHE.items()}},
                                       default=lambda o: float(o) if hasattr(o, '__float__') else str(o))
        _DISCO['cambios'] = 0
    except Exception:
        pass


def _leer(ruta, max_s=12.0):
    """(muestras (canales, n) a 48 kHz, tasa nativa, bitrate, duración) o None."""
    import av
    try:
        with av.open(str(ruta)) as c:
            a = c.streams.audio[0]
            tasa, br = int(a.codec_context.sample_rate or 0), int(a.codec_context.bit_rate or c.bit_rate or 0)
            dur = float(c.duration / 1e6) if c.duration else 0.0
            rs = av.AudioResampler(format='fltp', layout='stereo', rate=48000)
            trozos, total = [], 0
            for fr in c.decode(a):
                for g in rs.resample(fr):
                    x = g.to_ndarray()
                    trozos.append(x)
                    total += x.shape[1]
                if total > max_s * 48000:
                    break
            if not trozos:
                return None
            x = np.concatenate(trozos, axis=1).astype(np.float32)
            return x, tasa, br, dur or x.shape[1] / 48000.0
    except Exception:
        return None


def _clave(ruta):
    p = Path(ruta)
    st = p.stat()
    return hashlib.sha1(f'{p.resolve()}|{st.st_size}|{int(st.st_mtime)}'.encode('utf-8')).hexdigest()[:16]


def paso_alto(x, corte_hz, orden=2):
    """Paso alto de fase cero por FFT (la magnitud de un Butterworth de `orden`) sobre (canales, n) o (n,), con silencio de relleno para que la
    cola no se enrosque al principio del archivo. Quita también la DC."""
    x = np.asarray(x, np.float64)
    y = x[None] if x.ndim == 1 else x
    n = y.shape[1]
    if n < 16:
        return x
    N = n + max(2048, int(0.1 * SR))
    f = np.fft.rfftfreq(N, 1.0 / SR)
    r = (f / float(corte_hz)) ** orden
    z = np.fft.irfft(np.fft.rfft(y, N, axis=1) * (r / np.sqrt(1.0 + r ** 2)), N, axis=1)[:, :n]
    return z[0] if x.ndim == 1 else z


def indice_ataque(x, db=-20.0):
    """La primera muestra de la suma mono a `db` o más de su pico: lo que el oído toma como «el golpe» (el ataque, no un máximo de 2 ms que llega
    tras un pre-roll o en un segundo golpe)."""
    m = np.abs(np.asarray(x).mean(axis=0) if np.ndim(x) > 1 else np.asarray(x))
    if not m.size or m.max() <= 0:
        return 0
    return int(np.argmax(m >= m.max() * 10 ** (db / 20.0)))


def _movil(v, k):
    """La media móvil de `k` muestras, igual que np.convolve(v, unos/k, 'same') pero en O(n) (archivos de 10 s)."""
    vp = np.concatenate((np.zeros(k // 2), np.asarray(v, np.float64), np.zeros((k - 1) // 2)))
    s = np.concatenate(([0.0], np.cumsum(vp)))
    return (s[k:] - s[:-k]) / k


def _finas(x):
    """v5.39, las medidas que separan un pop limpio de un flam o un golpe sordo, y un whoosh con aire de un rumble o un bloque de ruido (las mismas
    del diagnóstico del 2026-10-22): ataque 10–90 % (1 ms), golpes a −10 dB en los primeros 150 ms, tramo a −40 dB, energía < 150 Hz y > 1 kHz,
    centroide del tramo que suena, suelo dentro de él, bordes del archivo (5 ms) y el corte de agudos de un MP3."""
    m = x.mean(axis=0).astype(np.float64)
    a = np.abs(x).max(axis=0).astype(np.float64)
    if m.size < 480 or a.max() <= 0:
        return {}
    e1 = np.sqrt(np.maximum(_movil(m ** 2, 48), 0.0) + 1e-20)
    e1db = 20 * np.log10(e1 / e1.max() + 1e-12)
    vivos = np.nonzero(e1db >= -40)[0]
    i0, i1 = int(np.argmax(a >= 0.01 * a.max())), int(vivos[-1])         # (desde la primera muestra a −40 dB hasta que su RMS de 1 ms cae 40 dB)
    i10, i90 = int(np.argmax(e1 >= 0.1 * e1.max())), int(np.argmax(e1 >= 0.9 * e1.max()))
    e2 = _movil(a, 96)
    e2n = e2 / (e2.max() + 1e-12)
    tramo = e2n[i0:min(e2n.size, i0 + int(0.15 * SR) + 1)]          # golpes: máximos a −10 dB o más, a > 25 ms y con un valle de −6 dB entre ellos
    golpes = []
    for i in sorted((i for i in range(1, tramo.size - 1) if tramo[i] >= 0.316 and tramo[i] >= tramo[i - 1] and tramo[i] > tramo[i + 1]),
                    key=lambda i: -tramo[i]):
        if all(abs(i - j) > 48 * 25 and tramo[min(i, j):max(i, j) + 1].min() <= 0.5 * min(tramo[i], tramo[j]) for j in golpes):
            golpes.append(i)
    seg = m[i0:i1 + 1] if i1 - i0 > 512 else m
    seg = seg - seg.mean()
    P = np.abs(np.fft.rfft(seg * np.hanning(seg.size))) ** 2
    f = np.fft.rfftfreq(seg.size, 1.0 / SR)
    tot = float(P.sum()) + 1e-20
    banda = (f >= 10000) & (f < 15000)
    corte = None
    if P[banda].sum() / tot >= 1e-4 and ((f >= 16500) & (f < 20000)).any():
        corte = round(float(10 * np.log10((P[(f >= 16500) & (f < 20000)].mean() + 1e-30) / (P[banda].mean() + 1e-30))), 1)
    e10 = np.sqrt(np.maximum(_movil(m ** 2, 480), 0.0) + 1e-20)
    e10db = 20 * np.log10(e10 / e10.max() + 1e-12)
    pk = float(np.abs(m).max()) or 1e-9
    k = min(240, m.size)
    return {'ataque_fino_ms': round((i90 - i10) / 48.0, 1), 'golpes_150ms': max(1, len(golpes)), 'tramo40_ms': round((i1 - i0) / 48.0),
            'graves150': round(float(P[f < 150].sum() / tot), 3), 'aire_1k': round(float(P[f >= 1000].sum() / tot), 3),
            'centroide_activo_hz': round(float((P * f).sum() / tot)), 'suelo_activo_db': round(float(np.percentile(e10db[i0:i1 + 1], 8)), 1),
            'borde_ini_db': round(float(20 * np.log10(np.abs(m[:k]).max() / pk + 1e-12)), 1),
            'borde_fin_db': round(float(20 * np.log10(np.abs(m[-k:]).max() / pk + 1e-12)), 1),
            'pico_s': round((int(np.argmax(e2)) - i0) / SR, 3), 'corte_mp3_db': corte}


def _vetos(med, tipo):
    """Los defectos que NO se compensan con puntos (v5.39). Conservadores: lo que es un defecto en cualquier estilo."""
    v = []
    if not med.get('tramo40_ms'):
        return v
    if tipo == 'ui':
        if med['golpes_150ms'] > 1:
            v.append(f"{med['golpes_150ms']} golpes en 150 ms (flam, no un pop)")
        if med['ataque_fino_ms'] > 8:
            v.append(f"ataque lento ({med['ataque_fino_ms']:.0f} ms) para un pop / clic")
        if med['graves150'] > 0.10:
            v.append(f"{100 * med['graves150']:.0f} % bajo 150 Hz (golpe sordo)")
        if med['centroide_activo_hz'] < 600:
            v.append(f"apagado para un pop (centroide {med['centroide_activo_hz']} Hz)")
    elif tipo == 'whoosh':
        if med['aire_1k'] < 0.10:
            v.append(f"sin aire ({100 * med['aire_1k']:.1f} % sobre 1 kHz: un rumble, no un whoosh)")
        if med['suelo_activo_db'] > -20:
            v.append(f"rectangular (suelo {med['suelo_activo_db']:.0f} dB bajo el pico: un bloque de ruido)")
        if max(med['borde_ini_db'], med['borde_fin_db']) > -20:
            v.append(f"cortado a nivel alto (bordes {med['borde_ini_db']:.0f} / {med['borde_fin_db']:.0f} dB)")
    return v


def vetos_estrictos(med, tipo, ruta, largo=None):
    """Además de los vetos de siempre, los del kit «Social» (y su «Otro sonido»): un pop corto de verdad, un whoosh limpio en sus bordes y con
    su pico antes del corte, y nada de la carpeta de impactos."""
    v = []
    if any('impact' in p.lower() for p in Path(ruta).parts[:-1]):
        v.append('carpeta de impactos (en Social nunca)')
    if not med.get('tramo40_ms'):
        return v
    if tipo == 'ui' and med['tramo40_ms'] > 200:
        v.append(f"cola larga para un pop ({med['tramo40_ms']} ms a −40 dB)")
    if tipo == 'whoosh':
        if max(med['borde_ini_db'], med['borde_fin_db']) > -35:
            v.append(f"bordes sucios ({med['borde_ini_db']:.0f} / {med['borde_fin_db']:.0f} dB bajo el pico)")
        if med['graves150'] > 0.15:
            v.append(f"{100 * med['graves150']:.0f} % bajo 150 Hz (un swipe es aire)")
        if largo and med['pico_s'] > largo - 0.1:
            v.append(f"su pico ({med['pico_s']:.2f} s) cae pasado el corte ({largo:.2f} s)")
    return v


def calidad(ruta, tipo=None):
    """QUALITY SCORE 0–100 y por qué (cada punto que se resta, con su medida)."""
    _cargar_disco()
    try:
        k = (_clave(ruta), tipo)
    except OSError:
        return {'score': 0, 'motivos': ['no existe'], 'medidas': {}}
    if k in _CACHE:
        return _CACHE[k]
    d = _leer(ruta)
    if d is None:
        r = {'score': 0, 'motivos': ['no se puede decodificar'], 'medidas': {}}
        _CACHE[k] = r
        return r
    x, tasa, br, dur = d
    m = x.mean(axis=0)
    pico = float(np.abs(x).max()) or 1e-9
    puntos, motivos, med = 100, [], {}

    def menos(n, motivo):
        nonlocal puntos
        puntos -= n
        motivos.append(f'−{n} {motivo}')
    pegadas = float(np.mean(np.abs(x) >= 0.999))
    med['clipping_pct'] = round(100 * pegadas, 4)
    if pegadas > 0.0001:
        menos(25, f'clipping ({100 * pegadas:.3f} %)')
    med['tasa'], med['bitrate'], med['duracion'] = tasa, br, round(dur, 3)
    if tasa and tasa < 44100:
        menos(15, f'muestreo bajo ({tasa} Hz)')
    if str(ruta).lower().endswith('.mp3') and br and br < 160000:
        menos(10, f'mp3 de {br // 1000} kbps')
    env = np.sqrt(np.convolve(m.astype(np.float64) ** 2, np.ones(480) / 480, 'same') + 1e-12)
    env_db = 20 * np.log10(env / pico + 1e-12)
    ruido = float(np.percentile(env_db, 8)) if env_db.size else -120
    med['fondo_rel_pico_db'] = round(ruido, 1)
    if ruido > -45 and tipo in ('golpe', 'ui', 'whoosh'):
        menos(15, f'ruido de fondo alto ({ruido:.0f} dB bajo el pico)')
    dc = float(abs(m.mean()))
    if dc > 0.01:
        menos(10, f'DC {dc:.3f}')
    n = min(m.size, 48000 * 4)
    P = np.abs(np.fft.rfft(m[:n] * np.hanning(n))) ** 2 if n > 1024 else None
    if P is not None:
        f = np.fft.rfftfreq(n, 1 / 48000)
        tot = P.sum() + 1e-12
        cent = float((P * f).sum() / tot)
        sub = float(P[f < 30].sum() / tot)
        aspero = float(P[(f > 2500) & (f < 5000)].sum() / tot)
        med.update(centroide_hz=round(cent), sub30=round(sub, 3), aspereza=round(aspero, 3))
        if sub > 0.3:
            menos(10, f'rumble por debajo de 30 Hz ({100 * sub:.0f} %)')
        if cent < 250 and tipo not in ('golpe',):
            menos(10, f'apagado (centroide {cent:.0f} Hz)')
        if aspero > 0.45:
            menos(10, f'áspero ({100 * aspero:.0f} % en 2,5–5 kHz)')
    i_pico = int(np.argmax(env))
    a10 = int(np.argmax(env[:i_pico + 1] >= 0.1 * env[i_pico])) if i_pico > 0 else 0
    ataque_ms = (i_pico - a10) / 48.0
    med['ataque_ms'] = round(ataque_ms, 1)
    if tipo in ('golpe', 'ui') and ataque_ms > 25:
        menos(10, f'transitorio blando ({ataque_ms:.0f} ms) para un {tipo}')
    rms = float(np.sqrt(np.mean(m.astype(np.float64) ** 2)) + 1e-12)
    cresta = 20 * np.log10(pico / rms)
    med['cresta_db'] = round(cresta, 1)
    if tipo == 'golpe' and cresta < 8:
        menos(10, f'golpe aplastado (cresta {cresta:.0f} dB)')
    if x.shape[0] == 2:
        l, r = x[0].astype(np.float64), x[1].astype(np.float64)
        corr = float(np.dot(l, r) / (np.sqrt(np.dot(l, l) * np.dot(r, r)) + 1e-12))
        med['correlacion_lr'] = round(corr, 3)
        if corr < 0:
            menos(15, f'fase invertida entre canales ({corr:.2f}: desaparece en mono)')
    util = float(np.sum(env_db > -40)) / 48000.0
    med['duracion_util_s'] = round(util, 3)
    if util < 0.04 or dur > 20:
        menos(10, f'duración útil rara ({util:.2f} s de {dur:.1f} s)')
    med.update(_finas(x))
    if med.get('corte_mp3_db') is not None and med['corte_mp3_db'] <= -25:      # (los previews MP3 pasados a .wav: el .mp3 de arriba no los ve)
        menos(15, f"origen con pérdida (los agudos caen {-med['corte_mp3_db']:.0f} dB pasados 16,5 kHz)")
    vetos = _vetos(med, tipo)
    r = {'score': 0 if vetos else int(max(0, puntos)), 'motivos': [f'VETO: {v}' for v in vetos] + motivos or ['sin defectos medidos'],
         'medidas': med, 'vetos': vetos}
    _CACHE[k] = r
    _DISCO['cambios'] += 1
    return r


def _palabras(ruta):
    """Las palabras del nombre y de su carpeta (v5.37: el autor ordena por carpetas: «Whooshes/…», «SELECCION (3)», «Chord Hits/…»)."""
    p = Path(ruta)
    return re.findall(r'[a-z0-9áéíóúñ]+', f'{p.stem} {p.parent.name}'.lower())


def _tiene(palabras, termino):
    """La palabra ENTERA (o su plural; los términos largos, también como prefijo: whoosh → whooshes): «pen» no está en «pensamiento»."""
    if ' ' in termino:
        return termino in ' '.join(palabras)
    return any(w == termino or w in (termino + 's', termino + 'es') or (len(termino) >= 5 and w.startswith(termino)) for w in palabras)


def semantica(ruta, tipo, brillo=None):
    """SEMANTIC FIT 0–1 por el nombre: +0,3 por cada palabra del diseño, −0,5 por cada objeto concreto (suena a ese objeto, no a un gráfico),
    −0,4 por un tono oscuro en un video luminoso; 0 si es algo que nunca va."""
    w = _palabras(ruta)
    if any(_tiene(w, p) for p in NUNCA):
        return 0.0
    bien = sum(1 for p in SEMANTICA.get(tipo, ()) if _tiene(w, p))
    mal = sum(1 for p in OBJETOS if _tiene(w, p))
    oscuro = sum(1 for p in OSCURO if _tiene(w, p)) if (brillo is not None and brillo >= 0.5) else 0
    valor = float(np.clip(0.4 + 0.3 * bien - 0.5 * mal - 0.4 * oscuro, 0.0, 1.0))
    if tipo in NUCLEO and not any(_tiene(w, p) for p in NUCLEO[tipo]):
        valor = min(valor, 0.4)                                      # sin palabra núcleo: no se elige
    return valor


def familia(ruta):
    """La «familia» de un archivo (su pack o su serie: «SoundBits - Hitting»): dos de la misma familia seguidos suenan repetidos."""
    partes = [p.strip() for p in Path(ruta).stem.split(' - ')]
    if len(partes) > 2:
        return ' - '.join(partes[:2]).lower()
    return re.sub(r'[\s_]*\d+$', '', Path(ruta).stem.lower())           # «Copy of Hit Slam Metal 04» → «copy of hit slam metal»


def candidatos(tipo, base=None, por_carpeta=30, extra=60):
    """Archivos de la biblioteca del autor para ese tipo, repartidos entre sus carpetas (no solo las primeras por orden alfabético) y, v5.37, los
    de TODO su material indexado (director_sonido_biblioteca: Film Score, ambientes, clics…) que encajan por su nombre. Sin `base` explícita."""
    salida = []
    for sub in CARPETAS.get(tipo, ()):
        d = (Path(base) if base else BIBLIOTECA_AUTOR) / sub
        if d.is_dir():
            todos = sorted(p for p in d.rglob('*') if p.suffix.lower() in EXT and p.is_file())
            paso = max(1, len(todos) // por_carpeta)
            salida += todos[::paso][:por_carpeta]
    if base is None and extra:
        try:
            import director_sonido_biblioteca as B
            ya = {str(p) for p in salida}
            salida += [Path(r) for r in B.de_categoria(tipo, extra) if r not in ya]
        except Exception:
            pass
    return salida


def elegir(lista, objetivo, usados=None):
    """El mejor candidato para `objetivo` {'tipo', 'dur', 'brillo' 0–1, 'energia' 0–1}: quality ≥ UMBRAL y luego duration_fit, spectral_fit,
    energy_fit y recent_similarity. Devuelve (ruta | None, ranking [(puntos, ruta, desglose)])."""
    usados = usados or {}
    familias = {}
    for r, n in usados.items():
        familias[familia(r)] = familias.get(familia(r), 0) + n
    ranking = []
    for ruta in lista:
        sem = semantica(ruta, objetivo.get('semantica') or objetivo.get('tipo'), objetivo.get('brillo'))
        if sem < 0.5:
            ranking.append((-1, str(ruta), {'semantic_fit': round(sem, 2), 'rechazado': ['no encaja con el diseño (por su nombre)']}))
            continue
        q = calidad(ruta, objetivo.get('tipo'))
        if q['score'] < UMBRAL:
            ranking.append((-1, str(ruta), {'quality': q['score'], 'rechazado': q['motivos']}))
            continue
        med = q['medidas']
        largo = objetivo.get('largo') or (float(objetivo.get('dur') or 0.5) + 0.2)
        estrictos = vetos_estrictos(med, objetivo.get('tipo'), ruta, largo) if objetivo.get('estricto') else []
        if estrictos:
            ranking.append((-1, str(ruta), {'quality': q['score'], 'rechazado': [f'VETO (Social): {v}' for v in estrictos]}))
            continue
        dur_u = med.get('duracion_util_s') or med.get('duracion') or 0.0
        tipo = objetivo.get('tipo')
        if tipo in ('golpe', 'tonal'):                               # la cola se recorta con fundido: basta con que tenga ataque y cuerpo
            dfit = 1.0 if 0.2 <= dur_u <= 4.0 else (0.6 if dur_u > 4.0 else dur_u / 0.2)
        elif tipo == 'riser':                                         # se usa el final: vale si dura al menos lo que hace falta
            dfit = float(min(1.0, dur_u / max(0.1, objetivo.get('dur', 1.0))))
        else:
            dfit = float(np.exp(-abs(np.log(max(dur_u, 0.02) / max(objetivo.get('dur', 0.5), 0.02)))))
        cent = med.get('centroide_hz') or 1500
        brillo = float(np.clip(np.log2(max(cent, 100) / 400.0) / 4.0, 0, 1))
        brillo_obj = 0.3 if tipo == 'golpe' else objetivo.get('brillo', 0.5)     # un golpe con cuerpo es oscuro por naturaleza
        sfit = 1.0 - abs(brillo - brillo_obj)
        efit = 1.0 - abs(float(np.clip((med.get('cresta_db', 12) - 6) / 14, 0, 1)) - objetivo.get('energia', 0.5))
        rep = 0.5 * usados.get(str(ruta), 0) + 0.15 * familias.get(familia(ruta), 0)
        tarde = 0.3 if tipo == 'whoosh' and (med.get('pico_s') or 0.0) > largo - 0.1 else 0.0   # (su pico se quedaría fuera del corte: mejor otro)
        puntos = 0.25 * sem + 0.25 * q['score'] / 100 + 0.25 * dfit + 0.15 * sfit + 0.1 * efit - rep - tarde
        ranking.append((round(puntos, 3), str(ruta), {'semantic_fit': round(sem, 2), 'quality': q['score'], 'duration_fit': round(dfit, 2),
                                                      'spectral_fit': round(sfit, 2), 'energy_fit': round(efit, 2), 'recent_similarity': round(rep, 2)}))
    ranking.sort(key=lambda r: -r[0])
    mejor = next((r[1] for r in ranking if r[0] >= 0), None)
    return mejor, ranking


def leer_para_mezcla(ruta, dur=None, fundido_s=0.03):
    """El archivo elegido como (2, n) a 48 kHz y LIMPIO (v5.39, todos los estilos): sin DC ni subgraves (paso alto 30 Hz), sin el silencio de
    delante (desde 5 ms antes de su ataque a −40 dB), con 3 ms de entrada en coseno (nunca un escalón al empezar), recortado a `dur` (si se da)
    con la cola que pida —hasta +0,3 s, hasta que sus 10 ms de RMS caigan 45 dB— y su fundido de salida (el mayor de `fundido_s` y el 25 % de lo
    que queda; sin `dur`, el archivo entero con `fundido_s`: el riser acaba en su clímax). Siempre una COPIA en memoria."""
    d = _leer(ruta, max_s=(dur or 10.0) + 1.0)
    if d is None:
        return None
    x = paso_alto(d[0] - d[0].mean(axis=1, keepdims=True), 30.0)
    a = np.abs(x).max(axis=0)
    if not a.size or a.max() <= 0:
        return None
    x = x[:, max(0, int(np.argmax(a >= 0.01 * a.max())) - int(0.005 * SR)):]
    fundido = fundido_s
    if dur:
        n0, tope = int(dur * SR), min(x.shape[1], int((dur + 0.3) * SR))
        if x.shape[1] > n0:
            e = 10 * np.log10(np.maximum(_movil((x.astype(np.float64) ** 2).mean(axis=0), 480), 0.0) + 1e-20)
            bajo = np.nonzero(e[n0:tope] <= e.max() - 45.0)[0]
            x = x[:, :n0 + int(bajo[0]) if bajo.size else tope]
        fundido = max(fundido_s, 0.25 * x.shape[1] / SR)
    x = np.array(x, np.float32)
    k = min(x.shape[1], int(0.003 * SR))
    x[:, :k] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))).astype(np.float32)
    k = min(x.shape[1], int(fundido * SR))
    if k:
        x[:, -k:] *= np.linspace(1, 0, k, dtype=np.float32)
    return x
