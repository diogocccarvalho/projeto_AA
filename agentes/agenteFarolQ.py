from agentes.agenteQ import AgenteQ

class AgenteFarolQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # Ajustamos o epsilon_decay para 0.99975 (igual à recoleção)
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon, epsilon_decay=0.99975)
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):
        if obs is None:
            return ((0, 0), tuple())

        # Usamos sorted para consistência e removemos acao_anterior
        # para diminuir o espaço de estados e acelerar a convergência.
        sensores_tuple = tuple(sorted(obs['sensores'].items()))
        
        return (obs['direcao_alvo'], sensores_tuple)