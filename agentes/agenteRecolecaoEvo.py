from agentes.agenteEvo import AgenteEvo
import numpy as np

from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # --- ARQUITETURA AJUSTADA ---
        # Input: 13 (dir_ninho(2) + dir_rec(2) + carga(1) + sensores(8))
        # Hidden layers ajustadas para o novo estado mais simples
        super().__init__(input_size=13, hidden1_size=16, hidden2_size=12, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        """
        Cria um vetor de estado a partir da observação do ambiente.
        O estado agora foca-se apenas na direção e nos sensores.
        """
        if obs is None:
            # Retorna um estado neutro se não houver observação
            return np.zeros(13)
            
        # --- Processar a observação simplificada ---

        # 1. Direção para o Ninho (2 valores)
        dir_ninho = np.array(obs['dir_ninho'])
        
        # 2. Direção para o Recurso (2 valores)
        dir_recurso = np.array(obs['dir_recurso'])

        # 3. Estado de Carga (1 valor)
        carregando = np.array([1 if obs['carregando'] else 0])

        # 4. Sensores de Obstáculo (8 valores)
        sensores = np.array(list(obs['sensores'].values()))
        
        # Concatenar tudo num único vetor de estado
        return np.concatenate([
            dir_ninho,
            dir_recurso,
            carregando,
            sensores
        ])