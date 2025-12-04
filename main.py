import pickle
import os
from simulador import Simulador
from gui import GuiRecolecao, GuiFarol
from ambientes.ambiente_farol import AmbienteFarol
from ambientes.ambiente_recolecao import AmbienteRecolecao

from agentes.agenteFarolQ import AgenteFarolQ
from agentes.agenteRecolecaoQ import AgenteRecolecaoQ
# from agentes.agenteFarolEvo import AgenteFarolEvo
# from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo

def main():
    sim = Simulador()

    CENARIO = "RECOLECAO"
    MODO = "DEMO_EQUIPAS" # "TREINO_Q", "TREINO_EVO", "DEMO", "DEMO_EQUIPAS"

    ClasseAgenteEvo = None
    if CENARIO == "FAROL":
        amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=50)
        gui = GuiFarol(amb, simulador=sim)
        ClasseQ = AgenteFarolQ
        # ClasseAgenteEvo = AgenteFarolEvo
        save_file = "agente_farol.pkl"
    else: # RECOLECAO
        amb = AmbienteRecolecao(largura=20, altura=20, num_obstaculos=5)
        gui = GuiRecolecao(amb, simulador=sim)
        ClasseQ = AgenteRecolecaoQ
        # ClasseAgenteEvo = AgenteRecolecaoEvo
        save_file = "agente_recolecao.pkl"

    sim.cria(amb)


    if MODO == "TREINO_Q":
        agente = ClasseQ()
        agente.learning_mode = True
        sim.adicionar_agente(agente)
        sim.treinar_q(num_episodios=1000, guardar_em=save_file)

        # Depois do treino, correr em modo DEMO
        print("\n--- MODO DEMONSTRAÇÃO PÓS-TREINO ---")
        cerebro = None
        if os.path.exists(save_file):
            with open(save_file, "rb") as f:
                cerebro = pickle.load(f)
        
        agente_demo = ClasseQ()
        if cerebro and hasattr(cerebro, 'q_table'):
            agente_demo.q_table = cerebro.q_table
        agente_demo.learning_mode = False
        
        # Limpar agentes antigos e posições
        sim._agentes = []
        sim._ambiente._posicoes_agentes = {}
        sim.adicionar_agente(agente_demo)
        
        sim.executa_episodio(visualizador=gui, delay=0.1)
        gui.root.mainloop()

    elif MODO == "TREINO_EVO":
        if ClasseAgenteEvo:
            sim.treinar_genetico(ClasseAgenteEvo, num_geracoes=50, pop_size=20, guardar_em=save_file)
        else:
            print("Classe de Agente Evolucionário não definida para este cenário.")

    elif MODO == "DEMO":
        print("--- MODO DEMONSTRAÇÃO ---")
        cerebro = None
        if os.path.exists(save_file):
            with open(save_file, "rb") as f:
                cerebro = pickle.load(f)
        
        # Adicionar 2 agentes para a demonstração
        for _ in range(2):
            agente = ClasseQ()
            if cerebro and hasattr(cerebro, 'q_table'):
                agente.q_table = cerebro.q_table
            agente.learning_mode = False
            sim.adicionar_agente(agente)
        
        sim.executa_episodio(visualizador=gui, delay=0.1)
        gui.root.mainloop()

    elif MODO == "DEMO_EQUIPAS":
        print("--- MODO TORNEIO ---")
        cerebro = None
        if os.path.exists(save_file):
            with open(save_file, "rb") as f:
                cerebro = pickle.load(f)

        # 2 equipas 2 agentes
        for i in range(4):
            novo = ClasseQ()
            if cerebro and hasattr(cerebro, 'q_table'):
                novo.q_table = cerebro.q_table.copy() #copiar agente
            
            novo.learning_mode = False
            id_equipa = 1 if i < 2 else 2
            sim.adicionar_agente(novo, equipa_id=id_equipa)
        
        #5 rondas
        pontos = {1: 0, 2: 0}
        for r in range(1, 6):
            print(f"Ronda {r}...")
            sim.executa_episodio(visualizador=gui, delay=0.05)
            scores = sim.obter_scores_equipas()
            for eq in [1, 2]:
                pontos[eq] += scores.get(eq, 0)
            print(f"Resultado da Ronda: {scores}")
        
        print(f"PONTUAÇÃO FINAL: {pontos}")
        gui.root.mainloop()

if __name__ == "__main__":
    main()
