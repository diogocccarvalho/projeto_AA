from agentes.agenteQ import AgenteQ

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        #placeholders, TODO logica dos sensores
        if obs is None:
            return ((0, 0), False)

        return (obs['posicao'], obs['carregando'])
