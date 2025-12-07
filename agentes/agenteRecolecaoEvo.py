from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input size: 
        # 2 (direcao alvo) 
        # + 4 (distancia discreta: 0,1,2,3) 
        # + 8 (sensores obstaculos) 
        # + 1 (carregando) 
        # = 15
        
        # Aumentado para 50 neurónios na camada oculta para tentar resolver o looping
        super().__init__(input_size=15, hidden_size=50, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(15)
            
        direcao = np.array(obs['direcao_alvo'])
        
        # One-hot encoding da distância (0 a 3)
        dist_one_hot = np.zeros(4)
        d_idx = int(obs['distancia_discreta'])
        if 0 <= d_idx < 4:
            dist_one_hot[d_idx] = 1
        
        sensores = np.array(list(obs['sensores'].values()))
        carregando = np.array([1 if obs['carregando'] else 0])
        
        return np.concatenate([direcao, dist_one_hot, sensores, carregando])