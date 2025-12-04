from agentes.agente import Agente
import random

class AgenteQ(Agente):

    def __init__(self, alpha=0.2, gamma=0.9, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999):
        super().__init__()

        #parametros
        self.q_table = {}
        self.alpha = alpha              # Taxa de aprendizagem (learning rate)
        self.gamma = gamma              # Fator de desconto (discount factor)
        self.epsilon = epsilon          # Taxa de exploração inicial (exploration rate)
        self.epsilon_min = epsilon_min      # Taxa de exploração mínima
        self.epsilon_decay = epsilon_decay  # Decaimento da taxa de exploração


        self.estado_anterior = None
        self.acao_anterior = None
        
        #ações definidas pelas subclasses
        self.accoes = []

    def _formar_estado(self, obs):
        raise NotImplementedError

    def obter_q(self, estado, acao):
        return self.q_table.get((estado, acao), 0.0)

    def _atualizar_q_table(self, estado_atual, recompensa):
        q_antigo = self.obter_q(self.estado_anterior, self.acao_anterior)
        
        #estimar melhor ação
        q_valores_futuros = [self.obter_q(estado_atual, a) for a in self.accoes]
        max_q_futuro = max(q_valores_futuros) if q_valores_futuros else 0.0

        #bellman
        q_novo = q_antigo + self.alpha * (recompensa + self.gamma * max_q_futuro - q_antigo)
        self.q_table[(self.estado_anterior, self.acao_anterior)] = q_novo

    def _escolher_melhor_acao(self, estado):
        melhor_acao = None
        melhor_valor = -float('inf')
        
        #desempates
        accoes_baralhadas = list(self.accoes)
        random.shuffle(accoes_baralhadas)
        
        for a in accoes_baralhadas:
            q_val = self.obter_q(estado, a)
            if q_val > melhor_valor:
                melhor_valor = q_val
                melhor_acao = a
        
        return melhor_acao if melhor_acao is not None else random.choice(self.accoes)

    def age(self):
        estado_atual = self._formar_estado(self.ultima_observacao)
        
        if self.learning_mode and random.random() < self.epsilon:
            acao = random.choice(self.accoes)
        else:
            acao = self._escolher_melhor_acao(estado_atual)

        self.estado_anterior = estado_atual
        self.acao_anterior = acao
        
        return acao

    def avaliar_recompensa(self, recompensa):
        if self.learning_mode and self.estado_anterior is not None:
            estado_atual = self._formar_estado(self.ultima_observacao)
            self._atualizar_q_table(estado_atual, recompensa)

        super().avaliar_recompensa(recompensa)

    def reset_episodio(self):
        super().reset_episodio()
        self.estado_anterior = None
        self.acao_anterior = None
        
        #reduzir exploração
        if self.learning_mode and self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay