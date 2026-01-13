from agentes.agenteEvo import AgenteEvo
import numpy as np
import random

class AgenteRecolecaoEvo(AgenteEvo):
    def __init__(self):
        # Input: 13
        #   - 2 (dir ninho)
        #   - 2 (dir recurso)
        #   - 1 (carga)
        #   - 8 (sensores)
        
        # Output: 6 Ações
        super().__init__(input_size=13, hidden1_size=32, hidden2_size=20, output_size=6)
        
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            return np.zeros(13)
            
        dir_ninho = np.array(obs['dir_ninho'])
        dir_recurso = np.array(obs['dir_recurso'])
        
        # Normalização: converter booleano para float
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

    def age(self):
        """
        Sobrescreve o método age para adicionar 'ruído' na demonstração.
        Isso impede que o agente fique preso em loops infinitos (oscilação)
        quando enfrenta situações ambíguas (Perceptual Aliasing).
        """
        # Se NÃO estiver treinando, adicionar 5% de chance de movimento aleatório
        # para quebrar loops de "vai-e-vem".
        if not self.learning_mode and random.random() < 0.05: # 5% de ruído
            return random.choice(self.accoes)

        obs = self._formar_estado(self.ultima_observacao)
        obs_vector = np.array(obs).flatten().reshape(1, -1)
        
        # --- Deep Forward Pass (2 Hidden Layers) ---
        # Camada 1 (ReLU)
        h1 = np.maximum(0, np.dot(obs_vector, self.W1) + self.b1)
        
        # Camada 2 (ReLU)
        h2 = np.maximum(0, np.dot(h1, self.W2) + self.b2)
        
        # Output (Linear)
        scores = np.dot(h2, self.W3) + self.b3
        
        # Escolher ação (Comportamento padrão Argmax)
        acao_idx = np.argmax(scores)
        return self.accoes[acao_idx]