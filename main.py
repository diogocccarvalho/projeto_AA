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

# ... (Funções auxiliares load_cerebro, demos, etc. mantêm-se iguais) ...
# Vou apenas reescrever a função main() e as chamadas de treino para não ocupar espaço desnecessário

def load_cerebro(file_path):
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Aviso: erro ao carregar '{file_path}': {e}")
        return None

# ... [MANTÉM AS FUNÇÕES run_lighthouse_demo, run_foraging_demo, show_graphs, run_presentation IGUAIS] ...
# COPIA AS FUNÇÕES DE DEMO DO TEU FICHEIRO ORIGINAL, ELAS ESTÃO BOAS.

def run_lighthouse_demo():
    print("\n--- Apresentação: Cenário Farol ---")
    sim = Simulador()
    amb = AmbienteFarol(largura=80, altura=80, num_obstaculos=200)
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)
    ClasseQ = AgenteFarolQ
    ClasseAgenteEvo = AgenteFarolEvo
    save_file_q = "agente_farol_q.pkl" # Tenta carregar o normal
    if os.path.exists("agente_farol_q_final.pkl"): save_file_q = "agente_farol_q_final.pkl" # Prioridade ao final

    save_file_evo = "agente_farol_evo.pkl"
    cerebro_q = load_cerebro(save_file_q)
    cerebro_evo = load_cerebro(save_file_evo)

    for i in range(2):
        agente_q = ClasseQ()
        if cerebro_q: agente_q.q_table = cerebro_q.q_table.copy()
        agente_q.learning_mode = False
        sim.adicionar_agente(agente_q, verbose=False, equipa_id=f"Q_{i}")
        agente_evo = ClasseAgenteEvo()
        if cerebro_evo: agente_evo.genes = cerebro_evo.genes
        agente_evo.learning_mode = False
        sim.adicionar_agente(agente_evo, verbose=False, equipa_id=f"Evo_{i}")
    
    for r in range(3):
        print(f"Ronda {r+1}/3")
        sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=1500)
    try:
        gui.root.after(3000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError: pass

def run_foraging_demo():
    print("\n--- Apresentação: Cenário Recolha de Recursos ---")
    sim = Simulador()
    amb = AmbienteRecolecao(largura=50, altura=50, num_obstaculos=100, num_recursos=50)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    
    ClasseQ = AgenteRecolecaoQ
    ClasseAgenteEvo = AgenteRecolecaoEvo
    
    # Tenta carregar a versão FINAL (mais treinada) se existir
    save_file_q = "agente_recolecao_q_final.pkl" if os.path.exists("agente_recolecao_q_final.pkl") else "agente_recolecao_q.pkl"
    save_file_evo = "agente_recolecao_evo.pkl"

    print(f"A carregar Q-Learning de: {save_file_q}")
    cerebro_q = load_cerebro(save_file_q)
    cerebro_evo = load_cerebro(save_file_evo)
        
    for _ in range(2):
        agente_q = ClasseQ()
        if cerebro_q: agente_q.q_table = cerebro_q.q_table.copy()
        agente_q.learning_mode = False
        sim.adicionar_agente(agente_q, equipa_id=1, verbose=False)
    
    for _ in range(2):
        agente_evo = ClasseAgenteEvo()
        if cerebro_evo: agente_evo.genes = cerebro_evo.genes
        agente_evo.learning_mode = False
        sim.adicionar_agente(agente_evo, equipa_id=2, verbose=False)
    
    print("A executar 3 rondas de demonstração para a Recolha...")
    for r in range(3):
        print(f"Ronda {r+1}/3")
        for agente in sim._agentes: agente.recompensa_total = 0
        sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=2000)

    try:
        print("Janela fecha em 5s...")
        gui.root.after(5000, gui.root.destroy)
        gui.root.mainloop()
    except tk.TclError: pass

def show_graphs():
    print("\n--- A apresentar gráficos de treino ---")
    graph_files = glob.glob("*_progress.png")
    for file_path in graph_files:
        try: webbrowser.open(f"file://{os.path.realpath(file_path)}")
        except: pass

def run_presentation():
    run_lighthouse_demo()
    run_foraging_demo()
    show_graphs()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", type=str, default="TREINO_Q_EVO_ALL")
    parser.add_argument("--cenario", type=str, default="FAROL")
    args = parser.parse_args()
    MODO = args.modo.upper()
    
    if MODO == "DEMO_GIGANTE":
        run_presentation()
        return

    sim = Simulador()
    # Configuração dummy para instanciar classes, o treino reconfigura depois
    if args.cenario == "FAROL":
        amb = AmbienteFarol() 
        ClasseQ = AgenteFarolQ
        ClasseAgenteEvo = AgenteFarolEvo
    else:
        amb = AmbienteRecolecao()
        ClasseQ = AgenteRecolecaoQ
        ClasseAgenteEvo = AgenteRecolecaoEvo

    if MODO == "TREINO_Q_EVO_ALL":
        print("--- INICIANDO TREINO PESADO (VAI DEMORAR) ---")
    
        # 1. FAROL (Já estava bom, mantemos parâmetros razoáveis)
        print("\n>>> Treino Q-Learning: Farol")
        env_params_farol = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (40, 150)}
        Simulador.treinar_q(
            ClasseAmbiente=AmbienteFarol, 
            ClasseAgente=AgenteFarolQ,
            env_params=env_params_farol,
            num_agentes=2,
            num_episodios=10000, # Farol aprende rápido
            guardar_em="agente_farol_q.pkl"
        )

        print("\n>>> Treino Genético: Farol")
        Simulador.treinar_genetico(
            ClasseAmbiente=AmbienteFarol,
            ClasseAgente=AgenteFarolEvo, 
            env_params=env_params_farol,
            pop_size=250,
            num_geracoes=1000, 
            guardar_em="agente_farol_evo.pkl"
        )

        # 2. RECOLHA (AQUI É QUE PRECISA DE FORÇA BRUTA)
        print("\n>>> Treino Q-Learning: Recolha (20k episódios)")
        # Aumentamos a variabilidade do mapa para ele generalizar bem
        env_params_recolha = {'largura': (20, 40), 'altura': (20, 40), 'num_obstaculos': (20, 60), 'num_recursos': (5, 15)}
        
        Simulador.treinar_q(
            ClasseAmbiente=AmbienteRecolecao, 
            ClasseAgente=AgenteRecolecaoQ,
            env_params=env_params_recolha,
            num_agentes=2,
            num_episodios=50000,
            guardar_em="agente_recolecao_q.pkl"
        )

        print("\n>>> Treino Genético: Recolha (Cérebro Grande)")
        # População grande para explorar o espaço de pesos maior (40 hidden neurons)
        Simulador.treinar_genetico(
            ClasseAmbiente=AmbienteRecolecao,
            ClasseAgente=AgenteRecolecaoEvo, 
            env_params=env_params_recolha,
            pop_size=250,      # População robusta
            num_geracoes=1000,  # Bastantes gerações
            guardar_em="agente_recolecao_evo.pkl"
        )

        print("\n--- TREINO COMPLETO CONCLUÍDO ---")

if __name__ == "__main__":
    main()