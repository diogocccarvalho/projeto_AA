import random
import numpy as np
from collections import deque
from ambientes.ambiente import Ambiente
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo

class AmbienteRecolecao(Ambiente):
    # AJUSTE DE RECOMPENSAS PARA EVITAR LOOPING E CLARIFICAR OBJETIVO EVO
    RECOMPENSA_DEPOSITO = 100      # Aumentado para ser o prémio máximo claro
    RECOMPENSA_RECOLHA = 20       
    
    PENALIDADE_ACAO_INVALIDA = -5.0
    PENALIDADE_OBSTACULO = -5.0
    PENALIDADE_COLISAO = -2.0
    
    # --- Recompensas de Shaping (APENAS para não-EVO) ---
    CUSTO_MOVIMENTO = -0.1
    PENALIDADE_PARADO = -2.0       
    PENALIDADE_REPETICAO = -2.0    
    RECOMPENSA_APROXIMACAO_FATOR = 0.5 
    # ---------------------------------------------------------
    
    TAMANHO_HISTORICO = 20 

    def __init__(self, largura=20, altura=20, num_recursos=10, num_obstaculos=10):
        super().__init__(largura, altura)
        self.num_recursos_inicial = num_recursos
        self.num_obstaculos_inicial = num_obstaculos
        self.pos_ninho = None
        self.recursos = set()
        self.obstaculos = set()
        
        self.agentes_carga = {}
        self._historico_posicoes = {} 
        self._passos_parado = {}
        
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

    def _encontrar_caminho(self, inicio, fim):
        if inicio == fim:
            return [inicio]
        fronteira = deque([inicio])
        visitados = {inicio: None}  # Usar um dicionário para guardar o "pai" de cada nó
        while fronteira:
            pos_atual = fronteira.popleft()
            if pos_atual == fim:
                # Reconstruir o caminho a partir do "fim"
                caminho = []
                while pos_atual is not None:
                    caminho.append(pos_atual)
                    pos_atual = visitados[pos_atual]
                return caminho[::-1]  # Inverter para ter do início para o fim

            (x, y) = pos_atual
            for dx, dy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                pos_vizinho = (nx, ny)
                pos_valida = 0 <= nx < self.largura and 0 <= ny < self.altura
                if pos_valida and pos_vizinho not in self.obstaculos and pos_vizinho not in visitados:
                    visitados[pos_vizinho] = pos_atual # Guardar o "pai"
                    fronteira.append(pos_vizinho)
        return None # Não há caminho

    def _gerar_novo_mapa(self):
        self.pos_ninho = self._gerar_pos_aleatoria()
        obs_area = {self.pos_ninho}
        self.obstaculos = self._gerar_elementos(self.num_obstaculos_inicial, obs_area)
        rec_area = obs_area.union(self.obstaculos)
        self.recursos = self._gerar_elementos(self.num_recursos_inicial, rec_area)

    def reset(self):
        self.terminou = False
        self.caminhos_otimos_visual.clear()
        agentes_existentes = list(self._posicoes_agentes.keys())
        self._posicoes_agentes = {} 
        self.agentes_carga = {}
        self._historico_posicoes = {}
        self._passos_parado = {}
        self._gerar_novo_mapa()
        area_proibida = self.obstaculos.union(self.recursos).union({self.pos_ninho})
        
        for agente in agentes_existentes:
            pos = self._gerar_pos_aleatoria(area_proibida)
            self._posicoes_agentes[agente] = pos
            area_proibida.add(pos) 
            self.agentes_carga[agente] = False
            self._historico_posicoes[agente] = deque(maxlen=self.TAMANHO_HISTORICO)
            self._passos_parado[agente] = 0

    def colocar_agente(self, agente):
        area_proibida = self.obstaculos.union(self.recursos).union({self.pos_ninho})
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
        return min(self.recursos, key=lambda r: abs(pos_agente[0]-r[0]) + abs(pos_agente[1]-r[1]))

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes: return None
        ax, ay = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)
        
        nx, ny = self.pos_ninho
        dx_ninho, dy_ninho = nx - ax, ny - ay
        dir_ninho = (np.sign(dx_ninho), np.sign(dy_ninho))

        recurso_prox = self._encontrar_recurso_mais_proximo((ax, ay))
        if recurso_prox:
            rx, ry = recurso_prox
            dx_rec, dy_rec = rx - ax, ry - ay
            dir_recurso = (np.sign(dx_rec), np.sign(dy_rec))
        else:
            dir_recurso = (0, 0)

        sensores = {}
        dirs_check = [("Norte",(0,-1)),("Sul",(0,1)),("Este",(1,0)),("Oeste",(-1,0)),("NE",(1,-1)),("SE",(1,1)),("SW",(-1,1)),("NW",(-1,-1))]
        for nome, (mx, my) in dirs_check:
            nx_sens, ny_sens = ax + mx, ay + my
            blocked = 1
            if 0 <= nx_sens < self.largura and 0 <= ny_sens < self.altura:
                if (nx_sens, ny_sens) not in self.obstaculos:
                    blocked = 0
            sensores[nome] = blocked

        return {
            "dir_ninho": dir_ninho,
            "dir_recurso": dir_recurso,
            "carregando": carregando, 
            "sensores": sensores
        }

    def agir(self, agente, accao):
        if self.terminou: return 0
        
        is_evo = isinstance(agente, AgenteRecolecaoEvo)

        if agente not in self._posicoes_agentes:
            return self.PENALIDADE_PARADO
            
        ax, ay = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False);
        
        movimentos = {"Norte": (0,-1), "Sul": (0,1), "Este": (1,0), "Oeste": (-1,0)}
        
        if accao in movimentos:
            dx, dy = movimentos[accao]
            nx, ny = ax + dx, ay + dy
            
            if not (0 <= nx < self.largura and 0 <= ny < self.altura) or (nx, ny) in self.obstaculos:
                return self.PENALIDADE_OBSTACULO
            
            if any(p == (nx, ny) for ag, p in self._posicoes_agentes.items() if ag != agente):
                return self.PENALIDADE_COLISAO

            self._posicoes_agentes[agente] = (nx, ny)
            self._passos_parado[agente] = 0

            # --- REWARD SHAPING (Aplicado a TODOS os agentes) ---
            alvo = self.pos_ninho if carregando else self._encontrar_recurso_mais_proximo((ax, ay))
            reward = self.CUSTO_MOVIMENTO
            if alvo:
                dist_antes = abs(ax - alvo[0]) + abs(ay - alvo[1])
                dist_depois = abs(nx - alvo[0]) + abs(ny - alvo[1])
                progresso = dist_antes - dist_depois
                reward += (progresso * self.RECOMPENSA_APROXIMACAO_FATOR)
            # --- FIM REWARD SHAPING ---

            # A penalidade de repetição é muito agressiva para o EVO, mantemos apenas para o Q-Learning
            if not is_evo and (nx, ny) in self._historico_posicoes[agente]:
                reward += self.PENALIDADE_REPETICAO
                
            self._historico_posicoes[agente].append((nx, ny))

            # --- LÓGICA DE VISUALIZAÇÃO DO CAMINHO ÓTIMO ---
            if self.visualizacao_ativa and alvo:
                self.caminhos_otimos_visual[agente] = self._encontrar_caminho((nx, ny), alvo)
            # --- FIM ---
            
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
            
        else: # Ação inválida ou "Ficar Parado"
            self._passos_parado[agente] += 1
            return self.PENALIDADE_PARADO * self._passos_parado[agente]