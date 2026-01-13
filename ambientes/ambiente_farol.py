import random
import numpy as np
from ambientes.ambiente import Ambiente
from agentes.agenteFarolEvo import AgenteFarolEvo

class AmbienteFarol(Ambiente):
    # Constante para referência no treino e lógica de recompensas
    RECOMPENSA_FAROL = 100.0

    def __init__(self, largura=20, altura=20, num_obstaculos=20):
        super().__init__(largura, altura)
        self.num_obstaculos_inicial = num_obstaculos
        self.reset()

    def reconfigurar(self, **kwargs):
        """Implementação obrigatória do método abstrato da classe Ambiente."""
        self.largura = kwargs.get('largura', self.largura)
        self.altura = kwargs.get('altura', self.altura)
        self.num_obstaculos_inicial = kwargs.get('num_obstaculos', self.num_obstaculos_inicial)
        # self.reset() -> REMOVIDO PARA EVITAR DUPLO RESET NO SIMULADOR

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes: return None
        ax, ay = self._posicoes_agentes[agente]
        
        bloqueios = self.obstaculos.copy()
        for outro, pos in self._posicoes_agentes.items():
            if outro != agente: bloqueios.add(pos)

        sensores = {}
        dirs = {"Norte":(0,-1), "Sul":(0,1), "Este":(1,0), "Oeste":(-1,0), 
                "NE":(1,-1), "SE":(1,1), "SW":(-1,1), "NW":(-1,-1)}
        for nome, (dx, dy) in dirs.items():
            nx, ny = ax+dx, ay+dy
            sensores[nome] = 1 if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in bloqueios else 0

        dir_alvo = (np.sign(self.pos_farol[0]-ax), np.sign(self.pos_farol[1]-ay))
        return {"direcao_alvo": dir_alvo, "sensores": sensores}

    def agir(self, agente, accao):
        ax, ay = self._posicoes_agentes[agente]
        is_evo = isinstance(agente, AgenteFarolEvo)
        
        movs = {"Norte":(0,-1), "Sul":(0,1), "Este":(1,0), "Oeste":(-1,0)}
        if accao in movs:
            nx, ny = ax+movs[accao][0], ay+movs[accao][1]
            if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in self.obstaculos: return -5.0
            if any(p == (nx, ny) for a, p in self._posicoes_agentes.items() if a != agente): return -2.0
            
            self._posicoes_agentes[agente] = (nx, ny)
            if (nx, ny) == self.pos_farol: 
                self.terminou = True
                return self.RECOMPENSA_FAROL
            
            reward = -0.2
            if not is_evo: # Shaping apenas para Q-Learning
                reward += (abs(ax-self.pos_farol[0])+abs(ay-self.pos_farol[1]) - 
                          (abs(nx-self.pos_farol[0])+abs(ny-self.pos_farol[1]))) * 2.0
            return reward
        return -1.0

    def reset(self):
        self.terminou = False
        self.pos_farol = (random.randint(0, self.largura-1), random.randint(0, self.altura-1))
        self.obstaculos = { (random.randint(0, self.largura-1), random.randint(0, self.altura-1)) 
                           for _ in range(self.num_obstaculos_inicial) }
        for ag in self._posicoes_agentes:
            self._posicoes_agentes[ag] = (random.randint(0, self.largura-1), 
                                          random.randint(0, self.altura-1))