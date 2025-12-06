from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteFarolEvo(AgenteEvo):
    def __init__(self):
        # Input size: 2 (distancia) + 8 (sensores) = 10
        # Output size: 4 (accoes)
        super().__init__(input_size=10, hidden_size=8, output_size=4)
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(10)
            
        dist = np.array(obs['distancia_discreta'])
        sensores = np.array(list(obs['sensores'].values()))
        return np.concatenate([dist, sensores])
