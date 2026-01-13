import pickle
import os
import glob
import sys
import time
import tkinter as tk
import argparse
import webbrowser
import subprocess
from simulador import Simulador
from gui import GuiRecolecao, GuiFarol
from ambientes.ambiente_farol import AmbienteFarol
from ambientes.ambiente_recolecao import AmbienteRecolecao

from agentes.agenteFarolQ import AgenteFarolQ
from agentes.agenteRecolecaoQ import AgenteRecolecaoQ
from agentes.agenteFarolEvo import AgenteFarolEvo
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo
from agentes.agenteFixo import AgenteFixo

def load_cerebro(file_path):
    """Carrega o ficheiro pkl do agente."""
    if not os.path.exists(file_path):
        print(f"Aviso: '{file_path}' não encontrado. O agente será aleatório.")
        return None
    try:
        with open(file_path, "rb") as f:
            agent = pickle.load(f)
            return agent
    except Exception as e:
        print(f"Erro ao carregar '{file_path}': {e}")
        return None

def show_graphs():
    """Abre os gráficos de progresso no navegador."""
    print("\n--- Gráficos de Treino ---")
    graph_files = glob.glob("*_progress.png")
    if not graph_files:
        print("Nenhum gráfico encontrado.")
        return
    for file_path in graph_files:
        try: 
            webbrowser.open(f"file://{os.path.realpath(file_path)}")
        except Exception: 
            pass

def run_presentation():
    """Executa a demonstração dos cenários com os agentes treinados."""
    print("\n=== INICIANDO APRESENTAÇÃO ===")
    print("Nota: Certifique-se que correu TREINO_ALL recentemente para atualizar os cérebros.")
    
    # ==========================================
    # CENÁRIO 1: FAROL (5 Rondas)
    # ==========================================
    print("\n>>> CENÁRIO: FAROL (5 Rondas) <<<")
    sim = Simulador()
    amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=60) 
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)
    
    gui.cores_equipas[3] = "#2ECC71"  # Verde para o Fixo
    
    cerebro_q = load_cerebro("agente_farol_q.pkl")
    cerebro_evo = load_cerebro("agente_farol_evo.pkl")
    
    # Adicionar Agentes para Comparação
    if cerebro_q: ag_q = cerebro_q.clone()
    else: ag_q = AgenteFarolQ()
    ag_q.learning_mode = False
    sim.adicionar_agente(ag_q, equipa_id=1, verbose=False)
    
    if cerebro_evo: 
        try: ag_evo = cerebro_evo.clone()
        except ValueError as e:
            print(e)
            ag_evo = AgenteFarolEvo()
    else: ag_evo = AgenteFarolEvo()
    ag_evo.learning_mode = False
    sim.adicionar_agente(ag_evo, equipa_id=2, verbose=False)
    
    sim.adicionar_agente(AgenteFixo(), equipa_id=3, verbose=False)
    
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=800)
            gui.root.update()
            scores = sim.obter_scores_equipas()
            print(f"   Scores -> Q: {scores.get(1,0):.0f} | Evo: {scores.get(2,0):.0f} | Fixo: {scores.get(3,0):.0f}")
        gui.root.destroy()
    except tk.TclError:
        print("Janela Farol fechada.")

    # ==========================================
    # CENÁRIO 2: RECOLEÇÃO (5 Rondas)
    # ==========================================
    print("\n>>> CENÁRIO: RECOLEÇÃO (5 Rondas) <<<")
    sim = Simulador()
    amb = AmbienteRecolecao(largura=40, altura=40, num_obstaculos=40, num_recursos=30)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    
    gui.cores_equipas[3] = "#9B59B6" # Roxo para Mista
    
    cerebro_q = load_cerebro("agente_recolecao_q.pkl")
    cerebro_evo = load_cerebro("agente_recolecao_evo.pkl")
    
    # Equipa 1: Q-Learning (2 agentes)
    for _ in range(2):
        ag = cerebro_q.clone() if cerebro_q else AgenteRecolecaoQ()
        ag.learning_mode = False
        sim.adicionar_agente(ag, equipa_id=1, verbose=False)

    # Equipa 2: Evolutivo (2 agentes treinados em equipa)
    for _ in range(2):
        if cerebro_evo:
            try: ag = cerebro_evo.clone()
            except ValueError: ag = AgenteRecolecaoEvo()
        else: ag = AgenteRecolecaoEvo()
        ag.learning_mode = False
        sim.adicionar_agente(ag, equipa_id=2, verbose=False)
        
    # Equipa 3: Mista
    ag_q_misto = cerebro_q.clone() if cerebro_q else AgenteRecolecaoQ()
    ag_q_misto.learning_mode = False
    sim.adicionar_agente(ag_q_misto, equipa_id=3, verbose=False)
    
    ag_evo_misto = cerebro_evo.clone() if cerebro_evo else AgenteRecolecaoEvo()
    ag_evo_misto.learning_mode = False
    sim.adicionar_agente(ag_evo_misto, equipa_id=3, verbose=False)
    sim.adicionar_agente(AgenteFixo(), equipa_id=3, verbose=False)
    
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=1000)
            gui.root.update()
            scores = sim.obter_scores_equipas()
            print(f"   Scores -> Equipa Q: {scores.get(1,0):.0f} | Equipa Evo: {scores.get(2,0):.0f} | Equipa Mista: {scores.get(3,0):.0f}")
        gui.root.destroy()
    except tk.TclError:
        print("Janela Recoleção fechada.")

    show_graphs()

