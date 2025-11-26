from agentes.agente import Agente
import numpy as np
import matplotlib.pyplot as plt
import random

class AgenteQ(Agente):
    def __init__(self):
        super().__init__()

        self.q_table = {}
        self.alpha = 0.1      #learning rate
        self.gamma = 0.9      
        self.epsilon = 1.0    #exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995 #reduzir exploração

        #short term memory
        self.estado_anterior = None
        self.acao_anterior = None
        self.recompensa_recente = 0

        self.accoes = []

        self.learning_mode = True

    def _formar_estado(self, obs):
        pass

    def obter_q(self, estado, acao):
        return self.q_table.get((estado, acao), 0.0)

    def observacao(self, obs):
        novo_estado = self._formar_estado(obs)
        
        if self.estado_anterior is not None and self.learning_mode:
            q_antigo = self.obter_q(self.estado_anterior, self.acao_anterior)
            max_q_futuro = -float('inf')
            if not self.accoes:
                max_q_futuro = 0.0
            else:
                for a in self.accoes:
                    q_val = self.obter_q(novo_estado, a)
                    if q_val > max_q_futuro:
                        max_q_futuro = q_val


            #bellman
            q_novo = q_antigo + self.alpha * (self.recompensa_recente + self.gamma * max_q_futuro - q_antigo)

            self.q_table[(self.estado_anterior, self.acao_anterior)] = q_novo

        super().observacao(obs)

    def age(self):
        estado_atual = self._formar_estado(self.ultima_observacao)
        if self.learning_mode and random.random() < self.epsilon:
            acao = random.choice(self.accoes)
        else:
            
            melhor_acao = None
            melhor_valor = -float('inf')
            
            random.shuffle(self.accoes) #desempate
            
            for a in self.accoes:
                q_val = self.obter_q(estado_atual, a)
                if q_val > melhor_valor:
                    melhor_valor = q_val
                    melhor_acao = a
            
            acao = melhor_acao

        self.estado_anterior = estado_atual
        self.acao_anterior = acao
        
        #reduzir exploration rate
        if self.learning_mode and self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
        return acao

    def avaliacao_estado_atual(self, recompensa):
        self.recompensa_recente = recompensa
        self.recompensa_total += recompensa #gráficos