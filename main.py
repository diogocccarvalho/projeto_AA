from simulador import Simulador
from ambientes.ambiente_recolecao import AmbienteRecolecao
from ambientes.ambiente_farol import AmbienteFarol
from agente import AgenteRandom
from gui import GuiRecolecao, GuiFarol

def main():
    # --- ESCOLHA DO PROBLEMA ---
    # Muda para 'False' para testar o Farol
    MODO_RECOLECAO = False

    sim = Simulador()

    if MODO_RECOLECAO:
        # 1. Criar Ambiente e GUI de Recoleção
        amb = AmbienteRecolecao(largura=20, altura=20, num_recursos=15)
        gui = GuiRecolecao(amb)
        
        # Agente para Recoleção (com ações extra)
        agente = AgenteRandom()
        agente.accoes = ["Norte", "Sul", "Este", "Oeste", "Recolher", "Depositar"]
    
    else:
        # 1. Criar Ambiente e GUI de Farol
        amb = AmbienteFarol(largura=15, altura=15)
        gui = GuiFarol(amb)

        # Agente para Farol (movimento simples)
        agente = AgenteRandom()
        # accoes default já são Norte/Sul/Este/Oeste
    
    # 2. Configuração Comum
    sim.cria(amb)
    sim.adicionar_agente(agente)
    sim._max_passos = 500

    # 3. LIGAÇÃO GUI <-> AMBIENTE
    # O ambiente chama 'self.display()' no simulador.
    # Nós substituímos essa função pelo método 'desenhar' da nossa GUI.
    amb.display = gui.desenhar

    # 4. Executar
    print(f"A iniciar simulação: {gui.root.title()}...")
    sim.executa()
    
    print("Simulação terminada.")
    gui.root.mainloop()

if __name__ == "__main__":
    main()