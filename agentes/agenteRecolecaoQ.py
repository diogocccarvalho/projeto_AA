from agentes.agenteQ import AgenteQ
import random

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            # Default state: no direction, no obstacles, not carrying
            return ((0, 0), (0, 0, 0, 0, 0, 0, 0, 0), False)

        return (obs['direcao_alvo'], obs['sensores'], obs['carregando'])

    def age(self):
        estado_atual = self._formar_estado(self.ultima_observacao)
        carregando = estado_atual[2] # O status de 'carregando' é o terceiro elemento do estado

        # Action Masking: filtrar ações válidas
        accoes_validas = ["Norte", "Sul", "Este", "Oeste"]
        if carregando:
            accoes_validas.append("Depositar")
        else:
            # Se houver recursos, a ação de recolher é válida
            # Esta verificação pode ser mais complexa se o agente souber a pos dos recursos
            accoes_validas.append("Recolher")
        
        # Escolher ação (exploração vs. explotação)
        if self.learning_mode and random.random() < self.epsilon:
            acao = random.choice(accoes_validas)
        else:
            # Escolher a melhor ação apenas do conjunto de ações válidas
            melhor_acao = None
            melhor_valor = -float('inf')
            
            # Desempatar aleatoriamente
            random.shuffle(accoes_validas)
            
            for a in accoes_validas:
                q_val = self.obter_q(estado_atual, a)
                if q_val > melhor_valor:
                    melhor_valor = q_val
                    melhor_acao = a
            
            acao = melhor_acao if melhor_acao is not None else random.choice(accoes_validas)

        self.estado_anterior = estado_atual
        self.acao_anterior = acao
        
        return acao
