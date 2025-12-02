from abc import ABC, abstractmethod

class Ambiente(ABC):
    # classe abstrata para definir interface de ambientes
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self._posicoes_agentes = {}
        self.terminou = False

    def atualizacao(self):
        pass

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def observacao_para(self, agente):
        raise NotImplementedError

    @abstractmethod
    def agir(self, agente, accao):
        raise NotImplementedError

    def colocar_agente(self, agente):
        self._posicoes_agentes[agente] = None