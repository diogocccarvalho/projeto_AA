import tkinter as tk

class GUI:
    def __init__(self, ambiente, simulador=None, titulo="Simulador SMA", tamanho_celula=30):
        self.amb = ambiente
        self.simulador = simulador
        self.tc = tamanho_celula
        self.largura = ambiente.largura
        self.altura = ambiente.altura
        self.is_destroyed = False
        
        self.root = tk.Tk()
        self.root.title(titulo)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Limitar o tamanho da janela e adicionar scrollbars
        max_w = self.root.winfo_screenwidth() - 100
        max_h = self.root.winfo_screenheight() - 150
        canvas_w = self.largura * self.tc
        canvas_h = self.altura * self.tc

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            frame,
            width=min(canvas_w, max_w),
            height=min(canvas_h, max_h),
            bg="#F0F0F0",
            scrollregion=(0, 0, canvas_w, canvas_h)
        )

        hbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._desenhar_grid()

    def on_close(self):
        self.is_destroyed = True
        self.root.destroy()

    def _desenhar_grid(self):
        # A grid é desenhada uma única vez e nunca é apagada
        for i in range(self.largura + 1):
            x = i * self.tc
            self.canvas.create_line(x, 0, x, self.altura * self.tc, fill="#D0D0D0", tags='grid')
        for i in range(self.altura + 1):
            y = i * self.tc
            self.canvas.create_line(0, y, self.largura * self.tc, y, fill="#D0D0D0", tags='grid')

    def _limpar_dinamicos(self):
        if self.is_destroyed: return
        self.canvas.delete('dinamico')

    def _limpar_estaticos(self):
        if self.is_destroyed: return
        self.canvas.delete('estatico')

    def _atualizar_tela(self):
        if self.is_destroyed: return
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass

    def desenhar(self):
        if self.is_destroyed: return
        
        # OTIMIZAÇÃO: Só redesenha os estáticos (obstáculos) no início do episódio
        # Se o passo atual for <= 1, assumimos que é um reset ou início
        if self.simulador and self.simulador._passo_atual <= 1:
            self._limpar_estaticos()
            self._desenhar_elementos_estaticos()
            
        self._limpar_dinamicos()
        self._desenhar_elementos_dinamicos()
        self._desenhar_caminho_otimo()
        self._atualizar_tela()

    def _desenhar_caminho_otimo(self):
        if not hasattr(self.amb, 'caminhos_otimos_visual'):
            return
        
        tc = self.tc
        for caminho in self.amb.caminhos_otimos_visual.values():
            if not caminho:
                continue

            for (x, y) in caminho:
                # Desenhar um pequeno círculo no centro da célula
                self.canvas.create_oval(
                    x * tc + tc * 0.35, y * tc + tc * 0.35,
                    x * tc + tc * 0.65, y * tc + tc * 0.65,
                    fill="#FFD700",  # Amarelo Dourado
                    outline="",
                    tags='dinamico'
                )

    def _desenhar_elementos_estaticos(self):
        raise NotImplementedError

    def _desenhar_elementos_dinamicos(self):
        raise NotImplementedError

