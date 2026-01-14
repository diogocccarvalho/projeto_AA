import pickle
import os
import glob
import sys
import time
import tkinter as tk
import argparse
import webbrowser
import subprocess
import traceback
from simulador import Simulador
from gui import GuiRecolecao, GuiFarol
from ambientes.ambiente_farol import AmbienteFarol
from ambientes.ambiente_recolecao import AmbienteRecolecao

from agentes.agenteFarolQ import AgenteFarolQ
from agentes.agenteRecolecaoQ import AgenteRecolecaoQ
from agentes.agenteFarolEvo import AgenteFarolEvo
from agentes.agenteRecolecaoEvo import AgenteRecolecaoEvo
from agentes.agenteFixo import AgenteFixo

def resolve_path(file_name):
    """Tenta encontrar o ficheiro no CWD ou na pasta do script."""
    if os.path.exists(file_name):
        return file_name
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alt_path = os.path.join(script_dir, file_name)
    if os.path.exists(alt_path):
        return alt_path
    return None

def load_q_agente(file_name):
    """Carrega o ficheiro pkl do agente Q com debug."""
    print(f"\n[DEBUG] A carregar Agente Q: '{file_name}'...")
    file_path = resolve_path(file_name)
    
    if not file_path:
        print(f"[AVISO] Ficheiro '{file_name}' não encontrado.")
        return None

    try:
        with open(file_path, "rb") as f:
            agent = pickle.load(f)
            # VERIFICAÇÃO DE INTEGRIDADE
            q_len = len(agent.q_table) if hasattr(agent, 'q_table') else 0
            print(f"[SUCESSO] Agente carregado. Estados na Memória (Q-Table): {q_len}")
            if q_len == 0:
                print("   >>> ALERTA: Este agente parece vazio (sem treino)!")
            return agent
    except Exception as e:
        print(f"[ERRO] Falha ao carregar '{file_path}': {e}")
        return None

def load_evo_genes(file_name):
    """Carrega os genes de um agente Evo a partir de um ficheiro pkl com debug."""
    print(f"\n[DEBUG] A carregar Genes Evo: '{file_name}'...")
    file_path = resolve_path(file_name)

    if not file_path:
        print(f"[AVISO] Ficheiro '{file_name}' não encontrado.")
        return None

    try:
        with open(file_path, "rb") as f:
            genes = pickle.load(f)
            print(f"[SUCESSO] Genes carregados. Tamanho do Genoma: {len(genes)}")
            return genes
    except Exception as e:
        print(f"[ERRO] Falha ao carregar '{file_path}': {e}")
        return None

def show_graphs():
    """Abre os gráficos de progresso no navegador."""
    print("\n--- Gráficos de Treino ---")
    candidates = glob.glob("*_progress.png")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates += glob.glob(os.path.join(script_dir, "*_progress.png"))
    graph_files = list(set(candidates))
    
    if not graph_files:
        print("Nenhum gráfico encontrado.")
        return
    for file_path in graph_files:
        try: webbrowser.open(f"file://{os.path.realpath(file_path)}")
        except Exception: pass

