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
    """
    Avalia um indivíduo spawnando uma equipa de clones.
    Isso ensina os agentes a lidar com o tráfego de parceiros.
    """
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
    def treinar_genetico(ClasseAmbiente, ClasseAgente, env_params, pop_size, num_geracoes=50, num_agents_per_eval=2, guardar_em=None, score_alvo=None):
        print(f"--- Treino Genético ({num_geracoes} ger) [Equipas de {num_agents_per_eval}] ---")
        populacao = [ClasseAgente() for _ in range(pop_size)]
        melhor_global = None
        best_score_global = -float('inf')
        historico = []

        with concurrent.futures.ProcessPoolExecutor() as executor:
            for g in range(num_geracoes):
                env_kwargs = {k: random.randint(*v) for k, v in env_params.items()}
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
            if random.random() < 0.2: filho.genes += np.random.randn(len(filho.genes)) * 0.05
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