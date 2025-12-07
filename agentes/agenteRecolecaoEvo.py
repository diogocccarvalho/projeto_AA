from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input size: 2 (direcao) + 4 (distancia) + 8 (sensores) + 1 (carregando) = 15
        # CORREÇÃO: Input size passou de 14 para 15 (devido à nova precisão de distância)
        super().__init__(input_size=15, hidden_size=40, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(15)
            
        direcao = np.array(obs['direcao_alvo'])
        
        # Agora são 4 níveis de distância (0,1,2,3)
        dist_one_hot = np.zeros(4)
        dist_idx = obs['distancia_discreta']
        # Proteção se vier algo fora do range (não deve acontecer)
        if 0 <= dist_idx < 4:
            dist_one_hot[dist_idx] = 1
        
        sensores = np.array(list(obs['sensores'].values()))
        carregando = np.array([1 if obs['carregando'] else 0])
        
        return np.concatenate([direcao, dist_one_hot, sensores, carregando])