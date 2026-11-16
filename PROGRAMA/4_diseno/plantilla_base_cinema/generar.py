# CineCaptions · By Cinema Productions
# 4_diseno/plantilla_base_cinema/generar.py — del .drt exportado por Resolve al .drb de la plantilla base nueva, y su instalación en plantillas_incluidas.
"""Pasos (después de construir los .drt dentro de Resolve con taller_base.construir):

    python generar.py drb        # .drt -> .drb provisional con el Pan/Tilt/Zoom de cada clip (provisionales/)
    python generar.py instalar   # copia .drb + .drt (apilado) + .posiciones.json a 2_recursos/plantillas_incluidas (guarda lo anterior en anteriores/)

Usa Python 3.14 (compression.zstd). Los .drb se sintetizan como los de «Plantillas virales cinema» y se comprueban
importándolos en Resolve (taller_base.verificar).
"""
import json
import pathlib
import shutil
import sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(AQUI.parent / 'plantillas_virales'))
sys.path.insert(0, str(RAIZ / '1_codigo'))
import sintetizar_drb as S       # noqa: E402
import packs_drt                 # noqa: E402
import diseno_base                 # noqa: E402

DESTINO = RAIZ / '2_recursos' / 'plantillas_incluidas'


def diseno():
    return json.loads((AQUI / 'diseno.json').read_text(encoding='utf-8'))


def drb():
    salida = AQUI / 'provisionales'
    for pk in diseno():
        pos = {c['nombre']: c['pos'] for c in pk['clips']}
        nombres = S.sintetizar(AQUI / 'disenos' / (pk['archivo'] + '.drt'), salida / (pk['archivo'] + '.drb'),
                               pk['archivo'], pos)
        info = packs_drt.leer_drb(salida / (pk['archivo'] + '.drb'))
        leidas = packs_drt.posiciones_de_drb(salida / (pk['archivo'] + '.drb'))
        print(pk['archivo'], len(nombres), 'clips | sets completos', info['completos'], '| imagen en', info['imagenes'],
              '| simple', info['base'], '| posiciones leídas', len(leidas), '| avisos', info['avisos'])


def instalar():
    ant = AQUI / 'anteriores'
    ant.mkdir(exist_ok=True)
    for pk in diseno():
        base = pk['archivo']
        pos = {c['nombre']: c['pos'] for c in pk['clips']}
        for ext in ('.drb', '.drt', '.posiciones.json'):
            viejo = DESTINO / (base + ext)
            if viejo.is_file() and not (ant / viejo.name).exists():
                shutil.copyfile(viejo, ant / viejo.name)
        shutil.copyfile(AQUI / 'provisionales' / (base + '.drb'), DESTINO / (base + '.drb'))
        # el .drt del pack es el APILADO (V1 principal · V2 arriba · V3 abajo · V4 imagen, una variante tras otra);
        # si no se apiló, el secuencial
        apilado = AQUI / 'apilados' / (base + '.drt')
        shutil.copyfile(apilado if apilado.is_file() else AQUI / 'disenos' / (base + '.drt'), DESTINO / (base + '.drt'))
        (DESTINO / (base + '.posiciones.json')).write_text(
            json.dumps({'origen': base + '.drb', 'clips': dict(sorted(pos.items()))}, ensure_ascii=False, indent=1),
            encoding='utf-8')
        # nombre y color del principal de cada variante: la app los usa para dibujar la vista previa (los Luxe llevan el
        # color enlazado a sus controles y no se puede leer del .drb)
        variantes = {str(n): {'nombre': v['nombre'], 'color': list(v['principal'])}
                     for n, v in diseno_base.VARIANTES.items()}
        (DESTINO / (base + '.variantes.json')).write_text(json.dumps(variantes, ensure_ascii=False, indent=1), encoding='utf-8')
        print('instalado', base)


if __name__ == '__main__':
    {'drb': drb, 'instalar': instalar}[sys.argv[1] if len(sys.argv) > 1 else 'drb']()
