import numpy as np
from agentes.agente import Agente

class AgenteEvo(Agente):
    def __init__(self, input_size, hidden1_size, hidden2_size, output_size):
        super().__init__()
        self.input_size = input_size
        self.h1_size = hidden1_size
        self.h2_size = hidden2_size
        self.output_size = output_size
        
        self.s1 = input_size * hidden1_size
        self.sb1 = hidden1_size
        self.s2 = hidden1_size * hidden2_size
        self.sb2 = hidden2_size
        self.s3 = hidden2_size * output_size
        self.sb3 = output_size
        
        self.num_genes = self.s1 + self.sb1 + self.s2 + self.sb2 + self.s3 + self.sb3
        
        # Initialization
        self._genes = np.random.randn(self.num_genes) * 0.05
        self._decodificar_genes()

    def _decodificar_genes(self):
        idx = 0
        end = idx + self.s1
        self.W1 = self._genes[idx:end].reshape(self.input_size, self.h1_size)
        idx = end
        end = idx + self.sb1
        self.b1 = self._genes[idx:end].reshape(1, self.h1_size)
        idx = end
        end = idx + self.s2
        self.W2 = self._genes[idx:end].reshape(self.h1_size, self.h2_size)
        idx = end
        end = idx + self.sb2
        self.b2 = self._genes[idx:end].reshape(1, self.h2_size)
        idx = end
        end = idx + self.s3
        self.W3 = self._genes[idx:end].reshape(self.h2_size, self.output_size)
        idx = end
        end = idx + self.sb3
        self.b3 = self._genes[idx:end].reshape(1, self.output_size)

    @property
    def genes(self):
        return self._genes

    @genes.setter
    def genes(self, novos_genes):
        if len(novos_genes) != self.num_genes:
            raise ValueError(f"Gene mismatch: Got {len(novos_genes)}, expected {self.num_genes}")
        self._genes = np.array(novos_genes)
        self._decodificar_genes()

    def clone(self):
        new_agent = self.__class__() 
        new_agent.genes = self.genes.copy()
        return new_agent

    def _formar_estado(self, obs):
        raise NotImplementedError

    def age(self):
        obs = self._formar_estado(self.ultima_observacao)
        obs_vector = np.array(obs).flatten().reshape(1, -1)
        
        # Forward Pass
        h1 = np.maximum(0, np.dot(obs_vector, self.W1) + self.b1)
        h2 = np.maximum(0, np.dot(h1, self.W2) + self.b2)
        scores = np.dot(h2, self.W3) + self.b3
        
        # DEBUG: Uncomment this to see what the brain is thinking!
        # if not self.learning_mode:
        #    print(f"DEBUG BRAIN: {scores.flatten()} -> Choice: {np.argmax(scores)}")

        acao_idx = np.argmax(scores)
        if hasattr(self, 'accoes') and acao_idx < len(self.accoes):
            return self.accoes[acao_idx]
        return None