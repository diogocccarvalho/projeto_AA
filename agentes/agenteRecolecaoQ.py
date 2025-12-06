from agentes.agenteQ import AgenteQ
import random

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            # Default state: no direction, medium distance, no obstacles, not carrying
            return ((0, 0), 1, tuple(), False)

        # Converter o dicionário de sensores para uma tuple de items para ser hasheable
        sensores_tuple = tuple(sorted(obs['sensores'].items()))
        return (obs['direcao_alvo'], obs['distancia_discreta'], sensores_tuple, obs['carregando'])

    def _get_accoes_validas(self, estado):
        accoes_validas = ["Norte", "Sul", "Este", "Oeste"]
        carregando = estado[3]
        if carregando:
            accoes_validas.append("Depositar")
        else:
            accoes_validas.append("Recolher")
        return accoes_validas
