# CineCaptions · By Cinema Productions
# 1_codigo/efectos_visuales.py — efectos visuales que acompañan a los captions: intro, transiciones en los cortes e iconos flotantes en las frases clave.
"""
efectos_visuales.py  (v5.4.6)
-----------------------------
La página «Efectos» y GO ponen, junto a los captions, la música y los emojis, tres tipos de efecto sobre el video (siempre en pistas propias «FX-…»; V1/A1 y los
captions no se tocan):

  * INTRO       un clip sobre negro mezclado en «Screen» en el segundo 0 (la fuga de luz / un destello);
  * TRANSICIÓN  el mismo tipo de clip centrado en cada CORTE entre tomas (se detectan comparando fotogramas con PyAV);
  * ICONOS      composiciones de iconos (2_recursos/efectos/iconos/packN: sprites RGBA ya separados con preparar_efectos.py) que entran con desenfoque,
                flotan y salen, cuando el texto tiene una FRASE IMPORTANTE (números, avisos, preguntas, el gancho del principio…). Se animan aquí y se
                guardan como secuencia de PNG con transparencia a la resolución del timeline (igual que los emojis animados).

    plan = planificar(video, palabras, idioma, opciones)       -> {'eventos': [...], 'resumen': '…'} (todo en segundos desde el inicio del video)
    aplicar(plan, al_estado=None)                              -> (ok, mensaje): lo coloca en el timeline actual de Resolve (colocar_efectos.py corre DENTRO de Resolve)

Las opciones (Ajustes de la página Efectos) viven en las preferencias: fx_intro, fx_cortes, fx_cortes_cuanto, fx_iconos (lista de packs), fx_iconos_cuanto.
"""
import hashlib
import json
import math
import re
import shutil
import threading
import time
from pathlib import Path

REVISION = 'r3'                    # súbela si cambia la animación de los iconos: se rehacen las secuencias en caché
FPS_FX = 30
DUR_ICONOS_S = 3.0

# ----------------------------------------------------------------------------------------------------------------------- catálogo
INTROS = (('fuga_de_luz', 'Fuga de luz', 'Un destello de luz con colores que se apaga en el primer segundo.'),
          ('destello', 'Destello', 'Un fogonazo blanco corto y limpio.'))
TRANSICIONES = (('fuga_de_luz', 'Fuga de luz', 'Una fuga de luz que tapa el corte y se apaga.'),
                ('destello', 'Destello', 'Un fogonazo blanco que esconde el salto entre tomas.'))
PACKS_ICONOS = (('pack1', 'Destellos', 'Estrellas verdes brillantes: ideas, novedades y cosas buenas.'),
                ('pack2', 'Alertas', 'Señales de aviso amarillas: errores, ojo y cuidado.'),
                ('pack3', 'Prohibido', 'Botones rojos con X y cinta de precaución: lo que NO hay que hacer.'),
                ('pack4', 'Creador', 'Libreta, cámara y flechas: contenido, video y crecimiento.'))
# cuánto: (cada cuántos segundos como mínimo un efecto, tope por video)
CANTIDAD_CORTES = {'pocos': (9.0, 6), 'normal': (5.0, 12), 'todos': (1.6, 60)}
CANTIDAD_ICONOS = {'pocos': (18.0, 3), 'normal': (11.0, 6), 'muchos': (7.0, 12)}

# v5.4.7: los efectos vienen ACTIVADOS (el usuario los apaga en la página Efectos o con el chip «Visuales» de Inicio)
OPCIONES_POR_DEFECTO = {'fx_intro': 'fuga_de_luz', 'fx_intro_sonido': 'riser_1', 'fx_cortes': 'fuga_de_luz', 'fx_cortes_cuanto': 'pocos',
                        'fx_iconos_activo': True, 'fx_iconos': ['pack1', 'pack2', 'pack3', 'pack4'], 'fx_iconos_cuanto': 'normal',
                        'fx_iconos_palabras': {}, 'fx_iconos_extra': True}
SONIDO_INTRO_S = 3.0                          # como mucho, los últimos 3 s del sonido con contenido (el Riser 1 tiene ~1,75 s audibles)
SONIDO_INTRO_DB = -3.0

# palabras que hacen importante una frase y qué icono piden (es / en; el resto de idiomas usa solo números, preguntas y el gancho)
CLAVES_ALERTA = ('error', 'errores', 'mistake', 'mistakes', 'wrong', 'never', 'nunca', 'stop', 'evita', 'evitar', 'avoid', "don't", 'dont', 'cuidado', 'careful',
                 'warning', 'danger', 'peligro', 'problema', 'problem', 'problemas', 'mal', 'peor', 'worst', 'bad', 'ojo', 'atención', 'atencion', 'lose', 'pierdes',
                 'perder', 'no', 'jamás', 'jamas', 'riesgo', 'risk', 'fail', 'falla')
