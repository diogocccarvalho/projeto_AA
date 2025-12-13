class Agente:
    
    def __init__(self):
        self.ultima_observacao = None
        self.recompensa_total = 0
        self.learning_mode = True

    def observacao(self, obs):
        self.ultima_observacao = obs

    def age(self):
        raise NotImplementedError

    def avaliar_recompensa(self, recompensa, obs=None):
        self.recompensa_total += recompensa
        pass

    def reset_episodio(self):
        self.recompensa_total = 0
        self.ultima_observacao = None

    def clone(self):
        raise NotImplementedError