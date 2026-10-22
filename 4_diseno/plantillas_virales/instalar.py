# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/instalar.py — copia los .drb/.drt de «Plantillas virales cinema» a plantillas_incluidas con su pack.json y posiciones.
"""Copia los 12 .drb/.drt a plantillas_incluidas (una carpeta por pack) con su pack.json y sus .posiciones.json."""
import json, pathlib, shutil
AQUI = pathlib.Path(__file__).resolve().parent
DEST = AQUI.parent.parent / '2_recursos' / 'plantillas_incluidas'
packs = json.loads((AQUI / 'diseno.json').read_text(encoding='utf-8'))
agrupados = {}
for pk in packs:
    agrupados.setdefault(pk['carpeta'], {})[pk['formato']] = pk
for carpeta, fmts in agrupados.items():
    d = DEST / carpeta
    d.mkdir(parents=True, exist_ok=True)
    formatos = {}
    for f, pk in fmts.items():
        nombre = pk['archivo']
        shutil.copyfile(AQUI / 'provisionales_pos' / (nombre + '.drb'), d / (nombre + '.drb'))
        shutil.copyfile(AQUI / 'disenos' / (nombre + '.drt'), d / (nombre + '.drt'))
        pos = {c['nombre']: c['pos'] for c in pk['clips']}
        (d / (nombre + '.posiciones.json')).write_text(
            json.dumps({'origen': nombre + '.drb', 'clips': dict(sorted(pos.items()))}, ensure_ascii=False, indent=1),
            encoding='utf-8')
        formatos[f] = {'drb': nombre + '.drb'}
    primero = next(iter(fmts.values()))
    (d / 'pack.json').write_text(json.dumps({'version': 2, 'nombre': primero['pack'],
                                             'formatos': {k: formatos[k] for k in ('h', 'v') if k in formatos}},
                                            ensure_ascii=False, indent=2), encoding='utf-8')
    print(carpeta, sorted(p.name for p in d.iterdir()))
