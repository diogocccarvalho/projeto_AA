-----

# Projeto de Sistemas Multi-Agente (SMA) - Simulação e Aprendizagem

Este projeto implementa um ambiente de simulação para agentes autónomos, explorando duas abordagens distintas de Inteligência Artificial: **Aprendizagem por Reforço (Q-Learning)** e **Computação Evolucionária (Neuroevolução)**.

O objetivo foi criar agentes capazes de resolver problemas de navegação e recolha de recursos em ambientes complexos, dinâmicos e hostis.

## 👥 Equipa

| Número de Aluno | Nome |
| :--- | :--- |
| **00000** | **Nome do Aluno 1** |
| **00000** | **Nome do Aluno 2** |
| **00000** | **Nome do Aluno 3** |

-----

## 🤖 Declaração de Uso de IA (Honestidade Académica)

Este projeto foi desenvolvido com a assistência de ferramentas de Inteligência Artificial (LLMs) como copiloto de desenvolvimento. A IA foi utilizada para:

  * **Refactoring e Otimização:** Limpeza de código, estruturação de classes e implementação de *multiprocessing* para treino paralelo.
  * **Ajuste Fino (Fine-tuning):** Sugestão de hiperparâmetros críticos (tamanho de camadas escondidas, taxas de penalidade, decay de epsilon) para acelerar o processo de tentativa-erro.
  * **Depuração Lógica:** Identificação de falhas em comportamentos de loop ("back-and-forth") e conflitos matemáticos nas tabelas de penalidade.
  * **Documentação:** Geração de estruturas para relatórios e este README.

A lógica arquitetural, a definição dos problemas e a validação final dos comportamentos emergentes foram inteiramente realizadas pela equipa.

-----

## 🚀 Funcionalidades Principais

### 1\. Ambientes Estocásticos e Robustez

Ao contrário de ambientes estáticos, o nosso simulador utiliza **Domain Randomization**. Em cada episódio de treino, o tamanho do mapa (20x20 a 50x50), o número de obstáculos, a posição dos recursos e os spawns mudam. Isto garante que os agentes não "decoram" o mapa, mas sim aprendem a **navegar** e generalizar para qualquer situação.

### 2\. Heterogeneidade de Agentes

O sistema suporta a execução simultânea de diferentes tipos de "cérebros":

  * **Agentes Q-Learning (Tabela):** Aprendizagem baseada em estados discretos, com memória de curto prazo e consciência da ação anterior.
  * **Agentes Evolucionários (Rede Neuronal):** Redes *Feed-forward* (Input 15 -\> Hidden 40 -\> Output 6) cujos pesos são evoluídos através de um Algoritmo Genético (Seleção por Torneio, Elitismo e Mutação Gaussiana).

### 3\. Modos de Competição e Cooperação

  * **Competição:** Múltiplos agentes competem pelos mesmos recursos limitados.
  * **Sentido de Urgência:** No cenário do Farol, o treino foca-se no score do **Vencedor** (Max Score), incentivando a velocidade em vez da segurança excessiva.

### 4\. Treino Massivo

Implementámos paralelismo no treino genético para permitir populações grandes (200+ indivíduos) e treinos longos (20.000+ episódios no Q-Learning) para superar a complexidade combinatória da Recoleção.

-----

## 🧠 Algoritmos e Mecanismos Implementados

### Q-Learning (Tabular)

  * **Estado Complexo:** Otimizado para evitar a "cegueira de estado". O tuplo de estado inclui:
      * Direção do Alvo (Quadrante).
      * Distância Discreta (4 níveis: Em cima, Muito Perto, Perto, Longe).
      * Leitura de Sensores (Obstáculos em 8 direções).
      * Estado de Carga (apenas na Recoleção).
      * **Última Ação:** Adicionada para que o agente saiba de onde veio.
  * **Exploração:** Implementação de `Epsilon-Greedy` com decaimento lento (`0.99975`) para garantir exploração profunda (até ao episódio 18.000).

### Neuroevolução (Algoritmo Genético)

  * **Cérebro:** Uma Rede Neuronal Densa (Fully Connected).
      * *Hidden Layer:* Aumentada de 10 para **50 neurónios** para permitir ao agente aprender a lógica condicional complexa de "Alternar entre Busca e Entrega".
  * **Evolução:** A cada geração, os melhores agentes são preservados (Elitismo) e os restantes são criados por cruzamento e mutação dos vencedores.

-----

## ⚠️ Dificuldades Encontradas e Soluções Técnicas

Durante o desenvolvimento, enfrentámos vários desafios de comportamento emergente indesejado.

| Problema | Sintoma Detalhado | Solução Técnica Implementada |
| :--- | :--- | :--- |
| **Oscilação "Back-and-Forth"** | Mesmo em espaço aberto, o agente vibrava entre Norte e Sul indefinidamente. | **Estado Estendido:** O agente sofria de *State Aliasing* (o estado na célula A era igual ao estado na célula B). Adicionámos a `self.acao_anterior` ao estado do Q-Learning para quebrar a simetria. |
| **Cegueira de Proximidade** | O agente chegava a 1 bloco do recurso e parava, "achando" que já tinha chegado, mas falhava a ação de Recolher. | **Refinamento de Sensores:** Alterámos a `distancia_discreta` para ter precisão cirúrgica: Distinguir explicitamente Distância 0 (Em cima) de Distância \< 2 (Adjacente). |
| **O "Círculo da Morte"** | Em mapas grandes (80x80), o agente entrava em estruturas complexas, dava a volta e esquecia-se que já tinha estado ali, entrando em loop infinito. | **Aumento de Memória:** O `TAMANHO_HISTORICO` de posições visitadas foi aumentado, permitindo ao agente reconhecer loops muito maiores. |
| **Matemática da Preguiça** | O agente preferia ficar parado a bater numa parede infinitamente do que tentar sair de um beco sem saída. | **Reequilíbrio de Penalidades:** A penalidade por bater na parede (-2.0) foi tornada superior à penalidade de repetição (-1.5), tornando matematicamente vantajoso voltar para trás. |
| **Score Negativo (-3000)** | Na recoleção, agentes morriam por timeout sem apanhar nada, aprendendo apenas a "não morrer". | **Força Bruta:** Aumentámos a camada escondida da rede neuronal (10-\>40) e o número de episódios Q-Learning (1k -\> 20k) para forçar a descoberta da recompensa esparsa. |

-----

## 🛠️ Como Executar

O projeto possui um ficheiro `main.py` robusto com vários modos de execução.

### Instalação

```bash
pip install numpy matplotlib
```

### Modos de Execução

**1. A "Demo Gigante" (Apresentação Final)**
Corre a sequência completa: Farol, Recolha e mostra os gráficos de evolução.

```bash
python main.py --modo DEMO_GIGANTE
```

**2. Treino Completo (Recomendado para gerar novos cérebros)**
Atenção: Este modo demora imenso tempo a executar.

```bash
python main.py --modo TREINO_Q_EVO_ALL
```

**3. Demonstrações Específicas**

```bash
# Ver agentes Q-Learning no Farol
python main.py --modo DEMO_Q --cenario FAROL

# Ver agentes Evolucionários na Recolha
python main.py --modo DEMO_EVO --cenario RECOLECAO
```

**4. Torneio (Equipa Q vs Equipa Evo)**

```bash
python main.py --modo DEMO_TEAMS --cenario RECOLECAO
```

-----

*Projeto realizado no âmbito da unidade curricular de Agentes Autónomos, 2025.*