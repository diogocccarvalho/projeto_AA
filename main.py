import pickle
import os
import glob
import subprocess
import sys
import time
import tkinter as tk
import argparse
import webbrowser
from simulador import Simulador
from gui import GuiRecolecao, GuiFarol
from ambientes.ambiente_farol import AmbienteFarol
from ambientes.ambiente_recolecao import AmbienteRecolecao

from agentes.agenteFarolQ import AgenteFarolQ
from agentes.agenteRecolecaoQ import AgenteRecolecaoQ
from agentes.agenteFarolEvo import AgenteFarolEvo
import matplotlib.pyplot as plt
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo

def load_cerebro(file_path):
    """Carrega um cérebro de agente de um ficheiro pickle."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except (pickle.UnpicklingError, EOFError) as e:
        print(f"Aviso: Não foi possível carregar o cérebro de '{file_path}'. Erro: {e}")
        return None

def run_lighthouse_demo():
    """Executa a demonstração para o cenário Farol."""
    print("\n--- Apresentação: Cenário Farol ---")
    sim = Simulador()
    amb = AmbienteFarol(largura=80, altura=80, num_obstaculos=200)
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)

    ClasseQ = AgenteFarolQ
    ClasseAgenteEvo = AgenteFarolEvo
    save_file_q = "agente_farol_q.pkl"
    save_file_evo = "agente_farol_evo.pkl"

    cerebro_q = load_cerebro(save_file_q)
    cerebro_evo = load_cerebro(save_file_evo)

    # Adicionar 2 agentes de cada tipo
    for i in range(2):
        agente_q = ClasseQ()
        if cerebro_q: agente_q.q_table = cerebro_q.q_table.copy()
        agente_q.learning_mode = False
        sim.adicionar_agente(agente_q, verbose=False, equipa_id=f"Q_{i}")

        agente_evo = ClasseAgenteEvo()
        if cerebro_evo: agente_evo.genes = cerebro_evo.genes
        agente_evo.learning_mode = False
        sim.adicionar_agente(agente_evo, verbose=False, equipa_id=f"Evo_{i}")
    
    print("A executar 3 rondas de demonstração para o Farol...")
    for r in range(3):
        print(f"Ronda {r+1}/3")
        sim.executa_episodio(visualizador=gui, delay=0.02, max_passos=1500)
    
    # Pausa para visualização antes de fechar
    try:
        print("Demonstração do Farol completa. A janela fechará em 5 segundos...")
        gui.root.after(5000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError:
        print("Janela fechada manualmente.")


def run_foraging_demo():
    """Executa a demonstração para o cenário Recolha."""
    print("\n--- Apresentação: Cenário Recolha de Recursos ---")
    sim = Simulador()
    amb = AmbienteRecolecao(largura=50, altura=50, num_obstaculos=100, num_recursos=50)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    
    ClasseQ = AgenteRecolecaoQ
    ClasseAgenteEvo = AgenteRecolecaoEvo
    save_file_q = "agente_recolecao_q.pkl"
    save_file_evo = "agente_recolecao_evo.pkl"

    cerebro_q = load_cerebro(save_file_q)
    cerebro_evo = load_cerebro(save_file_evo)
        
    # Team 1: 2 Q-learning
    for _ in range(2):
        agente_q = ClasseQ()
        if cerebro_q: agente_q.q_table = cerebro_q.q_table.copy()
        agente_q.learning_mode = False
        sim.adicionar_agente(agente_q, equipa_id=1, verbose=False)
    
    # Team 2: 2 Evolutionary
    for _ in range(2):
        agente_evo = ClasseAgenteEvo()
        if cerebro_evo: agente_evo.genes = cerebro_evo.genes
        agente_evo.learning_mode = False
        sim.adicionar_agente(agente_evo, equipa_id=2, verbose=False)
    
    # Team 3: 1 Q-learning, 1 Evolutionary
    agente_q_mix = ClasseQ()
    if cerebro_q: agente_q_mix.q_table = cerebro_q.q_table.copy()
    agente_q_mix.learning_mode = False
    sim.adicionar_agente(agente_q_mix, equipa_id=3, verbose=False)
    agente_evo_mix = ClasseAgenteEvo()
    if cerebro_evo: agente_evo_mix.genes = cerebro_evo.genes
    agente_evo_mix.learning_mode = False
    sim.adicionar_agente(agente_evo_mix, equipa_id=3, verbose=False)

    print("A executar 3 rondas de demonstração para a Recolha...")
    for r in range(3):
        print(f"Ronda {r+1}/3")
        for agente in sim._agentes: agente.recompensa_total = 0
        sim.executa_episodio(visualizador=gui, delay=0.02, max_passos=2000)

    try:
        print("Demonstração de Recolha completa. A janela fechará em 5 segundos...")
        gui.root.after(5000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError:
        print("Janela fechada manualmente.")


def show_graphs():
    """Encontra e abre os gráficos de progresso do treino."""
    print("\n--- A apresentar gráficos de treino ---")
    graph_files = glob.glob("*_progress.png")
    if not graph_files:
        print("Ficheiros de gráficos de treino (*_progress.png) não encontrados.")
        return

    print(f"Encontrados {len(graph_files)} gráficos. A abri-los...")
    for file_path in graph_files:
        try:
            webbrowser.open(f"file://{os.path.realpath(file_path)}")
        except Exception as e:
            print(f"Não foi possível abrir {file_path}. Erro: {e}")


def run_presentation():
    """Executa a sequência de apresentação completa."""
    run_lighthouse_demo()
    run_foraging_demo()
    show_graphs()

def main():
    parser = argparse.ArgumentParser(description="Simulador de Agentes - Treino e Demonstração")
    parser.add_argument(
        "--modo", 
        type=str, 
        default="TREINO_Q_EVO_ALL", 
        choices=["TREINO_Q", "TREINO_EVO", "DEMO_Q", "DEMO_EVO", "DEMO_TEAMS", "DEMO_GIGANTE", "TREINO_Q_EVO_ALL"],
        help="Modo de execução do simulador."
    )
    parser.add_argument(
        "--cenario", 
        type=str, 
        default="FAROL", 
        choices=["FAROL", "RECOLECAO"],
        help="Cenário a ser utilizado."
    )
    args = parser.parse_args()
    MODO = args.modo.upper()
    CENARIO = args.cenario.upper() 
    
    if MODO == "DEMO_GIGANTE":
        run_presentation()
        return # Termina após a apresentação

    # --- Lógica para os outros modos ---
    sim = Simulador()

    if CENARIO == "FAROL":
        amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=100)
        gui = GuiFarol(amb, simulador=sim)
        ClasseQ = AgenteFarolQ
        ClasseAgenteEvo = AgenteFarolEvo
        save_file_q = "agente_farol_q.pkl"
        save_file_evo = "agente_farol_evo.pkl"
    else: # RECOLECAO
        amb = AmbienteRecolecao(largura=25, altura=25, num_obstaculos=25)
        gui = GuiRecolecao(amb, simulador=sim)
        ClasseQ = AgenteRecolecaoQ
        ClasseAgenteEvo = AgenteRecolecaoEvo
        save_file_q = "agente_recolecao_q.pkl"
        save_file_evo = "agente_recolecao_evo.pkl"
    
    # O ambiente só é criado no simulador para os modos que não são de treino
    if MODO not in ["TREINO_Q", "TREINO_EVO"]:
        sim.cria(amb)
        
    # Restante da lógica...
    if MODO == "TREINO_Q":
        print("--- Preparando treino Q-learning ---")
        env_params = {'largura': (10, 100), 'altura': (10, 100)}
        if CENARIO == "RECOLECAO":
            env_params.update({'num_obstaculos': (20, 80), 'num_recursos': (5, 25)})
        else: # FAROL
            env_params.update({'num_obstaculos': (40, 100)})

        Simulador.treinar_q(
            ClasseAmbiente=type(amb), 
            ClasseAgente=ClasseQ,
            env_params=env_params,
            num_agentes=2,
            num_episodios=10000, 
            guardar_em=save_file_q
        )

    elif MODO == "TREINO_EVO":
        print("--- Preparando treino genético ---")
        env_params = {'largura': (10, 100), 'altura': (10, 100)}
        if CENARIO == "RECOLECAO":
            env_params.update({'num_obstaculos': (20, 80), 'num_recursos': (5, 25)})
        else: # FAROL
            env_params.update({'num_obstaculos': (40, 150)})
            
        Simulador.treinar_genetico(
            ClasseAmbiente=type(amb),
            ClasseAgente=ClasseAgenteEvo, 
            env_params=env_params,
            pop_size=100,
            num_geracoes=1000, 
            guardar_em=save_file_evo
        )

    elif MODO == "TREINO_Q_EVO_ALL":
        print("--- INICIANDO TREINO COMPLETO DE TODOS OS AGENTES E CENÁRIOS ---")
    
        # 1. Treino Q-Learning Farol
        print("\n--- Treino Q-Learning: Cenário Farol ---")
        env_params_farol = {'largura': (10, 100), 'altura': (10, 100), 'num_obstaculos': (20, 150)}
        Simulador.treinar_q(
            ClasseAmbiente=AmbienteFarol, 
            ClasseAgente=AgenteFarolQ,
            env_params=env_params_farol,
            num_agentes=3,
            num_episodios=1000000, 
            guardar_em="agente_farol_q.pkl"
        )

        # 2. Treino Genético Farol
        print("\n--- Treino Genético: Cenário Farol ---")
        Simulador.treinar_genetico(
            ClasseAmbiente=AmbienteFarol,
            ClasseAgente=AgenteFarolEvo, 
            env_params=env_params_farol,
            pop_size=500,
            num_geracoes=10000, 
            guardar_em="agente_farol_evo.pkl"
        )

        # 3. Treino Q-Learning Recolha
        print("\n--- Treino Q-Learning: Cenário Recolha ---")
        env_params_recolha = {'largura': (10, 100), 'altura': (10, 100), 'num_obstaculos': (20, 80), 'num_recursos': (5, 25)}
        Simulador.treinar_q(
            ClasseAmbiente=AmbienteRecolecao, 
            ClasseAgente=AgenteRecolecaoQ,
            env_params=env_params_recolha,
            num_agentes=3,
            num_episodios=1000000, 
            guardar_em="agente_recolecao_q.pkl"
        )

        # 4. Treino Genético Recolha
        print("\n--- Treino Genético: Cenário Recolha ---")
        Simulador.treinar_genetico(
            ClasseAmbiente=AmbienteRecolecao,
            ClasseAgente=AgenteRecolecaoEvo, 
            env_params=env_params_recolha,
            pop_size=500,
            num_geracoes=10000, 
            guardar_em="agente_recolecao_evo.pkl"
        )

        print("\n--- TREINO COMPLETO CONCLUÍDO ---")

    elif MODO == "DEMO_Q":
        print("--- MODO DEMONSTRAÇÃO Q-LEARNING ---")
        cerebro_q = load_cerebro(save_file_q)
        
        num_agentes = 2
        for _ in range(num_agentes):
            agente = ClasseQ()
            if cerebro_q and hasattr(cerebro_q, 'q_table'):
                agente.q_table = cerebro_q.q_table
            agente.learning_mode = False
            sim.adicionar_agente(agente, verbose=False)
        print(f"{num_agentes} agentes Q-learning adicionados para demonstração.")
        
        sim.executa_episodio(visualizador=gui, delay=0.1)
        gui.root.mainloop()

    elif MODO == "DEMO_EVO":
        print("--- MODO DEMONSTRAÇÃO EVOLUCIONÁRIO ---")
        cerebro_evo = load_cerebro(save_file_evo)
        
        num_agentes = 2
        for _ in range(num_agentes):
            agente = ClasseAgenteEvo()
            if cerebro_evo:
                agente.genes = cerebro_evo.genes
            agente.learning_mode = False
            sim.adicionar_agente(agente, verbose=False)
        print(f"{num_agentes} agentes evolucionários adicionados para demonstração.")
        
        sim.executa_episodio(visualizador=gui, delay=0.1)
        gui.root.mainloop()

    elif MODO == "DEMO_TEAMS":
        print("--- MODO TORNEIO ---")
        cerebro_q = load_cerebro(save_file_q)
        cerebro_evo = load_cerebro(save_file_evo)

        # Equipa Q-Learning
        num_agentes_q = 2
        for _ in range(num_agentes_q):
            agente_q = ClasseQ()
            if cerebro_q and hasattr(cerebro_q, 'q_table'):
                agente_q.q_table = cerebro_q.q_table.copy()
            agente_q.learning_mode = False
            sim.adicionar_agente(agente_q, equipa_id=1, verbose=False)
        print(f"{num_agentes_q} agentes Q-learning adicionados à equipa 1.")

        # Equipa Evolucionária
        num_agentes_evo = 2
        for _ in range(num_agentes_evo):
            agente_evo = ClasseAgenteEvo()
            if cerebro_evo:
                agente_evo.genes = cerebro_evo.genes
            agente_evo.learning_mode = False
            sim.adicionar_agente(agente_evo, equipa_id=2, verbose=False)
        print(f"{num_agentes_evo} agentes evolucionários adicionados à equipa 2.")
        
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