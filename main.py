from simulador import Simulador
from ambientes.ambiente_farol import AmbienteFarol
from agente import AgenteRandom

def main():
    # 1. Criar o Motor
    sim = Simulador()

    # 2. Criar o Ambiente (Farol)
    # Cria uma grelha 10x10 para ser fácil de testar
    amb = AmbienteFarol(largura=10, altura=10)
    
    # Carregar o ambiente no simulador
    sim.cria(amb)

    # 3. Criar o Agente de Teste
    agente_teste = AgenteRandom()
    
    # Adicionar o agente ao motor
    sim.adicionar_agente(agente_teste)

    # 4. Executar a Simulação
    # Vai correr 50 passos ou até o agente encontrar o farol (por sorte)
    sim._max_passos = 50 
    sim.executa()

if __name__ == "__main__":
    main()