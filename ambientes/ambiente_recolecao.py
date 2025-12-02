import random
from collections import deque
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):

    
    #recompensas
    RECOMPENSA_DEPOSITO = 50
    RECOMPENSA_RECOLHA = 10
    PENALIDADE_ACAO_INVALIDA = -2.0
    PENALIDADE_COLISAO = -1.0
    CUSTO_MOVIMENTO = -0.1

    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial = num_recursos
        self.num_obstaculos_inicial = num_obstaculos
        
        self.pos_ninho = None
        self.recursos = set()
        self.obstaculos = set()
        
        self.agentes_carga = {}
        self._pos_iniciais_agentes = []
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
        #por descargo de consciencia, bfs para garantir que existe caminho do agente ao goal
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
            
            # Gerar posições para agentes, recursos e obstáculos
            self._pos_iniciais_agentes = list(self._gerar_elementos(num_agentes, pos_a_evitar))
            pos_a_evitar.update(self._pos_iniciais_agentes)
            
            self.recursos = self._gerar_elementos(self.num_recursos_inicial, pos_a_evitar)
            pos_a_evitar.update(self.recursos)

            self.obstaculos = self._gerar_elementos(self.num_obstaculos_inicial, pos_a_evitar)

            #garantir caminho
            if num_agentes == 0 or all(self._tem_caminho(pos, self.pos_ninho) for pos in self._pos_iniciais_agentes):
                break
        
        for i, agente in enumerate(self._posicoes_agentes.keys()):
            self._posicoes_agentes[agente] = self._pos_iniciais_agentes[i]

    def colocar_agente(self, agente):
        super().colocar_agente(agente)
        self.agentes_carga[agente] = False

    def observacao_para(self, agente):
        #todo posicoes de ninho/recursos
        if agente not in self._posicoes_agentes or self._posicoes_agentes[agente] is None:
            return None
        return {
            "posicao": self._posicoes_agentes[agente],
            "carregando": self.agentes_carga.get(agente, False)
        }

    def agir(self, agente, accao):
        if self.terminou:
            return 0

        pos = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)

        movimentos = {"Norte": (0, -1), "Sul": (0, 1), "Este": (1, 0), "Oeste": (-1, 0)}
        if accao in movimentos:
            dx, dy = movimentos[accao]
            nx, ny = pos[0] + dx, pos[1] + dy

            pos_valida = 0 <= nx < self.largura and 0 <= ny < self.altura
            if pos_valida and (nx, ny) not in self.obstaculos:
                self._posicoes_agentes[agente] = (nx, ny)
                return self.CUSTO_MOVIMENTO
            else:
                return self.PENALIDADE_COLISAO

        elif accao == "Recolher":
            if pos in self.recursos and not carregando:
                self.recursos.remove(pos)
                self.agentes_carga[agente] = True
                return self.RECOMPENSA_RECOLHA
            else:
                return self.PENALIDADE_ACAO_INVALIDA

        elif accao == "Depositar":
            if pos == self.pos_ninho and carregando:
                self.agentes_carga[agente] = False
                #se não existem mais recurso, reset (no sim)
                if not self.recursos: self.terminou = True
                return self.RECOMPENSA_DEPOSITO
            else:
                return self.PENALIDADE_ACAO_INVALIDA
        
        return 0