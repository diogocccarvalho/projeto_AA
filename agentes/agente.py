import random

class Agente:
    def __init__(self):
        self.ultima_observacao = None
        self.recompensa_total = 0

    def observacao(self, obs):
        """
        Recebe os dados do ambiente (Sensores).z
        """
        self.ultima_observacao = obs

    def age(self):
        """
        Decide qual a ação a tomar.
        Deve ser sobrescrito pelas subclasses.
        """
        raise NotImplementedError("Este método deve ser implementado pela subclasse")

    def avaliacao_estado_atual(self, recompensa):
        """
        Recebe o feedback (Recompensa) da última ação.
        """
        self.recompensa_total += recompensa

        print(f"Score atual: {self.recompensa_total}")


class AgenteRandom(Agente):
    def __init__(self):
        super().__init__()
        # Define as ações possíveis num mundo de grelha
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def age(self):

        acao_escolhida = random.choice(self.accoes)
        return acao_escolhida