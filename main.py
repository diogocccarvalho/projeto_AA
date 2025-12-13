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
    if not os.path.exists(file_path):
        print(f"Aviso: '{file_path}' não encontrado.")
        return None
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Erro ao carregar '{file_path}': {e}")
        return None

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
    print("\n=== INICIANDO APRESENTAÇÃO ===")
    
    # --- CENÁRIO 1: FAROL (5 Rondas, 1 de cada tipo) ---
    print("\n--- APRESENTAÇÃO: Cenário Farol (5 Rondas) ---")
    sim = Simulador()
    amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=60) 
    gui = GuiFarol(amb, simulador=sim)
    sim.cria(amb)
    
    # Definir cor para o Agente Fixo (Team 3)
    gui.cores_equipas[3] = "#2ECC71"  # Verde
    
    # Carregar cérebros
    cerebro_q = load_cerebro("agente_farol_q.pkl")
    cerebro_evo = load_cerebro("agente_farol_evo.pkl")
    
    # 1. Agente Q-Learning (Equipa 1 - Cyan)
    if cerebro_q: ag_q = cerebro_q.clone()
    else: ag_q = AgenteFarolQ()
    ag_q.learning_mode = False
    sim.adicionar_agente(ag_q, equipa_id=1, verbose=False)
    
    # 2. Agente Evolutivo (Equipa 2 - Rosa)
    if cerebro_evo: ag_evo = cerebro_evo.clone()
    else: ag_evo = AgenteFarolEvo()
    ag_evo.learning_mode = False
    sim.adicionar_agente(ag_evo, equipa_id=2, verbose=False)
    
    # 3. Agente Fixo (Equipa 3 - Verde)
    ag_fixo = AgenteFixo()
    ag_fixo.learning_mode = False
    sim.adicionar_agente(ag_fixo, equipa_id=3, verbose=False)
    
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
                
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=1000)
            gui.root.update()
            
            # Mostrar Resultados da Ronda
            scores = sim.obter_scores_equipas()
            print(f"   -> Q-Learning: {scores.get(1,0):.2f} | Evolutivo: {scores.get(2,0):.2f} | Fixo: {scores.get(3,0):.2f}")
            
        gui.root.destroy()
    except tk.TclError:
        print("Janela Farol fechada.")
        return

    # --- CENÁRIO 2: RECOLEÇÃO (5 Rondas, Equipas + Mista) ---
    print("\n--- APRESENTAÇÃO: Cenário Recoleção (5 Rondas) ---")
    sim = Simulador()
    # Mapa ligeiramente maior para acomodar mais equipas
    amb = AmbienteRecolecao(largura=50, altura=50, num_obstaculos=50, num_recursos=40)
    gui = GuiRecolecao(amb, simulador=sim)
    sim.cria(amb)
    
    # Definir cor para a Equipa Mista (Team 3)
    gui.cores_equipas[3] = "#9B59B6" # Roxo
    
    cerebro_q = load_cerebro("agente_recolecao_q.pkl")
    cerebro_evo = load_cerebro("agente_recolecao_evo.pkl")
    
    # Equipa 1: Q-Learning (2 agentes)
    for _ in range(2):
        if cerebro_q: ag = cerebro_q.clone()
        else: ag = AgenteRecolecaoQ()
        ag.learning_mode = False
        sim.adicionar_agente(ag, equipa_id=1, verbose=False)

    # Equipa 2: Evolutivo (2 agentes)
    for _ in range(2):
        if cerebro_evo: ag = cerebro_evo.clone()
        else: ag = AgenteRecolecaoEvo()
        ag.learning_mode = False
        sim.adicionar_agente(ag, equipa_id=2, verbose=False)
        
    # Equipa 3: Mista (1 Q + 1 Evo + 1 Fixo)
    # Membro Q
    if cerebro_q: ag_mq = cerebro_q.clone()
    else: ag_mq = AgenteRecolecaoQ()
    ag_mq.learning_mode = False
    sim.adicionar_agente(ag_mq, equipa_id=3, verbose=False)
    
    # Membro Evo
    if cerebro_evo: ag_me = cerebro_evo.clone()
    else: ag_me = AgenteRecolecaoEvo()
    ag_me.learning_mode = False
    sim.adicionar_agente(ag_me, equipa_id=3, verbose=False)
    
    # Membro Fixo
    ag_mf = AgenteFixo()
    ag_mf.learning_mode = False
    sim.adicionar_agente(ag_mf, equipa_id=3, verbose=False)
    
    try:
        for r in range(5):
            print(f"Ronda {r+1}/5")
            for ag in sim._agentes: 
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()
                
            sim.executa_episodio(visualizador=gui, delay=0.01, max_passos=1500)
            gui.root.update()
            
            scores = sim.obter_scores_equipas()
            print(f"   -> Equipa Q (1): {scores.get(1,0):.2f} | Equipa Evo (2): {scores.get(2,0):.2f} | Equipa Mista (3): {scores.get(3,0):.2f}")
            
        print("Apresentação terminada. A janela vai fechar.")
        gui.root.destroy()
    except tk.TclError:
        print("Janela Recoleção fechada.")
        return

    # --- MOSTRAR GRÁFICOS ---
    show_graphs()

