import customtkinter as ctk

class ComandasView(ctk.CTkFrame):
    def __init__(self, master, controller):
        # Usando o Azul Petróleo Profundo do seu projeto
        super().__init__(master, fg_color="#2F5965") 
        self.controller = controller
        
        # --- PALETA DE CORES IDENTIDADE VISUAL ---
        self.CORES = {
            "fundo_claro": "#4C727D",    # Azul Petróleo Médio
            "fundo_escuro": "#2F5965",   # Azul Petróleo Profundo
            "detalhe": "#D4AF37",        # Dourado Metálico
            "botao_vinho": "#6C3940",    # Vinho Clássico
            "botao_hover": "#552d32",    # Vinho Escuro
            "texto": "#FFFFFF"
        }

        # Status com cores que harmonizam com o dourado/azul
        self.STATUS_CORES = {
            "ABERTO": "#4C727D", "EM PREPARO": "#d97706", "PRONTO": "#059669",
            "AGUARDANDO PAGAMENTO": "#D4AF37", "CANCELADO": "#ef4444", 
            "FINALIZADO": "#1a1a1a"
        }

        self.categorias = {
            "Mesas": "MESAS", "Pedidos Online": "ONLINE",
            "Delivery": "DELIVERY", "Balcão": "BALCÃO", "Balança": "BALANÇA"
        }

        self._setup_ui()

    def _setup_ui(self):
        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=40, pady=(30, 10))

        self.lbl_titulo = ctk.CTkLabel(
            self.header, text="📋 GESTÃO DE COMANDAS", 
            font=("Segoe UI", 32, "bold"), text_color=self.CORES["detalhe"]
        )
        self.lbl_titulo.pack(side="left")

        self.btn_nova = ctk.CTkButton(
            self.header, text="+ NOVA COMANDA", 
            fg_color=self.CORES["botao_vinho"], hover_color=self.CORES["botao_hover"],
            border_color=self.CORES["detalhe"], border_width=1,
            corner_radius=15, height=55, width=220,
            font=("Segoe UI", 16, "bold"),
            command=self.controller.solicitar_nova_comanda
        )
        self.btn_nova.pack(side="right")

        # --- TABVIEW (ESTILO LUXO) ---
        self.tabview = ctk.CTkTabview(
            self, 
            segmented_button_fg_color=self.CORES["fundo_claro"],
            segmented_button_selected_color=self.CORES["detalhe"],
            segmented_button_selected_hover_color="#B8952E",
            segmented_button_unselected_hover_color=self.CORES["fundo_escuro"],
            text_color="#FFFFFF",
            corner_radius=20
        )
        self.tabview.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Aumentando drasticamente a letra das abas
        self.tabview._segmented_button.configure(font=("Segoe UI", 18, "bold"))

        self.scroll_abas = {}
        for nome_aba in self.categorias.keys():
            self.tabview.add(nome_aba)
            scroll = ctk.CTkScrollableFrame(
                self.tabview.tab(nome_aba), 
                fg_color="transparent"
            )
            scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            for i in range(4):
                scroll.grid_columnconfigure(i, weight=1, uniform="col")
            self.scroll_abas[nome_aba] = scroll

    def renderizar_comandas(self, comandas_dict):
        """Limpa e redesenha os cards"""
        # 1. Limpa os widgets
        for scroll in self.scroll_abas.values():
            for widget in scroll.winfo_children():
                widget.destroy()
        
        # FORÇA o sistema a processar a destruição dos botões antes de continuar
        self.update_idletasks()

        # Se não houver nada para mostrar, para aqui (a tela já está limpa)
        if not comandas_dict: 
            return

        posicoes = {nome: 0 for nome in self.categorias.keys()}

        for id_comanda, dados in comandas_dict.items():
            # FILTRO DE SEGURANÇA: Só desenha se NÃO for cancelado
            status = str(dados.get("status", "")).upper()
            if status == "CANCELADO" or status == "FINALIZADO":
                continue
                
            cat_db = str(dados.get("categoria", "BALCÃO")).upper()
            nome_aba_alvo = next((k for k, v in self.categorias.items() if v == cat_db), "Balcão")
            
            idx = posicoes[nome_aba_alvo]
            self._criar_card(self.scroll_abas[nome_aba_alvo], id_comanda, dados, idx // 4, idx % 4)
            posicoes[nome_aba_alvo] += 1

    def _criar_card(self, parent_scroll, id_comanda, dados, linha, coluna):
        status = str(dados.get("status", "ABERTO")).upper()
        cor_status = self.STATUS_CORES.get(status, "#5a5a5a")
        
        # Card com borda dourada inspirada no seu Login
        card = ctk.CTkFrame(
            parent_scroll, 
            fg_color=self.CORES["fundo_claro"], 
            border_width=2, 
            border_color=self.CORES["detalhe"],
            corner_radius=25, height=240 
        )
        card.grid(row=linha, column=coluna, padx=15, pady=15, sticky="nsew")
        card.pack_propagate(False)

        # Badge de Status (Pequeno e Elegante)
        status_container = ctk.CTkFrame(card, fg_color=cor_status, corner_radius=10)
        status_container.pack(pady=(15, 0), padx=20)
        ctk.CTkLabel(status_container, text=status, font=("Segoe UI", 10, "bold"), text_color="white").pack(padx=10, pady=2)

        # ID Comanda
        lbl_id = ctk.CTkLabel(
            card, text=f"ID #{id_comanda}", 
            font=("Segoe UI", 20, "bold"), text_color="white"
        )
        lbl_id.pack(pady=(10, 0))

        # VALOR PRINCIPAL
        total_val = dados.get('total', 0)
        lbl_total = ctk.CTkLabel(
            card, text=f"R$ {total_val:,.2f}", 
            font=("Segoe UI", 38, "bold"), 
            text_color=self.CORES["detalhe"] # Valor em Dourado para destacar
        )
        lbl_total.pack(expand=True)

        # Rodapé com o tempo
        tempo = dados.get("tempo_abertura", "00:00")
        lbl_tempo = ctk.CTkLabel(
            card, text=f"🕒 ABERTA HÁ {tempo}", 
            font=("Segoe UI", 12, "bold"), text_color="#cbd5e1"
        )
        lbl_tempo.pack(side="bottom", pady=(0, 20))

        # --- EFEITOS E INTERAÇÃO ---
        def abrir_comanda(e=None): self.controller.gerenciar_comanda(id_comanda)
        
        # Efeito hover: Brilho na borda e mudança sutil de fundo
        def on_enter(e): 
            card.configure(border_width=4, fg_color="#567f8b")
        def on_leave(e): 
            card.configure(border_width=2, fg_color=self.CORES["fundo_claro"])

        # Aplicar eventos
        for el in [card, lbl_id, lbl_total, lbl_tempo]:
            el.bind("<Button-1>", abrir_comanda)
            el.bind("<Enter>", on_enter)
            el.bind("<Leave>", on_leave)
            el.configure(cursor="hand2")