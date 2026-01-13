from agentes.agente import Agente
import random
import copy

class AgenteQ(Agente):

    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.9995):
        super().__init__()
        self.q_table = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay # Decay mais lento para aguentar o treino longo
        
        self.estado_anterior = None
        self.acao_anterior = None
        self.accoes = []

    def _formar_estado(self, obs):
        raise NotImplementedError

    def obter_q(self, estado, acao):
        return self.q_table.get((estado, acao), 0.0)

    def _atualizar_q_table(self, estado_atual, recompensa, accoes_validas):
        q_antigo = self.obter_q(self.estado_anterior, self.acao_anterior)
        
        q_valores_futuros = [self.obter_q(estado_atual, a) for a in accoes_validas]
        max_q_futuro = max(q_valores_futuros) if q_valores_futuros else 0.0

        q_novo = q_antigo + self.alpha * (recompensa + self.gamma * max_q_futuro - q_antigo)
        self.q_table[(self.estado_anterior, self.acao_anterior)] = q_novo

    def _get_accoes_validas(self, estado):
        return self.accoes

    def _escolher_melhor_acao(self, estado):
        melhor_valor = -float('inf')
        melhores_accoes = []
        
        accoes_validas = self._get_accoes_validas(estado)
        
        for a in accoes_validas:
            q_val = self.obter_q(estado, a)
            if q_val > melhor_valor:
                melhor_valor = q_val
                melhores_accoes = [a]
            elif q_val == melhor_valor:
                melhores_accoes.append(a)
        
        return random.choice(melhores_accoes) if melhores_accoes else random.choice(accoes_validas)

    def age(self):
        estado_atual = self._formar_estado(self.ultima_observacao)
        
        if self.learning_mode and random.random() < self.epsilon:
            acao = random.choice(self._get_accoes_validas(estado_atual))
        else:
            acao = self._escolher_melhor_acao(estado_atual)

        self.estado_anterior = estado_atual
        self.acao_anterior = acao
        return acao

    def avaliar_recompensa(self, recompensa, obs=None):
        if self.learning_mode and self.estado_anterior is not None:
            observacao = obs if obs is not None else self.ultima_observacao
            if observacao:
                estado_atual = self._formar_estado(observacao)
                self._atualizar_q_table(estado_atual, recompensa, self._get_accoes_validas(estado_atual))
        super().avaliar_recompensa(recompensa)

    def reset_episodio(self):
        super().reset_episodio()
        self.estado_anterior = None
        self.acao_anterior = None
        
        if self.learning_mode and self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def boost_exploration(self, valor=0.5):
        """Reinjeta exploração quando o ambiente muda de dificuldade."""
        self.epsilon = max(self.epsilon, valor)
        # print(f"DEBUG: Epsilon Boosted to {self.epsilon}")

    def clone(self):
        new_agent = self.__class__()
        new_agent.q_table = copy.deepcopy(self.q_table)
        new_agent.epsilon = 0.01 # Agente clonado (para demo) não explora
        return new_agent