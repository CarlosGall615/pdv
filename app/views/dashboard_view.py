import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class DashboardView(ctk.CTkFrame): 

    def __init__(self, master, callback_filtro, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(fg_color="transparent")

        # Cabeçalho
        ctk.CTkLabel(self, text="📊 DASHBOARD DE VENDAS", 
                     font=("Arial", 22, "bold"), text_color="#1f538d").pack(pady=20)

        # --- FRAME DE FILTROS ---
        self.frame_filtros = ctk.CTkFrame(self, fg_color="#f0f0f0", corner_radius=10)
        self.frame_filtros.pack(fill="x", padx=20, pady=5)

        for p in ["Dia", "Semana", "Mês"]:
            ctk.CTkButton(self.frame_filtros, text=p, width=100, height=32,
                          fg_color="#1f538d", hover_color="#14375e",
                          command=lambda opt=p: callback_filtro(opt)).pack(side="left", padx=10, pady=10)

        # Container do Gráfico
        self.container_grafico = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        self.container_grafico.pack(fill="both", expand=True, padx=20, pady=20)



    def renderizar_grafico(self, dados, periodo):

        """Usa a lógica de Matplotlib para desenhar no container"""
        # Limpa o gráfico anterior para não acumular memória
        for widget in self.container_grafico.winfo_children():
            widget.destroy()
        plt.close('all') 

        if not dados:
            ctk.CTkLabel(self.container_grafico, text=f"Sem dados para: {periodo}", 
                         text_color="gray", font=("Arial", 14)).pack(pady=100)
            return

        # Processamento de dados (Sua lógica original)
        if periodo == "Dia":
            eixo_x_bruto = [d['hora'][:2] + "h" for d in dados]
        else:
            eixo_x_bruto = [datetime.strptime(d['data'], "%Y-%m-%d").strftime("%d/%m") for d in dados]
        
        contagem = {i: eixo_x_bruto.count(i) for i in sorted(set(eixo_x_bruto))}

        # Criação do Gráfico
        fig, ax = plt.subplots(figsize=(7, 4), dpi=100, facecolor='white')
        ax.set_facecolor('white')

        bars = ax.bar(contagem.keys(), contagem.values(), color="#1f538d", width=0.4, zorder=3)
        ax.bar_label(bars, padding=3, color="black", fontsize=10, weight='bold')

        ax.set_ylabel("Qtd. Vendas", fontsize=10, fontweight='bold')
        ax.grid(axis='y', linestyle='-', alpha=0.1, zorder=0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.container_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)


