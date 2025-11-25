import unittest
from ambientes.ambiente_recolecao import AmbienteRecolecao
from agente import Agente

class TestAmbienteRecolecao(unittest.TestCase):
    def test_recolecao_e_deposito(self):
        # Configurar o ambiente
        ambiente = AmbienteRecolecao(largura=5, altura=5, num_recursos=1)
        
        # Mock de um agente
        agente = Agente()

        # Adicionar o agente ao ambiente
        ambiente.colocar_agente(agente)

        # Forçar a posição do agente para cima de um recurso
        pos_recurso = list(ambiente.recursos)[0]
        ambiente._posicoes_agentes[agente] = pos_recurso

        # O agente deve conseguir recolher o recurso
        recompensa_recolha = ambiente.agir(agente, "Recolher")
        self.assertEqual(recompensa_recolha, 10) # Recolha bem-sucedida
        self.assertTrue(ambiente.agentes_carga[agente]) # Deve estar a carregar
        self.assertEqual(len(ambiente.recursos), 0) # Recurso foi removido

        # Mover o agente para o ninho
        ambiente._posicoes_agentes[agente] = ambiente.pos_ninho

        # O agente deve conseguir depositar o recurso
        recompensa_deposito = ambiente.agir(agente, "Depositar")
        self.assertEqual(recompensa_deposito, 50) # Depósito bem-sucedido
        self.assertFalse(ambiente.agentes_carga[agente]) # Já não está a carregar

if __name__ == '__main__':
    unittest.main()
