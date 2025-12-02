import tkinter as tk

class GUI:
    def __init__(self, ambiente, titulo="Simulador SMA", tamanho_celula=30):
        self.amb = ambiente
        self.tc = tamanho_celula
        self.largura = ambiente.largura
        self.altura = ambiente.altura
        
        self.root = tk.Tk()
        self.root.title(titulo)
        self.canvas = tk.Canvas(
            self.root, 
            width=self.largura * self.tc, 
            height=self.altura * self.tc, 
            bg="#F0F0F0"
        )
        self.canvas.pack()
        self._desenhar_grid()

    def _desenhar_grid(self):
        for i in range(self.largura + 1):
            x = i * self.tc
            self.canvas.create_line(x, 0, x, self.altura * self.tc, fill="#D0D0D0")
        for i in range(self.altura + 1):
            y = i * self.tc
            self.canvas.create_line(0, y, self.largura * self.tc, y, fill="#D0D0D0")

    def _limpar_dinamicos(self):
        self.canvas.delete('dinamico')

    def _atualizar_tela(self):
        self.root.update_idletasks()
        self.root.update()

    def desenhar(self):
        self._limpar_dinamicos()
        self._desenhar_elementos_dinamicos()
        self._atualizar_tela()

    def _desenhar_elementos_dinamicos(self):
        raise NotImplementedError

class GuiRecolecao(GUI):
    def __init__(self, ambiente, simulador=None):
        super().__init__(ambiente, titulo="Ambiente: Recoleção")
        self.simulador = simulador
        self.cores_equipas = {1: "cyan", 2: "#FF1493"}
        self.cores = {
            'Ninho': '#6B4226', 
            'Recurso': '#2ECC71', 
            'Agente': '#3498DB', 
            'AgenteCarga': '#E67E22'
        }
        self._desenhar_elementos_estaticos()

    def _desenhar_elementos_estaticos(self):
        tc = self.tc
        nx, ny = self.amb.pos_ninho
        self.canvas.create_rectangle(nx*tc, ny*tc, (nx+1)*tc, (ny+1)*tc, fill=self.cores['Ninho'], outline="", tags='estatico')
        self.canvas.create_text(nx*tc + tc/2, ny*tc + tc/2, text="N", fill="white", font=("Arial", int(tc/2), "bold"), tags='estatico')

    def _desenhar_elementos_dinamicos(self):
        tc = self.tc
        # desenhar recursos
        for (rx, ry) in self.amb.recursos:
            self.canvas.create_oval(rx*tc+tc*0.2, ry*tc+tc*0.2, (rx+1)*tc-tc*0.2, (ry+1)*tc-tc*0.2, fill=self.cores['Recurso'], outline="", tags='dinamico')

        # desenhar agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            ax, ay = pos
            cor_base = self.cores['AgenteCarga'] if self.amb.agentes_carga.get(agente, False) else self.cores['Agente']
            
            if self.simulador and not self.amb.agentes_carga.get(agente, False):
                equipa = self.simulador._equipas.get(agente)
                cor = self.cores_equipas.get(equipa, cor_base)
            else:
                cor = cor_base
            
            self.canvas.create_oval(ax*tc+2, ay*tc+2, (ax+1)*tc-2, (ay+1)*tc-2, fill=cor, outline="black", width=1, tags='dinamico')

class GuiFarol(GUI):
    def __init__(self, ambiente, simulador=None):
        super().__init__(ambiente, titulo="Ambiente: Farol")
        self.simulador = simulador
        self.cores_equipas = {1: "cyan", 2: "#FF1493"}
        self.cores = {'Farol': '#F1C40F', 'FarolBrilho': '#F39C12', 'Agente': '#9B59B6', 'Obstaculo': '#34495E'}
        self._desenhar_elementos_estaticos()

    def _desenhar_elementos_estaticos(self):
        tc = self.tc
        # farol
        fx, fy = self.amb.pos_farol
        self.canvas.create_oval(fx*tc-tc*0.2, fy*tc-tc*0.2, (fx+1)*tc+tc*0.2, (fy+1)*tc+tc*0.2, fill=self.cores['FarolBrilho'], outline="", tags='estatico')
        self.canvas.create_oval(fx*tc, fy*tc, (fx+1)*tc, (fy+1)*tc, fill=self.cores['Farol'], outline="", tags='estatico')

        # obstaculos
        for (ox, oy) in self.amb.obstaculos:
            self.canvas.create_rectangle(ox*tc, oy*tc, (ox+1)*tc, (oy+1)*tc, fill=self.cores['Obstaculo'], outline="#2C3E50", tags='estatico')

    def _desenhar_elementos_dinamicos(self):
        tc = self.tc
        # agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            ax, ay = pos
            cor_base = self.cores['Agente']
            
            if self.simulador:
                equipa = self.simulador._equipas.get(agente)
                cor = self.cores_equipas.get(equipa, cor_base)
            else:
                cor = cor_base
                
            self.canvas.create_oval(ax*tc+4, ay*tc+4, (ax+1)*tc-4, (ay+1)*tc-4, fill=cor, outline="black", width=1.5, tags='dinamico')
