import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

def _avaliar_individuo_wrapper(args):

    agent, env_config, ClasseAmbiente, num_agentes_equipa = args
    
    ambiente = ClasseAmbiente(**env_config)
    sim = Simulador()
    sim.cria(ambiente)
    
    equipa = []
    for _ in range(num_agentes_equipa):
        clone = agent.clone()
        sim.adicionar_agente(clone, verbose=False)
        equipa.append(clone)
    
    sim.executa_episodio(max_passos=1000)
    return sum(a.recompensa_total for a in equipa) / len(equipa)

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
        if equipa_id is not None:
            self._equipas[agente] = equipa_id

    def executa_episodio(self, visualizador=None, delay=0.0, max_passos=1000):
        self._ambiente.reset()
        self._passo_atual = 0
        for _ in range(max_passos):
            self._passo_atual += 1
            self._ambiente.atualizacao()
            
            decisoes = []
            for ag in self._agentes:
                obs = self._ambiente.observacao_para(ag)
                ag.observacao(obs)
                decisoes.append((ag, ag.age()))
            
            random.shuffle(decisoes)
            for ag, acao in decisoes:
                r = self._ambiente.agir(ag, acao)
                ag.avaliar_recompensa(r)
            
            if visualizador:
                visualizador.desenhar()
                visualizador.root.update()
                if delay > 0: time.sleep(delay)
            if self._ambiente.terminou: break

    @staticmethod
    def _guardar_grafico_progresso(historico, caminho_pkl):
        """Gera um gráfico com pontos semi-transparentes e uma curva de tendência suave."""
        if not historico: return
        
        nome_grafico = caminho_pkl.replace(".pkl", "_progress.png")
        plt.figure(figsize=(12, 6))
        
        x = range(len(historico))
        
        # 1. Pontos individuais com pouca opacidade (Scatter plot)
        # alpha=0.2 torna os pontos muito leves, s=10 define o tamanho
        plt.scatter(x, historico, color='royalblue', alpha=0.15, s=8, label="Scores Individuais")
        
        # 2. Função suavizada (Média Móvel)
        # Ajustamos a janela de suavização dependendo do tamanho do histórico
        window_size = max(10, len(historico) // 50)
        if len(historico) > window_size:
            smooth_y = np.convolve(historico, np.ones(window_size)/window_size, mode='valid')
            # Ajustamos o eixo X para a curva suavizada
            x_smooth = range(window_size - 1, len(historico))
            plt.plot(x_smooth, smooth_y, color='red', linewidth=2, label=f"Tendência (Média {window_size})")
        
        plt.title(f"Evolução do Treino - {caminho_pkl}", fontsize=14)
        plt.xlabel("Episódio / Geração", fontsize=12)
        plt.ylabel("Score Recompensa", fontsize=12)
        plt.legend(loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        # Ajuste de margens para o gráfico ficar bonito
        plt.tight_layout()
        plt.savefig(nome_grafico, dpi=150)
        plt.close()
        print(f"-> Gráfico atualizado: {nome_grafico}")

    @staticmethod
    def _calcular_obstaculos(progresso, total, max_obstaculos):
        """Calcula o número de obstáculos de forma dinâmica com base no progresso."""
        if max_obstaculos == 0:
            return 0
        # Aumenta o número de obstáculos de forma linear
        return int((progresso / total) * max_obstaculos)

    @staticmethod
    def treinar_q(ClasseAmbiente, ClasseAgente, env_params, num_agentes, num_episodios, 
                  guardar_em=None, score_alvo=None, parar_no_pico=False, pico_eps=100, dynamic_obstacles=False):
        print(f"--- Treino Q-Learning ({num_episodios} eps) ---")
        equipa = [ClasseAgente() for _ in range(num_agentes)]
        tabela_comum = equipa[0].q_table
        for ag in equipa:
            ag.q_table = tabela_comum
            ag.learning_mode = True
            
        historico = []
        raw_obstaculos = env_params.get('num_obstaculos', 0)
        max_obstaculos = raw_obstaculos[1] if isinstance(raw_obstaculos, tuple) else raw_obstaculos

        for e in range(num_episodios):
            env_kwargs = {k: random.randint(*v) if isinstance(v, tuple) else v for k, v in env_params.items()}
            
            if dynamic_obstacles:
                env_kwargs['num_obstaculos'] = Simulador._calcular_obstaculos(e, num_episodios, max_obstaculos)

            amb = ClasseAmbiente(**env_kwargs)
            sim = Simulador()
            sim.cria(amb)
            for ag in equipa: sim.adicionar_agente(ag, verbose=False)
            
            sim.executa_episodio(max_passos=1000)
            score_medio = sum(ag.recompensa_total for ag in equipa) / num_agentes
            historico.append(score_medio)
            for ag in equipa: ag.reset_episodio()
            
            if (e + 1) % 100 == 0:
                print(f"Ep {e+1}: Score={score_medio:.1f}, Epsilon={equipa[0].epsilon:.3f}")
        
        if guardar_em:
            with open(guardar_em, "wb") as f: pickle.dump(equipa[0], f)
            Simulador._guardar_grafico_progresso(historico, guardar_em)
        return historico

    @staticmethod
    def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=50, 
                         num_agents_per_eval=2, guardar_em=None, score_alvo=None, 
                         parar_no_pico=False, pico_gens=20, dynamic_obstacles=False):
        print(f"--- Treino Genético ({num_geracoes} ger) ---")
        populacao = [ClasseAgente() for _ in range(pop_size)]
        melhor_global = None
        best_score_global = -float('inf')
        historico = []
        raw_obstaculos = env_params.get('num_obstaculos', 0)
        max_obstaculos = raw_obstaculos[1] if isinstance(raw_obstaculos, tuple) else raw_obstaculos

        with concurrent.futures.ProcessPoolExecutor() as executor:
            for g in range(num_geracoes):
                env_kwargs = {k: random.randint(*v) if isinstance(v, tuple) else v for k, v in env_params.items()}
                
                if dynamic_obstacles:
                    env_kwargs['num_obstaculos'] = Simulador._calcular_obstaculos(g, num_geracoes, max_obstaculos)

                args_list = [(ind, env_kwargs, ClasseAmbiente, num_agents_per_eval) for ind in populacao]
                
                scores = list(executor.map(_avaliar_individuo_wrapper, args_list))
                max_s = max(scores)
                historico.append(max_s)
                
                if max_s > best_score_global:
                    best_score_global = max_s
                    melhor_global = copy.deepcopy(populacao[scores.index(max_s)])

                print(f"Ger {g+1}: Melhor={max_s:.1f}, Média={np.mean(scores):.1f}")
                populacao = Simulador._reproduzir_populacao(populacao, scores, pop_size)

        if guardar_em and melhor_global:
            with open(guardar_em, "wb") as f: pickle.dump(melhor_global, f)
            Simulador._guardar_grafico_progresso(historico, guardar_em)
        return historico

    @staticmethod
    def _reproduzir_populacao(pop, scores, size):
        nova = []
        idx = np.argsort(scores)[::-1]
        for i in range(int(size * 0.1)): nova.append(copy.deepcopy(pop[idx[i]]))
        while len(nova) < size:
            p1, p2 = Simulador._torneio(pop, scores), Simulador._torneio(pop, scores)
            filho = copy.deepcopy(p1)
            mask = np.random.rand(len(p1.genes)) > 0.5
            filho.genes = np.where(mask, p1.genes, p2.genes)
            if random.random() < 0.4: 
                filho.genes += np.random.randn(len(filho.genes)) * 0.1
            nova.append(filho)
        return nova

    @staticmethod
    def _torneio(pop, scores, k=3):
        idx = np.random.choice(len(pop), k)
        return pop[idx[np.argmax([scores[i] for i in idx])]]
    
    def obter_scores_equipas(self):
        res = {}
        for ag in self._agentes:
            eid = self._equipas.get(ag, "Solo")
            res[eid] = res.get(eid, 0) + ag.recompensa_total
        return res