import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures

# --- CORREÇÃO DO CRASH ---
# Forçar o backend 'Agg' ANTES de importar o pyplot.
# Isto impede que o Matplotlib tente usar o Tkinter/GUI nos processos paralelos.
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
# -------------------------

# --- Função auxiliar para multiprocessing (tem de estar fora da classe) ---
def _avaliar_individuo_wrapper(args):
    """
    Função helper para avaliar um indivíduo em paralelo.
    Agora suporta avaliação de EQUIPAS (Multiple Agents).
    """
    agent, env_config, ClasseAmbiente, num_agents_per_team = args
    
    # Criar ambiente e simulador isolados para este processo
    ambiente = ClasseAmbiente(**env_config)
    sim = Simulador()
    sim.cria(ambiente)
    
    # --- TEAM SPAWNING LOGIC ---
    # Adicionar o agente principal
    sim.adicionar_agente(agent, verbose=False)
    
    # Adicionar CLONES para formar a equipa
    # Isto garante que o agente aprende a trabalhar com outros iguais a ele
    for _ in range(num_agents_per_team - 1):
        clone = agent.clone()
        sim.adicionar_agente(clone, verbose=False)
    
    # Executa o episódio
    sim.executa_episodio(visualizador=None, delay=0, max_passos=1000)
    
    # Fitness = Média do score da equipa
    # (Poderia ser o minimo para forçar cooperação total, mas média é mais estável)
    total_score = sum(ag.recompensa_total for ag in sim._agentes)
    return total_score / len(sim._agentes)

