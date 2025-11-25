from simulador import Simulador
from ambientes.ambiente_farol import AmbienteFarol
from ambientes.ambiente_recolecao import AmbienteRecolecao
from agente import AgenteRandom

def main():

    sim = Simulador()

    #amb = AmbienteFarol(largura=10, altura=10)
    amb = AmbienteRecolecao(largura=10, altura=10, num_recursos=5)
    

    sim.cria(amb)

    agente_teste = AgenteRandom()
    

    sim.adicionar_agente(agente_teste)


    sim._max_passos = 50 
    sim.executa()

if __name__ == "__main__":
    main()