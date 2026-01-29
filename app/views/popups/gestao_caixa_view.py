import customtkinter as ctk
from tkinter import messagebox, ttk
from app.views.base_view import BaseView

class GestaoCaixaView(ctk.CTkToplevel, BaseView):

    def __init__(self, master, controller, dados_vendas, resumo):

        super().__init__(master)

        self.controller = controller
        self.title("Gestão de Caixa e Vendas")
        self.geometry("1000x700")
        self.configure(fg_color="#2F5965")
        self.attributes('-topmost', False)
        self.transient(master)
        self.center_window(1000, 700)
        # --- CABEÇALHO (Resumo Rápido) ---
        self.header = ctk.CTkFrame(self, fg_color="#4C727D", border_color="#D4AF37", border_width=2)
        self.header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(self.header, text="RESUMO DO DIA", font=("Arial", 18, "bold"), text_color="#D4AF37").pack(pady=5)
        
        # Grid de valores (Abertura, Entradas, Saídas)
        self.resumo_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.resumo_frame.pack(fill="x", padx=20, pady=10)
        
        # Exemplo de labels que o controller vai atualizar
        self.lbl_abertura = ctk.CTkLabel(self.resumo_frame, font=("Arial", 14, "bold"))
        self.lbl_abertura.grid(row=0, column=0, padx=20)

        self.lbl_vendas = ctk.CTkLabel(self.resumo_frame, font=("Arial", 14, "bold"))
        self.lbl_vendas.grid(row=0, column=1, padx=20)

        self.lbl_saldo = ctk.CTkLabel(self.resumo_frame, font=("Arial", 14, "bold"), text_color="#D4AF37")
        self.lbl_saldo.grid(row=0, column=2, padx=20)

        # --- LISTA DE VENDAS (Onde exclui) ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#4C727D", border_color="#D4AF37", border_width=1)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        ctk.CTkLabel(self.main_frame, text="HISTÓRICO DE VENDAS", font=("Arial", 16, "bold")).pack(pady=10)

        # Usando scrollable frame para listar as vendas
        self.scroll_vendas = ctk.CTkScrollableFrame(self.main_frame, fg_color="#2F5965")
        self.scroll_vendas.pack(expand=True, fill="both", padx=15, pady=10)

        # --- RODAPÉ (Botões de Ação) ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=(0, 20))

        # Botões com a paleta
        self.btn_reforco = ctk.CTkButton(self.footer, text="➕ REFORÇO", fg_color="#2fa572", width=150, height=45, command=lambda: self.controller.lancar_movimentacao("REFORÇO"))
        self.btn_reforco.pack(side="left", padx=10)

        self.btn_sangria = ctk.CTkButton(self.footer, text="➖ SANGRIA", fg_color="#6C3940", width=150, height=45, command=lambda: self.controller.lancar_movimentacao("SANGRIA"))
        self.btn_sangria.pack(side="left", padx=10)

        self.btn_fechar_caixa = ctk.CTkButton(self.footer, text="🔒 FECHAR CAIXA", fg_color="#D4AF37", text_color="black", font=("Arial", 14, "bold"), width=180, height=45, command=self.controller.processar_fechamento)
        self.btn_fechar_caixa.pack(side="right", padx=10)

        self.atualizar_resumo_tela(resumo)
        
        self.atualizar_lista_vendas(dados_vendas)


    
    def atualizar_resumo_tela(self, resumo):
        if not resumo: return

        # O VALOR DE ABERTURA (Missão 1)
        self.lbl_abertura.configure(text=f"Saldo Inicial: R$ {resumo['abertura']:.2f}")
        
        # O TOTAL DE VENDAS (Branco/Cinza)
        self.lbl_vendas.configure(text=f"Entradas: R$ {resumo['faturamento_total']:.2f}")
        
        # O SALDO ATUAL / GAVETA (Label Amarelo)
        self.lbl_saldo.configure(text=f"Saldo Final: R$ {resumo['saldo_atual_dinheiro']:.2f}")



    def atualizar_lista_vendas(self, vendas_e_movimentacoes):
        """Atualiza a lista aplicando cores: Vinho para Sangria, Verde para Reforço e Azul para Vendas"""
        # Limpa o scroll antes de redesenhar
        for widget in self.scroll_vendas.winfo_children():
            widget.destroy()

        for item in vendas_e_movimentacoes:
            # --- NOVA LÓGICA DE DETECÇÃO ---
            # Usamos a 'categoria' que definimos no Model para não haver confusão
            categoria = item.get('categoria', '')

            if categoria == "SANGRIA":
                cor_fundo = "#6C3940"  # Vinho
                icone = "➖ SANGRIA"
                valor_exibir = item.get('valor') or 0.0
                info = f"{icone} | Hora: {item.get('hora', '--:--')} | Valor: R$ {float(valor_exibir):.2f} | Motivo: {item.get('motivo', 'N/A')}"
                exibir_botao_excluir = False 

            elif categoria == "REFORÇO" or categoria == "MOVIMENTAÇÃO":
                cor_fundo = "#2fa572"  # Verde
                icone = "➕ REFORÇO"
                valor_exibir = item.get('valor') or 0.0
                info = f"{icone} | Hora: {item.get('hora', '--:--')} | Valor: R$ {float(valor_exibir):.2f} | Motivo: {item.get('motivo', 'N/A')}"
                exibir_botao_excluir = False

            else: # Aqui entra a VENDA
                cor_fundo = "#4C727D" # Azul padrão
                
                # Se o banco retornar 'valor', usamos ele como 'total'
                total_venda = item.get('total') or item.get('valor') or 0.0
                
                # Pega a forma de pagamento (que no model vira 'tipo')
                metodo = item.get('tipo', 'N/A') 
                
                info = f"🛒 VENDA | Hora: {item.get('hora', '--:--')} | Total: R$ {float(total_venda):.2f} | Pagto: {metodo}"
                exibir_botao_excluir = True

            # --- DESENHO DA LINHA (Igual ao seu) ---
            f = ctk.CTkFrame(self.scroll_vendas, fg_color=cor_fundo)
            f.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(f, text=info, font=("Arial", 13, "bold" if categoria != "VENDA" else "normal"), 
                        text_color="white").pack(side="left", padx=15, pady=10)
            
            if exibir_botao_excluir:
                ctk.CTkButton(f, text="🗑️", width=40, fg_color="#6C3940", 
                            command=lambda v=item: self.controller.solicitar_exclusao_venda(v)).pack(side="right", padx=10)