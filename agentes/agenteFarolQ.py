from agentes.agenteQ import AgenteQ

class AgenteFarolQ(AgenteQ):
    def __init__(self):
        super().__init__()
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):

        if obs is None:
            return (0, 0)
            
        return obs