import random
import numpy as np
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):
    # AJUSTE DE RECOMPENSAS PARA EVITAR LOOPING
    RECOMPENSA_DEPOSITO = 500      
    RECOMPENSA_RECOLHA = 200       
    
    PENALIDADE_ACAO_INVALIDA = -5.0
    PENALIDADE_OBSTACULO = -5.0
    PENALIDADE_COLISAO = -2.0
    
    # Custo de existência (incentiva rapidez)
    CUSTO_MOVIMENTO = -0.1
    PENALIDADE_PARADO = -2.0       
    PENALIDADE_REPETICAO = -5.0    
    
    RECOMPENSA_APROXIMACAO_FATOR = 0.5 
    TAMANHO_HISTORICO = 20 

    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial = num_recursos
        self.num_obstaculos_inicial = num_obstaculos
        self.pos_ninho = None
        self.recursos = set()
        self.obstaculos = set()
        
        # Inicialização importante para garantir que as estruturas existem
        self.agentes_carga = {}
        self._historico_posicoes = {} 
        self._passos_parado = {}
        
        # Gera o mapa inicial
        self._gerar_novo_mapa()

    def reconfigurar(self, **kwargs):
        self.largura = kwargs.get('largura', self.largura)
        self.altura = kwargs.get('altura', self.altura)
        self.num_recursos_inicial = kwargs.get('num_recursos', self.num_recursos_inicial)
        self.num_obstaculos_inicial = kwargs.get('num_obstaculos', self.num_obstaculos_inicial)
        self.reset()

    def _gerar_pos_aleatoria(self, pos_a_evitar=set()):
        count = 0
        while count < 2000:
            pos = (random.randint(0, self.largura - 1), random.randint(0, self.altura - 1))
            if pos not in pos_a_evitar: return pos
            count += 1
        return (0,0) 

    def _gerar_elementos(self, num_elementos, pos_a_evitar=set()):
        elementos = set()
        pos_ocupadas = set(pos_a_evitar)
        attempts = 0
        while len(elementos) < num_elementos and attempts < num_elementos * 10:
            pos = self._gerar_pos_aleatoria(pos_ocupadas)
            elementos.add(pos)
            pos_ocupadas.add(pos)
            attempts += 1
        return elementos

    def _gerar_novo_mapa(self):
        # Gerar Ninho
        self.pos_ninho = self._gerar_pos_aleatoria()
        
        # Gerar Obstáculos
        obs_area = {self.pos_ninho}
        self.obstaculos = self._gerar_elementos(self.num_obstaculos_inicial, obs_area)
        
        # Gerar Recursos
        rec_area = obs_area.union(self.obstaculos)
        self.recursos = self._gerar_elementos(self.num_recursos_inicial, rec_area)

    def reset(self):
        self.terminou = False
        
        # 1. GUARDAR OS AGENTES EXISTENTES (Correção do Bug)
        agentes_existentes = list(self._posicoes_agentes.keys())
        
        # 2. Limpar posições e estados
        self._posicoes_agentes = {} 
        self.agentes_carga = {}
        self._historico_posicoes = {}
        self._passos_parado = {}

        # 3. Gerar novo layout (Ninho, Obstáculos, Recursos)
        self._gerar_novo_mapa()

        # 4. Recolocar os agentes que já existiam
        area_proibida = self.obstaculos.union(self.recursos).union({self.pos_ninho})
        
        for agente in agentes_existentes:
            pos = self._gerar_pos_aleatoria(area_proibida)
            self._posicoes_agentes[agente] = pos
            # Recalcula area proibida para o proximo nao cair em cima deste
            area_proibida.add(pos) 
            
            # Resetar estados internos do agente
            self.agentes_carga[agente] = False
            self._historico_posicoes[agente] = deque(maxlen=self.TAMANHO_HISTORICO)
            self._passos_parado[agente] = 0

    def colocar_agente(self, agente):
        # Usado apenas na inicialização (Simulador.adicionar_agente)
        area_proibida = self.obstaculos.union(self.recursos).union({self.pos_ninho})
        # Adicionar posições de outros agentes para evitar spawn em cima
        for pos in self._posicoes_agentes.values():
            if pos: area_proibida.add(pos)
            
        pos = self._gerar_pos_aleatoria(area_proibida)
        
        super().colocar_agente(agente)
        self._posicoes_agentes[agente] = pos
        self.agentes_carga[agente] = False
        self._historico_posicoes[agente] = deque(maxlen=self.TAMANHO_HISTORICO)
        self._passos_parado[agente] = 0

    def _encontrar_recurso_mais_proximo(self, pos_agente):
        if not self.recursos: return None
        # Distância Manhattan
        return min(self.recursos, key=lambda r: abs(pos_agente[0]-r[0]) + abs(pos_agente[1]-r[1]))

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes: return None
        ax, ay = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)

        # Definir Alvo
        tx, ty = ax, ay
        if carregando:
            tx, ty = self.pos_ninho
        else:
            rec = self._encontrar_recurso_mais_proximo((ax, ay))
            if rec: tx, ty = rec
            elif not self.recursos: tx, ty = self.pos_ninho 

        # Direção relativa
        dx, dy = tx - ax, ty - ay
        dir_alvo = (np.sign(dx), np.sign(dy)) 

        # Distância Discreta (0, 1, 2, 3)
        dist = abs(dx) + abs(dy)
        if dist == 0: d_disc = 0   
        elif dist <= 2: d_disc = 1 
        elif dist <= 8: d_disc = 2 
        else: d_disc = 3           

        # Sensores (8 direções)
        sensores = {}
        dirs_check = [
            ("Norte", (0,-1)), ("Sul", (0,1)), ("Este", (1,0)), ("Oeste", (-1,0)),
            ("NE", (1,-1)), ("SE", (1,1)), ("SW", (-1,1)), ("NW", (-1,-1))
        ]
        for nome, (mx, my) in dirs_check:
            nx, ny = ax + mx, ay + my
            blocked = 1 # Assume bloqueado
            if 0 <= nx < self.largura and 0 <= ny < self.altura:
                if (nx, ny) not in self.obstaculos:
                    blocked = 0
            sensores[nome] = blocked

        return {
            "direcao_alvo": dir_alvo,
            "distancia_discreta": d_disc,
            "sensores": sensores,
            "carregando": carregando
        }

    def agir(self, agente, accao):
        if self.terminou: return 0
        
        # Proteção extra contra KeyError
        if agente not in self._posicoes_agentes:
            return self.PENALIDADE_PARADO
            
        ax, ay = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)
        
        alvo = self.pos_ninho if carregando else self._encontrar_recurso_mais_proximo((ax, ay))
        dist_antes = abs(ax - alvo[0]) + abs(ay - alvo[1]) if alvo else 0

        movimentos = {"Norte": (0,-1), "Sul": (0,1), "Este": (1,0), "Oeste": (-1,0)}
        
        if accao in movimentos:
            dx, dy = movimentos[accao]
            nx, ny = ax + dx, ay + dy
            
            # Verificar colisão com paredes ou obstaculos
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                return self.PENALIDADE_OBSTACULO
            
            # Verificar colisão com outros agentes
            ocupado = False
            for ag_vizinho, pos_vizinho in self._posicoes_agentes.items():
                if ag_vizinho != agente and pos_vizinho == (nx, ny):
                    ocupado = True
                    break
            
            if ocupado: return self.PENALIDADE_COLISAO

            # Mover
            self._posicoes_agentes[agente] = (nx, ny)
            self._passos_parado[agente] = 0
            
            # Recompensa Shaping
            reward = self.CUSTO_MOVIMENTO
            if alvo:
                dist_depois = abs(nx - alvo[0]) + abs(ny - alvo[1])
                reward += (dist_antes - dist_depois) * self.RECOMPENSA_APROXIMACAO_FATOR

            if (nx, ny) in self._historico_posicoes[agente]:
                reward += self.PENALIDADE_REPETICAO
            
            self._historico_posicoes[agente].append((nx, ny))
            return reward

        elif accao == "Recolher":
            if not carregando and (ax, ay) in self.recursos:
                self.recursos.remove((ax, ay))
                self.agentes_carga[agente] = True
                self._historico_posicoes[agente].clear()
                return self.RECOMPENSA_RECOLHA
            return self.PENALIDADE_ACAO_INVALIDA

        elif accao == "Depositar":
            if carregando and (ax, ay) == self.pos_ninho:
                self.agentes_carga[agente] = False
                if not self.recursos: self.terminou = True
                self._historico_posicoes[agente].clear()
                return self.RECOMPENSA_DEPOSITO
            return self.PENALIDADE_ACAO_INVALIDA
            
        else:
            self._passos_parado[agente] += 1
            return self.PENALIDADE_PARADO * self._passos_parado[agente]