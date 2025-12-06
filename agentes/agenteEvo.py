import numpy as np
from agentes.agente import Agente

class AgenteEvo(Agente):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.W1 = np.random.randn(input_size, hidden_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size)
        self.b2 = np.zeros((1, output_size))

    def _formar_estado(self, obs):
        raise NotImplementedError

    def age(self):
        obs = self._formar_estado(self.ultima_observacao)
        obs_vector = np.array(obs).flatten().reshape(1, -1)
        
        # Forward pass
        h1 = np.maximum(0, np.dot(obs_vector, self.W1) + self.b1) # ReLU activation
        scores = np.dot(h1, self.W2) + self.b2
        
        # Choose action with the highest score
        acao_idx = np.argmax(scores)
        return self.accoes[acao_idx]

    @property
    def genes(self):
        return np.concatenate([self.W1.flatten(), self.b1.flatten(), self.W2.flatten(), self.b2.flatten()])

    @genes.setter
    def genes(self, genes):
        s1 = self.W1.size
        s2 = self.b1.size
        s3 = self.W2.size
        
        self.W1 = genes[0:s1].reshape(self.W1.shape)
        self.b1 = genes[s1:s1+s2].reshape(self.b1.shape)
        self.W2 = genes[s1+s2:s1+s2+s3].reshape(self.W2.shape)
        self.b2 = genes[s1+s2+s3:].reshape(self.b2.shape)
