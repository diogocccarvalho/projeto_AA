from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input: 13
        #   - 2 (dir ninho)
        #   - 2 (dir recurso)
        #   - 1 (carga)
        #   - 8 (sensores)
        
        # Output: 6 Ações
        
        # AUMENTO DE CAPACIDADE: 
        # Antes: 13 -> 16 -> 12 -> 6 (Pequeno demais)
        # Agora: 13 -> 32 -> 20 -> 6 (Melhor para mapear obstáculos complexos)
        super().__init__(input_size=13, hidden1_size=32, hidden2_size=20, output_size=6)
        
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(13)
            
        dir_ninho = np.array(obs['dir_ninho'])
        dir_recurso = np.array(obs['dir_recurso'])
        
        # Normalização importante: converter booleano para float (0.0 ou 1.0)
        carga = np.array([1.0 if obs['carregando'] else 0.0])
        
        # Garantir ordem determinística dos sensores
        sensores_ordenados = [v for k, v in sorted(obs['sensores'].items())]
        sensores = np.array(sensores_ordenados)
        
        return np.concatenate([
            dir_ninho, 
            dir_recurso, 
            carga, 
            sensores
        ])