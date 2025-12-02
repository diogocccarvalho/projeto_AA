import time
import pickle
import random
import copy
import numpy as np
import concurrent.futures

class Simulador:

    def __init__(self):
        self._agentes = []
        self._ambiente = None
        self._passo_atual = 0
        #equipas
        self._equipas = {} 

    def cria(self, ambiente):
        self._ambiente = ambiente

    def adicionar_agente(self, agente, equipa_id=None):
        self._agentes.append(agente)
        self._ambiente.colocar_agente(agente)
        
        # sem equipa é competição individual
        if equipa_id is None:
            self._equipas[agente] = f"Solo_{id(agente)}"
        else:
            self._equipas[agente] = equipa_id

    def guardar_agente(self, agente, filename):
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

    def _executa_passo(self, executor, visualizador=None, delay=0.0):
        if visualizador:
            visualizador.desenhar()
            if delay > 0: time.sleep(delay)
        
        self._ambiente.atualizacao()
        #executar decisões em paralelo
        futures = [executor.submit(self._processar_decisao_agente, ag) for ag in self._agentes]
        decisoes = [f.result() for f in concurrent.futures.as_completed(futures)]

        #ação é sequencial para evitar erros
        for agente, acao in decisoes:
            recompensa = self._ambiente.agir(agente, acao)
            agente.avaliar_recompensa(recompensa)

    def executa_episodio(self, visualizador=None, delay=0.0, max_passos=1000):
        self._preparar_episodio()
        executando = True
        
        #concurrência
        with concurrent.futures.ThreadPoolExecutor() as executor:
            while executando and self._passo_atual < max_passos:
                self._passo_atual += 1
                self._executa_passo(executor, visualizador, delay)
                
                if self._ambiente.terminou:
                    executando = False


    def obter_scores_equipas(self):
        #pontuações
        scores = {}
        for agente in self._agentes:
            equipa = self._equipas.get(agente)
            if equipa not in scores:
                scores[equipa] = 0
            scores[equipa] += agente.recompensa_total
        return scores

    # reinforcement learning
    def treinar_q(self, num_episodios=1000, guardar_em=None):
        print(f"--- Treino Q-Learning: {num_episodios} episódios ---")
        historico = []
        melhor_media = -float('inf')
        melhor_agente = None

        for i in range(num_episodios):
            self.executa_episodio(visualizador=None, delay=0)
            
            score = self._agentes[0].recompensa_total
            historico.append(score)

            if (i+1) % 100 == 0:
                media = sum(historico[-100:]) / 100
                print(f"Episódio {i+1}: Média Score (últimos 100) = {media:.2f}")
                if media > melhor_media:
                    melhor_media = media
                    # Deepcopy to save the state of the agent at its best performance
                    melhor_agente = copy.deepcopy(self._agentes[0])

        # If no agent was ever saved (e.g. less than 100 episodes), save the last one.
        if melhor_agente is None:
            melhor_agente = self._agentes[0]

        if guardar_em:
            self.guardar_agente(melhor_agente, guardar_em)
        return historico

    #evolução
    def _avaliar_populacao(self, populacao):
        scores = []
        for individuo in populacao:
            self._agentes = []
            self.adicionar_agente(individuo)
            self.executa_episodio()
            scores.append(individuo.recompensa_total)
        return scores

    def _selecionar_pais(self, populacao, scores, k=3):
        selecao = random.sample(list(zip(populacao, scores)), k)
        selecao.sort(key=lambda x: x[1], reverse=True)
        return selecao[0][0]

    def _crossover(self, p1, p2):
        filho = copy.deepcopy(p1)
        mask = np.random.rand(*filho.genes.shape) > 0.5
        filho.genes[mask] = p2.genes[mask]
        return filho

    def _mutacao(self, individuo, chance=0.1, magnitude=0.2):
        if random.random() < chance:
            individuo.genes += np.random.normal(0, magnitude, individuo.genes.shape)
        return individuo

    def _reproduzir_populacao(self, populacao, scores, pop_size):
        nova_pop = []
        
        idx_best = scores.index(max(scores))
        nova_pop.append(copy.deepcopy(populacao[idx_best]))

        while len(nova_pop) < pop_size:

            p1 = self._selecionar_pais(populacao, scores)
            p2 = self._selecionar_pais(populacao, scores)
            
            filho = self._crossover(p1, p2)
            filho = self._mutacao(filho)
            
            nova_pop.append(filho)
        return nova_pop

    def treinar_genetico(self, ClasseAgente, num_geracoes=50, pop_size=20, guardar_em=None):
        print(f"--- Treino Genético: {num_geracoes} gerações, População de {pop_size} ---")
        
        populacao = [ClasseAgente() for _ in range(pop_size)]
        melhor_global = None
        best_score_global = -float('inf')

        for g in range(num_geracoes):
            scores = self._avaliar_populacao(populacao)


            max_s = max(scores)
            avg_s = sum(scores) / len(scores)
            print(f"Geração {g+1}: Melhor Score={max_s:.1f}, Média Score={avg_s:.1f}")
            
            if max_s > best_score_global:
                best_score_global = max_s
                idx_best = scores.index(max_s)
                melhor_global = copy.deepcopy(populacao[idx_best])

            populacao = self._reproduzir_populacao(populacao, scores, pop_size)

        if guardar_em and melhor_global:
            self.guardar_agente(melhor_global, guardar_em)
        
        return best_score_global