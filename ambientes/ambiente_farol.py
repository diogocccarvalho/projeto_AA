import random
from ambiente import Ambiente

class AmbienteFarol(Ambiente):
    def __init__(self, largura=20, altura=20):
        super().__init__()
        self.largura = largura
        self.altura = altura
        
        # posição de farol aleatória para otimizar o treino
        self.pos_farol = (
            random.randint(0, largura - 1),
            random.randint(0, altura - 1)
        )
        print(f"Ambiente Farol: Alvo em {self.pos_farol}")
        self.obstaculos = []

    def atualizacao(self):
        pass

    def observacao_para(self, agente):
        if agente not in self._posicoes_agentes:
            return None
        ax, ay = self._posicoes_agentes[agente]
        fx, fy = self.pos_farol
        return (fx - ax, fy - ay)

    def colocar_agente(self, agente, pos_inicial=None):
        # spawnar agente com distância mínima do farol
        if pos_inicial:
            self._posicoes_agentes[agente] = pos_inicial
            return

        distancia_minima = 5
        fx, fy = self.pos_farol
        
        while True:
            x = random.randint(0, self.largura - 1)
            y = random.randint(0, self.altura - 1)
            dist = abs(fx - x) + abs(fy - y)
            
            if dist >= distancia_minima:
                self._posicoes_agentes[agente] = (x, y)
                break

    def agir(self, agente, accao):
        x, y = self._posicoes_agentes[agente]
        fx, fy = self.pos_farol
        
        dist_antiga = abs(fx - x) + abs(fy - y)

        dx, dy = 0, 0
        if accao == "Norte": dy = -1
        elif accao == "Sul": dy = 1
        elif accao == "Este": dx = 1
        elif accao == "Oeste": dx = -1

        nx, ny = x + dx, y + dy
        recompensa = 0

        if 0 <= nx < self.largura and 0 <= ny < self.altura:
            self._posicoes_agentes[agente] = (nx, ny)
            
            dist_nova = abs(fx - nx) + abs(fy - ny)

            if (nx, ny) == self.pos_farol:
                recompensa = 100
                print(">>> CHEGOU! <<<")
            else:
                recompensa = -1 
                if dist_nova < dist_antiga:
                    recompensa += 0.5
        else:
            recompensa = -5 

        return recompensa

    def display(self):
        # Cria uma grelha vazia com pontos
        grelha = [['.' for _ in range(self.largura)] for _ in range(self.altura)]
        
        # Coloca o Farol
        fx, fy = self.pos_farol
        grelha[fy][fx] = 'F'
        
        # Coloca os Agentes
        for agente, pos in self._posicoes_agentes.items():
            ax, ay = pos
            grelha[ay][ax] = 'A'
            
        # Imprime no ecrã
        print("-" * (self.largura + 2))
        for linha in grelha:
            print("|" + "".join(linha) + "|")
        print("-" * (self.largura + 2))