CLAVES_CREADOR = ('video', 'videos', 'vídeo', 'vídeos', 'contenido', 'content', 'cámara', 'camara', 'camera', 'youtube', 'canal', 'channel', 'guion', 'script', 'editar',
                  'edit', 'publicar', 'post', 'seguidores', 'followers', 'suscríbete', 'subscribe', 'viral', 'redes', 'social', 'instagram', 'tiktok', 'reels', 'crear',
                  'create', 'creator', 'creador', 'audiencia', 'audience')
CLAVES_BUENAS = ('nuevo', 'nueva', 'new', 'mejor', 'best', 'increíble', 'increible', 'amazing', 'secreto', 'secret', 'gratis', 'free', 'éxito', 'exito', 'success',
                 'perfecto', 'perfect', 'magia', 'magic', 'truco', 'trick', 'tip', 'clave', 'key', 'importante', 'important', 'único', 'unico', 'unique', 'luxury',
                 'lujo', 'ganar', 'win', 'wow', 'descubre', 'discover', 'imagina', 'imagine', 'listo', 'ready')
CLAVES_IMPORTANTES = CLAVES_ALERTA + CLAVES_CREADOR + CLAVES_BUENAS
# las palabras de fábrica de cada pack (el usuario las cambia en la página Efectos: clic en el pack)
PALABRAS_POR_DEFECTO = {
    'pack1': CLAVES_BUENAS,
    'pack2': ('error', 'errores', 'mistake', 'mistakes', 'wrong', 'warning', 'careful', 'cuidado', 'ojo', 'atención', 'atencion', 'problema', 'problemas', 'problem', 'problems',
              'peligro', 'danger', 'riesgo', 'risk', 'fail', 'falla', 'fallo'),
    'pack3': ('never', 'nunca', 'jamás', 'jamas', 'stop', "don't", 'dont', 'evita', 'evitar', 'avoid', 'peor', 'worst', 'bad', 'mal', 'lose', 'pierdes', 'perder'),
    'pack4': CLAVES_CREADOR,
}

CACHE = Path.home() / 'DaVinciSubtitles' / 'efectos_cache'
PLAN_JSON = Path.home() / 'DaVinciSubtitles' / 'efectos_plan.json'


def carpeta_efectos():
    try:
        from sfx_rules import base_recursos
        return Path(base_recursos()) / 'efectos'
    except Exception:
        return Path(__file__).resolve().parent.parent / '2_recursos' / 'efectos'


def opciones_guardadas():
    """Las opciones de la página Efectos (con los valores por defecto donde falte algo)."""
    op = dict(OPCIONES_POR_DEFECTO)
    try:
        import ajustes_ui
        p = ajustes_ui.leer_prefs()
        for k in OPCIONES_POR_DEFECTO:
            if k in p and p[k] is not None:
                op[k] = p[k]
    except Exception:
        pass
    if not isinstance(op.get('fx_iconos'), (list, tuple)):
        op['fx_iconos'] = []
    if not isinstance(op.get('fx_iconos_palabras'), dict):
        op['fx_iconos_palabras'] = {}
    return op


def activado():
    """El interruptor general (chip «Visuales» de Inicio)."""
    try:
        import ajustes_ui
        return bool(ajustes_ui.leer_prefs().get('go_efectos_visuales', True))
    except Exception:
        return True


def _clip(tipo, ident, formato):
    """El mp4 sobre negro (se mezcla en Screen) de una intro o transición: _v para vertical y cuadrado, _h para horizontal."""
    carpeta = carpeta_efectos() / ('intro' if tipo == 'intro' else 'corte')
    for base in (carpeta, carpeta_efectos() / 'corte'):
        r = base / f'{ident}_{formato}.mp4'
        if r.is_file():
            return r
    return None


