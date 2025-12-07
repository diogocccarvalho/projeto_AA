import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures
import matplotlib.pyplot as plt

# --- Função auxiliar para multiprocessing (tem de estar fora da classe) ---
def _avaliar_individuo_wrapper(args):
    """
    Função helper para avaliar um indivíduo em paralelo.
    """
    agent, env_config, ClasseAmbiente = args
    
    # Criar ambiente e simulador isolados para este processo
    ambiente = ClasseAmbiente(**env_config)
    sim = Simulador()
    sim.cria(ambiente)
    sim.adicionar_agente(agent, verbose=False)
    
    # Executa o episódio
    sim.executa_episodio(visualizador=None, delay=0, max_passos=1000)
    
    return agent.recompensa_total

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
            print(f"Agente adicionado. Número total de agentes: {len(self._agentes)}")
        
        if equipa_id is None:
            self._equipas[agente] = f"Solo_{id(agente)}"
        else:
            self._equipas[agente] = equipa_id

    @staticmethod
    def guardar_agente(agente, filename):
        with open(filename, "wb") as f:
            pickle.dump(agente, f)
        print(f"Agente guardado em: {filename}")

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
        executando = True
        
        while executando and self._passo_atual < max_passos:
            self._passo_atual += 1
            self._executa_passo(visualizador, delay)
            
            if self._ambiente.terminou:
                executando = False
        
        if visualizador:
            visualizador.desenhar()
            if delay > 0:
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
    def treinar_q(ClasseAmbiente, ClasseAgente, env_params, num_agentes, num_episodios=1000, guardar_em=None):
        print(f"--- Treino Q-Learning Competitivo: {num_episodios} episódios ---")

        agentes = [ClasseAgente() for _ in range(num_agentes)]
        for ag in agentes:
            ag.learning_mode = True
        
        print(f"{num_agentes} agentes criados. A métrica será o score do VENCEDOR (Max Score).")

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
                print(f"Episódio {i+1}: Média do Vencedor (últimos 100) = {media_recente:.2f}")
                
                if media_recente > melhor_media_vencedores:
                    melhor_media_vencedores = media_recente
                    best_agent_now = max(sim._agentes, key=lambda a: a.recompensa_total)
                    melhor_agente = copy.deepcopy(best_agent_now)

        if guardar_em and melhor_agente:
            Simulador.guardar_agente(melhor_agente, guardar_em)
        
        if guardar_em and agentes:
            final_agent = max(agentes, key=lambda a: getattr(a, 'recompensa_total', 0))
            filename_final = guardar_em.replace('.pkl', '_final.pkl')
            Simulador.guardar_agente(final_agent, filename_final)
            print(f"NOTA: Agente do final do treino salvo em '{filename_final}'.")

        # Plot com janela grande de suavização para Q-Learning (muito ruído)
        Simulador._plotar_progresso(historico_max_scores, guardar_em, "Q-Learning (Score Vencedor)", window_size=100)
        return historico_max_scores

    @staticmethod
    def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=50, guardar_em=None):
        print(f"--- Treino Genético: {num_geracoes} gerações, População de {pop_size} ---")

        populacao = [ClasseAgente() for _ in range(pop_size)]
        melhor_global = None
        best_score_global = -float('inf')

        historico_melhor_score = []

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
                    
                    args_list.append((ind, env_kwargs, ClasseAmbiente))

                scores = list(executor.map(_avaliar_individuo_wrapper, args_list))

                max_s = max(scores) if scores else -float('inf')
                avg_s = np.mean(scores) if scores else -float('inf')
                
                historico_melhor_score.append(max_s)

                print(f"Geração {g+1}: Melhor Score={max_s:.1f}, Média Score={avg_s:.1f}")
                
                if max_s > best_score_global:
                    best_score_global = max_s
                    if scores:
                        idx_best = scores.index(max_s)
                        melhor_global = copy.deepcopy(populacao[idx_best])

                populacao = Simulador._reproduzir_populacao(populacao, scores, pop_size)

        if guardar_em and melhor_global:
            Simulador.guardar_agente(melhor_global, guardar_em)
        
        # Plot com janela menor para Genético (menos dados, menos ruído)
        Simulador._plotar_progresso(historico_melhor_score, guardar_em, "Genético (Melhor Score)", window_size=20)
        return best_score_global

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
            
            genes_filho = (genes_p1 + genes_p2) / 2.0
            
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
    def _plotar_progresso(dados_principal, filename, titulo, extra_data=None, window_size=50):
        """
        Gera gráfico com Média Móvel (Suavizada) e Derivada.
        """
        if not dados_principal: return
        
        # Converter para numpy e calcular média móvel (suavização)
        data = np.array(dados_principal)
        if len(data) > window_size:
            kernel = np.ones(window_size) / window_size
            data_smoothed = np.convolve(data, kernel, mode='valid')
            # Ajustar eixo X para corresponder à convolução
            x_axis = np.arange(window_size - 1, len(data))
        else:
            data_smoothed = data
            x_axis = np.arange(len(data))
            
        # Calcular Derivada (Tendência)
        derivada = np.gradient(data_smoothed)
        
        fig, ax1 = plt.subplots(figsize=(12, 7))
        
        # Eixo 1: Score Suavizado
        color = 'tab:blue'
        ax1.set_xlabel('Episódio / Geração')
        ax1.set_ylabel('Score (Média Móvel)', color=color, fontweight='bold')
        ax1.plot(x_axis, data_smoothed, color=color, linewidth=2, label='Score (Suavizado)')
        ax1.tick_params(axis='y', labelcolor=color)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Eixo 2: Derivada (Taxa de Aprendizagem)
        ax2 = ax1.twinx()
        color = 'tab:orange'
        ax2.set_ylabel('Derivada (Tendência de Aprendizagem)', color=color, fontweight='bold')
        ax2.plot(x_axis, derivada, color=color, linestyle='--', linewidth=1.5, label='Derivada', alpha=0.8)
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Linha de referência zero para a derivada
        ax2.axhline(0, color='grey', linewidth=1, linestyle='-')
        
        # Título e Legendas
        plt.title(f'Evolução do Treino: {titulo}\n(Janela de Suavização: {window_size})', fontsize=14)
        fig.tight_layout()
        
        if filename:
            nome_grafico = filename.replace('.pkl', '_progress.png')
            plt.savefig(nome_grafico)
            print(f"Gráfico melhorado guardado: {nome_grafico}")
        plt.close(fig)