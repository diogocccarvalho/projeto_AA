from agentes.agenteQ import AgenteQ
import random

class AgenteRecolecaoQ(AgenteQ):
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=1.0):
        # CORREÇÃO: epsilon_decay alterado de 0.999 (padrão) para 0.99975
        super().__init__(alpha=alpha, gamma=gamma, epsilon=epsilon, epsilon_decay=0.999)
        self.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]

    def _formar_estado(self, obs):
        """
        Converte a observação do ambiente num estado hasheável para a Q-table.
        """
        if obs is None:
            return ( (0,0), (0,0), tuple([0]*8), False )

        # FIX: Forçar conversão para int padrão do Python
        nx, ny = obs['dir_ninho']
        dir_ninho = (int(nx), int(ny))
        
        rx, ry = obs['dir_recurso']
        dir_recurso = (int(rx), int(ry))

        # Sorted garante que a ordem 'Norte', 'Sul' etc se mantém consistente
        sensores_tuple = tuple(sorted(obs['sensores'].items()))

        # O estado é uma combinação da informação contextual
        return (
            dir_ninho,
            dir_recurso,
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