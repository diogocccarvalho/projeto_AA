import random
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):
    # Recompensas
    RECOMPENSA_DEPOSITO = 100
    RECOMPENSA_RECOLHA = 50
    PENALIDADE_ACAO_INVALIDA = -5.0
    CUSTO_MOVIMENTO = -0.1
    
    # Recompensas e penalidades espelhadas do AmbienteFarol
    PENALIDADE_COLISAO = -1.0
    PENALIDADE_OBSTACULO = -5.0
    PENALIDADE_REPETICAO = -2.0
    PENALIDADE_PARADO = -1.0
    RECOMPENSA_APROXIMACAO_FATOR = 3.0
    TAMANHO_HISTORICO = 5

    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial = num_recursos
        self.num_obstaculos_inicial = num_obstaculos
        
        self.pos_ninho = None
        self.recursos = set()
        self.obstaculos = set()
        
        self.agentes_carga = {}
        self._pos_iniciais_agentes = []
        self._historico_posicoes = {} # Adicionado
        self.reset()


    def _gerar_pos_aleatoria(self, pos_a_evitar=set()):
        while True:
            pos = (random.randint(0, self.largura - 1), random.randint(0, self.altura - 1))
            if pos not in pos_a_evitar:
                return pos

    def _gerar_elementos(self, num_elementos, pos_a_evitar=set()):
        elementos = set()
        pos_ocupadas = set(pos_a_evitar)
        num_a_gerar = min(num_elementos, self.largura * self.altura - len(pos_ocupadas))
        for _ in range(num_a_gerar):
            pos = self._gerar_pos_aleatoria(pos_ocupadas)
            elementos.add(pos)
            pos_ocupadas.add(pos)
        return elementos

    def _tem_caminho(self, inicio, fim):
        if not fim: return True # Se não há alvo, há "caminho"
        if inicio == fim:
            return True
        fronteira = deque([inicio])
        visitados = {inicio}
        while fronteira:
            (x, y) = fronteira.popleft()
            if (x, y) == fim:
                return True
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                pos_vizinho = (nx, ny)
                pos_valida = 0 <= nx < self.largura and 0 <= ny < self.altura
                if pos_valida and pos_vizinho not in self.obstaculos and pos_vizinho not in visitados:
                    visitados.add(pos_vizinho)
                    fronteira.append(pos_vizinho)
        return False


    def reset(self):
        self.terminou = False
        num_agentes = len(self._posicoes_agentes)
        for agente in self._posicoes_agentes:
            self.agentes_carga[agente] = False

        while True:
            self.pos_ninho = self._gerar_pos_aleatoria()
            pos_a_evitar = {self.pos_ninho}
            
            self._pos_iniciais_agentes = list(self._gerar_elementos(num_agentes, pos_a_evitar))
            pos_a_evitar.update(self._pos_iniciais_agentes)
            
            self.recursos = self._gerar_elementos(self.num_recursos_inicial, pos_a_evitar)
            pos_a_evitar.update(self.recursos)

            self.obstaculos = self._gerar_elementos(self.num_obstaculos_inicial, pos_a_evitar)

            caminho_ok = True
            for pos_agente in self._pos_iniciais_agentes:
                caminho_para_ninho = self._tem_caminho(pos_agente, self.pos_ninho)
                caminho_para_recurso = any(self._tem_caminho(pos_agente, r) for r in self.recursos)
                if not (caminho_para_ninho and (caminho_para_recurso or not self.recursos)):
                    caminho_ok = False
                    break
            if caminho_ok:
                break
        
        for i, agente in enumerate(self._posicoes_agentes.keys()):
            self._posicoes_agentes[agente] = self._pos_iniciais_agentes[i]
        
        for hist in self._historico_posicoes.values():
            hist.clear()

    def colocar_agente(self, agente):
        super().colocar_agente(agente)
        self.agentes_carga[agente] = False
        if agente not in self._historico_posicoes:
            self._historico_posicoes[agente] = deque(maxlen=self.TAMANHO_HISTORICO)

    def _encontrar_recurso_mais_proximo(self, pos_agente):
        if not self.recursos:
            return None
        
        recursos_dist = [(r, abs(pos_agente[0] - r[0]) + abs(pos_agente[1] - r[1])) for r in self.recursos]
        recursos_dist.sort(key=lambda x: x[1])
        return recursos_dist[0][0]

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes or self._posicoes_agentes[agente] is None:
            return None

        pos_agente = self._posicoes_agentes[agente]
        ax, ay = pos_agente
        carregando = self.agentes_carga.get(agente, False)

        if carregando:
            tx, ty = self.pos_ninho
        else:
            pos_recurso_proximo = self._encontrar_recurso_mais_proximo(pos_agente)
            if pos_recurso_proximo:
                tx, ty = pos_recurso_proximo
            else: 
                tx, ty = ax, ay 

        dx = tx - ax
        dy = ty - ay
        dist_discreta_alvo = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))

        sensores = []
        dirs = [(0, -1), (0, 1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx_s, dy_s in dirs:
            nx, ny = ax + dx_s, ay + dy_s
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                sensores.append(1)
            else:
                sensores.append(0)

        return {
            "direcao_alvo": dist_discreta_alvo,
            "sensores": tuple(sensores),
            "carregando": carregando
        }

    def agir(self, agente, accao):
        if self.terminou:
            return 0

        x, y = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)

        alvo = self.pos_ninho if carregando else self._encontrar_recurso_mais_proximo((x,y))
        
        dist_antes = 0
        if alvo:
            dist_antes = abs(x - alvo[0]) + abs(y - alvo[1])

        movimentos = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0)}
        if accao in movimentos:
            dx, dy = movimentos[accao]
            nx, ny = x + dx, y + dy

            pos_valida = 0 <= nx < self.largura and 0 <= ny < self.altura
            if not pos_valida:
                return self.PENALIDADE_COLISAO + self.PENALIDADE_PARADO
            if (nx, ny) in self.obstaculos:
                return self.PENALIDADE_OBSTACULO
            
            outros_agentes_pos = [p for a, p in self._posicoes_agentes.items() if a != agente]
            if (nx, ny) in outros_agentes_pos:
                return self.PENALIDADE_COLISAO

            self._posicoes_agentes[agente] = (nx, ny)
            
            recompensa_dist = 0
            if alvo:
                dist_depois = abs(nx - alvo[0]) + abs(ny - alvo[1])
                recompensa_dist = (dist_antes - dist_depois) * self.RECOMPENSA_APROXIMACAO_FATOR
            
            recompensa_final = self.CUSTO_MOVIMENTO + recompensa_dist

            if (nx, ny) in self._historico_posicoes.get(agente, []):
                recompensa_final += self.PENALIDADE_REPETICAO
            
            self._historico_posicoes[agente].append((nx, ny))
            
            return recompensa_final

        elif accao == "Recolher":
            if (x, y) in self.recursos and not carregando:
                self.recursos.remove((x,y))
                self.agentes_carga[agente] = True
                return self.RECOMPENSA_RECOLHA
            else:
                return self.PENALIDADE_ACAO_INVALIDA

        elif accao == "Depositar":
            if (x, y) == self.pos_ninho and carregando:
                self.agentes_carga[agente] = False
                if not self.recursos:
                    self.terminou = True
                return self.RECOMPENSA_DEPOSITO
            else:
                return self.PENALIDADE_ACAO_INVALIDA
        
        return 0