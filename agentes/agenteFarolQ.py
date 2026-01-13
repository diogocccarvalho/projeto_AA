from agentes.agenteQ import AgenteQ

class AgenteFarolQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # Ajustamos o epsilon_decay para 0.99975 (igual à recoleção)
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon, epsilon_decay=0.99975)
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def _formar_estado(self, obs):
        if obs is None:
            return ((0, 0), tuple())

        # FIX: Forçar conversão para int padrão do Python
        # Isso evita que numpy.int64 cause erros de chave na Q-Table carregada
        dx, dy = obs['direcao_alvo']
        dir_alvo = (int(dx), int(dy))

        # Usamos sorted para consistência e removemos acao_anterior
        sensores_tuple = tuple(sorted(obs['sensores'].items()))
        
        return (dir_alvo, sensores_tuple)