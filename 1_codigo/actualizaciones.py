# CineCaptions · By Cinema Productions
# 1_codigo/actualizaciones.py — «Buscar actualizaciones» y canal beta (lee un version.json publicado en internet).
"""
actualizaciones.py
------------------
«Buscar actualizaciones» y «Recibir versiones beta» (Ajustes > Acerca de).

El programa lee un archivo version.json publicado en internet:

    {
      "estable": {"version": "5.1.0", "url": "https://.../Instalar_CineCaptions.exe",
                  "notas": "Lo nuevo en una o dos lineas"},
      "beta":    {"version": "5.2.0-beta.1", "url": "...", "notas": "..."}
    }

Mientras URL_MANIFIESTO este vacia (todavia no hay un sitio donde publicar
las versiones) el boton lo dice tal cual, sin inventarse que esta al dia.
"""
import json
import re
import ssl
import urllib.request

# Pon aqui la direccion de tu version.json (GitHub, tu web...) y recompila.
URL_MANIFIESTO = ''


def _partes(v):
    """'5.2.0-beta.3' -> (5, 2, 0, 0, 3): una beta va antes que su estable."""
    m = re.match(r'(\d+)\.(\d+)\.(\d+)(?:-beta\.?(\d+))?', str(v or '').strip())
    if not m:
        return (0, 0, 0, 1, 0)
    a, b, c, beta = m.groups()
    return (int(a), int(b), int(c), 0 if beta is not None else 1, int(beta or 0))


def es_mas_nueva(remota, local):
    return _partes(remota) > _partes(local)


def configurado():
    return bool(URL_MANIFIESTO)


def comprobar(version_local, canal_beta=False, timeout=12):
    """{'estado': 'al_dia'|'nueva'|'sin_canal'|'error', 'version', 'url', 'notas', 'mensaje'}"""
    if not URL_MANIFIESTO:
        return {'estado': 'sin_canal'}
    try:
        try:
            import certifi
            contexto = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            contexto = None
        pedido = urllib.request.Request(URL_MANIFIESTO, headers={'User-Agent': f'CineCaptions/{version_local}'})
        with urllib.request.urlopen(pedido, timeout=timeout, context=contexto) as r:
            datos = json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'estado': 'error', 'mensaje': str(e)}
    candidatos = [datos.get('estable') or {}]
    if canal_beta:
        candidatos.append(datos.get('beta') or {})
    mejor = max((c for c in candidatos if c.get('version')), key=lambda c: _partes(c['version']), default=None)
    if mejor and es_mas_nueva(mejor['version'], version_local):
        return {'estado': 'nueva', 'version': mejor['version'], 'url': mejor.get('url') or '',
                'notas': mejor.get('notas') or ''}
    return {'estado': 'al_dia', 'version': version_local}
