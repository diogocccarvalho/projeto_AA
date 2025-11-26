import random
from ambientes.ambiente import Ambiente

class AmbienteRecolecao(Ambiente):
    def __init__(self, largura=20, altura=20, num_recursos=10):
        super().__init__()
        self.largura = largura
        self.altura = altura
        
        #posição do ninho aleatória para melhorar treino
        self.pos_ninho = (
            random.randint(0, largura - 1),
            random.randint(0, altura - 1)
        )
        
        # recursos aleatórios
        self.recursos = set()
        while len(self.recursos) < num_recursos:
            rx = random.randint(0, largura - 1)
            ry = random.randint(0, altura - 1)
            
            #adiciona se não for em cima do ninho
            if (rx, ry) != self.pos_ninho:
                self.recursos.add((rx, ry))
        

        self.agentes_carga = {}

    def atualizacao(self):
        # todo
        pass

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes:
            return None
        
        return {
            "posicao": self._posicoes_agentes[agente],
            "ninho": self.pos_ninho,
            "recursos": list(self.recursos),
            "carregando": self.agentes_carga.get(agente, False)
        }

    def colocar_agente(self, agente, pos_inicial=None):
        self.agentes_carga[agente] = False

        if pos_inicial:
            self._posicoes_agentes[agente] = pos_inicial
            return

        # posição random
        while True:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            
            #não nascer no ninho/recursos
            if (x, y) != self.pos_ninho and (x, y) not in self.recursos:
                self._posicoes_agentes[agente] = (x, y)
                break

    def agir(self, agente, accao):
        x, y = self._posicoes_agentes[agente]
        carregando = self.agentes_carga.get(agente, False)
        recompensa = 0
        
        dx, dy = 0, 0
        if accao == "Norte": dy = -1
        elif accao == "Sul": dy = 1
        elif accao == "Este": dx = 1
        elif accao == "Oeste": dx = -1
        
        if dx != 0 or dy != 0:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.largura and 0 <= ny < self.altura:
                self._posicoes_agentes[agente] = (nx, ny)
                recompensa = -0.1 #energia
            else:
                recompensa = -1 #se bater na parede
        
        elif accao == "Recolher":
            if (x, y) in self.recursos and not carregando:
                self.recursos.remove((x, y))
                self.agentes_carga[agente] = True
                recompensa = 10
                print(f"> Agente apanhou recurso em {(x,y)}!")
            else:
                recompensa = -2 #falha recolha

        # --- Depositar ---
        elif accao == "Depositar":
            if (x, y) == self.pos_ninho and carregando:
                self.agentes_carga[agente] = False
                recompensa = 50 #entrega
                print(f">>> ENTREGA FEITA NO NINHO {(x,y)}! <<<")
            else:
                recompensa = -2 #falha entrega
        
        return recompensa

    def display(self):
        grelha = [['.' for _ in range(self.largura)] for _ in range(self.altura)]
        
        # Ninho
        nx, ny = self.pos_ninho
        grelha[ny][nx] = 'N'
        
        # Recursos
        for (rx, ry) in self.recursos:
            grelha[ry][rx] = 'R'
            
        # Agentes
        for agente, pos in self._posicoes_agentes.items():
            ax, ay = pos
            char = 'A' if self.agentes_carga.get(agente, False) else 'a'
            grelha[ay][ax] = char

        print("-" * (self.largura + 2))
        for linha in grelha:
            print("|" + "".join(linha) + "|")
        print("-" * (self.largura + 2))