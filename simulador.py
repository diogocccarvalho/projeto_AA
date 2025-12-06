import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures
import matplotlib.pyplot as plt

class Simulador:

    def __init__(self):
        self._agentes = []
        self._ambiente = None
        self._passo_atual = 0
        #equipas
        self._equipas = {} 

    def cria(self, ambiente):
        self._ambiente = ambiente

    def adicionar_agente(self, agente, equipa_id=None, verbose=True):
        self._agentes.append(agente)
        self._ambiente.colocar_agente(agente)
        if verbose:
            print(f"Agente adicionado. Número total de agentes: {len(self._agentes)}")
        
        # sem equipa é competição individual
        if equipa_id is None:
            self._equipas[agente] = f"Solo_{id(agente)}"
        else:
            self._equipas[agente] = equipa_id

    @staticmethod
    def guardar_agente(agente, filename):
        #guardar melhor agente
        with open(filename, "wb") as f:
            pickle.dump(agente, f)
        print(f"Agente guardado em: {filename}")

    #processar as decisõe dos agentes em paralelo
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

        #ação é sequencial para evitar erros
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
        
        # Desenhar o estado final para garantir que a GUI mostra a conclusão
        if visualizador:
            visualizador.desenhar()
            visualizador.root.after(1000, visualizador.on_close) # Pausar por 1 segundo para ver o resultado final



    def obter_scores_equipas(self):
        #pontuações
        scores = {}
        for agente in self._agentes:
            equipa = self._equipas.get(agente)
            if equipa not in scores:
                scores[equipa] = 0
            scores[equipa] += agente.recompensa_total
        return scores

    @staticmethod
    def treinar_q(ClasseAmbiente, ClasseAgente, env_params, num_agentes, num_episodios=1000, guardar_em=None):
        print(f"--- Treino Q-Learning: {num_episodios} episódios ---")

        agentes = [ClasseAgente() for _ in range(num_agentes)]
        for ag in agentes:
            ag.learning_mode = True
        
        print(f"{num_agentes} agentes criados para o treino.")

        historico_media_scores = []
        melhor_media = -float('inf')
        melhor_agente = None

        # Criar o simulador e o ambiente uma vez
        sim = Simulador()
        ambiente = ClasseAmbiente(largura=1, altura=1) # Tamanho inicial, será reconfigurado
        sim.cria(ambiente)
        for ag in agentes:
            sim.adicionar_agente(ag, verbose=False)

        for i in range(num_episodios):
            # Randomizar e reconfigurar o ambiente existente
            largura = random.randint(*env_params['largura'])
            altura = random.randint(*env_params['altura'])
            
            env_kwargs = {'largura': largura, 'altura': altura}
            if 'num_obstaculos' in env_params:
                min_obs, max_obs = env_params['num_obstaculos']
                env_kwargs['num_obstaculos'] = random.randint(min_obs, max_obs)
            if 'num_recursos' in env_params:
                min_rec, max_rec = env_params['num_recursos']
                env_kwargs['num_recursos'] = random.randint(min_rec, max_rec)
            
            sim.ambiente.reconfigurar(**env_kwargs)

            # Resetar estado dos agentes para o novo episódio
            for ag in sim._agentes:
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'):
                    ag.reset_episodio()

            sim.executa_episodio(visualizador=None, delay=0)
            
            scores = [ag.recompensa_total for ag in sim._agentes]
            score_medio = np.mean(scores) if scores else 0
            historico_media_scores.append(score_medio)

            if (i+1) % 100 == 0:
                media_recente = np.mean(historico_media_scores[-100:])
                print(f"Episódio {i+1}: Média Score (últimos 100) = {media_recente:.2f}")
                if media_recente > melhor_media:
                    melhor_media = media_recente
                    if scores:
                        # Encontrar e salvar o agente com o melhor score da última centena de episódios
                        best_score_episode = -float('inf')
                        best_agent_episode = None
                        for ag in sim._agentes:
                            if ag.recompensa_total > best_score_episode:
                                best_score_episode = ag.recompensa_total
                                best_agent_episode = ag
                        if best_agent_episode:
                            melhor_agente = copy.deepcopy(best_agent_episode)

        if melhor_agente is None and agentes:
            melhor_agente = agentes[0]

        if guardar_em and melhor_agente:
            Simulador.guardar_agente(melhor_agente, guardar_em)
        
        # Plotar o histórico de scores
        medias_scores_plot = [np.mean(historico_media_scores[i:i+100]) for i in range(0, len(historico_media_scores), 100)]
        episodios = [i*100 for i in range(len(medias_scores_plot))]

        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.set_xlabel('Episódio')
        ax1.set_ylabel('Score Médio', color='tab:blue')
        ax1.plot(episodios, medias_scores_plot, marker='o', linestyle='-', label='Média de Score', color='tab:blue')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        if historico_media_scores:
            melhor_score_geral = max(historico_media_scores)
            ax1.axhline(y=melhor_score_geral, color='r', linestyle='--', label=f'Melhor Score Médio: {melhor_score_geral:.2f}')

        if len(episodios) > 1:
            derivada = np.diff(medias_scores_plot) / np.diff(episodios)
            ax2 = ax1.twinx()  
            ax2.set_ylabel('Taxa de Aprendizagem', color='tab:green')
            ax2.plot(episodios[1:], derivada, linestyle='--', marker='x', label='Taxa de Aprendizagem', color='tab:green')
            ax2.tick_params(axis='y', labelcolor='tab:green')
            ax2.legend(loc='upper right')

        fig.tight_layout()  
        plt.title('Progresso e Taxa de Aprendizagem do Agente Q-Learning')
        ax1.legend(loc='upper left')
        plt.grid(True)
        
        if guardar_em:
            graph_filename = guardar_em.replace('.pkl', '_q_learning_progress.png')
            plt.savefig(graph_filename)
            print(f"Gráfico de progresso guardado em: {graph_filename}")
        
        plt.close(fig)

        return historico_media_scores

        @staticmethod

        def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=50, guardar_em=None):

            print(f"--- Treino Genético: {num_geracoes} gerações, População de {pop_size} ---")

            

            populacao = [ClasseAgente() for _ in range(pop_size)]

            melhor_global = None

            best_score_global = -float('inf')

    

            historico_melhor_score = []

            historico_media_score = []

    

            def _avaliar_individuo(args):

                agent, env_config = args

                

                # Criar ambiente e simulador uma vez por processo

                ambiente = ClasseAmbiente(**env_config)

                sim = Simulador()

                sim.cria(ambiente)

                sim.adicionar_agente(agent, verbose=False)

                sim.executa_episodio(max_passos=1000)

                return agent.recompensa_total

    

            with concurrent.futures.ProcessPoolExecutor() as executor:

                for g in range(num_geracoes):

                    # Gerar configurações de ambiente para cada indivíduo

                    env_configs = []

                    for _ in range(pop_size):

                        largura = random.randint(*env_params['largura'])

                        altura = random.randint(*env_params['altura'])

                        

                        env_kwargs = {'largura': largura, 'altura': altura}

                        if 'num_obstaculos' in env_params:

                            min_obs, max_obs = env_params['num_obstaculos']

                            env_kwargs['num_obstaculos'] = random.randint(min_obs, max_obs)

                        if 'num_recursos' in env_params:

                            min_rec, max_rec = env_params['num_recursos']

                            env_kwargs['num_recursos'] = random.randint(min_rec, max_rec)

                        env_configs.append(env_kwargs)

    

                    # Mapear a avaliação para a pool de processos

                    args_list = zip(populacao, env_configs)

                    scores = list(executor.map(_avaliar_individuo, args_list))

    

                    max_s = max(scores) if scores else -float('inf')

                    avg_s = np.mean(scores) if scores else -float('inf')

                    

                    historico_melhor_score.append(max_s)

                    historico_media_score.append(avg_s)

    

                    print(f"Geração {g+1}: Melhor Score={max_s:.1f}, Média Score={avg_s:.1f}")

                    

                    if max_s > best_score_global:

                        best_score_global = max_s

                        if scores:

                            idx_best = scores.index(max_s)

                            melhor_global = copy.deepcopy(populacao[idx_best])

    

                    populacao = Simulador._reproduzir_populacao(populacao, scores, pop_size)

    

            if guardar_em and melhor_global:

                Simulador.guardar_agente(melhor_global, guardar_em)

            

            # Plotting

            fig, ax1 = plt.subplots(figsize=(12, 6))

            

            geracoes = range(1, num_geracoes + 1)

            ax1.plot(geracoes, historico_melhor_score, marker='o', linestyle='-', label='Melhor Score por Geração', color='tab:blue')

            ax1.plot(geracoes, historico_media_score, marker='x', linestyle='--', label='Média de Score por Geração', color='tab:cyan')

            ax1.set_xlabel('Geração')

            ax1.set_ylabel('Score', color='tab:blue')

            ax1.tick_params(axis='y', labelcolor='tab:blue')

            ax1.legend(loc='upper left')

            

            # Adicionar derivada da média

            if num_geracoes > 1:

                derivada = np.diff(historico_media_score)

                ax2 = ax1.twinx()

                ax2.plot(geracoes[1:], derivada, linestyle=':', marker='.', label='Taxa de Aprendizagem (Derivada da Média)', color='tab:green')

                ax2.set_ylabel('Taxa de Aprendizagem', color='tab:green')

                ax2.tick_params(axis='y', labelcolor='tab:green')

                ax2.legend(loc='upper right')

    

            plt.title('Progresso do Algoritmo Genético')

            plt.grid(True)

            fig.tight_layout()

            

            if guardar_em:

                graph_filename = guardar_em.replace('.pkl', '_genetico_progress.png')

                plt.savefig(graph_filename)

                print(f"Gráfico de progresso guardado em: {graph_filename}")

                

            plt.close(fig)

    

            return best_score_global

    