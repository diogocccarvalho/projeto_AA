from agentes.agenteQ import AgenteQ
import random

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # CORREÇÃO: epsilon_decay alterado de 0.999 (padrão) para 0.99975
        # Isto garante exploração durante ~18.000 episódios em vez de morrer aos 4.000
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon, epsilon_decay=0.99975)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        if obs is None:
            # Default state: no direction, medium distance, no obstacles, not carrying, no last action
            return ((0, 0), 1, tuple(), False, None)

        # Converter o dicionário de sensores para uma tuple de items para ser hasheable
        sensores_tuple = tuple(sorted(obs['sensores'].items()))
        
        # O estado inclui a última ação para evitar o "back and forth"
        return (obs['direcao_alvo'], obs['distancia_discreta'], sensores_tuple, obs['carregando'], self.acao_anterior)

    def _get_accoes_validas(self, estado):
        accoes_validas = ["Norte", "Sul", "Este", "Oeste"]
        carregando = estado[3]
        if carregando:
            accoes_validas.append("Depositar")
        else:
            accoes_validas.append("Recolher")
        return accoes_validas