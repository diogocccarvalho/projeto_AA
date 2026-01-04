import random
import numpy as np
from ambientes.ambiente import Ambiente
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo

class AmbienteRecolecao(Ambiente):
    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial, self.num_obstaculos_inicial = num_recursos, num_obstaculos
        self.agentes_carga = {}
        self.reset()

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes: return None
        ax, ay = self._posicoes_agentes[agente]
        
        # Bloqueios = Paredes + Outros Agentes
        bloqueios = self.obstaculos.copy()
        for outro, pos in self._posicoes_agentes.items():
            if outro != agente: bloqueios.add(pos)

        sensores = {}
        dirs = [("Norte",(0,-1)),("Sul",(0,1)),("Este",(1,0)),("Oeste",(-1,0)),
                ("NE",(1,-1)),("SE",(1,1)),("SW",(-1,1)),("NW",(-1,-1))]
        for nome, (dx, dy) in dirs:
            nx, ny = ax+dx, ay+dy
            sensores[nome] = 1 if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in bloqueios else 0

        # Direções
        dir_ninho = (np.sign(self.pos_ninho[0]-ax), np.sign(self.pos_ninho[1]-ay))
        rec = min(self.recursos, key=lambda r: abs(ax-r[0])+abs(ay-r[1])) if self.recursos else (ax, ay)
        dir_recurso = (np.sign(rec[0]-ax), np.sign(rec[1]-ay))

        return {"dir_ninho": dir_ninho, "dir_recurso": dir_recurso, 
                "carregando": self.agentes_carga[agente], "sensores": sensores}

    def agir(self, agente, accao):
        ax, ay = self._posicoes_agentes[agente]
        carga = self.agentes_carga[agente]
        is_evo = isinstance(agente, AgenteRecolecaoEvo)

        if accao in ["Norte", "Sul", "Este", "Oeste"]:
            movs = {"Norte":(0,-1), "Sul":(0,1), "Este":(1,0), "Oeste":(-1,0)}
            nx, ny = ax+movs[accao][0], ay+movs[accao][1]
            
            if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in self.obstaculos: return -5.0
            if any(p == (nx, ny) for a, p in self._posicoes_agentes.items() if a != agente): return -2.0
            
            self._posicoes_agentes[agente] = (nx, ny)
            reward = -0.1
            if not is_evo: # Shaping apenas para Q-Learning
                alvo = self.pos_ninho if carga else min(self.recursos, key=lambda r: abs(nx-r[0])+abs(ny-r[1]))
                reward += (abs(ax-alvo[0])+abs(ay-alvo[1]) - (abs(nx-alvo[0])+abs(ny-alvo[1]))) * 0.5
            return reward

        if accao == "Recolher" and not carga and (ax, ay) in self.recursos:
            self.recursos.remove((ax, ay)); self.agentes_carga[agente] = True; return 20.0
        if accao == "Depositar" and carga and (ax, ay) == self.pos_ninho:
            self.agentes_carga[agente] = False; return 100.0
        return -1.0

    def reset(self):
        self.terminou = False
        self.pos_ninho = (random.randint(0, self.largura-1), random.randint(0, self.altura-1))
        self.obstaculos = { (random.randint(0, self.largura-1), random.randint(0, self.altura-1)) for _ in range(self.num_obstaculos_inicial) }
        self.recursos = { (random.randint(0, self.largura-1), random.randint(0, self.altura-1)) for _ in range(self.num_recursos_inicial) }
        for ag in self._posicoes_agentes:
            self._posicoes_agentes[ag] = (random.randint(0, self.largura-1), random.randint(0, self.altura-1))
            self.agentes_carga[ag] = False