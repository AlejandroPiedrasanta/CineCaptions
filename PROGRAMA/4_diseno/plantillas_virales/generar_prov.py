# CineCaptions · By Cinema Productions
# 4_diseno/plantillas_virales/generar_prov.py — regenera los 12 .drb de «Plantillas virales cinema» desde sus .drt.
"""Regenera los 12 .drb provisionales con la posición (Tilt) de cada clip embebida."""
import json, pathlib, sys
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import sintetizar_drb as S
packs = json.loads((AQUI / 'diseno.json').read_text(encoding='utf-8'))
sal = AQUI / 'provisionales_pos'
for pk in packs:
    pos = {c['nombre']: c['pos'][1] for c in pk['clips']}
    n = S.sintetizar(AQUI / 'disenos' / (pk['archivo'] + '.drt'), sal / (pk['archivo'] + '.drb'), pk['archivo'], pos)
    print(pk['archivo'], len(n))