# ----------------------------------------------------------------------------------------------------------------------- iconos animados
def _suave(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def _rebote(u, s=1.7):
    u = max(0.0, min(1.0, u)) - 1.0
    return u * u * ((s + 1) * u + s) + 1.0


_SPRITES = {}


def _sprites(pack):
    if pack not in _SPRITES:
        from PIL import Image
        carpeta = carpeta_efectos() / 'iconos' / pack
        datos = json.loads((carpeta / 'pack.json').read_text(encoding='utf-8'))
        lista = []
        for s in datos['sprites']:
            lista.append(dict(s, img=Image.open(carpeta / s['archivo']).convert('RGBA')))
        _SPRITES[pack] = (datos['base'], lista)
    return _SPRITES[pack]


def _estado(i, t, borde, dur, fase):
    """(escala, giro°, dx, dy, opacidad, desenfoque, deslizamiento) del icono i en el instante t de la secuencia."""
    entrada, salida = 0.55, 0.42
    tt = t - 0.09 * i
    if tt <= 0:
        return 1.0, 0.0, 0.0, 0.0, 0.0, 24.0, 1.0
    u = tt / entrada
    esc, giro, op, desen, desliza = 1.0, 0.0, 1.0, 0.0, 0.0
    if u < 1.0:
        e = _rebote(u)
        op = min(1.0, u * 3.2)
        desen = (1.0 - _suave(u)) * 22.0
        if borde:
            desliza = 1.0 - _suave(u)
        else:
            esc = 0.35 + 0.65 * e
            giro = (1.0 - _suave(u)) * (14.0 if i % 2 == 0 else -14.0)
    # a flote
    dy = 7.0 * math.sin(2 * math.pi * (t / 2.4 + fase))
    dx = 4.0 * math.sin(2 * math.pi * (t / 3.1 + fase * 1.7))
    if not borde:
        giro += 2.6 * math.sin(2 * math.pi * (t / 2.9 + fase))
    else:
        dx, dy = dx * 0.4, dy * 0.4
    # salida
    ini_sal = dur - salida
    if t > ini_sal:
        v = _suave((t - ini_sal) / salida)
        op *= 1.0 - v
        desen = max(desen, v * 16.0)
        if borde:
            desliza = max(desliza, v * 0.9)
        else:
            esc *= 1.0 - 0.14 * v
    return esc, giro, dx, dy, max(0.0, min(1.0, op)), desen, desliza


def _componer_frame(base_w, base_h, W, H, sprites, t, dur, variante):
    from PIL import Image, ImageFilter
    lienzo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    corto = min(W, H)
    k = corto / float(min(base_w, base_h))
    for i, s in enumerate(sprites):
        borde = s.get('borde') or []
        img = s['_base']
        esc, giro, dx, dy, op, desen, desliza = _estado(i, t, borde, dur, s['_fase'])
        if op <= 0.003:
            continue
        w0, h0 = img.size
        w1, h1 = max(2, int(w0 * esc)), max(2, int(h0 * esc))
        im = img if (w1, h1) == (w0, h0) else img.resize((w1, h1), Image.Resampling.BICUBIC)
        if abs(giro) > 0.15:
            im = im.rotate(giro, resample=Image.Resampling.BICUBIC, expand=True)
        if desen > 0.6:
            pad = int(desen * 2.5) + 2
            marco = Image.new('RGBa', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
            marco.paste(im, (pad, pad))
            im = marco.filter(ImageFilter.GaussianBlur(desen))
        if op < 0.995:
            im = Image.blend(Image.new('RGBa', im.size, (0, 0, 0, 0)), im, op)
        # posición: el centro del icono (fracciones del cuadro), pegado a su borde si lo toca
        cx, cy = s['cx'] * W, s['cy'] * H
        ancho_i, alto_i = s['_base'].size
        if 'izq' in borde and 'der' not in borde:
            cx = ancho_i / 2.0
        if 'der' in borde and 'izq' not in borde:
            cx = W - ancho_i / 2.0
        if 'arriba' in borde and 'abajo' not in borde:
            cy = alto_i / 2.0
        if 'abajo' in borde and 'arriba' not in borde:
            cy = H - alto_i / 2.0
        if 'izq' in borde and 'der' in borde:
            cx = W / 2.0
        if 'arriba' in borde and 'abajo' in borde:
            cy = H / 2.0
        if desliza:
            vx = (-1 if 'izq' in borde else 0) + (1 if 'der' in borde else 0)
            vy = (-1 if 'arriba' in borde else 0) + (1 if 'abajo' in borde else 0)
            if vx == 0 and vy == 0:
                vy = 1
            cx += vx * desliza * ancho_i * 0.45
            cy += vy * desliza * alto_i * 0.45
        if variante % 2 == 1:                       # variante 1: reflejada horizontalmente
            cx = W - cx
        x, y = int(round(cx + dx - im.width / 2.0)), int(round(cy + dy - im.height / 2.0))
        im = im.convert('RGBA')
        # recorte si se sale del lienzo
        ix0, iy0 = max(0, -x), max(0, -y)
        ix1, iy1 = min(im.width, W - x), min(im.height, H - y)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        lienzo.alpha_composite(im, (x + ix0, y + iy0), (ix0, iy0, ix1, iy1))
    return lienzo


def secuencia_iconos(pack, ancho, alto, variante=0, al_estado=None):
    """La secuencia de PNG con transparencia (DUR_ICONOS_S a FPS_FX) de un pack de iconos a la resolución ancho×alto. Devuelve {'patron', 'n', 'dur'} o None."""
    from PIL import Image
    n = int(round(DUR_ICONOS_S * FPS_FX))
    carpeta = CACHE / f'iconos_{pack}_{ancho}x{alto}_v{variante % 2}_{FPS_FX}_{REVISION}'
    patron = carpeta / 'f_%04d.png'
    if carpeta.is_dir() and all((carpeta / f'f_{k:04d}.png').is_file() for k in range(1, n + 1)):
        return {'patron': str(patron), 'n': n, 'dur': DUR_ICONOS_S}
    try:
        (base_w, base_h), sprites = _sprites(pack)
    except Exception:
        return None
    k = min(ancho, alto) / float(min(base_w, base_h))
    trabajo = []
    for i, s in enumerate(sprites):
        copia = dict(s)
        im = s['img']
        borde = s.get('borde') or []
        w, h = max(2, int(round(im.width * k))), max(2, int(round(im.height * k)))
        if 'izq' in borde and 'der' in borde:          # un trazo de lado a lado: ocupa todo el ancho del cuadro
            w = ancho
        if 'arriba' in borde and 'abajo' in borde:
            h = alto
        base = im.resize((w, h), Image.Resampling.LANCZOS).convert('RGBa')
        copia['_base'] = base
        copia['_fase'] = (i * 0.37) % 1.0
        trabajo.append(copia)
    tmp = carpeta.with_name(carpeta.name + '_tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True, exist_ok=True)
    for f in range(n):
        t = f / float(FPS_FX)
        cuadro = _componer_frame(base_w, base_h, ancho, alto, trabajo, t, DUR_ICONOS_S, variante)
        cuadro.save(tmp / f'f_{f + 1:04d}.png', compress_level=6)
        if al_estado and f % 15 == 0:
            try:
                al_estado(f'{pack} {f}/{n}')
            except Exception:
                pass
    shutil.rmtree(carpeta, ignore_errors=True)
    tmp.rename(carpeta)
    limpiar_cache()
    return {'patron': str(patron), 'n': n, 'dur': DUR_ICONOS_S}


def limpiar_cache(maximo_mb=700):
    """Las secuencias de otra revisión se borran y, si la caché pasa de `maximo_mb`, las más viejas (se rehacen solas al hacer falta)."""
    try:
        carpetas = [c for c in CACHE.iterdir() if c.is_dir()]
        for c in carpetas:
            if not c.name.endswith(REVISION) and not c.name.endswith('_tmp'):
                shutil.rmtree(c, ignore_errors=True)
        vivas = sorted((c for c in CACHE.iterdir() if c.is_dir()), key=lambda c: c.stat().st_mtime)
        total = sum(f.stat().st_size for c in vivas for f in c.glob('*.png')) / 1e6
        while vivas and total > maximo_mb:
            viejo = vivas.pop(0)
            total -= sum(f.stat().st_size for f in viejo.glob('*.png')) / 1e6
            shutil.rmtree(viejo, ignore_errors=True)
    except Exception:
        pass


# ----------------------------------------------------------------------------------------------------------------------- cortes entre tomas
def duracion_video(video):
    """Lo que dura el video (s); 0.0 si no se puede leer."""
    try:
        import av
        with av.open(str(video)) as c:
            if c.duration:
                return float(c.duration) / 1_000_000.0
            s = c.streams.video[0]
            return float(s.duration * s.time_base) if s.duration else 0.0
    except Exception:
        return 0.0


def detectar_cortes(video, al_progreso=None, tope_s=None):
    """Los instantes (s) donde la imagen salta de una toma a otra. Compara cada fotograma, reducido a 48×86 en grises, con el anterior: un salto muy por encima de
    lo normal del momento (movimiento de cámara incluido) es un corte. Devuelve [(t, fuerza)]."""
    import av
    import numpy as np
    cortes = []
    try:
        c = av.open(str(video))
    except Exception:
        return cortes
    try:
        s = c.streams.video[0]
        s.thread_type = 'AUTO'
        total = float(s.duration * s.time_base) if s.duration else (float(c.duration) / 1_000_000.0 if c.duration else 0.0)
        previo = None
        recientes = []
        ultimo_corte = -9.0
        for fr in c.decode(s):
            t = float(fr.pts * s.time_base) if fr.pts is not None else None
            if t is None:
                continue
            if tope_s and t > tope_s:
                break
            g = fr.reformat(width=48, height=86, format='gray').to_ndarray().astype(np.float32)
            if previo is not None:
                d = float(np.abs(g - previo).mean())
                med = float(np.median(recientes)) if recientes else 0.0
                # corte = salto grande en absoluto Y varias veces mayor que el movimiento normal reciente
                if d > 20.0 and d > 3.2 * max(med, 2.0) and (t - ultimo_corte) > 0.6:
                    cortes.append((round(t, 3), round(d, 1)))
                    ultimo_corte = t
                else:
                    recientes.append(d)
                    if len(recientes) > 18:
                        recientes.pop(0)
            previo = g
            if al_progreso and total:
                try:
                    al_progreso(min(1.0, t / total))
                except Exception:
                    pass
    except Exception:
        pass
    finally:
        try:
            c.close()
        except Exception:
            pass
    return cortes


def elegir_cortes(cortes, duracion, cuanto='pocos', margen_ini=1.4, margen_fin=1.2):
    """De todos los cortes, los que llevan transición: los más fuertes, separados lo que pida «cuánto» y lejos de la intro y del final."""
    sep, tope = CANTIDAD_CORTES.get(cuanto, CANTIDAD_CORTES['pocos'])
    candidatos = [(t, f) for t, f in cortes if margen_ini <= t <= max(margen_ini, duracion - margen_fin)]
    elegidos = []
    for t, f in sorted(candidatos, key=lambda c: -c[1]):
        if len(elegidos) >= tope:
            break
        if all(abs(t - e) >= sep for e in elegidos):
            elegidos.append(t)
    return sorted(elegidos)


# ----------------------------------------------------------------------------------------------------------------------- frases importantes
def _texto_palabra(p):
    return str(p.get('word') or p.get('text') or p.get('palabra') or '').strip()


def partir_en_frases(palabras, pausa=0.7):
    """Frases = trozos de palabras que acaban en . ? ! … o en una pausa larga. Cada una: {'ini','fin','texto','pregunta','palabras'}."""
    frases, actual = [], []

    def cerrar():
        nonlocal actual
        if actual:
            texto = ' '.join(_texto_palabra(p) for p in actual).strip()
            frases.append({'ini': float(actual[0].get('start', 0.0)), 'fin': float(actual[-1].get('end', 0.0)), 'texto': texto, 'pregunta': texto.rstrip().endswith('?'),
                           'palabras': len(actual)})
            actual = []
    for k, p in enumerate(palabras):
        actual.append(p)
        t = _texto_palabra(p)
        siguiente = palabras[k + 1] if k + 1 < len(palabras) else None
        hueco = (float(siguiente.get('start', 0.0)) - float(p.get('end', 0.0))) if siguiente else 99.0
        if re.search(r'[.?!…]["”\')]*$', t) or p.get('fin_frase') or hueco >= pausa or len(actual) >= 22:
            cerrar()
    cerrar()
    return frases


def _normal(w):
    return re.sub(r"[^\wáéíóúüñ']", '', w.lower())


def clase_de_frase(frase):
    """'alerta' | 'creador' | 'buena' | None: el tipo de icono que pide el texto."""
    ws = {_normal(w) for w in frase['texto'].split()}
    if ws & set(CLAVES_ALERTA):
        return 'alerta'
    if ws & set(CLAVES_CREADOR):
        return 'creador'
    if ws & set(CLAVES_BUENAS):
        return 'buena'
    return None


def puntuar_frase(frase, es_primera=False):
    texto = frase['texto']
    ws = [_normal(w) for w in texto.split()]
    puntos = 0.0
    if re.search(r'\d', texto):
        puntos += 3.0
    puntos += min(4.0, 2.0 * sum(1 for w in ws if w in CLAVES_IMPORTANTES))
    if frase.get('pregunta'):
        puntos += 2.0
    if es_primera:
        puntos += 2.0
    if 4 <= frase['palabras'] <= 14:
        puntos += 1.0
    if frase['palabras'] < 3:
        puntos -= 3.0
    return puntos


def elegir_frases(palabras, duracion, cuanto='normal', margen_ini=1.0, margen_fin=3.2):
    """Las frases donde poner un icono flotante: las más importantes, separadas y sin pisar el inicio ni el final. Devuelve [{'ini','fin','texto','clase'}]."""
    sep, tope = CANTIDAD_ICONOS.get(cuanto, CANTIDAD_ICONOS['normal'])
    frases = partir_en_frases(palabras)
    if not frases:
        return []
    tope_por_duracion = max(1, int(round(duracion / sep))) if duracion else tope
    cuantas = max(1, min(tope, tope_por_duracion))
    puntuadas = [(puntuar_frase(f, k == 0), k, f) for k, f in enumerate(frases) if f['ini'] >= margen_ini and f['ini'] <= max(margen_ini, duracion - margen_fin)]
    elegidas = []
    for pts, k, f in sorted(puntuadas, key=lambda x: (-x[0], x[1])):
        if len(elegidas) >= cuantas:
            break
        if pts <= 0 and elegidas:
            break
        if all(abs(f['ini'] - e['ini']) >= sep * 0.7 for e in elegidas):
            elegidas.append(dict(f, clase=clase_de_frase(f)))
    return sorted(elegidas, key=lambda e: e['ini'])


def _pack_para(clase, permitidos, usados):
    """El pack de iconos que pide la clase de frase (entre los que el usuario dejó activos); si no hay, rotando."""
    mapa = {'alerta': ('pack2', 'pack3'), 'creador': ('pack4',), 'buena': ('pack1',)}
    for p in mapa.get(clase, ()):
        if p in permitidos and usados.get(p, 0) <= min(usados.get(q, 0) for q in permitidos):
            return p
    for p in sorted(permitidos, key=lambda q: usados.get(q, 0)):
        return p
    return None


# ----------------------------------------------------------------------------------------------------------------------- sonido de la intro
def fuente_sonido_intro(op=None):
    """El archivo de sonido de la intro según las preferencias: el Riser 1 que trae el programa, el que eligió el usuario, o None si está silenciado."""
    op = op or opciones_guardadas()
    v = str(op.get('fx_intro_sonido') if op.get('fx_intro_sonido') is not None else 'riser_1').strip()
    if v.lower() in ('', 'ninguno', 'none', 'mute'):
        return None
    if v == 'riser_1':
        r = carpeta_efectos() / 'sonidos' / 'riser_1.mp3'
        return r if r.is_file() else None
    r = Path(v)
    return r if r.is_file() else None


def nombre_sonido_intro(op=None):
    f = fuente_sonido_intro(op)
    if f is None:
        return ''
    return 'Riser 1' if f.name == 'riser_1.mp3' else f.stem


def _decodificar_audio(ruta, rate=48000):
    import av
    import numpy as np
    partes = []
    with av.open(str(ruta)) as c:
        s = c.streams.audio[0]
        res = av.AudioResampler(format='fltp', layout='stereo', rate=rate)
        for fr in c.decode(s):
            salida = res.resample(fr)
            for r in (salida if isinstance(salida, (list, tuple)) else [salida]):
                if r is not None:
                    partes.append(r.to_ndarray())
        resto = res.resample(None)
        for r in (resto if isinstance(resto, (list, tuple)) else [resto]):
            if r is not None:
                partes.append(r.to_ndarray())
    return np.concatenate(partes, axis=1) if partes else np.zeros((2, 0), dtype=np.float32)


def preparar_sonido_intro(ruta, maximo_s=SONIDO_INTRO_S, db=SONIDO_INTRO_DB, rate=48000):
    """Los ÚLTIMOS `maximo_s` segundos CON CONTENIDO del sonido (sin el silencio del principio ni el del final: el Riser 1 tiene ~1,25 s de nada al empezar y ~2 s al
    acabar), con un fundido de entrada de 15 ms, uno de salida de 40 ms y `db` de ganancia, como WAV estéreo de 48 kHz en la caché. Devuelve (ruta_wav, duración_s) o (None, 0)."""
    import wave
    import numpy as np
    ruta = Path(ruta)
    try:
        clave = hashlib.md5(f'{ruta.resolve()}|{ruta.stat().st_mtime_ns}|{maximo_s}|{db}|{REVISION}'.encode('utf-8')).hexdigest()[:12]
    except OSError:
        return None, 0.0
    destino = CACHE / f'sonido_intro_{clave}.wav'
    if destino.is_file() and destino.stat().st_size > 1000:
        try:
            with wave.open(str(destino), 'rb') as w:
                return str(destino), w.getnframes() / float(w.getframerate())
        except Exception:
            pass
    try:
        a = _decodificar_audio(ruta, rate)
    except Exception:
        return None, 0.0
    if a.shape[1] == 0:
        return None, 0.0
    pico = float(np.abs(a).max())
    if pico <= 1e-6:
        return None, 0.0
    umbral = pico * (10.0 ** (-45.0 / 20.0))
    activo = np.nonzero(np.abs(a).max(axis=0) > umbral)[0]
    if len(activo) == 0:
        return None, 0.0
    fin = int(activo[-1]) + 1
    ini = max(int(activo[0]), fin - int(maximo_s * rate))
    t = a[:, ini:fin].copy()
    n = t.shape[1]
    f_in, f_out = min(n // 4, int(0.015 * rate)), min(n // 4, int(0.040 * rate))
    if f_in > 0:
        t[:, :f_in] *= np.linspace(0.0, 1.0, f_in, dtype=np.float32)
    if f_out > 0:
        t[:, -f_out:] *= np.linspace(1.0, 0.0, f_out, dtype=np.float32)
    t *= 10.0 ** (db / 20.0)
    pcm = (np.clip(t, -1.0, 1.0) * 32767.0).astype('<i2').T.copy()          # (muestras, canales) intercalado
    CACHE.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return str(destino), n / float(rate)


def oir_sonido_intro(op=None):
    """Reproduce (sin bloquear) el sonido de la intro tal como va a sonar. Devuelve True si pudo."""
    import subprocess
    import sys
    f = fuente_sonido_intro(op)
    if f is None:
        return False
    wav, _dur = preparar_sonido_intro(f)
    if not wav:
        return False
    try:
        if sys.platform.startswith('win'):
            import winsound
            winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == 'darwin':
            subprocess.Popen(['afplay', wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return False
        return True
    except Exception:
        return False


# ----------------------------------------------------------------------------------------------------------------------- palabras que activan los iconos
def palabras_de_pack(pack, op=None):
    """Las palabras que hacen aparecer ese pack: las del usuario si las cambió, si no las de fábrica."""
    op = op or opciones_guardadas()
    propias = (op.get('fx_iconos_palabras') or {}).get(pack)
    if isinstance(propias, (list, tuple)):
        return [str(p) for p in propias if str(p).strip()]
    return list(PALABRAS_POR_DEFECTO.get(pack, ()))


def _frases_de_palabras(lista):
    """['no hagas', 'Error'] -> [('no','hagas'), ('error',)] (cada entrada puede ser una palabra o una frase corta)."""
    salida = []
    for p in lista:
        toks = tuple(t for t in (_normal(x) for x in str(p).split()) if t)
        if toks:
            salida.append(toks)
    return salida


def coincidencias_de_palabras(palabras, packs, op=None):
    """Cada vez que se dice una palabra (o frase) activadora de un pack activo: [{'ini', 'pack', 'texto'}], en orden de tiempo."""
    op = op or opciones_guardadas()
    tokens = [_normal(_texto_palabra(p)) for p in palabras]
    listas = {pk: _frases_de_palabras(palabras_de_pack(pk, op)) for pk in packs}
    salida = []
    for i, tok in enumerate(tokens):
        if not tok:
            continue
        for pk, frases in listas.items():
            for toks in frases:
                if tuple(tokens[i:i + len(toks)]) == toks:
                    salida.append({'ini': float(palabras[i].get('start', 0.0)), 'pack': pk, 'texto': ' '.join(toks)})
                    break
    return salida


def _separar(candidatos, ya, sep, cuantas):
    """Elige hasta `cuantas` candidatos {'ini'} separados al menos `sep` s de los ya elegidos y entre sí, repartidos por todo el video (el siguiente es el más lejos de los ya
    puestos, no el más cercano al principio)."""
    elegidos = list(ya)
    pendientes = sorted(candidatos, key=lambda c: c['ini'])
    nuevos = []
    while pendientes and len(elegidos) < cuantas:
        validos = [c for c in pendientes if all(abs(c['ini'] - e['ini']) >= sep for e in elegidos)]
        if not validos:
            break
        if not elegidos:
            mejor = validos[0]
        else:
            mejor = max(validos, key=lambda c: min(abs(c['ini'] - e['ini']) for e in elegidos))
        elegidos.append(mejor)
        nuevos.append(mejor)
        pendientes = [c for c in pendientes if c is not mejor]
    return nuevos


def _pack_de_frase(frase, packs, op, usados):
    """El pack de una frase importante: el que más palabras suyas tiene en ella; si ninguno, rotando entre los activos."""
    toks = [_normal(w) for w in frase['texto'].split()]
    mejor, mejor_n = None, 0
    for pk in packs:
        n = 0
        for tt in _frases_de_palabras(palabras_de_pack(pk, op)):
            if any(tuple(toks[i:i + len(tt)]) == tt for i in range(len(toks))):
                n += 1
        if n > mejor_n:
            mejor, mejor_n = pk, n
    if mejor is not None:
        return mejor
    return sorted(packs, key=lambda q: (usados.get(q, 0), q))[0] if packs else None


# ----------------------------------------------------------------------------------------------------------------------- el plan
def planificar(video, palabras, duracion=None, opciones=None, al_estado=None, cortes=None):
    """Qué efecto va dónde. `palabras`: [{'word','start','end'}]. Devuelve {'eventos': [{'tipo','ini','asset'…}], 'duracion', 'resumen'}."""
    op = dict(opciones_guardadas())
    op.update(opciones or {})
    eventos = []
    resumen = []
    if duracion is None:
        duracion = duracion_video(video) if video else 0.0
        if palabras:
            duracion = max(duracion, float(palabras[-1].get('end', 0.0)))
    # el sonido de la intro (los últimos segundos con contenido del Riser 1, o el que eligió el usuario; silenciable). El riser SUBE: el destello cae justo al acabar
    # el sonido, no antes (con el sonido silenciado, el destello va en el segundo 0 como siempre).
    intro_ini = 0.0
    fuente = fuente_sonido_intro(op)
    if fuente is not None:
        try:
            wav, dur_s = preparar_sonido_intro(fuente)
        except Exception:
            wav, dur_s = None, 0.0
        if wav and dur_s > 0.2 and (not duracion or dur_s < duracion * 0.6):
            eventos.append({'tipo': 'sonido', 'ini': 0.0, 'archivo': wav, 'dur': round(dur_s, 3), 'asset': nombre_sonido_intro(op)})
            intro_ini = round(dur_s, 2) if op.get('fx_intro') else 0.0
            resumen.append('sonido de intro')
    if op.get('fx_intro'):
        eventos.append({'tipo': 'intro', 'ini': intro_ini, 'asset': op['fx_intro']})
        resumen.append('intro')
    if op.get('fx_cortes') and video:
        if al_estado:
            al_estado('Buscando los cortes entre tomas…')
        todos = cortes if cortes is not None else detectar_cortes(video)
        elegidos = elegir_cortes(todos, duracion or 0.0, op.get('fx_cortes_cuanto', 'pocos'))
        for t in elegidos:
            eventos.append({'tipo': 'corte', 'ini': float(t), 'asset': op['fx_cortes']})
        resumen.append(f'{len(elegidos)} de {len(todos)} cortes')
    packs = [p for p in (op.get('fx_iconos') or []) if p in {x[0] for x in PACKS_ICONOS}]
    if op.get('fx_iconos_activo', True) and packs and palabras:
        sep, tope = CANTIDAD_ICONOS.get(op.get('fx_iconos_cuanto', 'normal'), CANTIDAD_ICONOS['normal'])
        cuantas = max(1, min(tope, int(round((duracion or 0.0) / sep)) if duracion else tope))
        margen_ini, margen_fin = 1.0, 3.2
        dentro = lambda t: margen_ini <= t <= max(margen_ini, (duracion or t) - margen_fin)
        sep_min = max(3.2, sep * 0.5)
        # 1) las palabras que el usuario (o la fábrica) asignó a cada pack: el icono sale cuando se dice
        activadas = [dict(c, ini=max(0.0, c['ini'] - 0.05)) for c in coincidencias_de_palabras(palabras, packs, op) if dentro(c['ini'])]
        elegidas = _separar(activadas, [], sep_min, cuantas)
        # 2) con «también en frases importantes», lo que falte se completa con las frases que importan (números, preguntas, el gancho…)
        extra = []
        if op.get('fx_iconos_extra', True) and len(elegidas) < cuantas:
            frases = elegir_frases(palabras, duracion or 0.0, op.get('fx_iconos_cuanto', 'normal'))
            usados0 = {p: sum(1 for e in elegidas if e['pack'] == p) for p in packs}
            cand = []
            for f in frases:
                pk = _pack_de_frase(f, packs, op, usados0)
                if pk is not None:
                    usados0[pk] = usados0.get(pk, 0) + 1
                    cand.append({'ini': float(f['ini']), 'pack': pk, 'texto': f['texto'][:80], 'frase': True})
            extra = _separar(cand, elegidas, sep_min, cuantas)
        total = sorted(elegidas + extra, key=lambda c: c['ini'])
        for k, c in enumerate(total):
            eventos.append({'tipo': 'icono', 'ini': round(c['ini'], 3), 'asset': c['pack'], 'variante': k % 2, 'frase': c.get('texto', ''), 'por': 'frase' if c.get('frase') else 'palabra'})
        resumen.append(f'{len(total)} iconos ({len(elegidas)} por palabra)')
    # los de un mismo tipo no se pisan en su pista
    eventos.sort(key=lambda e: (e['tipo'], e['ini']))
    return {'eventos': eventos, 'duracion': duracion, 'resumen': ', '.join(resumen)}


# ----------------------------------------------------------------------------------------------------------------------- Resolve
_INFO_TIMELINE = r"""
tl = project.GetCurrentTimeline()
res = {'proyecto': project.GetName(), 'timeline': tl.GetName() if tl else None}
if tl:
    res['fps'] = float(tl.GetSetting('timelineFrameRate') or 30)
    res['ancho'] = int(float(tl.GetSetting('timelineResolutionWidth') or 1080))
    res['alto'] = int(float(tl.GetSetting('timelineResolutionHeight') or 1920))
    res['inicio'] = int(tl.GetStartFrame())
result = res
"""


def aplicar(plan, al_estado=None, offset_frames=0):
    """Coloca el plan en el timeline ACTUAL de Resolve. Devuelve (ok, mensaje)."""
    import resolve_mcp
    eventos = (plan or {}).get('eventos') or []
    ok, info, err = resolve_mcp.script(_INFO_TIMELINE, timeout=40)
    if not ok or not (info or {}).get('timeline'):
        return False, f'No pude leer el timeline de Resolve: {err or info}'
    ancho, alto, fps = int(info['ancho']), int(info['alto']), float(info['fps'])
    formato = 'h' if ancho > alto * 1.2 else 'v'
    listos = []
    for e in eventos:
        e = dict(e)
        if e['tipo'] == 'sonido':
            if not e.get('archivo') or not Path(e['archivo']).is_file():
                continue
            e['modo'] = 'audio'
        elif e['tipo'] in ('intro', 'corte'):
            ruta = _clip(e['tipo'], e['asset'], formato)
            if ruta is None:
                continue
            e['archivo'] = str(ruta)
            e['modo'] = 'screen'
        else:
            if al_estado:
                al_estado(f"Preparando los iconos «{e['asset']}»…")
            sec = secuencia_iconos(e['asset'], ancho, alto, e.get('variante', 0))
            if sec is None:
                continue
            e['secuencia'] = sec
            e['modo'] = 'normal'
        listos.append(e)
    datos = {'eventos': listos, 'fps': fps, 'inicio': info['inicio'], 'offset_frames': int(offset_frames or 0)}
    PLAN_JSON.parent.mkdir(parents=True, exist_ok=True)
    try:
        import archivos_seguros
        archivos_seguros.escribir_json(PLAN_JSON, datos)
    except Exception:
        PLAN_JSON.write_text(json.dumps(datos, ensure_ascii=False), encoding='utf-8')
    if al_estado:
        al_estado('Colocando los efectos en Resolve…')
    script = carpeta_efectos() / 'colocar_efectos.py'
    return resolve_mcp.ejecutar_py(script, timeout=300)
