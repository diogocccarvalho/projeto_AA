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

        dx, dy = 0, 0

        # --- Lógica para Ambiente Recolecao ---
        if 'carregando' in obs:
            if obs['carregando']:
                # Se carregado, vai ao ninho
                if obs['dir_ninho'] == (0, 0): # Chegou
                    return "Depositar"
                dx, dy = obs['dir_ninho']
            else:
                # Se vazio, vai ao recurso
                if obs['dir_recurso'] == (0, 0): # Chegou (ou não há recursos)
                    return "Recolher"
                dx, dy = obs['dir_recurso']
        
        # --- Lógica para Ambiente Farol ---
        elif 'direcao_alvo' in obs:
            dx, dy = obs['direcao_alvo']
        
        else:
            # Fallback
            return random.choice(["Norte", "Sul", "Este", "Oeste"])

        # Mapear direção (dx, dy) para ação
        # (dx, dy) são valores normalizados (-1, 0, 1)
        if dx == 1:
            return "Este"
        elif dx == -1:
            return "Oeste"
        elif dy == 1:
            return "Sul"
        elif dy == -1:
            return "Norte"
        
        # Se dx=0, dy=0 e não retornou antes, movimento aleatório para desbloquear
        return random.choice(["Norte", "Sul", "Este", "Oeste"])

    def obter_accao(self, estado, accoes_validas):
        return self.age()

    def treinar(self, *args):
        pass