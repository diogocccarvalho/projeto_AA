from agentes.agente import Agente
import random

class AgenteQ(Agente):

    def __init__(self, alpha=0.2, gamma=0.9, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.999, exploration_beta=0.1):
        super().__init__()

        #parametros
        self.q_table = {}
        self.visited_states = {}
        self.alpha = alpha              # Taxa de aprendizagem (learning rate)
        self.gamma = gamma              # Fator de desconto (discount factor)
        self.epsilon = epsilon          # Taxa de exploração inicial (exploration rate)
        self.epsilon_min = epsilon_min      # Taxa de exploração mínima
        self.epsilon_decay = epsilon_decay  # Decaimento da taxa de exploração
        self.exploration_beta = exploration_beta # Fator de exploração


        self.estado_anterior = None
        self.acao_anterior = None
        
        #ações definidas pelas subclasses
        self.accoes = []

    def _formar_estado(self, obs):
        raise NotImplementedError

    def obter_q(self, estado, acao):
        return self.q_table.get((estado, acao), 0.0)

    def _atualizar_q_table(self, estado_atual, recompensa, accoes_validas):
        # Incrementar contagem de visitas ao estado anterior
        self.visited_states[self.estado_anterior] = self.visited_states.get(self.estado_anterior, 0) + 1

        # Calcular bônus de exploração
        exploration_bonus = self.exploration_beta / (self.visited_states.get(self.estado_anterior, 1) ** 0.5)

        q_antigo = self.obter_q(self.estado_anterior, self.acao_anterior)
        
        #estimar melhor ação
        q_valores_futuros = [self.obter_q(estado_atual, a) for a in accoes_validas]
        max_q_futuro = max(q_valores_futuros) if q_valores_futuros else 0.0

        #bellman
        q_novo = q_antigo + self.alpha * (recompensa + exploration_bonus + self.gamma * max_q_futuro - q_antigo)
        self.q_table[(self.estado_anterior, self.acao_anterior)] = q_novo

    def _get_accoes_validas(self, estado):
        # Por padrão, todas as ações são válidas. As subclasses podem sobrepor este método.
        return self.accoes

    def _escolher_melhor_acao(self, estado):
        melhor_acao = None
        melhor_valor = -float('inf')
        
        accoes_validas = self._get_accoes_validas(estado)
        random.shuffle(accoes_validas)
        
        for a in accoes_validas:
            q_val = self.obter_q(estado, a)
            if q_val > melhor_valor:
                melhor_valor = q_val
                melhor_acao = a
        
        return melhor_acao if melhor_acao is not None else random.choice(accoes_validas)

    def age(self):
        estado_atual = self._formar_estado(self.ultima_observacao)
        
        # --- LOOP BREAKER (Correção para a Demo) ---
        # Se não estamos a aprender (Modo Demo), verificamos se estamos presos
        if not self.learning_mode:
            # Hash simples do estado para detetar repetição imediata
            # Usamos um histórico local curto apenas para detetar loops
            if not hasattr(self, '_demo_history'): self._demo_history = []
            
            self._demo_history.append(estado_atual)
            if len(self._demo_history) > 10: self._demo_history.pop(0)
            
            # Se o mesmo estado aparece 3 vezes nos últimos 10 passos -> PÂNICO
            if self._demo_history.count(estado_atual) >= 3:
                # Força uma ação aleatória para sair do loop
                acao = random.choice(self._get_accoes_validas(estado_atual))
                self.estado_anterior = estado_atual
                self.acao_anterior = acao
                self._demo_history = [] 
                return acao
        # -------------------------------------------

        if self.learning_mode and random.random() < self.epsilon:
            acao = random.choice(self._get_accoes_validas(estado_atual))
        else:
            acao = self._escolher_melhor_acao(estado_atual)

        self.estado_anterior = estado_atual
        self.acao_anterior = acao
        
        return acao

    def avaliar_recompensa(self, recompensa, obs=None):
        if self.learning_mode and self.estado_anterior is not None:
            # Se uma nova observação for passada, use-a. Senão, use a última guardada.
            observacao = obs if obs is not None else self.ultima_observacao
            if observacao:
                estado_atual = self._formar_estado(observacao)
                accoes_validas_futuras = self._get_accoes_validas(estado_atual)
                self._atualizar_q_table(estado_atual, recompensa, accoes_validas_futuras)

        super().avaliar_recompensa(recompensa)

    def reset_episodio(self):
        super().reset_episodio()
        self.estado_anterior = None
        self.acao_anterior = None
        
        #reduzir exploração
        if self.learning_mode and self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay