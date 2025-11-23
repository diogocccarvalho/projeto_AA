class Simulador:
    def __init__(self):
        self._agentes = []
        self._ambiente = None
        self._passo_atual = 0
        self._max_passos = 1000 

    def cria(self, ambiente):
        #inicialização
        self._ambiente = ambiente
        self._passo_atual = 0

    def adicionar_agente(self, agente):
        self._agentes.append(agente)
        self._ambiente.colocar_agente(agente)

    def listaAgentes(self):
        #todos os agentes
        return self._agentes

    def executa(self):
        #motor de execução
        running = True
        
        while running and self._passo_atual < self._max_passos:
            self._passo_atual += 1
            

            self._ambiente.atualizacao()


            for agente in self._agentes:
                # Perceção
                obs = self._ambiente.observacao_para(agente)
                agente.observacao(obs)


                acao = agente.age()

                recompensa = self._ambiente.agir(agente, acao)

                agente.avaliacao_estado_atual(recompensa)


            if self._passo_atual >= self._max_passos:
                running = False