class GuiRecolecao(GUI):
    def __init__(self, ambiente, simulador=None):
        super().__init__(ambiente, simulador, titulo="Ambiente: Recoleção")
        self.cores_equipas = {1: "cyan", 2: "#FF1493"}
        self.cores = {
            'Ninho': '#6B4226', 
            'Recurso': '#2ECC71', 
            'Agente': '#3498DB', 
            'AgenteCarga': '#E67E22',
            'Obstaculo': '#34495E'
        }

    def _desenhar_elementos_estaticos(self):
        # Objetos que não se mexem DURANTE o episódio
        tc = self.tc
        
        # Desenhar Ninho
        if self.amb.pos_ninho:
            nx, ny = self.amb.pos_ninho
            self.canvas.create_rectangle(nx*tc, ny*tc, (nx+1)*tc, (ny+1)*tc, 
                                       fill=self.cores['Ninho'], outline="", tags='estatico')
            self.canvas.create_text(nx*tc + tc/2, ny*tc + tc/2, text="N", 
                                  fill="white", font=("Arial", int(tc/2), "bold"), tags='estatico')

        # Desenhar Obstáculos
        for (ox, oy) in self.amb.obstaculos:
            self.canvas.create_rectangle(ox*tc, oy*tc, (ox+1)*tc, (oy+1)*tc, 
                                       fill=self.cores['Obstaculo'], outline="#2C3E50", tags='estatico')

    def _desenhar_elementos_dinamicos(self):
        tc = self.tc
        
        # Desenhar recursos (são dinâmicos porque desaparecem quando apanhados)
        for (rx, ry) in self.amb.recursos:
            self.canvas.create_oval(rx*tc+tc*0.2, ry*tc+tc*0.2, (rx+1)*tc-tc*0.2, (ry+1)*tc-tc*0.2, 
                                  fill=self.cores['Recurso'], outline="", tags='dinamico')

        # Desenhar agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            if pos:
                ax, ay = pos
                cor_base = self.cores['AgenteCarga'] if self.amb.agentes_carga.get(agente, False) else self.cores['Agente']
                
                if self.simulador and not self.amb.agentes_carga.get(agente, False):
                    equipa = self.simulador._equipas.get(agente)
                    cor = self.cores_equipas.get(equipa, cor_base)
                else:
                    cor = cor_base
                
                self.canvas.create_oval(ax*tc+2, ay*tc+2, (ax+1)*tc-2, (ay+1)*tc-2, 
                                      fill=cor, outline="black", width=1, tags='dinamico')

class GuiFarol(GUI):
    def __init__(self, ambiente, simulador=None):
        tamanho_celula = 15 if ambiente.largura > 30 else 30
        super().__init__(ambiente, simulador, titulo="Ambiente: Farol", tamanho_celula=tamanho_celula)
        self.cores_equipas = {1: "cyan", 2: "#FF1493"}
        self.cores = {'Farol': '#F1C40F', 'FarolBrilho': '#F39C12', 'Agente': '#9B59B6', 'Obstaculo': '#34495E'}

    def _desenhar_elementos_estaticos(self):
        # Objetos que não se mexem DURANTE o episódio
        tc = self.tc
        
        # Farol (Fixo durante o episódio)
        if self.amb.pos_farol:
            fx, fy = self.amb.pos_farol
            self.canvas.create_oval(fx*tc-tc*0.2, fy*tc-tc*0.2, (fx+1)*tc+tc*0.2, (fy+1)*tc+tc*0.2, 
                                  fill=self.cores['FarolBrilho'], outline="", tags='estatico')
            self.canvas.create_oval(fx*tc, fy*tc, (fx+1)*tc, (fy+1)*tc, 
                                  fill=self.cores['Farol'], outline="", tags='estatico')

        # Obstaculos
        for (ox, oy) in self.amb.obstaculos:
            self.canvas.create_rectangle(ox*tc, oy*tc, (ox+1)*tc, (oy+1)*tc, 
                                       fill=self.cores['Obstaculo'], outline="#2C3E50", tags='estatico')

    def _desenhar_elementos_dinamicos(self):
        tc = self.tc
        # Agentes
        for agente, pos in self.amb._posicoes_agentes.items():
            if pos:
                ax, ay = pos
                cor_base = self.cores['Agente']
                
                if self.simulador:
                    equipa = self.simulador._equipas.get(agente)
                    cor = self.cores_equipas.get(equipa, cor_base)
                else:
                    cor = cor_base
                    
                self.canvas.create_oval(ax*tc+4, ay*tc+4, (ax+1)*tc-4, (ay+1)*tc-4, 
                                      fill=cor, outline="black", width=1.5, tags='dinamico')