def run_presentation():
    """Executa a demonstração dos cenários com os agentes treinados."""
    print("\n=== INICIANDO APRESENTAÇÃO ===")
    print("DICA: Se os agentes andarem aos círculos, corra '--modo TREINO_ALL' para recriar os cérebros.")
    
    # ==========================================
    # CENÁRIO 1: FAROL (5 Rondas)
    # ==========================================
    print("\n>>> CENÁRIO: FAROL (5 Rondas) <<<")
    sim = Simulador()
    amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=50) 
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)
    gui.cores_equipas[3] = "#2ECC71"
    
    agente_q = load_q_agente("agente_farol_q.pkl")
    genes_evo = load_evo_genes("agente_farol_evo.pkl")
    
    if agente_q: ag_q = agente_q.clone()
    else: ag_q = AgenteFarolQ()
    ag_q.learning_mode = False
    
    # CORREÇÃO: Pequeno epsilon para evitar loops infinitos em estados aliased
    ag_q.epsilon = 0.05 
    
    sim.adicionar_agente(ag_q, equipa_id=1, verbose=False)
    
    ag_evo = AgenteFarolEvo()
    if genes_evo is not None:
        try: ag_evo.genes = genes_evo
        except ValueError as e: print(f"[ERRO] Genes incompatíveis: {e}")
    ag_evo.learning_mode = False
    sim.adicionar_agente(ag_evo, equipa_id=2, verbose=False)
    
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=800)
            gui.root.update()
            scores = sim.obter_scores_equipas()
            print(f"   Scores -> Q: {scores.get(1,0):.0f} | Evo: {scores.get(2,0):.0f}")
        gui.root.destroy()
    except tk.TclError:
        print("Janela Farol fechada.")

    # ==========================================
    # CENÁRIO 2: RECOLEÇÃO (5 Rondas)
    # ==========================================
    print("\n>>> CENÁRIO: RECOLEÇÃO (5 Rondas) <<<")
    sim = Simulador()
    amb = AmbienteRecolecao(largura=40, altura=40, num_obstaculos=30, num_recursos=30)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    gui.cores_equipas[3] = "#9B59B6"
    
    agente_q = load_q_agente("agente_recolecao_q.pkl")
    genes_evo = load_evo_genes("agente_recolecao_evo.pkl")
    
    # Equipa 1: Q-Learning (2 agentes)
    for _ in range(2):
        ag = agente_q.clone() if agente_q else AgenteRecolecaoQ()
        ag.learning_mode = False
        # CORREÇÃO: Pequeno epsilon aqui também
        ag.epsilon = 0.05
        sim.adicionar_agente(ag, equipa_id=1, verbose=False)

    # Equipa 2: Evolutivo (2 agentes)
    for _ in range(2):
        ag = AgenteRecolecaoEvo()
        if genes_evo is not None:
            try: ag.genes = genes_evo
            except ValueError as e: print(e)
        ag.learning_mode = False 
        sim.adicionar_agente(ag, equipa_id=2, verbose=False)
        
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=1000)
            gui.root.update()
            scores = sim.obter_scores_equipas()
            print(f"   Scores -> Equipa Q: {scores.get(1,0):.0f} | Equipa Evo: {scores.get(2,0):.0f}")
        gui.root.destroy()
    except tk.TclError:
        print("Janela Recoleção fechada.")

    show_graphs()

# --- Funções de Treino ---

def treinar_farol_q():
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolQ,
        env_params=params, num_agentes=3, num_episodios=100000, 
        guardar_em="agente_farol_q.pkl",
        parar_no_pico=False, score_alvo=AmbienteFarol.RECOMPENSA_FAROL, pico_eps=200,
        dynamic_obstacles=True
    )

def treinar_farol_evo():
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolEvo, 
        env_params=params, pop_size=250, num_geracoes=5000, 
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
        env_params=params, num_agentes=2, num_episodios=100000, 
        guardar_em="agente_recolecao_q.pkl",
        parar_no_pico=False, score_alvo=score_alvo, pico_eps=200,
        dynamic_obstacles=True
    )

def treinar_recolecao_evo():
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    avg_recursos = 35
    score_alvo = (avg_recursos * 20) + 100
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoEvo, 
        env_params=params, pop_size=250, num_geracoes=10000,
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
        print("deleting old brains")
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
                # Fallback
                print(f"Tentando fallback para 'python'...")
                try: subprocess.run(["python", "main.py", "--modo", modo_task, "--cenario", cenario_task], check=True)
                except Exception as e2: print(f"Erro FATAL: {e2}")

    elif MODO == "TREINO_Q":
        if CENARIO == "FAROL": treinar_farol_q()
        else: treinar_recolecao_q()
            
    elif MODO == "TREINO_EVO":
        if CENARIO == "FAROL": treinar_farol_evo()
        else: treinar_recolecao_evo()

if __name__ == "__main__":
    main()