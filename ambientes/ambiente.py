from abc import ABC, abstractmethod

class Ambiente(ABC):
    PENALIDADE_PARADO_CRESCENTE = -0.2
    # classe abstrata para definir interface de ambientes
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self._posicoes_agentes = {}
        self._passos_parado = {}
        self.terminou = False

    def atualizacao(self):
        pass

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def reconfigurar(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def observacao_para(self, agente):
        raise NotImplementedError

    @abstractmethod
    def agir(self, agente, accao):
        raise NotImplementedError

    def colocar_agente(self, agente):
        self._posicoes_agentes[agente] = None
        self._passos_parado[agente] = 0

    def _is_posicao_valida(self, pos):
        x, y = pos
        if not (0 <= x < self.largura and 0 <= y < self.altura):
            return False  # Fora dos limites
        if hasattr(self, 'obstaculos') and pos in self.obstaculos:
            return False  # Colisão com obstáculo
        return True

    def _mover_agente(self, agente, nova_pos):
        if self._is_posicao_valida(nova_pos):
            self._posicoes_agentes[agente] = nova_pos
            self._passos_parado[agente] = 0
            return True, 0  # Movimento bem-sucedido
        else:
            self._passos_parado[agente] += 1
            penalidade = self._passos_parado[agente] * self.PENALIDADE_PARADO_CRESCENTE
            return False, penalidade  # Movimento inválido/colisão