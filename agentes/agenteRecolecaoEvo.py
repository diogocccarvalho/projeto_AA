from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input size: 15 (2 dir + 4 dist + 8 sensores + 1 carga)
        # Arquitetura robusta: 15 -> 40 -> 30 -> 6
        super().__init__(input_size=15, hidden1_size=40, hidden2_size=30, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(15)
            
        direcao = np.array(obs['direcao_alvo'])
        
        dist_one_hot = np.zeros(4)
        d_idx = int(obs['distancia_discreta'])
        if 0 <= d_idx < 4:
            dist_one_hot[d_idx] = 1
        
        sensores = np.array(list(obs['sensores'].values()))
        carregando = np.array([1 if obs['carregando'] else 0])
        
        return np.concatenate([direcao, dist_one_hot, sensores, carregando])