# --- Funções de Treino Específicas ---

def treinar_farol_q():
    print("\n=== TREINO: FAROL (Q-Learning) ===")
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolQ,
        env_params=params, num_agentes=1, num_episodios=100000, 
        guardar_em="agente_farol_q.pkl",
        parar_no_pico=True, score_alvo=AmbienteFarol.RECOMPENSA_FAROL,
        pico_eps=500
    )

def treinar_farol_evo():
    print("\n=== TREINO: FAROL (Evolutivo) ===")
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolEvo, 
        env_params=params, pop_size=100, num_geracoes=500, 
        guardar_em="agente_farol_evo.pkl",
        parar_no_pico=False, score_alvo=AmbienteFarol.RECOMPENSA_FAROL, pico_gens=20
    )

def treinar_recolecao_q():
    print("\n=== TREINO: RECOLEÇÃO (Q-Learning) ===")
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    avg_recursos = (params['num_recursos'][0] + params['num_recursos'][1]) / 2
    score_alvo_dinamico = (avg_recursos * AmbienteRecolecao.RECOMPENSA_RECOLHA) + AmbienteRecolecao.RECOMPENSA_DEPOSITO
    print(f"--> Meta de Score para Paragem Antecipada: ~{score_alvo_dinamico:.0f}")
    
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoQ,
        env_params=params, num_agentes=2, num_episodios=100000, 
        guardar_em="agente_recolecao_q.pkl",
        parar_no_pico=False, score_alvo=score_alvo_dinamico,
        pico_eps=500
    )

def treinar_recolecao_evo():
    print("\n=== TREINO: RECOLEÇÃO (Evolutivo) ===")
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    avg_recursos = (params['num_recursos'][0] + params['num_recursos'][1]) / 2
    score_alvo_dinamico = (avg_recursos * AmbienteRecolecao.RECOMPENSA_RECOLHA) + AmbienteRecolecao.RECOMPENSA_DEPOSITO
    print(f"--> Meta de Score para Paragem Antecipada: ~{score_alvo_dinamico:.0f}")

    Simulador.treinar_genetico(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoEvo, 
        env_params=params, pop_size=500, num_geracoes=100000,
        guardar_em="agente_recolecao_evo.pkl",
        parar_no_pico=False, score_alvo=score_alvo_dinamico, pico_gens=50
    )

