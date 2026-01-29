import customtkinter as ctk

class ComandasView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master, fg_color="transparent")
        self.controller = controller

        # --- CABEÇALHO ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(10, 20))

        self.lbl_titulo = ctk.CTkLabel(self.header, text="📋 COMANDAS ATIVAS", 
                                       font=("Arial", 24, "bold"))
        self.lbl_titulo.pack(side="left")

        self.btn_nova = ctk.CTkButton(self.header, text="+ NOVA COMANDA", 
                                      fg_color="#2fa572", hover_color="#248259",
                                      width=150, height=40, font=("Arial", 13, "bold"),
                                      command=self.controller.solicitar_nova_comanda)
        self.btn_nova.pack(side="right")

        # --- ÁREA DE SCROLL (ONDE FICAM OS CARDS) ---
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True, padx=10)
        
        # Configuramos o grid para ter 4 colunas fixas com peso igual
        self.scroll_area.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="col")

    def renderizar_comandas(self, comandas_dict):
        """
        Limpa a tela e desenha os cards baseados no dicionário de comandas
        comandas_dict = {"01": {"total": 10.50, "status": "aberta"}, ...}
        """
        # Limpar widgets antigos
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        colunas = 4
        for i, (id_comanda, dados) in enumerate(comandas_dict.items()):
            linha = i // colunas
            coluna = i % colunas
            self._criar_card(id_comanda, dados, linha, coluna)

    def _criar_card(self, id_comanda, dados, linha, coluna):
        """Cria o card individual compacto"""
        cor_status = "#2b2b2b"
        if dados.get("status") == "conta":
            cor_status = "#a67c00"

        card = ctk.CTkFrame(self.scroll_area, fg_color=cor_status, 
                            border_width=2, border_color="#3d3d3d", height=150)
        
        # Função de clique unificada
        def abrir_comanda(event=None):
            self.controller.gerenciar_comanda(id_comanda)

        # Bind no Frame principal
        card.bind("<Button-1>", abrir_comanda)
        card.grid(row=linha, column=coluna, padx=15, pady=15, sticky="nsew")
        
        # ID da Comanda
        lbl_id = ctk.CTkLabel(card, text=f"COMANDA {id_comanda}", 
                              font=("Arial", 16, "bold"))
        lbl_id.pack(pady=(15, 5))
        lbl_id.bind("<Button-1>", abrir_comanda) # BIND AQUI TAMBÉM

        # Valor Total
        lbl_total = ctk.CTkLabel(card, text=f"R$ {dados['total']:.2f}", 
                                 font=("Arial", 22, "bold"), text_color="#2fa572")
        lbl_total.pack(pady=5)
        lbl_total.bind("<Button-1>", abrir_comanda) # BIND AQUI TAMBÉM
        
        # Status
        status_texto = "● ABERTA" if dados.get("status") == "aberta" else "● AGUARDANDO PGTO"
        lbl_status = ctk.CTkLabel(card, text=status_texto, font=("Arial", 10))
        lbl_status.pack(side="bottom", pady=10)
        lbl_status.bind("<Button-1>", abrir_comanda) # BIND AQUI TAMBÉM