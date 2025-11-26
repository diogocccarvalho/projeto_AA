#a sobrepor pelos 2 ambientes de cada situação

class Ambiente:
    def __init__(self):
        self._posicoes_agentes = {}

    def atualizacao(self):
        #atualizar o estado de jogo
        pass

    def observacao_para(self, agente):
        #info para agente
        pass

    def agir(self, agente, accao):
        #ação do agente + recompensa
        pass

    def colocar_agente(self, agente, pos_inicial=(0,0)):
        #adicionar agente
        self._posicoes_agentes[agente] = pos_inicial