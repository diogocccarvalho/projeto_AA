import random
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteFarol(Ambiente):
    RECOMPENSA_FAROL = 1000
    
    # NOVAS PENALIDADES (Balanceadas para evitar "Cabeçadas na Parede")
    PENALIDADE_OBSTACULO = -5.0   # Pior de todos
    PENALIDADE_COLISAO = -2.0     # Mau (Bater nos limites)
    PENALIDADE_REPETICAO = -1.5   # Mau, mas melhor que bater (Permite sair de dead-ends)
    
    CUSTO_MOVIMENTO = -0.01
    PENALIDADE_PARADO = -1.0
    
    # Aumentar memória para evitar loops em mapas grandes
    TAMANHO_HISTORICO = 40       
    
    RECOMPENSA_APROXIMACAO_FATOR = 1 
    PENALIDADE_TEMPO_FATOR = 0.01    
    MIN_DIST_INICIAL = 5       

    def __init__(self, largura=20, altura=20, num_obstaculos=20):
        super().__init__(largura, altura)
        self.num_obstaculos_inicial = num_obstaculos
        self.pos_farol = None
        self.obstaculos = set()
        self._pos_iniciais_agentes = []
        self._historico_posicoes = {}
        self.passos_no_episodio = 0
        self.reset()

    def reconfigurar(self, **kwargs):
        self.largura = kwargs.get('largura', self.largura)
        self.altura = kwargs.get('altura', self.altura)
        self.num_obstaculos_inicial = kwargs.get('num_obstaculos', self.num_obstaculos_inicial)
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
        if inicio == fim: return True
        fronteira = deque([inicio])
        visitados = {inicio}
        while fronteira:
            (x, y) = fronteira.popleft()
            if (x, y) == fim: return True
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
        for agente in self._posicoes_agentes:
            self._passos_parado[agente] = 0
        num_agentes = len(self._posicoes_agentes)

        while True:
            self.pos_farol = self._gerar_pos_aleatoria()
            pos_a_evitar = {self.pos_farol}
            self._pos_iniciais_agentes = list(self._gerar_elementos(num_agentes, pos_a_evitar))

            perto_demais = False
            for pos_agente in self._pos_iniciais_agentes:
                dist = abs(pos_agente[0] - self.pos_farol[0]) + abs(pos_agente[1] - self.pos_farol[1])
                if dist < self.MIN_DIST_INICIAL:
                    perto_demais = True
                    break
            if perto_demais: continue

            pos_a_evitar.update(self._pos_iniciais_agentes)
            num_obstaculos = random.randint(self.num_obstaculos_inicial // 2, int(self.num_obstaculos_inicial * 1.5))
            self.obstaculos = self._gerar_elementos(num_obstaculos, pos_a_evitar)
            
            if num_agentes == 0 or all(self._tem_caminho(pos_inicial, self.pos_farol) for pos_inicial in self._pos_iniciais_agentes):
                break
        
        for i, agente in enumerate(self._posicoes_agentes.keys()):
            self._posicoes_agentes[agente] = self._pos_iniciais_agentes[i]
        
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

        dx = fx - ax
        dy = fy - ay
        dist_discreta = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))

        sensores = {}
        dirs = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0), "Noroeste": (-1, -1), "Sudoeste": (-1, 1), "Nordeste": (1, -1), "Sudeste": (1, 1)}
        for nome_dir, (dx, dy) in dirs.items():
            nx, ny = ax + dx, ay + dy
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                sensores[nome_dir] = 1
            else:
                sensores[nome_dir] = 0

        return {
            "distancia_discreta": dist_discreta,
            "sensores": sensores
        }

    def agir(self, agente, accao):
        if self.terminou: return 0

        self.passos_no_episodio += 1
        x, y = self._posicoes_agentes[agente]
        fx, fy = self.pos_farol

        dist_antes = abs(x - fx) + abs(y - fy)
        
        movimentos = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0)}
        dx, dy = movimentos.get(accao, (0, 0))
        nx, ny = x + dx, y + dy

        sucesso, _ = self._mover_agente(agente, (nx, ny))
        
        # CORREÇÃO: Usar penalidades explícitas
        if not sucesso:
            if (nx, ny) in self.obstaculos:
                return self.PENALIDADE_OBSTACULO
            return self.PENALIDADE_COLISAO # Paredes

        x, y = self._posicoes_agentes[agente]
        if (x, y) == self.pos_farol:
            self.terminou = True
            return self.RECOMPENSA_FAROL
        
        dist_depois = abs(x - fx) + abs(y - fy)
        recompensa_dist = (dist_antes - dist_depois) * self.RECOMPENSA_APROXIMACAO_FATOR
        recompensa_final = self.CUSTO_MOVIMENTO + recompensa_dist

        if (x, y) in self._historico_posicoes.get(agente, []):
            recompensa_final += self.PENALIDADE_REPETICAO
        
        if agente in self._historico_posicoes:
            self._historico_posicoes[agente].append((x, y))

        recompensa_final -= self.PENALIDADE_TEMPO_FATOR
        return recompensa_final