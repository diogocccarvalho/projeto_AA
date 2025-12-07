from agentes.agenteQ import AgenteQ

class AgenteFarolQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon)
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):
        if obs is None:
            return ((0, 0), tuple(), None)
            

        sensores_tuple = tuple(sorted(obs['sensores'].items()))
        
        return (obs['distancia_discreta'], sensores_tuple, self.acao_anterior)