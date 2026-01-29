import customtkinter as ctk
from tkinter import messagebox

class ComandaModalView(ctk.CTkToplevel):
    def __init__(self, master, id_comanda, dados, controller):
        super().__init__(master)
        
        self.controller = controller
        self.id_comanda = id_comanda
        self.dados = dados 
        self.cancelando = False 
        
        # Garante que a lista de itens exista
        if 'itens' not in self.dados or self.dados['itens'] is None:
            self.dados['itens'] = []

        # Configurações da Janela
        self.title(f"Gerenciar Comanda: {id_comanda}")
        self.geometry("1100x750") 
        self.grab_set()
        
        self.grid_columnconfigure(0, weight=1, minsize=460) 
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ===================================================
        # LADO ESQUERDO: CARRINHO E CONTROLES
        # ===================================================
        self.frame_esquerda = ctk.CTkFrame(self, border_width=2)
        self.frame_esquerda.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Cabeçalho ID
        self.lbl_id = ctk.CTkLabel(self.frame_esquerda, text=f"CONTA: {id_comanda}", 
                                   font=("Arial", 22, "bold"))
        self.lbl_id.pack(pady=(10, 5))

        # --- SELETORES (Status e Categoria) ---
        self.frame_controles = ctk.CTkFrame(self.frame_esquerda, fg_color="transparent")
        self.frame_controles.pack(fill="x", padx=10, pady=5)

        # Dropdown Categoria
        self.lista_categorias = ["MESAS", "ONLINE", "DELIVERY", "BALCÃO", "BALANÇA"]
        ctk.CTkLabel(self.frame_controles, text="Setor:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky="w")
        self.menu_categoria = ctk.CTkOptionMenu(self.frame_controles, values=self.lista_categorias,
                                                fg_color="#2b2b2b", button_color="#3d3d3d")
        self.menu_categoria.set(self.dados.get('categoria', 'BALCÃO'))
        self.menu_categoria.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="ew")

        # Dropdown Status
        self.lista_status = [
            "ABERTO", "AGUARDANDO PEDIDO", "EM PREPARO", "PRONTO", 
            "ENTREGUE NA MESA", "AGUARDANDO PAGAMENTO", "SAIU PARA ENTREGA", "CANCELADO"
        ]
        ctk.CTkLabel(self.frame_controles, text="Status Atual:", font=("Arial", 12)).grid(row=0, column=1, padx=5, sticky="w")
        self.menu_status = ctk.CTkOptionMenu(self.frame_controles, values=self.lista_status,
                                             fg_color="#1f538d", button_color="#163e66",
                                             command=self._ao_mudar_status) 
        self.menu_status.set(self.dados.get('status', 'ABERTO'))
        self.menu_status.grid(row=1, column=1, padx=5, pady=(0, 10), sticky="ew")
        
        self.frame_controles.grid_columnconfigure((0, 1), weight=1)

        # --- LISTA DE ITENS (SCROLL) ---
        self.scroll_itens = ctk.CTkScrollableFrame(self.frame_esquerda, fg_color="#1a1a1a")
        self.scroll_itens.pack(fill="both", expand=True, padx=10, pady=5)

        # --- TOTAL ---
        self.lbl_total = ctk.CTkLabel(self.frame_esquerda, text=f"TOTAL: R$ {self.dados['total']:.2f}", 
                                      font=("Arial", 32, "bold"), text_color="#ffcc00")
        self.lbl_total.pack(pady=10)

        # --- BOTÕES PRINCIPAIS ---
        self.btn_salvar = ctk.CTkButton(self.frame_esquerda, text="💾 ATUALIZAR E SALVAR", 
                                        fg_color="#f39c12", hover_color="#d68910", 
                                        height=50, font=("Arial", 14, "bold"),
                                        command=self._on_salvar)
        self.btn_salvar.pack(fill="x", padx=20, pady=5)

        self.btn_pagar = ctk.CTkButton(self.frame_esquerda, text="💰 FINALIZAR PAGAMENTO", 
                                       fg_color="#2fa572", height=50, font=("Arial", 14, "bold"),
                                       command=self._on_pagar)
        self.btn_pagar.pack(fill="x", padx=20, pady=5)

        # ===================================================
        # LADO DIREITO: PRODUTOS
        # ===================================================
        self.frame_direita = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_direita.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.ent_busca = ctk.CTkEntry(self.frame_direita, placeholder_text="🔍 Buscar produto...", height=35)
        self.ent_busca.pack(fill="x", padx=10, pady=(0, 10))

        # Tabs de Categorias
        self.tabview = ctk.CTkTabview(self.frame_direita)
        self.tabview.pack(fill="both", expand=True, padx=5)

        # Rodapé Direito
        self.frame_rodape_modal = ctk.CTkFrame(self.frame_direita, fg_color="transparent")
        self.frame_rodape_modal.pack(fill="x", pady=(10, 0), padx=10)
        
        ctk.CTkButton(self.frame_rodape_modal, text="📄 EXTRATO", fg_color="#1f538d", width=100, height=35, 
                      command=self._on_imprimir).pack(side="left", padx=2)
        
        ctk.CTkButton(self.frame_rodape_modal, text="❌ CANCELAR", fg_color="#cc3333", width=100, height=35, 
                      command=self._on_cancelar).pack(side="left", padx=2)
        
        ctk.CTkButton(self.frame_rodape_modal, text="SAIR", fg_color="#555555", width=80, height=35, 
                      command=self.destroy).pack(side="right", padx=2)

        # Inicialização
        self.renderizar_grade_no_modal()
        self.atualizar_lista_itens()

    # ===================================================
    # LÓGICA DE INTERFACE (Delegada ao Controller)
    # ===================================================

    def renderizar_grade_no_modal(self):
        """Pede ao controller para desenhar os botões de produtos"""
        
        # Função interna que recebe o clique do botão
        def callback_add(*args, **kwargs):
            
            # --- 1. Tratamento dos Dados (Que já arrumamos) ---
            nome = kwargs.get('nome')
            preco = kwargs.get('preco') or kwargs.get('preco_venda') or kwargs.get('preco_unit')
            pid = kwargs.get('id') or kwargs.get('produto_id') or kwargs.get('id_produto')
            
            if (nome is None or preco is None) and args:
                if isinstance(args[0], dict):
                    dados = args[0]
                    nome = dados.get('nome')
                    preco = dados.get('preco') or dados.get('preco_venda') or dados.get('preco_unit')
                    pid = dados.get('id') or dados.get('produto_id')
                elif len(args) >= 2:
                    nome = args[0]
                    preco = args[1]
                    if len(args) > 2: pid = args[2]

            if nome is None or preco is None:
                print(f"ERRO: Produto inválido. args={args}, kwargs={kwargs}")
                return

            produto_final = {
                "id": pid,
                "nome": str(nome).upper(),
                "preco_venda": float(preco)
            }
            
            print(f"DEBUG: Adicionando item {produto_final['nome']} - R$ {produto_final['preco_venda']}")
            
            # --- 2. NOVA CORREÇÃO: Encontrando o Controller Certo ---
            
            # Tenta direto (caso o controller seja o ComandaController)
            if hasattr(self.controller, 'adicionar_item_comanda_direto'):
                self.controller.adicionar_item_comanda_direto(self.id_comanda, produto_final)
                
            # Tenta via sub-controller (caso o controller seja o GestaoController/Main)
            elif hasattr(self.controller, 'comanda_ctrl') and hasattr(self.controller.comanda_ctrl, 'adicionar_item_comanda_direto'):
                self.controller.comanda_ctrl.adicionar_item_comanda_direto(self.id_comanda, produto_final)
                
            else:
                print("ERRO CRÍTICO: Método 'adicionar_item_comanda_direto' não encontrado em lugar nenhum!")

        # Chama a função que desenha os botões na tela
        self.controller.renderizar_botoes_produtos_modal(self.tabview, callback_add)

    def atualizar_lista_itens(self):
        """Limpa o scroll e pede ao controller para redesenhar cada linha"""
        for w in self.scroll_itens.winfo_children(): 
            w.destroy()
        
        for idx, item in enumerate(self.dados['itens']):
            # O controller desenha a linha (nome, qtd, botões +/-, lixeira)
            self.controller.desenhar_linha_comanda_modal(self.scroll_itens, idx, item)

    # ===================================================
    # AÇÕES DOS BOTÕES
    # ===================================================

    def _ao_mudar_status(self, novo_status):
        """
        Chamado automaticamente quando você troca a opção no menu.
        Tenta encontrar a função no controller principal ou no sub-controller de comanda.
        """
        print(f"DEBUG: Trocando status para {novo_status}")
        self.dados['status'] = novo_status 
        
        # 1. Tenta usar a função direto no controller recebido
        if hasattr(self.controller, 'alterar_status_comanda'):
            self.controller.alterar_status_comanda(self.id_comanda, novo_status)
            
        # 2. Se não achou, vê se o controller tem um 'comanda_ctrl' (que é o caso do MainController)
        elif hasattr(self.controller, 'comanda_ctrl') and hasattr(self.controller.comanda_ctrl, 'alterar_status_comanda'):
            print("DEBUG: Função encontrada dentro de comanda_ctrl!")
            self.controller.comanda_ctrl.alterar_status_comanda(self.id_comanda, novo_status)
            
        else:
            print("ERRO CRÍTICO: Método alterar_status_comanda não encontrado nem no pai nem no filho!")
            # Fallback: Tenta atualizar visual forçado se tiver acesso ao db
            try:
                if hasattr(self.controller, 'db'):
                    self.controller.db.execute("UPDATE comandas SET status = ? WHERE id = ?", (novo_status, self.id_comanda))
                    if hasattr(self.controller.db, 'conn'): self.controller.db.conn.commit()
                    print("DEBUG: Status salvo via Fallback (direto no banco).")
                    
                    # Tenta atualizar a tela principal
                    if hasattr(self.controller, 'comanda_ctrl'):
                        self.controller.comanda_ctrl.atualizar_visual_comandas()
                    elif hasattr(self.controller, 'atualizar_visual_comandas'):
                        self.controller.atualizar_visual_comandas()
            except Exception as e:
                print(f"Erro no fallback: {e}")

    def _on_salvar(self):
        self.dados['categoria'] = self.menu_categoria.get()
        self.dados['status'] = self.menu_status.get()
        self.controller.salvar_dados_comanda_direto(self.id_comanda, self.dados, self)


    def _on_pagar(self):
        # Atualiza os dados locais com o que está nos menus
        self.dados['categoria'] = self.menu_categoria.get()
        self.dados['status'] = self.menu_status.get()
        
        # --- AQUI ESTÁ A MUDANÇA ---
        # Adicione imprimir=False para evitar a impressão de cozinha neste momento
        self.controller.salvar_dados_comanda_direto(self.id_comanda, self.dados, self, imprimir=False)
        
        # Depois manda para o caixa
        self.controller.finalizar_comanda(self.id_comanda)
        
        # O destroy pode ou não ser necessário dependendo se o finalizar_comanda já fecha
        self.destroy()

    

    def _on_cancelar(self):
        self.controller.cancelar_comanda_total(self.id_comanda, self)

    def _on_imprimir(self):
        # Tenta imprimir extrato se a função existir
        if hasattr(self.controller, 'imprimir_extrato_comanda'):
            self.controller.imprimir_extrato_comanda(self.id_comanda)
        elif hasattr(self.controller.main, 'impressao_service'):
             self.controller.main.impressao_service.imprimir_extrato_comanda(self.id_comanda)
        else:
            messagebox.showinfo("Impressão", "Função de impressão não configurada.")