import random

# ==============================================================================
# 1. CLASSE MÃE (Interface Genérica)
# Define o que todos os agentes têm de ter, sejam burros ou inteligentes.
# ==============================================================================
class Agente:
    def __init__(self):
        self.ultima_observacao = None
        self.recompensa_total = 0

    def observacao(self, obs):
        """
        Recebe os dados do ambiente (Sensores).
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
        # Opcional: podes descomentar para ver o score a mudar em tempo real
        # print(f"Score atual: {self.recompensa_total}")

# ==============================================================================
# 2. AGENTE DE TESTE (Random Walk)
# Serve apenas para validar a simulação na Fase 1.
# ==============================================================================
class AgenteRandom(Agente):
    def __init__(self):
        super().__init__()
        # Define as ações possíveis num mundo de grelha
        self.accoes = ["Norte", "Sul", "Este", "Oeste"]

    def age(self):
        """
        Comportamento: Escolhe uma direção totalmente à sorte.
        Ignora a observação (é cego).
        """
        acao_escolhida = random.choice(self.accoes)
        return acao_escolhida