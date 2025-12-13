from agentes.agente import Agente
import random

class AgenteFixo(Agente):
    def __init__(self):
        super().__init__()
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def age(self):
        obs = self.ultima_observacao
        if obs is None:
            return random.choice(self.accoes)

        # Lógica para o ambiente de Recolecao
        if 'carregando' in obs:
            if obs['carregando']:
                # Se estiver carregando, vai para o ninho
                if obs['dist_ninho'] == 0:
                    return "Depositar"
                dx, dy = obs['dir_ninho']
            else:
                # Se não estiver carregando, vai para o recurso mais próximo
                if obs['dist_recurso'] == 0:
                    return "Recolher"
                dx, dy = obs['dir_recurso']
        # Lógica para o ambiente do Farol
        elif 'distancia_discreta' in obs:
            dx, dy = obs['distancia_discreta']
        else:
            return random.choice(["Norte", "Sul", "Este", "Oeste"])

        # Mapear direção para ação
        if dx == 1:
            return "Este"
        elif dx == -1:
            return "Oeste"
        elif dy == 1:
            return "Sul"
        elif dy == -1:
            return "Norte"
        
        # Se estiver em cima do objetivo (dist (0,0)) ou se houver um obstáculo, escolhe uma ação aleatória
        return random.choice(["Norte", "Sul", "Este", "Oeste"])

    def obter_accao(self, estado, accoes_validas):
        # Este agente não usa Q-learning, então apenas chama age()
        return self.age(estado)

    def treinar(self, estado_anterior, accao, recompensa, estado_novo):
        pass
