import customtkinter as ctk

class PdvView(ctk.CTkFrame):

    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.configure(fg_color="transparent")
        
        # Atributos atualizados
        self.lista_carrinho_ui = None
        self.lbl_total = None
        self.btn_pagar = None
        self.ent_busca_pdv = None
        self.tab_categorias = None
        
        # Novos atributos para identificação de cliente
        self.lbl_cliente_nome = None
        self.ent_busca_cliente = None

    def desenhar_estrutura_pdv(self, callback_busca, callback_pagar):
        """Monta o esqueleto do PDV com identificação de cliente"""
        for widget in self.winfo_children():
            widget.destroy()
        
        # --- BARRA SUPERIOR DE IDENTIFICAÇÃO DO CLIENTE ---
        frame_top_cliente = ctk.CTkFrame(self, height=50, fg_color="#242424", border_width=1)
        frame_top_cliente.pack(fill="x", padx=10, pady=(10, 0))
        
        # Status do Cliente
        self.lbl_cliente_nome = ctk.CTkLabel(
            frame_top_cliente, 
            text="👤 CLIENTE: CONSUMIDOR FINAL", 
            font=("Arial", 14, "bold"),
            text_color="#AAAAAA"
        )
        self.lbl_cliente_nome.pack(side="left", padx=20)

        # Campo de busca de cliente
        self.ent_busca_cliente = ctk.CTkEntry(
            frame_top_cliente, 
            placeholder_text="Identificar Cliente (CPF ou Nome)...",
            width=250,
            height=30,
            border_color="#555555"
        )
        self.ent_busca_cliente.pack(side="right", padx=10, pady=10)
        
        # Evento para o controller buscar o cliente (usando 'identificar_cliente_venda' no controller)
        self.ent_busca_cliente.bind("<Return>", lambda e: self.controller.identificar_cliente_venda(self.ent_busca_cliente.get()))

        # --- ÁREA PRINCIPAL ---
        pdv_frame = ctk.CTkFrame(self, fg_color="transparent")
        pdv_frame.pack(fill="both", expand=True)
        
        pdv_frame.grid_columnconfigure(0, weight=6, uniform="col") 
        pdv_frame.grid_columnconfigure(1, weight=4, uniform="col")
        pdv_frame.grid_rowconfigure(0, weight=1)

        # --- ESQUERDA: CARRINHO ---
        frame_esquerda = ctk.CTkFrame(pdv_frame, border_width=2)
        frame_esquerda.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
        
        ctk.CTkLabel(frame_esquerda, text="🛒 VENDA ATUAL", font=("Arial", 20, "bold")).pack(pady=10)
        
        self.lista_carrinho_ui = ctk.CTkScrollableFrame(frame_esquerda, fg_color="#1a1a1a")
        self.lista_carrinho_ui.pack(fill="both", expand=True, padx=10, pady=5)
        
        rodape = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        rodape.pack(fill="x", pady=20, padx=20)
        
        self.lbl_total = ctk.CTkLabel(rodape, text="TOTAL: R$ 0,00", font=("Arial", 28, "bold"), text_color="#2fa572")
        self.lbl_total.pack(side="left")
        
        self.btn_pagar = ctk.CTkButton(rodape, text="PAGAR (F12)", fg_color="#2fa572", 
                                        command=callback_pagar, height=50, font=("Arial", 16, "bold"))
        self.btn_pagar.pack(side="right")

        # --- DIREITA: PESQUISA PRODUTOS E CATEGORIAS ---
        frame_direita = ctk.CTkFrame(pdv_frame, fg_color="transparent")
        frame_direita.grid(row=0, column=1, sticky="nsew", pady=10, padx=(0, 10))

        # Campo de Pesquisa de Produtos
        self.ent_busca_pdv = ctk.CTkEntry(frame_direita, placeholder_text="Código de Barras / Nome / Nº Comanda...", height=45, border_color="#D4AF37")
        self.ent_busca_pdv.pack(fill="x", pady=(0, 10))
               
        # AQUI ESTÁ A CHAVE:
        # O callback precisa passar o texto digitado para o controller
        def ao_pressionar_enter(event):
            codigo = self.ent_busca_pdv.get()
            # Chama a nova função inteligente
            self.controller.processar_busca_pdv(codigo)

        self.ent_busca_pdv.bind("<Return>", ao_pressionar_enter)
        self.ent_busca_pdv.focus()

        self.tab_categorias = ctk.CTkTabview(frame_direita)
        self.tab_categorias.pack(fill="both", expand=True)
        
        return self.tab_categorias


    
    @staticmethod
    def criar_linha_carrinho(item, cb_mais, cb_menos, cb_remover, cb_manual, cb_obs, container_pai):
        # Aumentado para 80 para acomodar a descrição embaixo
        linha = ctk.CTkFrame(container_pai, fg_color="#242424", height=80)
        linha.pack(fill="x", pady=3, padx=5)
        linha.pack_propagate(False) 
        
        # Container para Nome e Observação (Empilhados)
        frame_identificacao = ctk.CTkFrame(linha, fg_color="transparent")
        frame_identificacao.pack(side="left", padx=15, fill="y")

        # Nome do Produto
        lbl_nome = ctk.CTkLabel(frame_identificacao, text=item['nome'].upper(), font=("Arial", 12, "bold"))
        lbl_nome.pack(side="top", anchor="w", pady=(10, 0))

        # Descrição/Observação (Texto menor embaixo)
        obs_texto = item.get('observacao', '')
        if obs_texto:
            lbl_obs = ctk.CTkLabel(frame_identificacao, text=obs_texto, font=("Arial", 10, "italic"), text_color="#aaaaaa")
            lbl_obs.pack(side="top", anchor="w")

        # --- BOTÕES DE AÇÃO (Lado Direito) ---
        ctk.CTkButton(linha, text="🗑️", width=30, height=30, fg_color="transparent", 
                    text_color="#ff4d4d", command=cb_remover).pack(side="right", padx=15)

        if cb_obs:
            ctk.CTkButton(linha, text="✏️", width=30, height=30, fg_color="transparent", 
                        text_color="#D4AF37", command=cb_obs).pack(side="right", padx=5)

        # Preço Total da Linha
        total_exibir = item.get('total', item['qtd'] * item['preco_unit'])
        ctk.CTkLabel(linha, text=f"R$ {total_exibir:.2f}", font=("Arial", 13, "bold"), 
                    text_color="#5cb8ff", width=80).pack(side="right", padx=10)

        # Container Quantidade
        frame_qtd = ctk.CTkFrame(linha, fg_color="transparent")
        frame_qtd.pack(side="right", padx=10)

        # Botão menos
        ctk.CTkButton(frame_qtd, text="-", width=30, height=30, fg_color="#2B2B2B", 
                    command=cb_menos).pack(side="left", padx=2)

        # Lógica de Quantidade
        qtd_valor = item.get('qtd', 0)
        is_peso = item.get('is_balanca') or item.get('unidade') == 'kg'
        texto_qtd = f"{qtd_valor:.3f}" if is_peso or (qtd_valor % 1 != 0) else f"{int(qtd_valor)}"
        
        ent_qtd = ctk.CTkEntry(frame_qtd, width=75, height=28, justify="center", font=("Arial", 13, "bold"))
        ent_qtd.insert(0, texto_qtd)
        ent_qtd.pack(side="left", padx=5)

        def disparar_update(event=None):
            cb_manual(ent_qtd.get())

        ent_qtd.bind("<Return>", disparar_update)
        ent_qtd.bind("<FocusOut>", disparar_update)
        ent_qtd.bind("<Button-1>", lambda e: ent_qtd.select_range(0, 'end'))

        # Botão mais
        ctk.CTkButton(frame_qtd, text="+", width=30, height=30, fg_color="#2B2B2B", 
                    command=cb_mais).pack(side="left", padx=2)



    def desenhar_espera_pdv(self, usuario, status_caixa, callback_iniciar, callback_abrir_caixa):
        """Tela de bloqueio quando o caixa está fechado ou em espera"""
        for widget in self.winfo_children():
            widget.destroy()

        card_espera = ctk.CTkFrame(self, fg_color="#6C3940", border_color="#D4AF37",
                                   border_width=3, corner_radius=30, width=500, height=550)
        card_espera.place(relx=0.5, rely=0.5, anchor="center")
        card_espera.pack_propagate(False)

        ctk.CTkLabel(card_espera, text="👤", font=("Arial", 60)).pack(pady=(40, 5))
        ctk.CTkLabel(card_espera, text=f"OPERADOR: {usuario.upper()}", 
                     font=("Segoe UI", 16, "bold"), text_color="#D4AF37").pack(pady=5)
        
        ctk.CTkFrame(card_espera, fg_color="#D4AF37", height=2, width=300).pack(pady=20)

        esta_aberto = (status_caixa == "ABERTO")
        cor_status = "#D4AF37" if esta_aberto else "#BDC3C7"
        
        ctk.CTkLabel(card_espera, text=f"📦 CAIXA {status_caixa}", 
                     font=("Segoe UI", 32, "bold"), text_color=cor_status).pack(pady=10)

        if esta_aberto:
            ctk.CTkButton(card_espera, text="➕ INICIAR NOVO CUPOM", font=("Segoe UI", 18, "bold"),
                          fg_color="#2F5965", hover_color="#1f424b", height=70, width=350,
                          corner_radius=15, command=callback_iniciar).pack(pady=40)
        else:
            ctk.CTkLabel(card_espera, text="O sistema está bloqueado para vendas.", 
                         font=("Segoe UI", 13), text_color="#BDC3C7").pack(pady=(10, 0))
            
            ctk.CTkButton(card_espera, text="🔑 ABRIR CAIXA AGORA", font=("Segoe UI", 18, "bold"),
                          fg_color="#2F5965", hover_color="#1f424b", border_color="#D4AF37",
                          border_width=2, height=70, width=350, corner_radius=15,
                          command=callback_abrir_caixa).pack(pady=40)



    def renderizar_grade_produtos(self, tabview, lista_produtos, callback_clique):
        """Constrói os botões de atalho por categoria"""
        posicoes = {}
        for p in lista_produtos:
            cat = p.get('categoria') or p.get('cat') or "Geral"
            if cat not in posicoes:
                try: tabview.add(cat)
                except: pass
                aba = tabview.tab(cat)
                aba.grid_columnconfigure((0, 1, 2), weight=1, uniform="aba_col")
                posicoes[cat] = {"linha": 0, "coluna": 0}

            aba = tabview.tab(cat)
            cor_botao = p.get('cor', "#1f538d") 

            btn = ctk.CTkButton(aba, text=f"{p['nome']}\nR$ {p.get('preco', 0):.2f}",
                                fg_color=cor_botao, height=80, font=("Arial", 11, "bold"),
                                command=lambda prod=p: callback_clique(
                                                        nome=prod['nome'], 
                                                        qtd=1.0, 
                                                        preco_unit=prod['preco'],
                                                        produto_id=prod.get('id'),
                                                        is_balanca=bool(prod.get('codigo_balanca'))
                                                    )
                                                )
            
            lin, col = posicoes[cat]["linha"], posicoes[cat]["coluna"]
            btn.grid(row=lin, column=col, padx=5, pady=5, sticky="new")

            col += 1
            if col > 2: col = 0; lin += 1
            posicoes[cat]["linha"], posicoes[cat]["coluna"] = lin, col

            