class Simulador:

    def __init__(self):
        self._agentes = []
        self._ambiente = None
        self._passo_atual = 0
        self._equipas = {} 

    def cria(self, ambiente):
        self._ambiente = ambiente

    def adicionar_agente(self, agente, equipa_id=None, verbose=True):
        self._agentes.append(agente)
        self._ambiente.colocar_agente(agente)
        if verbose:
            print(f"Agente adicionado (Total: {len(self._agentes)})")
        
        if equipa_id is None:
            self._equipas[agente] = f"Solo_{id(agente)}"
        else:
            self._equipas[agente] = equipa_id

    @staticmethod
    def guardar_agente(agente, filename):
        with open(filename, "wb") as f:
            pickle.dump(agente, f)
        print(f"-> Agente guardado em: {filename}")

    def _processar_decisao_agente(self, agente):
        obs = self._ambiente.observacao_para(agente)
        agente.observacao(obs)
        acao = agente.age()
        return agente, acao

    def _preparar_episodio(self):
        self._ambiente.reset()
        self._passo_atual = 0
        for agente in self._agentes:
            if hasattr(agente, 'reset_episodio'):
                agente.reset_episodio()

    def _executa_passo(self, visualizador=None, delay=0.0):
        if visualizador:
            visualizador.desenhar()
            if delay > 0: time.sleep(delay)
        
        self._ambiente.atualizacao()
        
        decisoes = []
        for ag in self._agentes:
            decisoes.append(self._processar_decisao_agente(ag))

        random.shuffle(decisoes)

        for agente, acao in decisoes:
            recompensa = self._ambiente.agir(agente, acao)
            nova_obs = self._ambiente.observacao_para(agente)
            agente.observacao(nova_obs)
            agente.avaliar_recompensa(recompensa)
            
    def executa_episodio(self, visualizador=None, delay=0.0, max_passos=1000):
        self._preparar_episodio()
        self._ambiente.visualizacao_ativa = (visualizador is not None)
        executando = True
        
        while executando and self._passo_atual < max_passos:
            self._passo_atual += 1
            self._executa_passo(visualizador, delay)
            
            if self._ambiente.terminou:
                executando = False
        
        if visualizador:
            visualizador.desenhar()
            visualizador.root.update()

    def obter_scores_equipas(self):
        scores = {}
        for agente in self._agentes:
            equipa = self._equipas.get(agente)
            if equipa not in scores:
                scores[equipa] = 0
            scores[equipa] += agente.recompensa_total
        return scores

    @staticmethod
    def treinar_q(ClasseAmbiente, ClasseAgente, env_params, num_agentes, num_episodios=1000, guardar_em=None, parar_no_pico=False, score_alvo=None, pico_eps=100, pico_percentagem=0.95):
        print(f"--- Treino Q-Learning ({num_episodios} ep) ---")

        agentes = [ClasseAgente() for _ in range(num_agentes)]
        for ag in agentes:
            ag.learning_mode = True
        
        historico_max_scores = []
        melhor_media_vencedores = -float('inf')
        melhor_agente = None

        sim = Simulador()
        ambiente = ClasseAmbiente(largura=20, altura=20)
        sim.cria(ambiente)
        for ag in agentes:
            sim.adicionar_agente(ag, verbose=False)

        for i in range(num_episodios):
            largura = random.randint(*env_params['largura'])
            altura = random.randint(*env_params['altura'])
            env_kwargs = {'largura': largura, 'altura': altura}
            if 'num_obstaculos' in env_params:
                min_obs, max_obs = env_params['num_obstaculos']
                env_kwargs['num_obstaculos'] = random.randint(min_obs, max_obs)
            if 'num_recursos' in env_params:
                min_rec, max_rec = env_params['num_recursos']
                env_kwargs['num_recursos'] = random.randint(min_rec, max_rec)
            
            sim._ambiente.reconfigurar(**env_kwargs)

            for ag in sim._agentes:
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'):
                    ag.reset_episodio()

            sim.executa_episodio(visualizador=None, delay=0)
            
            scores = [ag.recompensa_total for ag in sim._agentes]
            score_vencedor = max(scores) if scores else 0
            historico_max_scores.append(score_vencedor)

            if (i+1) % 100 == 0:
                media_recente = np.mean(historico_max_scores[-100:])
                print(f"Ep {i+1}: Média Score (Top 100) = {media_recente:.2f}, Epsilon = {agentes[0].epsilon:.4f}")

                if parar_no_pico and score_alvo is not None and len(historico_max_scores) >= pico_eps:
                    scores_recentes = historico_max_scores[-pico_eps:]
                    limite_score = score_alvo * pico_percentagem
                    if min(scores_recentes) >= limite_score:
                        print(f"\n!! PARAGEM ANTECIPADA: Performance estável acima de {limite_score:.2f} por {pico_eps} episódios.")
                        break
                
                if media_recente > melhor_media_vencedores:
                    melhor_media_vencedores = media_recente
                    best_agent_now = max(sim._agentes, key=lambda a: a.recompensa_total)
                    melhor_agente = copy.deepcopy(best_agent_now)

        if guardar_em and melhor_agente:
            Simulador.guardar_agente(melhor_agente, guardar_em)
        
        Simulador._plotar_progresso(historico_max_scores, guardar_em, "Q-Learning", score_alvo=score_alvo, window_size=100)
        return historico_max_scores

    @staticmethod
    def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=50, guardar_em=None, parar_no_pico=False, score_alvo=None, pico_gens=10, pico_percentagem=0.95, num_agents_per_eval=1):
        print(f"--- Treino Genético ({num_geracoes} ger) [Agentes/Sim: {num_agents_per_eval}] ---")

        populacao = [ClasseAgente() for _ in range(pop_size)]
        
        melhor_global = None
        best_score_global = -float('inf')

        historico_melhor_score = []
        scores = [] 

        with concurrent.futures.ProcessPoolExecutor() as executor:
            for g in range(num_geracoes):
                args_list = []
                for ind in populacao:
                    largura = random.randint(*env_params['largura'])
                    altura = random.randint(*env_params['altura'])
                    env_kwargs = {'largura': largura, 'altura': altura}
                    
                    if 'num_obstaculos' in env_params:
                        min_obs, max_obs = env_params['num_obstaculos']
                        env_kwargs['num_obstaculos'] = random.randint(min_obs, max_obs)
                    if 'num_recursos' in env_params:
                        min_rec, max_rec = env_params['num_recursos']
                        env_kwargs['num_recursos'] = random.randint(min_rec, max_rec)
                    
                    # Passar o numero de agentes para o wrapper
                    args_list.append((ind, env_kwargs, ClasseAmbiente, num_agents_per_eval))

                scores = list(executor.map(_avaliar_individuo_wrapper, args_list))

                max_s = max(scores) if scores else -float('inf')
                avg_s = np.mean(scores) if scores else -float('inf')
                
                historico_melhor_score.append(max_s)

                print(f"Ger {g+1}: Melhor={max_s:.1f}, Média={avg_s:.1f}")

                if parar_no_pico and score_alvo is not None and len(historico_melhor_score) >= pico_gens:
                    scores_recentes = historico_melhor_score[-pico_gens:]
                    limite_score = score_alvo * pico_percentagem
                    if min(scores_recentes) >= limite_score:
                        print(f"\n!! PARAGEM ANTECIPADA: Performance estável acima de {limite_score:.2f} por {pico_gens} gerações.")
                        break
                
                if max_s > best_score_global:
                    best_score_global = max_s
                    if scores:
                        idx_best = scores.index(max_s)
                        melhor_global = copy.deepcopy(populacao[idx_best])

                populacao = Simulador._reproduzir_populacao(populacao, scores, pop_size, mutation_rate=0.05)

        if guardar_em and melhor_global:
            Simulador.guardar_agente(melhor_global, guardar_em)
        
        Simulador._plotar_progresso(historico_melhor_score, guardar_em, "Genético", score_alvo=score_alvo, window_size=20)
        return max(historico_melhor_score) if historico_melhor_score else -float('inf')

    @staticmethod
    def _reproduzir_populacao(populacao, scores, pop_size, elite_pct=0.1, mutation_rate=0.05):
        nova_populacao = []
        num_elites = max(1, int(pop_size * elite_pct))
        indices_ordenados = np.argsort(scores)[::-1]
        
        for i in range(num_elites):
            idx = indices_ordenados[i]
            nova_populacao.append(copy.deepcopy(populacao[idx]))
            
        while len(nova_populacao) < pop_size:
            pai1 = Simulador._torneio(populacao, scores)
            pai2 = Simulador._torneio(populacao, scores)
            
            filho = copy.deepcopy(pai1)
            genes_p1 = pai1.genes
            genes_p2 = pai2.genes
            
            mask = np.random.rand(len(genes_p1)) > 0.5
            genes_filho = np.where(mask, genes_p1, genes_p2)
            
            if random.random() < 0.8:
                noise = np.random.randn(len(genes_filho)) * mutation_rate
                genes_filho += noise
            
            filho.genes = genes_filho
            nova_populacao.append(filho)
            
        return nova_populacao

    @staticmethod
    def _torneio(populacao, scores, k=3):
        indices = np.random.choice(len(populacao), k)
        best_idx = indices[0]
        best_score = scores[best_idx]
        
        for idx in indices[1:]:
            if scores[idx] > best_score:
                best_score = scores[idx]
                best_idx = idx
        return populacao[best_idx]

    @staticmethod
    def _plotar_progresso(dados_principal, filename, titulo, score_alvo=None, window_size=50):
        if not dados_principal: return
        
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(14, 8))
        
        ax.scatter(
            range(len(dados_principal)), 
            dados_principal, 
            alpha=0.15, 
            color='lightblue', 
            s=15,
            label='Score de Episódio Individual'
        )

        data = np.array(dados_principal)
        if len(data) > window_size:
            kernel = np.ones(window_size) / window_size
            data_smoothed = np.convolve(data, kernel, mode='valid')
            x_axis_smoothed = np.arange(window_size - 1, len(data))
            ax.plot(x_axis_smoothed, data_smoothed, color='#0033A0', linewidth=2.5, label=f'Média Móvel (janela={window_size})')
        
        if score_alvo is not None:
            ax.axhline(y=score_alvo, color='#D40000', linestyle='--', linewidth=2, label=f'Score Alvo ({score_alvo:.0f})')
            
        if dados_principal:
            peak_score = max(dados_principal)
            peak_episode = np.argmax(dados_principal)
            ax.annotate(
                f'Pico: {peak_score:.0f}',
                xy=(peak_episode, peak_score),
                xytext=(peak_episode, peak_score + (max(dados_principal) - min(dados_principal)) * 0.1),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
                ha='center'
            )

        ax.set_title(f'Progresso do Treino: {titulo}', fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Episódio / Geração', fontsize=12)
        ax.set_ylabel('Score Máximo', fontsize=12)
        ax.legend(fontsize=10)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        
        fig.tight_layout()
        
        if filename:
            nome_grafico = filename.replace('.pkl', '_progress.png')
            plt.savefig(nome_grafico, dpi=120)
            print(f"Gráfico melhorado guardado: {nome_grafico}")
        plt.close(fig)