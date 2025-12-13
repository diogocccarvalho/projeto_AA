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
    for _ in range(2):
        if cerebro_q:
            ag_q = cerebro_q.clone()
        else:
            ag_q = AgenteFarolQ()
        ag_q.learning_mode = False
        sim.adicionar_agente(ag_q, verbose=False, equipa_id=1)

        if cerebro_evo:
            ag_evo = cerebro_evo.clone()
        else:
            ag_evo = AgenteFarolEvo()
        ag_evo.learning_mode = False
        sim.adicionar_agente(ag_evo, verbose=False, equipa_id=2)
    
    # Executar
    try:
        for r in range(3):
            print(f"Ronda {r+1}/3")
            for ag in sim._agentes: ag.recompensa_total = 0
            sim.executa_episodio(visualizador=gui, delay=0.02, max_passos=1500)
            gui.root.update()
            
            scores = sim.obter_scores_equipas()
            score_q = scores.get(1, 0)
            score_evo = scores.get(2, 0)
            print(f"Pontuação Q-Learning: {score_q:.2f}")
            print(f"Pontuação Evolutivo: {score_evo:.2f}")
            if score_q > score_evo:
                print("🏆 Vencedor da Ronda: Q-Learning!")
            elif score_evo > score_q:
                print("🏆 Vencedor da Ronda: Evolutivo!")
            else:
                print("Empate na Ronda!")

        print("Demo Farol terminada. A janela vai fechar.")
        gui.root.destroy()
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
        if cerebro_q:
            ag_q = cerebro_q.clone()
        else:
            ag_q = AgenteRecolecaoQ()
        ag_q.learning_mode = False
        sim.adicionar_agente(ag_q, equipa_id=1, verbose=False)
    
    for _ in range(2):
        if cerebro_evo:
            ag_evo = cerebro_evo.clone()
        else:
            ag_evo = AgenteRecolecaoEvo()
        ag_evo.learning_mode = False
        sim.adicionar_agente(ag_evo, equipa_id=2, verbose=False)
    
    try:
        print("A executar 3 rondas...")
        for r in range(3):
            print(f"Ronda {r+1}/3")
            for ag in sim._agentes: ag.recompensa_total = 0
            sim.executa_episodio(visualizador=gui, delay=0.03, max_passos=2000)
            gui.root.update()

            scores = sim.obter_scores_equipas()
            score_q = scores.get(1, 0)
            score_evo = scores.get(2, 0)
            print(f"Pontuação Q-Learning: {score_q:.2f}")
            print(f"Pontuação Evolutivo: {score_evo:.2f}")
            if score_q > score_evo:
                print("🏆 Vencedor da Ronda: Q-Learning!")
            elif score_evo > score_q:
                print("🏆 Vencedor da Ronda: Evolutivo!")
            else:
                print("Empate na Ronda!")

        print("Demo Recolha terminada. A janela vai fechar.")
        gui.root.destroy()
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
    try:
        run_lighthouse_demo()
        run_foraging_demo()
        show_graphs()
    except tk.TclError:
        print("Apresentação interrompida.")

# --- Funções de Treino Específicas ---

def treinar_farol_q():
    print("\n=== TREINO: FAROL (Q-Learning) ===")
    params = {'largura': (20, 80), 'altura': (20, 80), 'num_obstaculos': (25, 200)}
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteFarol, ClasseAgente=AgenteFarolQ,
        env_params=params, num_agentes=1, num_episodios=100000, 
        guardar_em="agente_farol_q.pkl",
        parar_no_pico=True, score_alvo=AmbienteFarol.RECOMPENSA_FAROL,
        pico_eps=500 # Janela de estabilidade maior
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
    # Calcular score alvo dinâmico
    avg_recursos = (params['num_recursos'][0] + params['num_recursos'][1]) / 2
    score_alvo_dinamico = (avg_recursos * AmbienteRecolecao.RECOMPENSA_RECOLHA) + AmbienteRecolecao.RECOMPENSA_DEPOSITO
    print(f"--> Meta de Score para Paragem Antecipada: ~{score_alvo_dinamico:.0f}")
    
    Simulador.treinar_q(
        ClasseAmbiente=AmbienteRecolecao, ClasseAgente=AgenteRecolecaoQ,
        env_params=params, num_agentes=2, num_episodios=100000, # Aumentado de 10k para 50k
        guardar_em="agente_recolecao_q.pkl",
        parar_no_pico=False, score_alvo=score_alvo_dinamico,
        pico_eps=500 # Aumentar a janela para garantir estabilidade
    )

