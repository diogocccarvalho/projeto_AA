import random
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):
    # Recompensas
    RECOMPENSA_DEPOSITO = 200
    RECOMPENSA_RECOLHA = 100
    PENALIDADE_ACAO_INVALIDA = -10.0
    CUSTO_MOVIMENTO = -0.1
    
    # Recompensas e penalidades espelhadas do AmbienteFarol
    PENALIDADE_COLISAO = -1.0
    PENALIDADE_OBSTACULO = -5.0
    PENALIDADE_REPETICAO = -2.5
    PENALIDADE_PARADO = -1.0
    RECOMPENSA_APROXIMACAO_FATOR = 5.0
    TAMANHO_HISTORICO = 5
    PENALIDADE_TEMPO_SEM_DEPOSITO = -0.05

    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial = num_recursos
        self.num_obstaculos_inicial = num_obstaculos
        self.passos_sem_deposito = 0
        
        self.pos_ninho = None
        self.recursos = set()
        self.obstaculos = set()
        
        self.agentes_carga = {}
        self._pos_iniciais_agentes = []
        self._historico_posicoes = {} # Adicionado
        self.reset()

    def reconfigurar(self, **kwargs):
        self.largura = kwargs.get('largura', self.largura)
        self.altura = kwargs.get('altura', self.altura)
        self.num_recursos_inicial = kwargs.get('num_recursos', self.num_recursos_inicial)
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
        self.passos_sem_deposito = 0
        for agente in self._posicoes_agentes:
            self._passos_parado[agente] = 0
        num_agentes = len(self._posicoes_agentes)
        for agente in self._posicoes_agentes:
            self.agentes_carga[agente] = False

        while True:
            self.pos_ninho = self._gerar_pos_aleatoria()
            pos_a_evitar = {self.pos_ninho}
            
            self._pos_iniciais_agentes = list(self._gerar_elementos(num_agentes, pos_a_evitar))
            pos_a_evitar.update(self._pos_iniciais_agentes)
            
            num_recursos = random.randint(self.num_recursos_inicial // 2, int(self.num_recursos_inicial * 1.5))
            self.recursos = self._gerar_elementos(num_recursos, pos_a_evitar)
            pos_a_evitar.update(self.recursos)

            num_obstaculos = random.randint(self.num_obstaculos_inicial // 2, int(self.num_obstaculos_inicial * 1.5))
            self.obstaculos = self._gerar_elementos(num_obstaculos, pos_a_evitar)

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
        direcao_alvo = ((dx > 0) - (dx < 0), (dy > 0) - (dy < 0))

        distancia = abs(dx) + abs(dy)
        if distancia < 5:
            distancia_discreta = 0
        elif distancia < 15:
            distancia_discreta = 1
        else:
            distancia_discreta = 2

        sensores = {}
        dirs = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0), "Noroeste": (-1, -1), "Sudoeste": (-1, 1), "Nordeste": (1, -1), "Sudeste": (1, 1)}
        for nome_dir, (dx_s, dy_s) in dirs.items():
            nx, ny = ax + dx_s, ay + dy_s
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                sensores[nome_dir] = 1
            else:
                sensores[nome_dir] = 0

        return {
            "direcao_alvo": direcao_alvo,
            "distancia_discreta": distancia_discreta,
            "sensores": sensores,
            "carregando": carregando
        }

    def agir(self, agente, accao):
        if self.terminou:
            return 0

        self.passos_sem_deposito += 1
        x, y = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)

        alvo = self.pos_ninho if carregando else self._encontrar_recurso_mais_proximo((x, y))

        dist_antes = 0
        if alvo:
            dist_antes = abs(x - alvo[0]) + abs(y - alvo[1])
        else:
            # Se não há alvo, o agente não deve ser penalizado ou recompensado pela distância
            dist_antes = 0

        movimentos = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0)}
        if accao in movimentos:
            dx, dy = movimentos[accao]
            nx, ny = x + dx, y + dy

            sucesso, recompensa_colisao = self._mover_agente(agente, (nx, ny))

            if not sucesso:
                return recompensa_colisao
            
            # Posição atualizada
            nx, ny = self._posicoes_agentes[agente]

            recompensa_dist = 0
            if alvo:
                dist_depois = abs(nx - alvo[0]) + abs(ny - alvo[1])
                recompensa_dist = (dist_antes - dist_depois) * self.RECOMPENSA_APROXIMACAO_FATOR
            
            recompensa_final = self.CUSTO_MOVIMENTO + recompensa_dist

            if (nx, ny) in self._historico_posicoes.get(agente, []):
                recompensa_final += self.PENALIDADE_REPETICAO
            
            self._historico_posicoes[agente].append((nx, ny))
            
            return recompensa_final + (self.passos_sem_deposito * self.PENALIDADE_TEMPO_SEM_DEPOSITO)

        else: # Ações "Recolher" ou "Depositar"
            self._passos_parado[agente] += 1
            penalidade_parado = self._passos_parado[agente] * self.PENALIDADE_PARADO_CRESCENTE

            if accao == "Recolher":
                if (x, y) in self.recursos and not carregando:
                    self.recursos.remove((x,y))
                    self.agentes_carga[agente] = True
                    self._passos_parado[agente] = 0
                    return self.RECOMPENSA_RECOLHA
                else:
                    return self.PENALIDADE_ACAO_INVALIDA + penalidade_parado

            elif accao == "Depositar":
                if (x, y) == self.pos_ninho and carregando:
                    self.agentes_carga[agente] = False
                    self.passos_sem_deposito = 0
                    if not self.recursos:
                        self.terminou = True
                    self._passos_parado[agente] = 0
                    return self.RECOMPENSA_DEPOSITO
                else:
                    return self.PENALIDADE_ACAO_INVALIDA + penalidade_parado
        
        return 0