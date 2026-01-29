import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class HomeView(ctk.CTk):
    def __init__(self, usuario_nome):
        super().__init__()

        self.title("Sistema de Balança Pro")
        self.geometry("1000x700") # Aumentei um pouco para caber tudo bem

        # Configuração de Grid para layout responsivo
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar (Barra Lateral Unificada) ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Faz os itens dentro da sidebar respeitarem o espaço
        self.sidebar.grid_rowconfigure(4, weight=1) # Empurra o botão sair e status para baixo

        self.label_user = ctk.CTkLabel(self.sidebar, text=f"Usuário:\n{usuario_nome}", font=("Arial", 14, "bold"))
        self.label_user.pack(pady=20, padx=10)

        self.btn_historico = ctk.CTkButton(self.sidebar, text="Histórico")
        self.btn_historico.pack(pady=10, padx=10)

        self.btn_config = ctk.CTkButton(self.sidebar, text="Configurações", fg_color="gray")
        self.btn_config.pack(pady=10, padx=10)

        # Logs de Pesagens
        self.log_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.log_frame.pack(fill="x", padx=10, pady=20)

        self.label_log = ctk.CTkLabel(self.log_frame, text="PESAGENS DO DIA", font=("Arial", 12, "bold"))
        self.label_log.pack()

        self.lista_logs = ctk.CTkTextbox(self.log_frame, width=180, height=150, font=("Consolas", 11))
        self.lista_logs.pack(pady=5)
        self.lista_logs.configure(state="disabled")

        # CHAMADA DOS INDICADORES (Agora dentro da sidebar correta)
        self.criar_indicadores_status()

        self.btn_sair = ctk.CTkButton(self.sidebar, text="Sair", fg_color="transparent",
                                    border_width=2, text_color="red",
                                    command=self.confirmar_saida)
        self.btn_sair.pack(side="bottom", pady=20, padx=10)

        # --- Área Central ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.label_titulo = ctk.CTkLabel(self.main_frame, text="PAINEL DE PESAGEM", font=("Arial", 20, "bold"))
        self.label_titulo.pack(pady=10)

        self.frame_comandas = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_comandas.pack(fill="both", expand=True, padx=10, pady=10)

        self.btn_pesar = ctk.CTkButton(self.main_frame, text="INICIAR BALANÇA", font=("Arial", 18, "bold"), height=50)
        self.btn_pesar.pack(pady=20)

    def confirmar_saida(self):
        from tkinter import messagebox
        
        # Abre a caixa de diálogo padrão do sistema
        if messagebox.askyesno("Confirmar Saída", "Deseja realmente encerrar o sistema?", parent=self):
        
            if hasattr(self, 'controller'):
                    self.controller.encerrar_sistema()
            else:
                    # Se não tiver a referência direta, apenas destrua
                self.destroy()
                import os
                os._exit(0)
        
    def criar_indicadores_status(self):
        # Agora usamos self.sidebar como mestre (parent)
        self.frame_status = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_status.pack(side="bottom", pady=(0, 10), padx=10, fill="x")

        self.lbl_balanca_status = ctk.CTkLabel(
            self.frame_status, text="● BALANÇA", 
            text_color="#ff4444", 
            font=("Arial", 11, "bold")
        )
        self.lbl_balanca_status.pack(anchor="w", padx=10)

        self.lbl_impressora_status = ctk.CTkLabel(
            self.frame_status, text="● IMPRESSORA", 
            text_color="#ff4444", 
            font=("Arial", 11, "bold")
        )
        self.lbl_impressora_status.pack(anchor="w", padx=10, pady=(5, 0))

    def atualizar_cor_status(self, hardware, online):
        """Muda a cor do indicador: True = Verde, False = Vermelho"""
        if online:
            cor =  "#44ff44"
            icone = "✅"
        else:
            cor = "#ff4444"
            icone = "❌"

        # Tentamos atualizar a cor, mas usamos um try/except para evitar erros 
        # caso a janela seja fechada enquanto o loop ainda roda
        try:
            if hardware == "balanca":
                self.lbl_balanca_status.configure(text=f"{icone} BALANÇA", text_color=cor)
            elif hardware == "impressora":
                self.lbl_impressora_status.configure(text=f"{icone} IMPRESSORA", text_color=cor)
        except Exception as e:
            print(f"Erro ao atualizar status visual: {e}") 

    def abrir_janela_config(self, portas, config_atual, callback_salvar):
            janela = ctk.CTkToplevel(self)
            janela.title("Configurações de Hardware")
            janela.geometry("400x300")
            janela.attributes("-topmost", True) # Fica na frente

            ctk.CTkLabel(janela, text="Porta da Balança:").pack(pady=5)
            combo_balanca = ctk.CTkOptionMenu(janela, values=portas)
            combo_balanca.set(config_atual['porta_balanca'])
            combo_balanca.pack()

            ctk.CTkLabel(janela, text="Porta da Impressora:").pack(pady=5)
            combo_impressora = ctk.CTkOptionMenu(janela, values=portas)
            combo_impressora.set(config_atual['porta_impressora'])
            combo_impressora.pack()

            def salvar():
                novas_configs = {
                    "porta_balanca": combo_balanca.get(),
                    "porta_impressora": combo_impressora.get(),
                    "baudrate": 9600
                }
                callback_salvar(novas_configs)
                janela.destroy()

            ctk.CTkButton(janela, text="Salvar", command=salvar).pack(pady=20)

    def abrir_dashboard_vazia(self, callback_filtro):
        janela = ctk.CTkToplevel(self)
        janela.title("Dashboard de Produtividade")
        janela.geometry("850x650")
        janela.configure(fg_color="white") # Fundo da janela branco
        janela.attributes("-topmost", True)

        # Cabeçalho com cor de destaque
        ctk.CTkLabel(janela, text="RELATÓRIO DE VENDAS", 
                     font=("Arial", 22, "bold"), text_color="#1f538d").pack(pady=(20,10))

        # Frame de Filtros
        frame_filtros = ctk.CTkFrame(janela, fg_color="#f0f0f0") # Cinza bem clarinho
        frame_filtros.pack(fill="x", padx=20, pady=5)

        for p in ["Dia", "Semana", "Mês"]:
            ctk.CTkButton(frame_filtros, text=p, width=100, height=32,
                          fg_color="#1f538d", hover_color="#14375e",
                          command=lambda opt=p: callback_filtro(opt)).pack(side="left", padx=10, pady=5)

        # Container do Gráfico
        janela.container_grafico = ctk.CTkFrame(janela, fg_color="white")
        janela.container_grafico.pack(fill="both", expand=True, padx=20, pady=20)
        
        return janela

    def atualizar_grafico_dashboard(self, janela, dados, periodo):
        for widget in janela.container_grafico.winfo_children():
            widget.destroy()
        plt.close('all') 

        if not dados:
            ctk.CTkLabel(janela.container_grafico, text="Nenhum dado para o período.", text_color="black").pack(pady=100)
            return

        # Processamento de dados
        if periodo == "Dia":
            eixo_x_bruto = [d['hora'][:2] + "h" for d in dados]
        else:
            eixo_x_bruto = [datetime.strptime(d['data'], "%Y-%m-%d").strftime("%d/%m") for d in dados]
        
        contagem = {i: eixo_x_bruto.count(i) for i in sorted(set(eixo_x_bruto))}

        # --- GRÁFICO CLEAN (BRANCO) ---
        plt.style.use('default') # Volta para o padrão claro
        fig, ax = plt.subplots(figsize=(8, 5), dpi=100, facecolor='white')
        ax.set_facecolor('white')

        # Barras em azul profissional
        bars = ax.bar(contagem.keys(), contagem.values(), color="#1f538d", 
                      width=0.4, label="Qtd. Pratos", zorder=3)

        # Ajuste de cores para fundo branco
        ax.set_xlabel("PERÍODO", fontsize=10, fontweight='bold', color="#333333")
        ax.set_ylabel("QUANTIDADE DE PESAGENS", fontsize=10, fontweight='bold', color="#333333")
        
        ax.tick_params(axis='both', colors='#333333', labelsize=9)
        if len(contagem) > 10: plt.xticks(rotation=45)

        # Legenda e Grade
        ax.legend(loc="upper right")
        ax.grid(axis='y', linestyle='-', alpha=0.1, zorder=0)
        
        # Números acima das barras (em preto para ler melhor)
        ax.bar_label(bars, padding=3, color="black", fontsize=10, weight='bold')

        # Remover bordas superiores e direitas para ficar moderno
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=janela.container_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        

    