# --- Funções de Treino ---

def treinar_farol_q():
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    # Treinar com 3 agentes para aprender a evitar tráfego dinâmico
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolQ,
        env_params=params, num_agentes=3, num_episodios=5000, 
        guardar_em="agente_farol_q.pkl",
        parar_no_pico=False, score_alvo=AmbienteFarol.RECOMPENSA_FAROL, pico_eps=200,
        dynamic_obstacles=True
    )

def treinar_farol_evo():
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    # Treino genético em equipas de 3 para consistência com o Q-Learning
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolEvo, 
        env_params=params, pop_size=100, num_geracoes=750, 
        guardar_em="agente_farol_evo.pkl",
        parar_no_pico=False, score_alvo=AmbienteFarol.RECOMPENSA_FAROL, pico_gens=20,
        num_agents_per_eval=3,
        dynamic_obstacles=True
    )

def treinar_recolecao_q():
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    avg_recursos = 35
    score_alvo = (avg_recursos * 20) + 100
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoQ,
        env_params=params, num_agentes=2, num_episodios=10000, 
        guardar_em="agente_recolecao_q.pkl",
        parar_no_pico=False, score_alvo=score_alvo, pico_eps=200,
        dynamic_obstacles=True
    )

def treinar_recolecao_evo():
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    avg_recursos = 35
    score_alvo = (avg_recursos * 20) + 100
    # Treino genético em equipas de 2 (clones) para aprender partilha de espaço
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoEvo, 
        env_params=params, pop_size=100, num_geracoes=1000,
        guardar_em="agente_recolecao_evo.pkl",
        parar_no_pico=False, score_alvo=score_alvo, pico_gens=30,
        num_agents_per_eval=2,
        dynamic_obstacles=True
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--modo", type=str, default="APRESENTACAO",
        choices=["TREINO_ALL", "TREINO_Q", "TREINO_EVO", "APRESENTACAO"])
    parser.add_argument("--cenario", type=str, default="FAROL", choices=["FAROL", "RECOLECAO"])
    args = parser.parse_args()
    
    MODO = args.modo.upper()
    CENARIO = args.cenario.upper()

    if MODO == "APRESENTACAO":
        run_presentation()
    
    elif MODO == "TREINO_ALL":
        # Apagar ficheiros antigos para garantir que as novas dimensões de rede são aplicadas
        print("!!! LIMPANDO FICHEIROS PKL ANTIGOS PARA GARANTIR CONSISTÊNCIA !!!")
        for f in glob.glob("*.pkl"): 
            try: os.remove(f)
            except Exception: pass
        
        print("--- MODO TREINO_ALL ---")
        tasks = [
            ("TREINO_Q", "FAROL", "pypy3"),
            ("TREINO_EVO", "FAROL", "python3"),
            ("TREINO_Q", "RECOLECAO", "python3"),
            ("TREINO_EVO", "RECOLECAO", "python3")
        ]
        
        for modo_task, cenario_task, interpreter in tasks:
            print(f"\n>> {modo_task} - {cenario_task} ({interpreter})")
            command = [interpreter, "main.py", "--modo", modo_task, "--cenario", cenario_task]
            try: 
                subprocess.run(command, check=True)
            except Exception as e: 
                print(f"Erro na tarefa {modo_task}: {e}")

    elif MODO == "TREINO_Q":
        if CENARIO == "FAROL": treinar_farol_q()
        else: treinar_recolecao_q()
            
    elif MODO == "TREINO_EVO":
        if CENARIO == "FAROL": treinar_farol_evo()
        else: treinar_recolecao_evo()

if __name__ == "__main__":
    main()