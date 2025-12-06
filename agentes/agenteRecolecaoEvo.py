from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input size: 2 (direcao) + 3 (distancia) + 8 (sensores) + 1 (carregando) = 14
        # Output size: 6 (accoes)
        super().__init__(input_size=14, hidden_size=10, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(14)
            
        direcao = np.array(obs['direcao_alvo'])
        
        dist_one_hot = np.zeros(3)
        dist_one_hot[obs['distancia_discreta']] = 1
        
        sensores = np.array(list(obs['sensores'].values()))
        
        carregando = np.array([1 if obs['carregando'] else 0])
        
        return np.concatenate([direcao, dist_one_hot, sensores, carregando])
