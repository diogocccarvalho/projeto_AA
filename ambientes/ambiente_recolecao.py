import numpy as np
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):
    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial, self.num_obstaculos_inicial = num_recursos, num_obstaculos
        self.agentes_carga = {}
        self.np_random = np.random.RandomState()
        self.reset()

    def reconfigurar(self, **kwargs):
        """Implementação obrigatória do método abstrato da classe Ambiente."""
        self.largura = kwargs.get('largura', self.largura)
        self.altura = kwargs.get('altura', self.altura)
        self.num_recursos_inicial = kwargs.get('num_recursos', self.num_recursos_inicial)
        self.num_obstaculos_inicial = kwargs.get('num_obstaculos', self.num_obstaculos_inicial)
        # self.reset() -> REMOVIDO PARA EVITAR DUPLO RESET

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes: return None
        ax, ay = self._posicoes_agentes[agente]
        
        # Bloqueios = Paredes + Outros Agentes
        bloqueios = self.obstaculos.copy()
        for outro, pos in self._posicoes_agentes.items():
            if outro != agente: bloqueios.add(pos)

        sensores = {}
        # Manter a lógica de sensores consistente com os agentes Evo
        dirs = [("Norte",(0,-1)),("Sul",(0,1)),("Este",(1,0)),("Oeste",(-1,0)),
                ("NE",(1,-1)),("SE",(1,1)),("SW",(-1,1)),("NW",(-1,-1))]
        for nome, (dx, dy) in dirs:
            nx, ny = ax+dx, ay+dy
            sensores[nome] = 1 if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in bloqueios else 0

        # Direções
        dir_ninho = (np.sign(self.pos_ninho[0]-ax), np.sign(self.pos_ninho[1]-ay))
        # Fallback: se não houver recursos, a direção aponta para a posição atual (0,0)
        rec = min(self.recursos, key=lambda r: abs(ax-r[0])+abs(ay-r[1])) if self.recursos else (ax, ay)
        dir_recurso = (np.sign(rec[0]-ax), np.sign(rec[1]-ay))

        return {"dir_ninho": dir_ninho, "dir_recurso": dir_recurso, 
                "carregando": self.agentes_carga[agente], "sensores": sensores}

    def agir(self, agente, accao):
        ax, ay = self._posicoes_agentes[agente]
        carga = self.agentes_carga[agente]
        # Ativamos o shaping para todos para ajudar a evolução a encontrar objetivos
        # is_evo = isinstance(agente, AgenteRecolecaoEvo) 

        if accao in ["Norte", "Sul", "Este", "Oeste"]:
            movs = {"Norte":(0,-1), "Sul":(0,1), "Este":(1,0), "Oeste":(-1,0)}
            nx, ny = ax+movs[accao][0], ay+movs[accao][1]
            
            if not (0<=nx<self.largura and 0<=ny<self.altura) or (nx, ny) in self.obstaculos: return -5.0
            if any(p == (nx, ny) for a, p in self._posicoes_agentes.items() if a != agente): return -2.0
            
            self._posicoes_agentes[agente] = (nx, ny)
            reward = -0.1
            
            # Reward Shaping: Agora aplicado a Q-Learning e Evolutivo
            if carga:
                alvo = self.pos_ninho
            elif self.recursos:
                alvo = min(self.recursos, key=lambda r: abs(nx-r[0])+abs(ny-r[1]))
            else:
                alvo = None
            
            if alvo:
                # O shaping guia o agente para o objetivo
                reward += (abs(ax-alvo[0])+abs(ay-alvo[1]) - (abs(nx-alvo[0])+abs(ny-alvo[1]))) * 0.5
            return reward

        if accao == "Recolher" and not carga and (ax, ay) in self.recursos:
            self.recursos.remove((ax, ay)); self.agentes_carga[agente] = True; return 20.0
        if accao == "Depositar" and carga and (ax, ay) == self.pos_ninho:
            self.agentes_carga[agente] = False; return 100.0
        
        # Penalidade por ação inválida (tentar recolher onde não há nada)
        return -1.0

    def reset(self):
        self.terminou = False
        posicoes_proibidas = set()

        self.pos_ninho = self._gerar_posicao_livre(posicoes_proibidas)
        posicoes_proibidas.add(self.pos_ninho)

        self.obstaculos = set()
        for _ in range(self.num_obstaculos_inicial):
            pos_obstaculo = self._gerar_posicao_livre(posicoes_proibidas)
            self.obstaculos.add(pos_obstaculo)
            posicoes_proibidas.add(pos_obstaculo)

        self.recursos = set()
        for _ in range(self.num_recursos_inicial):
            pos_recurso = self._gerar_posicao_livre(posicoes_proibidas)
            self.recursos.add(pos_recurso)
            posicoes_proibidas.add(pos_recurso)

        for ag in self._posicoes_agentes:
            pos_agente = self._gerar_posicao_livre(posicoes_proibidas)
            self._posicoes_agentes[ag] = pos_agente
            posicoes_proibidas.add(pos_agente)
            self.agentes_carga[ag] = False