def treinar_recolecao_evo():
    print("\n=== TREINO: RECOLEÇÃO (Evolutivo) ===")
    params = {'largura': (20, 50), 'altura': (20, 50), 'num_obstaculos': (20, 70), 'num_recursos': (20, 50)}
    # Calcular score alvo dinâmico
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

    Modos de Treino:
    - TREINO_ALL: Executa todos os módulos de treino em sequência.
    - TREINO_FAROL_Q: Treina o agente Q-Learning para o cenário Farol.
    - TREINO_FAROL_EVO: Treina o agente Evolutivo para o cenário Farol.
    - TREINO_RECOLECAO_Q: Treina o agente Q-Learning para o cenário Recolha.
    - TREINO_RECOLECAO_EVO: Treina o agente Evolutivo para o cenário Recolha.

    Modos de Demonstração:
    - APRESENTACAO: Executa uma demonstração completa com ambos os cenários e abre os gráficos de progresso.
    - DEMO_TEAMS: Demonstração de equipas (Q vs Evo) no cenário especificado com --cenario.
    - DEMO_Q: Demonstração apenas com agentes Q-Learning no cenário especificado.
    - DEMO_EVO: Demonstração apenas com agentes Evolutivos no cenário especificado.
    """, formatter_class=argparse.RawTextHelpFormatter)
    
    parser.add_argument("--modo", type=str, default="APRESENTACAO",
        choices=["TREINO_ALL", "TREINO_FAROL_Q", "TREINO_FAROL_EVO", "TREINO_RECOLECAO_Q", "TREINO_RECOLECAO_EVO",
                 "APRESENTACAO", "DEMO_TEAMS", "DEMO_Q", "DEMO_EVO", "DEMO_FIXO"])
    parser.add_argument("--cenario", type=str, default="FAROL", choices=["FAROL", "RECOLECAO"])
    parser.add_argument("--test_mode", action="store_true", help="Ativa o modo de teste (learning_mode=False)")
    args = parser.parse_args()
    
    MODO = args.modo.upper()
    CENARIO = args.cenario.upper()

    # --- Seletor de Modos ---
    if MODO == "APRESENTACAO":
        run_presentation()
    
    elif MODO == "TREINO_ALL":
        print("--- MODO TREINO_ALL: A executar todos os módulos de treino com o melhor interpretador ---")
        
        # Dicionário de tarefas e seus interpretadores ótimos
        tasks = {
            "TREINO_FAROL_Q": "pypy3",
            "TREINO_RECOLECAO_Q": "python3",
            "TREINO_FAROL_EVO": "python3",
            "TREINO_RECOLECAO_EVO": "python3"
        }
        
        for task, interpreter in tasks.items():
            print(f"\n--- A iniciar tarefa: {task} com '{interpreter}' ---")
            command = [interpreter, "main.py", "--modo", task]
            try:
                # O ideal é verificar se o interpretador existe, mas para simplicidade vamos tentar executar.
                # Um try-except lida com o caso de não ser encontrado.
                subprocess.run(command, check=True)
            except FileNotFoundError:
                print(f"!! ERRO: O interpretador '{interpreter}' não foi encontrado no seu sistema.")
                print(f"!! A saltar a tarefa '{task}'. Por favor, instale '{interpreter}' ou execute a tarefa manualmente.")
            except subprocess.CalledProcessError as e:
                print(f"!! ERRO: A tarefa '{task}' falhou com o código de saída {e.returncode}.")

        print("\n--- TREINO_ALL concluído ---")
        
    elif MODO == "TREINO_FAROL_Q":
        treinar_farol_q()
    
    elif MODO == "TREINO_FAROL_EVO":
        treinar_farol_evo()
        
    elif MODO == "TREINO_RECOLECAO_Q":
        treinar_recolecao_q()
        
    elif MODO == "TREINO_RECOLECAO_EVO":
        treinar_recolecao_evo()
        
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
            print("A configurar equipas: 1x Q-Learning, 1x Evolutivo, 1x Fixo")
            if cerebro_q:
                aq = cerebro_q.clone()
            else:
                aq = AgQ()
            aq.learning_mode = not args.test_mode
            sim.adicionar_agente(aq, equipa_id=1, verbose=False)

            if cerebro_evo:
                ae = cerebro_evo.clone()
            else:
                ae = AgEvo()
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
                if Cerebro:
                    ag = Cerebro.clone()
                else:
                    ag = TipoAgente()
                ag.learning_mode = not args.test_mode
                sim.adicionar_agente(ag, verbose=False)
        
        print(f"A iniciar DEMO ({MODO}) no cenário {CENARIO}...")
        
        try:
            sim.executa_episodio(visualizador=gui, delay=0.1)

            # Determinar e anunciar o vencedor
            if MODO == "DEMO_TEAMS":
                scores = sim.obter_scores_equipas()
                score_q = scores.get(1, 0)
                score_evo = scores.get(2, 0)
                score_fixo = scores.get(3, 0)
                print(f"--- Fim da Demo ---")
                print(f"Pontuação Q-Learning: {score_q:.2f}")
                print(f"Pontuação Evolutivo: {score_evo:.2f}")
                print(f"Pontuação Fixo: {score_fixo:.2f}")

                vencedores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
                if not vencedores or vencedores[0][1] == 0:
                    print("Facto Curioso: Ninguém pontuou!")
                elif len(vencedores) > 1 and vencedores[0][1] == vencedores[1][1]:
                    print("Facto Curioso: Houve um empate entre os primeiros!")
                else:
                    id_vencedor = vencedores[0][0]
                    nomes = {1: "Q-Learning", 2: "Evolutivo", 3: "Fixo"}
                    print(f"🏆 Facto Curioso: A equipa {nomes.get(id_vencedor, 'Desconhecida')} foi a vencedora!")
            else: # DEMO_Q ou DEMO_EVO
                if sim._agentes:
                    vencedor = max(sim._agentes, key=lambda ag: ag.recompensa_total)
                    tipo_agente = "Q-Learning" if MODO == "DEMO_Q" else "Evolutivo"
                    print(f"--- Fim da Demo ---")
                    print(f"🏆 Facto Curioso: O agente {tipo_agente} com a maior pontuação ({vencedor.recompensa_total:.2f}) foi o vencedor!")

            # Fechar a janela automaticamente
            print("Simulação terminada. A janela vai fechar em 5 segundos...")
            gui.root.after(5000, gui.root.destroy)
            gui.root.mainloop()

        except tk.TclError:
            print("Janela fechada antes do fim da simulação.")

if __name__ == "__main__":
    main()