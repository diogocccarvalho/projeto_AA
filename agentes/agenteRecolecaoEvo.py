from agentes.agenteEvo import AgenteEvo
import numpy as np

from agentes.agenteEvo import AgenteEvo
import numpy as np

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # --- ARQUITETURA AJUSTADA ---
        # Input: 17 (dir_ninho(2) + dirs_recursos(3*2) + carga(1) + sensores(8))
        # Hidden layers ajustadas para o novo estado mais complexo
        super().__init__(input_size=17, hidden1_size=24, hidden2_size=16, output_size=6)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        """
        Cria um vetor de estado a partir da observação do ambiente.
        O estado agora foca-se na direção para o ninho, para os 3 recursos
        mais próximos, e nos sensores.
        """
        if obs is None:
            # Retorna um estado neutro se não houver observação
            return np.zeros(17)
            
        # --- Processar a observação com visão global ---

        # 1. Direção para o Ninho (2 valores)
        dir_ninho = np.array(obs['dir_ninho'])
        
        # 2. Direções para os 3 Recursos mais próximos (6 valores)
        dir_recurso = np.array(obs['dir_recurso']).flatten()

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