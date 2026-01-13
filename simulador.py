import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures
import matplotlib
# Configuração para evitar erros de display em servidores/headless
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# --- Função auxiliar para multiprocessing ---
def _avaliar_individuo_wrapper(args):
    """Avalia um indivíduo num ambiente isolado."""
    agent, env_config, ClasseAmbiente, num_passos = args
    
    # Criar ambiente e simulador isolados
    # Nota: env_config já deve vir limpo (apenas com args suportados pelo Ambiente)
    ambiente = ClasseAmbiente(**env_config)
    sim = Simulador()
    sim.cria(ambiente)
    # Adicionar apenas 1 agente para avaliação pura (sem competição)
    sim.adicionar_agente(agent, verbose=False)
    
    sim.executa_episodio(visualizador=None, delay=0, max_passos=num_passos)
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
            print(f"Agente adicionado. Total: {len(self._agentes)}")
        
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
            time.sleep(0.1)
        
        self._ambiente.atualizacao()
        
        decisoes = []
        for ag in self._agentes:
            decisoes.append(self._processar_decisao_agente(ag))

        random.shuffle(decisoes)

        for agente, acao in decisoes:
            recompensa = self._ambiente.agir(agente, acao)
            nova_obs = self._ambiente.observacao_para(agente)
            agente.avaliar_recompensa(recompensa, nova_obs)
            
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
            visualizador.root.update()

    def obter_scores_equipas(self):
        scores = {}
        for agente in self._agentes:
            equipa = self._equipas.get(agente)
            if equipa not in scores: scores[equipa] = 0
            scores[equipa] += agente.recompensa_total
        return scores

    @staticmethod
    def treinar_q(ClasseAmbiente, ClasseAgente, env_params, num_agentes, num_episodios=1000, guardar_em=None, parar_no_pico=False, score_alvo=None, pico_eps=100, dynamic_obstacles=False):
        print(f"--- Treino Q-Learning ({num_episodios} eps) ---")
        if dynamic_obstacles: print(">>> MODO CURRICULUM: Dificuldade Progressiva Ativada <<<")

        agentes = [ClasseAgente() for _ in range(num_agentes)]
        for ag in agentes: ag.learning_mode = True
        
        historico_scores = []
        sim = Simulador()
        sim.cria(ClasseAmbiente(largura=20, altura=20)) # Inicialização dummy
        for ag in agentes: sim.adicionar_agente(ag, verbose=False)

        # Configuração dos Obstáculos Alvo
        min_obs_target, max_obs_target = env_params.get('num_obstaculos', (10, 10))
        
        # Pontos de transição de fase
        fase1_end = int(num_episodios * 0.3)
        fase2_end = int(num_episodios * 0.6)

        for i in range(num_episodios):
            # --- LÓGICA DE CURRICULUM (FASES) ---
            cur_min_obs, cur_max_obs = min_obs_target, max_obs_target
            
            if dynamic_obstacles:
                if i < fase1_end:
                    # FASE 1: Jardim de Infância (0 Obstáculos)
                    cur_min_obs, cur_max_obs = 0, 0
                    if i == 0: print("[Fase 1] Ambiente Livre: Foco na Lógica de Recolha")
                
                elif i < fase2_end:
                    # FASE 2: Escola Primária (50% Obstáculos)
                    cur_min_obs = max(1, int(min_obs_target * 0.5))
                    cur_max_obs = max(1, int(max_obs_target * 0.5))
                    
                    if i == fase1_end: 
                        print(f"[Fase 2] Introdução de Obstáculos ({cur_max_obs}). BOOST EXPLORAÇÃO!")
                        for ag in sim._agentes:
                            if hasattr(ag, 'boost_exploration'): ag.boost_exploration(0.6)

                else:
                    # FASE 3: Vida Real (100% Obstáculos)
                    cur_min_obs, cur_max_obs = min_obs_target, max_obs_target
                    
                    if i == fase2_end:
                        print(f"[Fase 3] Dificuldade Máxima ({cur_max_obs}). BOOST EXPLORAÇÃO!")
                        for ag in sim._agentes:
                            if hasattr(ag, 'boost_exploration'): ag.boost_exploration(0.4)

            # Reconfigurar ambiente para este episódio
            largura = random.randint(*env_params['largura'])
            altura = random.randint(*env_params['altura'])
            num_obs = random.randint(cur_min_obs, cur_max_obs)
            
            # CORREÇÃO: Criar kwargs apenas com o que existe
            reconfig_args = {
                'largura': largura, 
                'altura': altura, 
                'num_obstaculos': num_obs
            }
            if 'num_recursos' in env_params:
                reconfig_args['num_recursos'] = random.randint(*env_params['num_recursos'])
            
            sim._ambiente.reconfigurar(**reconfig_args)

            for ag in sim._agentes:
                ag.recompensa_total = 0
                if hasattr(ag, 'reset_episodio'): ag.reset_episodio()

            sim.executa_episodio(visualizador=None, delay=0)
            
            scores = [ag.recompensa_total for ag in sim._agentes]
            max_s = max(scores) if scores else 0
            historico_scores.append(max_s)

            if (i+1) % 100 == 0:
                med = np.mean(historico_scores[-100:])
                epsilon_atual = sim._agentes[0].epsilon if hasattr(sim._agentes[0], 'epsilon') else 0
                print(f"Ep {i+1}: Média Score={med:.1f} | Epsilon={epsilon_atual:.3f}")
                
                # --- OTIMIZAÇÃO: Parar no Pico ---
                if parar_no_pico and score_alvo is not None and med >= score_alvo:
                    print(f"!!! PICO ALCANÇADO (Ep {i+1}) - Score Médio: {med:.1f} !!!")
                    if guardar_em:
                        top_ag = max(sim._agentes, key=lambda a: a.recompensa_total)
                        Simulador.guardar_agente(top_ag, guardar_em)
                    break
                
                # Guardar melhor
                if guardar_em:
                    top_ag = max(sim._agentes, key=lambda a: a.recompensa_total)
                    Simulador.guardar_agente(top_ag, guardar_em)

        Simulador._plotar_progresso(historico_scores, guardar_em, "Q-Learning (Curriculum)", window_size=100)

    @staticmethod
    def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=100, guardar_em=None, parar_no_pico=False, score_alvo=None, pico_gens=20, num_agents_per_eval=1, dynamic_obstacles=False):
        print(f"--- Treino Genético ({num_geracoes} ger) ---")
        if dynamic_obstacles: print(">>> MODO CURRICULUM GENÉTICO <<<")

        populacao = [ClasseAgente() for _ in range(pop_size)]
        melhor_global = None
        best_score_global = -float('inf')
        historico_melhor = []

        # Configuração Curriculum
        min_obs_target, max_obs_target = env_params.get('num_obstaculos', (10, 10))
        fase1_end = int(num_geracoes * 0.3)
        fase2_end = int(num_geracoes * 0.6)

        with concurrent.futures.ProcessPoolExecutor() as executor:
            for g in range(num_geracoes):
                # Determinar Dificuldade da Geração
                cur_min_obs, cur_max_obs = min_obs_target, max_obs_target
                
                if dynamic_obstacles:
                    if g < fase1_end:
                        cur_min_obs, cur_max_obs = 0, 0
                        if g == 0: print("[Geração 0] Fase 1: Sem Obstáculos")
                    elif g < fase2_end:
                        cur_min_obs = max(1, int(min_obs_target * 0.5))
                        cur_max_obs = max(1, int(max_obs_target * 0.5))
                        if g == fase1_end: print(f"[Geração {g}] Fase 2: Obstáculos Médios")
                    else:
                        if g == fase2_end: print(f"[Geração {g}] Fase 3: Obstáculos Máximos")

                args_list = []
                for ind in populacao:
                    l = random.randint(*env_params['largura'])
                    a = random.randint(*env_params['altura'])
                    obs = random.randint(cur_min_obs, cur_max_obs)
                    
                    # CORREÇÃO: Criar config segura
                    config = {'largura': l, 'altura': a, 'num_obstaculos': obs}
                    if 'num_recursos' in env_params:
                        config['num_recursos'] = random.randint(*env_params['num_recursos'])
                    
                    # Limitar passos no início para acelerar (se não come em 800 passos, é burro)
                    steps = 800 if dynamic_obstacles and g < fase1_end else 1200
                    args_list.append((ind, config, ClasseAmbiente, steps))

                scores = list(executor.map(_avaliar_individuo_wrapper, args_list))

                max_s = max(scores) if scores else -float('inf')
                avg_s = np.mean(scores) if scores else -float('inf')
                historico_melhor.append(max_s)

                if (g+1) % 10 == 0:
                    print(f"Ger {g+1}: Melhor={max_s:.1f}, Média={avg_s:.1f}")
                    # --- OTIMIZAÇÃO: Parar no Pico ---
                    if parar_no_pico and score_alvo is not None and avg_s >= score_alvo:
                        print(f"!!! GENÉTICO CONVERGIU (Ger {g+1}) - Média: {avg_s:.1f} !!!")
                        # Salvar antes de sair
                        if best_score_global > -float('inf'):
                             if guardar_em: Simulador.guardar_agente(melhor_global, guardar_em)
                        break

                if max_s > best_score_global:
                    best_score_global = max_s
                    idx = scores.index(max_s)
                    melhor_global = copy.deepcopy(populacao[idx])
                    if guardar_em: Simulador.guardar_agente(melhor_global, guardar_em)

                populacao = Simulador._reproduzir_populacao(populacao, scores, pop_size)

        Simulador._plotar_progresso(historico_melhor, guardar_em, "Genético (Curriculum)", window_size=20)

    @staticmethod
    def _reproduzir_populacao(populacao, scores, pop_size, elite_pct=0.1, mutation_rate=0.05):
        nova_populacao = []
        # Elitismo
        num_elites = max(1, int(pop_size * elite_pct))
        indices_ordenados = np.argsort(scores)[::-1]
        for i in range(num_elites):
            nova_populacao.append(copy.deepcopy(populacao[indices_ordenados[i]]))
            
        # Reprodução
        while len(nova_populacao) < pop_size:
            # Torneio
            pais = []
            for _ in range(2):
                idxs = np.random.choice(len(populacao), 3)
                best_i = idxs[np.argmax([scores[i] for i in idxs])]
                pais.append(populacao[best_i])
            
            filho = copy.deepcopy(pais[0])
            # Crossover (Média)
            filho.genes = (pais[0].genes + pais[1].genes) / 2.0
            # Mutação
            if random.random() < 0.8:
                noise = np.random.randn(len(filho.genes)) * mutation_rate
                filho.genes += noise
            nova_populacao.append(filho)
            
        return nova_populacao

    @staticmethod
    def _plotar_progresso(dados, filename, titulo, window_size=50):
        if not dados: return
        data = np.array(dados)
        win = min(window_size, len(data))
        if win < 2: return 

        kernel = np.ones(win) / win
        smooth = np.convolve(data, kernel, mode='valid')
        x = np.arange(win - 1, len(data))
        
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(x, smooth, color='tab:blue', label='Score (Suavizado)')
        ax1.set_ylabel('Score', color='tab:blue')
        ax1.set_title(f'{titulo}')
        ax1.grid(True, alpha=0.3)
        
        if filename:
            name = filename.replace('.pkl', '_progress.png')
            plt.savefig(name)
            print(f"Gráfico salvo: {name}")
        plt.close(fig)