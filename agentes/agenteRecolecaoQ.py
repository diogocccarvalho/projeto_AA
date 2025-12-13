from agentes.agenteQ import AgenteQ
import random

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # CORREÇÃO: epsilon_decay alterado de 0.999 (padrão) para 0.99975
        # Isto garante exploração durante ~18.000 episódios em vez de morrer aos 4.000
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon, epsilon_decay=0.99975)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        """
        Converte a observação do ambiente num estado hasheável para a Q-table.
        """
        if obs is None:
            # Estado para quando a observação não é válida (ex: início do episódio)
            return ( (0,0), (0,0), tuple([0]*8), False )

        # A tupla de sensores precisa de ser ordenada para consistência
        sensores_tuple = tuple(sorted(obs['sensores'].values()))

        # O estado é uma combinação da informação contextual (sem distâncias)
        return (
            obs['dir_ninho'],
            obs['dir_recurso'],
            sensores_tuple,
            obs['carregando']
        )

    def _get_accoes_validas(self, estado):
        accoes_validas = ["Norte", "Sul", "Este", "Oeste"]
        # O estado foi encurtado, 'carregando' está agora no índice 3
        carregando = estado[3]
        if carregando:
            accoes_validas.append("Depositar")
        else:
            accoes_validas.append("Recolher")
        return accoes_validas