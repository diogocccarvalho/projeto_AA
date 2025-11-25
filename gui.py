import tkinter as tk
import time

class GUI:
    def __init__(self, ambiente, titulo="Simulador SMA", tamanho_celula=30):
        self.amb = ambiente
        self.tc = tamanho_celula
        self.largura = ambiente.largura
        self.altura = ambiente.altura
        
        # Configuração da Janela
        self.root = tk.Tk()
        self.root.title(titulo)
        self.canvas = tk.Canvas(
            self.root, 
            width=self.largura * self.tc, 
            height=self.altura * self.tc, 
            bg="white"
        )
        self.canvas.pack()

    def desenhar(self):
        """Método abstrato que deve ser implementado pelas subclasses"""
        raise NotImplementedError("A subclasse deve implementar o método desenhar")

    def _limpar_e_atualizar(self):
        """Método auxiliar para finalizar o desenho"""
        self.root.update()
        # Pequeno delay para a animação ser visível ao olho humano
        time.sleep(0.1) 


class GuiRecolecao(GUI):
    def __init__(self, ambiente):
        super().__init__(ambiente, titulo="Ambiente: Recoleção")
        self.cores = {
            'Ninho': 'green',
            'Recurso': 'blue',
            'Agente': 'red',
            'AgenteCarga': '#8B0000' # Vermelho escuro
        }

    def desenhar(self):
        self.canvas.delete("all") # Limpar tela

        # 1. Desenhar Ninho
        nx, ny = self.amb.pos_ninho
        x, y = nx * self.tc, ny * self.tc
        self.canvas.create_rectangle(x, y, x+self.tc, y+self.tc, fill=self.cores['Ninho'], outline="")
        self.canvas.create_text(x+15, y+15, text="N", fill="white")

        # 2. Desenhar Recursos
        for (rx, ry) in self.amb.recursos:
            x, y = rx * self.tc, ry * self.tc
            self.canvas.create_oval(x+5, y+5, x+self.tc-5, y+self.tc-5, fill=self.cores['Recurso'], outline="")

        # 3. Desenhar Agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            ax, ay = pos
            carregado = self.amb.agentes_carga.get(agente, False)
            cor = self.cores['AgenteCarga'] if carregado else self.cores['Agente']
            
            x, y = ax * self.tc, ay * self.tc
            self.canvas.create_rectangle(x+4, y+4, x+self.tc-4, y+self.tc-4, fill=cor, outline="black")

        self._limpar_e_atualizar()


class GuiFarol(GUI):
    def __init__(self, ambiente):
        super().__init__(ambiente, titulo="Ambiente: Farol")
        self.cores = {
            'Farol': '#FFD700', # Dourado
            'Agente': 'purple',
            'Obstaculo': 'gray'
        }

    def desenhar(self):
        self.canvas.delete("all")

        # 1. Desenhar Farol
        fx, fy = self.amb.pos_farol
        x, y = fx * self.tc, fy * self.tc
        self.canvas.create_oval(x, y, x+self.tc, y+self.tc, fill=self.cores['Farol'], outline="orange", width=3)
        self.canvas.create_text(x+15, y+15, text="F", fill="black")

        # 2. Desenhar Obstáculos (caso existam na lista do ambiente)
        if hasattr(self.amb, 'obstaculos'):
            for (ox, oy) in self.amb.obstaculos:
                x, y = ox * self.tc, oy * self.tc
                self.canvas.create_rectangle(x, y, x+self.tc, y+self.tc, fill=self.cores['Obstaculo'], outline="")

        # 3. Desenhar Agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            ax, ay = pos
            x, y = ax * self.tc, ay * self.tc
            self.canvas.create_oval(x+5, y+5, x+self.tc-5, y+self.tc-5, fill=self.cores['Agente'], outline="black")

        self._limpar_e_atualizar()