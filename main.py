import pickle
import os
import glob
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
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo

def load_cerebro(file_path):
    if not os.path.exists(file_path):
        print(f"Aviso: '{file_path}' não encontrado.")
        return None
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Erro ao carregar '{file_path}': {e}")
        return None

def run_lighthouse_demo():
    print("\n--- DEMO: Cenário Farol ---")
    sim = Simulador()
    amb = AmbienteFarol(largura=80, altura=80, num_obstaculos=200)
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)

    # Carregar cérebros
    cerebro_q = load_cerebro("agente_farol_q.pkl")
    cerebro_evo = load_cerebro("agente_farol_evo.pkl")

    # Adicionar Agentes
    for i in range(2):
        ag_q = AgenteFarolQ()
        if cerebro_q: ag_q.q_table = cerebro_q.q_table.copy()
        ag_q.learning_mode = False
        sim.adicionar_agente(ag_q, verbose=False, equipa_id=f"Q_{i}")

        ag_evo = AgenteFarolEvo()
        if cerebro_evo: ag_evo.genes = cerebro_evo.genes
        ag_evo.learning_mode = False
        sim.adicionar_agente(ag_evo, verbose=False, equipa_id=f"Evo_{i}")
    
    # Executar
    try:
        for r in range(3):
            print(f"Ronda {r+1}/3")
            sim.executa_episodio(visualizador=gui, delay=0.02, max_passos=1500)
            gui.root.update()
        
        print("Demo Farol terminada. A janela fecha em 5s...")
        gui.root.after(5000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError:
        print("Janela fechada.")

def run_foraging_demo():
    print("\n--- DEMO: Cenário Recolha ---")
    sim = Simulador()
    amb = AmbienteRecolecao(largura=40, altura=40, num_obstaculos=60, num_recursos=40)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    
    cerebro_q = load_cerebro("agente_recolecao_q.pkl")
    cerebro_evo = load_cerebro("agente_recolecao_evo.pkl")
        
    # Adicionar Agentes (2 de cada equipa)
    for _ in range(2):
        ag_q = AgenteRecolecaoQ()
        if cerebro_q: ag_q.q_table = cerebro_q.q_table.copy()
        ag_q.learning_mode = False
        sim.adicionar_agente(ag_q, equipa_id=1, verbose=False)
    
    for _ in range(2):
        ag_evo = AgenteRecolecaoEvo()
        if cerebro_evo: ag_evo.genes = cerebro_evo.genes
        ag_evo.learning_mode = False
        sim.adicionar_agente(ag_evo, equipa_id=2, verbose=False)
    
    try:
        print("A executar 3 rondas...")
        for r in range(3):
            print(f"Ronda {r+1}/3")
            for ag in sim._agentes: ag.recompensa_total = 0
            sim.executa_episodio(visualizador=gui, delay=0.03, max_passos=2000)
            gui.root.update()

        print("Demo Recolha terminada. A janela fecha em 5s...")
        gui.root.after(5000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError:
        print("Janela fechada.")

def show_graphs():
    print("\n--- Gráficos de Treino ---")
    graph_files = glob.glob("*_progress.png")
    if not graph_files:
        print("Nenhum gráfico encontrado.")
        return
    for file_path in graph_files:
        try: webbrowser.open(f"file://{os.path.realpath(file_path)}")
        except: pass

def run_presentation():
    run_lighthouse_demo()
    run_foraging_demo()
    show_graphs()

# --- Funções de Treino Específicas ---

def treinar_farol():
    print("\n=== TREINO: FAROL (Q + EVO) ===")
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (30, 120)}
    
    # Q-Learning
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolQ,
        env_params=params, num_agentes=2, num_episodios=100000, 
        guardar_em="agente_farol_q.pkl"
    )
    # Genético
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolEvo, 
        env_params=params, pop_size=200, num_geracoes=10000, 
        guardar_em="agente_farol_evo.pkl"
    )

