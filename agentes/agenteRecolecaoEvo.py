from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input: 13 (ninho:2, recurso:2, carga:1, sensores:8)
        super().__init__(input_size=13, hidden1_size=16, hidden2_size=12, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None: return np.zeros(13)
        dir_ninho = np.array(obs['dir_ninho'])
        dir_recurso = np.array(obs['dir_recurso'])
        carga = np.array([1.0 if obs['carregando'] else 0.0])

        sensores_ordenados = [v for k, v in sorted(obs['sensores'].items())]
        sensores = np.array(sensores_ordenados)

        return np.concatenate([
            dir_ninho, 
            dir_recurso, 
            carga, 
            sensores
        ])