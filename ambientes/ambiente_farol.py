import random
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteFarol(Ambiente):
    #recompensas
    RECOMPENSA_FAROL = 1000
    PENALIDADE_COLISAO = -1.0
    PENALIDADE_OBSTACULO = -5.0
    CUSTO_MOVIMENTO = -0.01
    PENALIDADE_REPETICAO = -5.0  # Penalidade por visitar posições recentes
    PENALIDADE_PARADO = -1.0     # Penalidade adicional por colidir e ficar parado
    TAMANHO_HISTORICO = 5       # Número de passos a lembrar
    RECOMPENSA_APROXIMACAO_FATOR = 5 # Fator de multiplicação para a recompensa de aproximação
    PENALIDADE_TEMPO_FATOR = 0.01    # Fator de penalidade por passo
    MIN_DIST_INICIAL = 5       # Distância mínima inicial entre agente e farol

    def __init__(self, largura=20, altura=20, num_obstaculos=20):
        super().__init__(largura, altura)
        self.num_obstaculos_inicial = num_obstaculos
        self.pos_farol = None
        self.obstaculos = set()
        self._pos_iniciais_agentes = []
        self._historico_posicoes = {}
        self.passos_no_episodio = 0
        self.reset()


    def _gerar_pos_aleatoria(self, pos_a_evitar=set()):
        while True:
            pos = (random.randint(0, self.largura - 1), random.randint(0, self.altura - 1))
            if pos not in pos_a_evitar:
                return pos

    def _gerar_elementos(self, num_elementos, pos_a_evitar=set()):
        #gerar posições válidas para meter tudo
        elementos = set()
        pos_ocupadas = set(pos_a_evitar)
        
        num_a_gerar = min(num_elementos, self.largura * self.altura - len(pos_ocupadas))
        
        for _ in range(num_a_gerar):
            pos = self._gerar_pos_aleatoria(pos_ocupadas)
            elementos.add(pos)
            pos_ocupadas.add(pos)
        return elementos

    def _tem_caminho(self, inicio, fim):
        #bfs de novo
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
        self.passos_no_episodio = 0
        num_agentes = len(self._posicoes_agentes)

        #loop para ver se o mapa é válido
        while True:
            self.pos_farol = self._gerar_pos_aleatoria()
            
            pos_a_evitar = {self.pos_farol}
            self._pos_iniciais_agentes = list(self._gerar_elementos(num_agentes, pos_a_evitar))

            # Verificar se o agente está muito perto do farol
            perto_demais = False
            for pos_agente in self._pos_iniciais_agentes:
                dist = abs(pos_agente[0] - self.pos_farol[0]) + abs(pos_agente[1] - self.pos_farol[1])
                if dist < self.MIN_DIST_INICIAL:
                    perto_demais = True
                    break
            
            if perto_demais:
                continue

            pos_a_evitar.update(self._pos_iniciais_agentes)
            self.obstaculos = self._gerar_elementos(self.num_obstaculos_inicial, pos_a_evitar)
            
            #verificar caminho
            if num_agentes == 0 or all(self._tem_caminho(pos_inicial, self.pos_farol) for pos_inicial in self._pos_iniciais_agentes):
                break
        
        for i, agente in enumerate(self._posicoes_agentes.keys()):
            self._posicoes_agentes[agente] = self._pos_iniciais_agentes[i]
        
        # Limpar históricos de posições
        for hist in self._historico_posicoes.values():
            hist.clear()

    def colocar_agente(self, agente):
        super().colocar_agente(agente)
        if agente not in self._historico_posicoes:
            self._historico_posicoes[agente] = deque(maxlen=self.TAMANHO_HISTORICO)

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes or self._posicoes_agentes[agente] is None:
            return None
        
        ax, ay = self._posicoes_agentes[agente]
        fx, fy = self.pos_farol

        # Discretizar a distância para o farol
        dx = fx - ax
        dy = fy - ay
        dist_discreta = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))

        # Sensores de obstaculos
        sensores = []
        # Norte, Sul, Este, Oeste, Noroeste, Sudoeste, Nordeste, Sudeste
        dirs = [(0, -1), (0, 1), (1, 0), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in dirs:
            nx, ny = ax + dx, ay + dy
            # 1 se for obstáculo ou parede, 0 caso contrário
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                sensores.append(1)
            else:
                sensores.append(0)

        return {
            "distancia_discreta": dist_discreta,
            "sensores": tuple(sensores)
        }

    def agir(self, agente, accao):
        if self.terminou:
            return 0

        self.passos_no_episodio += 1
        x, y = self._posicoes_agentes[agente]
        fx, fy = self.pos_farol

        # Distância de Manhattan antes do movimento
        dist_antes = abs(x - fx) + abs(y - fy)
        
        movimentos = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0)}
        dx, dy = movimentos.get(accao, (0, 0))

        nx, ny = x + dx, y + dy

        # Lógica de colisão
        pos_valida = 0 <= nx < self.largura and 0 <= ny < self.altura
        
        if not pos_valida:  # Colisão com a parede
            # Posição não muda
            return self.PENALIDADE_COLISAO + self.PENALIDADE_PARADO
        
        if (nx, ny) in self.obstaculos:  # Colisão com obstáculo
            # Posição não muda
            return self.PENALIDADE_OBSTACULO

        # Colisão com outro agente
        if (nx, ny) in self._posicoes_agentes.values() and (nx, ny) != (x,y):
            # Posição não muda
            return self.PENALIDADE_COLISAO

        # Se não houver colisão, o agente move-se
        self._posicoes_agentes[agente] = (nx, ny)
        
        if (nx, ny) == self.pos_farol:
            self.terminou = True
            return self.RECOMPENSA_FAROL
        
        # Distância de Manhattan depois do movimento
        dist_depois = abs(nx - fx) + abs(ny - fy)
        
        # Reward shaping: recompensa amplificada por se aproximar do farol
        recompensa_dist = (dist_antes - dist_depois) * self.RECOMPENSA_APROXIMACAO_FATOR

        recompensa_final = self.CUSTO_MOVIMENTO + recompensa_dist

        # Penalidade por repetição de posições recentes
        if (nx, ny) in self._historico_posicoes.get(agente, []):
            recompensa_final += self.PENALIDADE_REPETICAO
        
        # Adicionar posição atual ao histórico
        if agente in self._historico_posicoes:
            self._historico_posicoes[agente].append((nx, ny))

        # Penalidade de tempo constante por passo
        recompensa_final -= self.PENALIDADE_TEMPO_FATOR

        return recompensa_final