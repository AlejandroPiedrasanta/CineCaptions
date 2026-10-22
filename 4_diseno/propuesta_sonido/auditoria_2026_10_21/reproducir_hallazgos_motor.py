"""Reproduce cinco hallazgos de Sonido con estado y preferencias simulados.

Ejecutar desde la raiz del repositorio:
  6_compilacion/venv315/Scripts/python.exe -B \
    4_diseno/propuesta_sonido/auditoria_2026_10_21/reproducir_hallazgos_motor.py

No inicia Resolve, no importa sus conectores y no escribe archivos de usuario.
Solo importa los tres modulos auditados y sustituye sus dependencias de estado.
Estos casos documentan el comportamiento actual: PASA significa que el hallazgo
continua reproducible, no que ese comportamiento sea el deseado.
"""

import copy
import sys
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / '1_codigo'))

import director_sonido as D
import director_sonido_estado as E
import director_sonido_sesion as S


def main():
    estados = {
        'A.mp4': {},
        'B.mp4': {'sound_events': [], 'analisis': {}, 'ultimo_go': {'con_director': True}},
    }
    general = {'ultimo_video': 'B.mp4'}
    escrituras = []

    def cargar(video):
        return copy.deepcopy(estados.get(str(video), {}))

    def guardar(video, estado):
        estados[str(video)] = copy.deepcopy(estado)
        escrituras.append((str(video), copy.deepcopy(estado)))
        return copy.deepcopy(estado)

    with ExitStack() as pila:
        pila.enter_context(patch.object(E, 'cargar', cargar))
        pila.enter_context(patch.object(E, 'guardar', guardar))
        pila.enter_context(patch.object(E, 'general', lambda: copy.deepcopy(general)))
        pila.enter_context(patch.object(E, 'poner_general', lambda **cambios: general.update(cambios)))
        pila.enter_context(patch.object(D, 'activo', lambda *a, **kw: True))
        pila.enter_context(patch.object(D, 'controles', lambda *a, **kw: {}))
        pila.enter_context(patch.object(D, 'cargar_contexto', lambda *a, **kw: {}))
        pila.enter_context(patch.object(D, 'log', lambda *a, **kw: None))
        pila.enter_context(patch.object(D, '_pistas_sfx_captions', lambda: ['SFX']))
        pila.enter_context(patch.object(S, '_nota_material', lambda: {'clave': 'material'}))

        # 1. Ambos archivos se simulan existentes; A carece de diseno y B es el ultimo.
        with patch.object(Path, 'is_file', return_value=True):
            resumen = S.resumen('A.mp4')
        assert resumen['video'] == 'B.mp4'
        assert resumen['otro_video'] is True
        assert resumen['puede_aplicar'] is True
        print('PASA 1/5: resumen(A.mp4) cambia a B.mp4 y permite aplicar.')

        # 2. Solo arma un plan; no se llama a efectos_visuales ni a Resolve.
        plan = D.al_colocar(None, {'sfx': {'eventos': []}}, 'B.mp4')
        assert isinstance(plan, dict)
        assert estados['B.mp4']['pendiente_resolve'] is False
        assert estados['B.mp4']['en_resolve']
        assert estados['B.mp4']['ultimo_go']['con_director'] is True
        print('PASA 2/5: al_colocar marca en_resolve antes de ejecutar la colocacion.')

        # 3. El texto negativo activa la regla positiva de densidad.
        negacion = S.interpretar('No quiero mas sonidos')['acciones']
        assert ('control', 'densidad', 'mucho') in negacion
        print('PASA 3/5: "No quiero mas sonidos" produce densidad=mucho.')

        # 4. La peticion temporal se transforma en un control de todo el video.
        alcance = S.interpretar('Sin musica al final', duracion=60)['acciones']
        assert alcance == [('control', 'musica', 'nada')]
        print('PASA 4/5: "Sin musica al final" produce control global musica=nada.')

        # 5. Se intercepta el redisenado final: interesa el argumento capas.
        llamadas = []
        def poner_control(*args):
            llamadas.append(('control', args))
        def rehacer(*args, **kwargs):
            llamadas.append(('rehacer', kwargs))
            return {}
        with patch.object(S, 'poner_control', poner_control), patch.object(S, '_rehacer', rehacer):
            S.ejecutar('B.mp4', [('control', 'musica', 'nada'), ('seccion', 0, 6)])
        assert ('control', ('musica', 'nada')) in llamadas
        recalculos = [kwargs for nombre, kwargs in llamadas if nombre == 'rehacer']
        assert len(recalculos) == 1
        assert not recalculos[0].get('capas', False)
        print('PASA 5/5: musica + seccion llama _rehacer sin regenerar las capas.')

    print('Resultado: 5 hallazgos reproducidos; estado solo en memoria; Resolve no ejecutado.')
    print('Limite: no prueba audio, Qt, timelines reales, proveedores ni el recorrido GO completo.')


if __name__ == '__main__':
    main()