def main():
    parser = argparse.ArgumentParser(description="""
    Sistema de Treino e Demonstração para Agentes Inteligentes.
    """)
    
    parser.add_argument("--modo", type=str, default="APRESENTACAO",
        choices=["TREINO_ALL", "TREINO_Q", "TREINO_EVO",
                 "APRESENTACAO", "DEMO_TEAMS", "DEMO_Q", "DEMO_EVO", "DEMO_FIXO"])
    
    parser.add_argument("--cenario", type=str, default="FAROL", 
        choices=["FAROL", "RECOLECAO"])
    
    parser.add_argument("--test_mode", action="store_true", help="Ativa o modo de teste (learning_mode=False)")
    args = parser.parse_args()
    
    MODO = args.modo.upper()
    CENARIO = args.cenario.upper()

    if MODO == "APRESENTACAO":
        run_presentation()
    
    elif MODO == "TREINO_ALL":
        print("--- MODO TREINO_ALL: A executar todos os módulos de treino ---")
        tasks = [
            ("TREINO_Q", "FAROL", "pypy3"),
            ("TREINO_Q", "RECOLECAO", "python3"),
            ("TREINO_EVO", "FAROL", "python3"),
            ("TREINO_EVO", "RECOLECAO", "python3")
        ]
        
        for modo_task, cenario_task, interpreter in tasks:
            task_name = f"{modo_task} - {cenario_task}"
            print(f"\n--- A iniciar tarefa: {task_name} com '{interpreter}' ---")
            command = [interpreter, "main.py", "--modo", modo_task, "--cenario", cenario_task]
            try:
                subprocess.run(command, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"!! ERRO ao executar {task_name}: {e}")

        print("\n--- TREINO_ALL concluído ---")

    elif MODO == "TREINO_Q":
        if CENARIO == "FAROL": treinar_farol_q()
        elif CENARIO == "RECOLECAO": treinar_recolecao_q()
            
    elif MODO == "TREINO_EVO":
        if CENARIO == "FAROL": treinar_farol_evo()
        elif CENARIO == "RECOLECAO": treinar_recolecao_evo()
        
    elif "DEMO" in MODO:
        # Lógica de demonstrações individuais (mantida como fallback ou uso específico)
        sim = Simulador()
        if CENARIO == "FAROL":
            amb = AmbienteFarol(largura=50, altura=50, num_obstaculos=80)
            gui = GuiFarol(amb, simulador=sim)
            save_q, save_evo, AgQ, AgEvo = "agente_farol_q.pkl", "agente_farol_evo.pkl", AgenteFarolQ, AgenteFarolEvo
        else:
            amb = AmbienteRecolecao(largura=30, altura=30, num_obstaculos=30, num_recursos=30)
            gui = GuiRecolecao(amb, simulador=sim)
            save_q, save_evo, AgQ, AgEvo = "agente_recolecao_q.pkl", "agente_recolecao_evo.pkl", AgenteRecolecaoQ, AgenteRecolecaoEvo
        
        sim.cria(amb)
        cerebro_q = load_cerebro(save_q)
        cerebro_evo = load_cerebro(save_evo)

        if MODO == "DEMO_TEAMS":
            if cerebro_q: aq = cerebro_q.clone()
            else: aq = AgQ()
            aq.learning_mode = not args.test_mode
            sim.adicionar_agente(aq, equipa_id=1, verbose=False)

            if cerebro_evo: ae = cerebro_evo.clone()
            else: ae = AgEvo()
            ae.learning_mode = not args.test_mode
            sim.adicionar_agente(ae, equipa_id=2, verbose=False)
            
            af = AgenteFixo()
            af.learning_mode = False
            sim.adicionar_agente(af, equipa_id=3, verbose=False)

        elif MODO == "DEMO_FIXO":
            for _ in range(2):
                ag = AgenteFixo()
                ag.learning_mode = False
                sim.adicionar_agente(ag, verbose=False)
        else:
            TipoAgente = AgQ if MODO == "DEMO_Q" else AgEvo
            Cerebro = cerebro_q if MODO == "DEMO_Q" else cerebro_evo
            for _ in range(2):
                if Cerebro: ag = Cerebro.clone()
                else: ag = TipoAgente()
                ag.learning_mode = not args.test_mode
                sim.adicionar_agente(ag, verbose=False)
        
        try:
            sim.executa_episodio(visualizador=gui, delay=0.1)
            print("Simulação terminada.")
            gui.root.after(3000, gui.root.destroy)
            gui.root.mainloop()
        except tk.TclError: pass

if __name__ == "__main__":
    main()