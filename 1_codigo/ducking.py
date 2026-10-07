# CineCaptions · By Cinema Productions
# 1_codigo/ducking.py — baja la música sola mientras hay voz (ducking), calculado desde las palabras de la transcripción.
"""
Resolve no deja cambiar el volumen de un clip por script, así que el ducking se HORNEA en una copia de la música: un WAV con la
ganancia ya aplicada (baja ~14 dB un instante antes de cada frase y vuelve a subir despacio al terminar). Esa copia es la que se
pone en la línea de tiempo.

    intervalos_de_voz(palabras)            [(inicio, fin)] de las frases (palabras separadas por menos de 'union' s van juntas)
    curva_de_ganancia(intervalos, duracion) ganancia 0..1 a 100 valores/s (ataque y relajación suaves)
    aplicar(ruta_musica, palabras, destino) escribe el WAV (estéreo, 48 kHz) y devuelve su ruta
"""
import wave
from pathlib import Path

import numpy as np

CARPETA_SALIDA = Path.home() / 'DaVinciSubtitles' / 'musica_ducking'
TASA = 48000
PASO = 100                  # valores de la curva por segundo
DB_BAJA = -14.0             # cuanto baja la musica con voz
ADELANTO_S = 0.12           # empieza a bajar un poco ANTES de la primera palabra
ATAQUE_S = 0.10             # tiempo en bajar
RELAJACION_S = 0.55         # tiempo en volver a subir
UNION_S = 0.40              # pausas mas cortas que esto no dejan subir la musica


def intervalos_de_voz(palabras, union=UNION_S):
    """[(inicio, fin)] de lo que se habla; palabras casi pegadas forman UNA frase."""
    marcas = sorted((float(p.get('start') or 0.0), float(p.get('end') or p.get('start') or 0.0)) for p in palabras
                    if str(p.get('word', p.get('texto', ''))).strip())
    salida = []
    for a, b in marcas:
        b = max(a, b)
        if salida and a - salida[-1][1] <= union:
            salida[-1] = (salida[-1][0], max(salida[-1][1], b))
        else:
            salida.append((a, b))
    return salida


def curva_de_ganancia(intervalos, duracion, db_baja=DB_BAJA, adelanto=ADELANTO_S, ataque=ATAQUE_S, relajacion=RELAJACION_S):
    """Un valor de ganancia (1.0 = sin tocar) cada 1/PASO s, suavizado: baja rapido y sube despacio."""
    n = int(np.ceil(max(0.0, duracion) * PASO)) + 2
    objetivo = np.ones(n, dtype=np.float64)
    minimo = 10 ** (db_baja / 20.0)
    for a, b in intervalos:
        i = max(0, int((a - adelanto) * PASO))
        j = min(n, int(np.ceil(b * PASO)) + 1)
        if j > i:
            objetivo[i:j] = minimo
    # filtro de un polo con constantes distintas al bajar (ataque) y al subir (relajacion)
    ga = 1.0 - np.exp(-1.0 / (PASO * max(0.01, ataque)))
    gr = 1.0 - np.exp(-1.0 / (PASO * max(0.01, relajacion)))
    curva = np.empty(n, dtype=np.float64)
    actual = 1.0
    for k in range(n):
        t = objetivo[k]
        actual += (t - actual) * (ga if t < actual else gr)
        curva[k] = actual
    return curva


def _cargar_estereo(ruta):
    """(audio float32 [n, 2], tasa) de cualquier archivo que PyAV o wave sepan abrir."""
    try:
        import av
        cont = av.open(str(ruta))
        flujo = next(s for s in cont.streams if s.type == 'audio')
        res = av.audio.resampler.AudioResampler(format='s16', layout='stereo', rate=TASA)
        trozos = []
        for frame in cont.decode(flujo):
            for r in res.resample(frame):
                trozos.append(r.to_ndarray().reshape(-1, 2))
        for r in res.resample(None):
            trozos.append(r.to_ndarray().reshape(-1, 2))
        cont.close()
        if trozos:
            return np.concatenate(trozos).astype(np.float32) / 32768.0, TASA
    except Exception:
        pass
    with wave.open(str(ruta), 'rb') as w:
        canales, ancho, tasa, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        crudo = w.readframes(n)
    tipo = {1: np.uint8, 2: np.int16, 4: np.int32}[ancho]
    datos = np.frombuffer(crudo, dtype=tipo).astype(np.float32)
    if ancho == 1:
        datos = (datos - 128.0) / 128.0
    else:
        datos /= float(2 ** (8 * ancho - 1))
    datos = datos.reshape(-1, canales)
    if canales == 1:
        datos = np.repeat(datos, 2, axis=1)
    return datos[:, :2], tasa


def aplicar(ruta_musica, palabras, destino=None, db_baja=DB_BAJA):
    """Escribe la musica con ducking y devuelve la ruta del WAV. Lanza si el audio no se puede abrir."""
    audio, tasa = _cargar_estereo(ruta_musica)
    duracion = len(audio) / float(tasa)
    curva = curva_de_ganancia(intervalos_de_voz(palabras), duracion, db_baja=db_baja)
    t_curva = np.arange(len(curva)) / float(PASO)
    t_audio = np.arange(len(audio)) / float(tasa)
    ganancia = np.interp(t_audio, t_curva, curva).astype(np.float32)
    salida = np.clip(audio * ganancia[:, None], -1.0, 1.0)
    if destino is None:
        CARPETA_SALIDA.mkdir(parents=True, exist_ok=True)
        destino = CARPETA_SALIDA / (Path(ruta_musica).stem + '_ducking.wav')
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(tasa)
        w.writeframes((salida * 32767.0).astype(np.int16).tobytes())
    return destino


if __name__ == '__main__':
    pal = [{'word': 'a', 'start': 1.0, 'end': 1.3}, {'word': 'b', 'start': 1.4, 'end': 1.8}, {'word': 'c', 'start': 4.0, 'end': 4.4}]
    iv = intervalos_de_voz(pal)
    assert iv == [(1.0, 1.8), (4.0, 4.4)], iv
    c = curva_de_ganancia(iv, 6.0)
    assert c[50] > 0.95 and c[150] < 0.3 and c[350] > 0.95 and c[420] < 0.3, (c[50], c[150], c[350], c[420])
    print('ok')
