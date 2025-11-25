from agente import Agente

class AgenteTeste(Agente):
    def __init__(self, accoes):
        super().__init__()
        self.accoes = accoes

    def age(self):
        if self.accoes:
            return self.accoes.pop(0)
        return "Norte" # Ação padrão se a lista estiver vazia