def treinar_recolecao():
    print("\n=== TREINO: RECOLEÇÃO (Q + EVO) ===")
    # DICA: Começamos com mapas mais pequenos para eles aprenderem a lógica básica
    params = {'largura': (15, 20), 'altura': (15, 20), 'num_obstaculos': (5, 10), 'num_recursos': (15, 25)}
    
    # Q-Learning (Precisa de muitos episódios para Q-Table convergir em estados complexos)
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoQ,
        env_params=params, num_agentes=4, num_episodios=100000, # Aumentado
        guardar_em="agente_recolecao_q.pkl"
    )
    # Genético (População maior para explorar melhor)
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoEvo, 
        env_params=params, pop_size=500, num_geracoes=10000, # Aumentado
        guardar_em="agente_recolecao_evo.pkl"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", type=str, default="TREINO_ALL",
        choices=["TREINO_ALL", "TREINO_FAROL", "TREINO_RECOLECAO", 
                 "DEMO_Q", "DEMO_EVO", "DEMO_TEAMS", "DEMO_GIGANTE"])
    parser.add_argument("--cenario", type=str, default="FAROL", choices=["FAROL", "RECOLECAO"])
    args = parser.parse_args()
    
    MODO = args.modo.upper()
    CENARIO = args.cenario.upper()

    # --- Seletor de Modos ---
    if MODO == "DEMO_GIGANTE":
        run_presentation()
    
    elif MODO == "TREINO_ALL":
        treinar_farol()
        treinar_recolecao()
        
    elif MODO == "TREINO_FAROL":
        treinar_farol()
        
    elif MODO == "TREINO_RECOLECAO":
        treinar_recolecao()
        
    elif "DEMO" in MODO:
        # Lógica genérica de Demo para um único cenário
        sim = Simulador()
        if CENARIO == "FAROL":
            amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=80)
            save_q = "agente_farol_q.pkl"
            save_evo = "agente_farol_evo.pkl"
            gui = GuiFarol(amb, simulador=sim)
            AgQ = AgenteFarolQ
            AgEvo = AgenteFarolEvo
        else:
            amb = AmbienteRecolecao(largura=30, altura=30, num_obstaculos=30, num_recursos=30)
            save_q = "agente_recolecao_q.pkl"
            save_evo = "agente_recolecao_evo.pkl"
            gui = GuiRecolecao(amb, simulador=sim)
            AgQ = AgenteRecolecaoQ
            AgEvo = AgenteRecolecaoEvo
        
        sim.cria(amb)
        cerebro_q = load_cerebro(save_q)
        cerebro_evo = load_cerebro(save_evo)

        # Configurar equipas
        if MODO == "DEMO_TEAMS":
            # 2 vs 2
            for _ in range(2):
                aq = AgQ()
                if cerebro_q: aq.q_table = cerebro_q.q_table.copy()
                aq.learning_mode = False
                sim.adicionar_agente(aq, equipa_id=1, verbose=False)
            for _ in range(2):
                ae = AgEvo()
                if cerebro_evo: ae.genes = cerebro_evo.genes
                ae.learning_mode = False
                sim.adicionar_agente(ae, equipa_id=2, verbose=False)
        else:
            # Apenas 1 tipo
            TipoAgente = AgQ if MODO == "DEMO_Q" else AgEvo
            Cerebro = cerebro_q if MODO == "DEMO_Q" else cerebro_evo
            for _ in range(2):
                ag = TipoAgente()
                if Cerebro: 
                    if MODO == "DEMO_Q": ag.q_table = Cerebro.q_table
                    else: ag.genes = Cerebro.genes
                ag.learning_mode = False
                sim.adicionar_agente(ag, verbose=False)
        
        print(f"A iniciar DEMO ({MODO}) no cenário {CENARIO}...")
        sim.executa_episodio(visualizador=gui, delay=0.1)
        gui.root.mainloop()

if __name__ == "__main__":
    main()