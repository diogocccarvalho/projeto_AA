from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteFarolEvo(AgenteEvo):
    def __init__(self):
        # Input: 2 (distancia) + 8 (sensores) = 10
        # Output: 4
        # Arquitetura: 10 -> 16 -> 12 -> 4
        super().__init__(input_size=10, hidden1_size=16, hidden2_size=12, output_size=4)
        
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(10)
            
        dist = np.array(obs['direcao_alvo'])
        sensores = np.array(list(obs['sensores'].values()))
        return np.concatenate([dist, sensores])