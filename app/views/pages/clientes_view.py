import customtkinter as ctk
from tkinter import messagebox

class ClientesView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller

        # --- A CORREÇÃO ESTÁ AQUI ---
        # A view se registra dentro do controller automaticamente
        self.controller.pagina_clientes = self 
        print("DEBUG: ClientesView registrada no Controller com sucesso!")
        # ----------------------------

        self.configure(fg_color="transparent")
        
        self.exibir_escolha_inicial()
        # Título da Tela


    def exibir_formulario_cadastro(self):
        """ESTADO 2: Seu formulário original completo"""
        for widget in self.winfo_children():
            widget.destroy()

        # Botão para voltar aos cards
        btn_voltar = ctk.CTkButton(self, text="← VOLTAR", width=100, command=self.exibir_escolha_inicial)
        btn_voltar.pack(anchor="w", padx=20, pady=10)

        # --- AQUI RECOLOQUEI TODO O SEU DESIGN ORIGINAL ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="GESTÃO DE CLIENTES (PF/PJ)", 
                     font=("Segoe UI", 24, "bold"), text_color="#D4AF37").pack(side="left")

        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="#6C3940", border_width=2, border_color="#D4AF37")
        self.scroll_canvas.pack(fill="both", expand=True, padx=20, pady=10)

        self._criar_subtitulo(self.scroll_canvas, "Identificação do Cliente")
        self.tabview = ctk.CTkTabview(self.scroll_canvas, fg_color="#4C727D", 
                                      segmented_button_selected_color="#D4AF37")
        self.tabview.pack(fill="x", padx=10, pady=10)
        self.tabview.add("Pessoa Física")
        self.tabview.add("Pessoa Jurídica")
        
        # (Tabs e campos idênticos ao que você tinha...)
        tab_pf = self.tabview.tab("Pessoa Física")
        self.ent_nome = self._add_entry(tab_pf, "Nome Completo:", "Ex: João da Silva")
        frame_pf_docs = self._criar_linha_dupla(tab_pf)
        self.ent_cpf = self._add_entry(frame_pf_docs, "CPF:", "000.000.000-00", side="left")
        self.ent_rg = self._add_entry(frame_pf_docs, "RG:", "Opcional", side="left")

        tab_pj = self.tabview.tab("Pessoa Jurídica")
        self.ent_razao = self._add_entry(tab_pj, "Razão Social:", "Ex: Empresa LTDA")
        self.ent_fantasia = self._add_entry(tab_pj, "Nome Fantasia:", "Como é conhecido")
        frame_pj_docs = self._criar_linha_dupla(tab_pj)
        self.ent_cnpj = self._add_entry(frame_pj_docs, "CNPJ:", "00.000.000/0001-00", side="left")
        self.ent_ie = self._add_entry(frame_pj_docs, "Insc. Estadual:", "Opcional", side="left")

        self._criar_subtitulo(self.scroll_canvas, "Informações de Contato")
        frame_contato = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_telefone = self._add_entry(frame_contato, "Telefone/WhatsApp:", "(00) 00000-0000", side="left")
        self.ent_email = self._add_entry(frame_contato, "E-mail:", "cliente@email.com", side="left")

        self._criar_subtitulo(self.scroll_canvas, "Endereço Completo")
        self.ent_endereco = self._add_entry(self.scroll_canvas, "Logradouro, Nº, Bairro e Cidade:", "Rua..., 123 - Centro")

        self._criar_subtitulo(self.scroll_canvas, "Configurações de Crediário")
        frame_financeiro = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_limite = self._add_entry(frame_financeiro, "Limite de Crédito (R$):", "0.00", side="left")

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(footer, text="LISTAR CLIENTES", fg_color="#555", 
                      command=self.controller.listar_todos_clientes).pack(side="left", padx=5)
        ctk.CTkButton(footer, text="SALVAR CLIENTE", fg_color="#27AE60", command=self._coletar_e_salvar).pack(side="right", padx=5)


    def abrir_central_financeira(self):
        """ESTADO 3: Tela de busca para crediário"""
        for widget in self.winfo_children():
            widget.destroy()
        btn_voltar = ctk.CTkButton(self, text="← VOLTAR", width=100, command=self.exibir_escolha_inicial)
        btn_voltar.pack(anchor="w", padx=20, pady=10)
        ctk.CTkLabel(self, text="CENTRAL FINANCEIRA", font=("Segoe UI", 24, "bold"), text_color="#D4AF37").pack(pady=20)
        # Chama a busca no controller
        self.controller.abrir_pesquisa_financeiro()


    # --- FUNÇÕES AUXILIARES ---
    def _criar_subtitulo(self, master, texto):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x", pady=(15, 5))
        ctk.CTkLabel(f, text=texto, font=("Segoe UI", 18, "bold"), text_color="#D4AF37").pack(side="left", padx=10)
        ctk.CTkFrame(f, height=2, fg_color="#333").pack(side="left", fill="x", expand=True, padx=5)

    def _add_entry(self, master, label, placeholder, side="top", expand=True):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(side=side, fill="x", expand=expand, padx=10, pady=2)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 14), text_color="white").pack(anchor="w")
        entry = ctk.CTkEntry(frame, placeholder_text=placeholder,
                            border_color="#D4AF37", fg_color="#4C727D",
                            border_width=1, height=35)
        entry.pack(fill="x", pady=2)
        return entry

    def _criar_linha_dupla(self, master):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x")
        return f

    def _coletar_e_salvar(self):
        aba_ativa = self.tabview.get()
        
        if aba_ativa == "Pessoa Física":
            dados = {
                "tipo": "F",
                "nome": self.ent_nome.get(),
                "documento": self.ent_cpf.get(),
                "ie_rg": self.ent_rg.get()
            }
        else:
            dados = {
                "tipo": "J",
                "nome": self.ent_razao.get(),
                "fantasia": self.ent_fantasia.get(),
                "documento": self.ent_cnpj.get(),
                "ie_rg": self.ent_ie.get()
            }
        
        # Dados comuns incluíndo o novo limite_credito
        dados.update({
            "telefone": self.ent_telefone.get(),
            "email": self.ent_email.get(),
            "endereco": self.ent_endereco.get(),
            "limite_credito": self.ent_limite.get().replace(",", ".") or "0.00"
        })
        
        self.controller.salvar_cliente(dados)

    def renderizar_lista(self, clientes):
        from app.views.base_view import BaseView
        """Tabela Profissional: Correção do erro de fonte e alinhamento total."""
        janela_lista = ctk.CTkToplevel(self)
        janela_lista.title("CLIENTES CADASTRADOS")
        janela_lista.geometry("1000x600")
        janela_lista.attributes("-topmost", True)
        janela_lista.configure(fg_color="#1a1a1a")

        BaseView.center_window(janela_lista, 1000, 600)

        ctk.CTkLabel(janela_lista, text="DADOS DO CLIENTE", 
                    font=("Segoe UI", 20, "bold"), text_color="#D4AF37").pack(pady=(15, 10))
        

        scroll = ctk.CTkScrollableFrame(janela_lista, fg_color="#242424", border_color="#D4AF37", border_width=1)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # 1. Configuração de colunas
        scroll.grid_columnconfigure(0, weight=10) 
        scroll.grid_columnconfigure(1, weight=2)  
        scroll.grid_columnconfigure(2, weight=4)  
        scroll.grid_columnconfigure(3, weight=4)  
        scroll.grid_columnconfigure(4, weight=5)  

        # 2. CABEÇALHO
        titulos = [
            ("NOME / RAZÃO SOCIAL", "w"), 
            ("TIPO", "center"), 
            ("DOCUMENTO", "w"), 
            ("TELEFONE", "w"), 
            ("AÇÕES", "center")
        ]
        
        for j, (texto, alinhar) in enumerate(titulos):
            lbl_head = ctk.CTkLabel(scroll, text=texto, font=("Segoe UI", 11, "bold"), 
                                    text_color="#D4AF37", anchor=alinhar)
            lbl_head.grid(row=0, column=j, sticky="ew", padx=15, pady=15)

        div = ctk.CTkFrame(scroll, height=2, fg_color="#D4AF37")
        div.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=(0, 10))

        # 3. LOOP DE CLIENTES
        for i, c in enumerate(clientes):
            row_idx = i + 2
            bg_color = "#2d2d2d" if i % 2 == 0 else "#242424"
            
            # Parâmetros comuns (removida a fonte daqui para evitar conflito)
            params = {"height": 45, "fg_color": bg_color}

            # Nome (Negrito)
            ctk.CTkLabel(scroll, text=f"  {c['nome_razao'].upper()[:35]}", 
                        font=("Segoe UI", 11, "bold"), text_color="white", 
                        anchor="w", **params).grid(row=row_idx, column=0, sticky="ew", padx=0, pady=1)

            # Tipo
            cor_tipo = "#1f538d" if c['tipo'] == "PF" else "#538d1f"
            ctk.CTkLabel(scroll, text=c['tipo'], font=("Segoe UI", 10, "bold"),
                        text_color=cor_tipo, anchor="center", **params
                        ).grid(row=row_idx, column=1, sticky="ew", padx=0, pady=1)

            # Documento
            ctk.CTkLabel(scroll, text=f"  {c['documento']}", font=("Segoe UI", 11),
                        text_color="#bbbbbb", anchor="w", **params
                        ).grid(row=row_idx, column=2, sticky="ew", padx=0, pady=1)

            # Telefone
            ctk.CTkLabel(scroll, text=f"  {c.get('telefone', '-') or '-'}", font=("Segoe UI", 11),
                        text_color="#bbbbbb", anchor="w", **params
                        ).grid(row=row_idx, column=3, sticky="ew", padx=0, pady=1)

            # AÇÕES
            acoes_frame = ctk.CTkFrame(scroll, fg_color=bg_color, corner_radius=0, height=45)
            acoes_frame.grid(row=row_idx, column=4, sticky="ew", pady=1)
            acoes_frame.pack_propagate(False)

            btn_container = ctk.CTkFrame(acoes_frame, fg_color="transparent")
            btn_container.pack(expand=True)
            
            # Botão EDITAR
            

            # Botão EXCLUIR
            ctk.CTkButton(btn_container, text="🗑 Excluir", width=30, height=30, corner_radius=15,
                        fg_color="#8d1f1f", hover_color="#5e1414", font=("Segoe UI", 14),
                        command=lambda cli=c: self._excluir_cliente(cli, janela_lista)
                        ).pack(side="left", padx=3)

            # Botão SELECIONAR (Check)
            ctk.CTkButton(btn_container, text="✎ Editar", width=30, height=30, corner_radius=15,
                        fg_color="#2fa572", hover_color="#1e6e4c", font=("Segoe UI", 14, "bold"),
                        command=lambda cli=c: [self._carregar_cliente_nos_campos(cli), janela_lista.destroy()]
                        ).pack(side="left", padx=3)

        janela_lista.focus_force()


    

    def _excluir_cliente(self, cliente, janela_pai):
        from tkinter import messagebox
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir {cliente['nome_razao']}?", parent=janela_pai):
            # Chama o controller que acabamos de criar
            sucesso = self.controller.deletar_cliente(cliente['id'])
            
            if sucesso:
                messagebox.showinfo("Sucesso", "Cliente removido com sucesso!", parent=janela_pai)
                janela_pai.destroy() # Fecha a lista atual
                # Opcional: Chama a busca novamente para abrir a lista atualizada
                # self.controller.listar_clientes_para_venda() 
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o cliente.", parent=janela_pai)
    

    def _carregar_cliente_nos_campos(self, cliente):
        """Preenche o formulário com os dados do cliente, tratando valores nulos."""
        self._limpar_campos() 
        
        if cliente.get('tipo') == 'F':
            self.tabview.set("Pessoa Física")
            self.ent_nome.insert(0, str(cliente.get('nome_razao') or ''))
            self.ent_cpf.insert(0, str(cliente.get('documento') or ''))
            self.ent_rg.insert(0, str(cliente.get('ie_rg') or ''))
        else:
            self.tabview.set("Pessoa Jurídica")
            self.ent_razao.insert(0, str(cliente.get('nome_razao') or ''))
            self.ent_fantasia.insert(0, str(cliente.get('apelido_fantasia') or ''))
            self.ent_cnpj.insert(0, str(cliente.get('documento') or ''))
            self.ent_ie.insert(0, str(cliente.get('ie_rg') or ''))

        # Campos comuns
        self.ent_telefone.insert(0, str(cliente.get('telefone') or ''))
        self.ent_email.insert(0, str(cliente.get('email') or ''))
        self.ent_endereco.insert(0, str(cliente.get('endereco') or ''))
        
        # NOVO: Carregar limite de crédito
        limite = cliente.get('limite_credito', 0.0)
        self.ent_limite.insert(0, f"{limite:.2f}")

    def _limpar_campos(self):
        """Limpa todos os campos de entrada."""
        campos = [
            self.ent_nome, self.ent_cpf, self.ent_rg,
            self.ent_razao, self.ent_fantasia, self.ent_cnpj, self.ent_ie,
            self.ent_telefone, self.ent_email, self.ent_endereco,
            self.ent_limite # NOVO
        ]
        for campo in campos:
            if hasattr(campo, 'delete'):
                campo.delete(0, 'end')


    def exibir_escolha_inicial(self):
        """Cria a tela com os dois cards centrais"""
        # Limpa o frame principal da página de clientes
        for widget in self.winfo_children():
            widget.destroy()

        # Container centralizado
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True)

        # --- CARD 1: CADASTRAR NOVO ---
        card_cadastro = ctk.CTkFrame(container, width=300, height=350, corner_radius=20, border_width=2, border_color="#333333")
        card_cadastro.pack(side="left", padx=20)
        card_cadastro.pack_propagate(False)

        ctk.CTkLabel(card_cadastro, text="👤", font=("Arial", 60)).pack(pady=(40, 10))
        ctk.CTkLabel(card_cadastro, text="NOVO CLIENTE", font=("Segoe UI", 18, "bold")).pack()
        ctk.CTkLabel(card_cadastro, text="Cadastrar novos clientes\nno sistema.", 
                    font=("Segoe UI", 12), text_color="#888888").pack(pady=20)

        btn_cad = ctk.CTkButton(card_cadastro, text="ABRIR CADASTRO", fg_color="#1f538d",
                                command=self.exibir_formulario_cadastro)
        btn_cad.pack(side="bottom", pady=30, padx=20, fill="x")

        # --- CARD 2: GESTÃO / CREDIÁRIO ---
        card_gestao = ctk.CTkFrame(container, width=300, height=350, corner_radius=20, border_width=2, border_color="#D4AF37")
        card_gestao.pack(side="left", padx=20)
        card_gestao.pack_propagate(False)

        ctk.CTkLabel(card_gestao, text="💰", font=("Arial", 60)).pack(pady=(40, 10))
        ctk.CTkLabel(card_gestao, text="CENTRAL FINANCEIRA", font=("Segoe UI", 18, "bold"), text_color="#D4AF37").pack()
        ctk.CTkLabel(card_gestao, text="Consultar débitos, limites\ne dar baixa em contas.", 
                    font=("Segoe UI", 12), text_color="#888888").pack(pady=20)

        btn_gestao = ctk.CTkButton(card_gestao, text="ABRIR CREDIÁRIO", fg_color="#D4AF37", text_color="black",
                                hover_color="#B8962E",
                                command=self.abrir_central_financeira)
        btn_gestao.pack(side="bottom", pady=30, padx=20, fill="x")


    def abrir_pesquisa_financeiro_view(self, clientes):
        from app.views.base_view import BaseView
        """Versão da lista profissional com BARRA DE BUSCA integrada e CORREÇÃO DE CLIQUE."""
        
        janela_lista = ctk.CTkToplevel(self)
        janela_lista.title("SELECIONAR CLIENTE - FINANCEIRO")
        janela_lista.geometry("1000x650")
        janela_lista.attributes("-topmost", True)
        janela_lista.configure(fg_color="#1a1a1a")

        BaseView.center_window(janela_lista, 1000, 650)

        # --- BARRA DE BUSCA (TOP) ---
        search_frame = ctk.CTkFrame(janela_lista, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(search_frame, text="BUSCAR CLIENTE:", 
                    font=("Segoe UI", 12, "bold"), text_color="#D4AF37").pack(side="left", padx=10)
        
        ent_busca = ctk.CTkEntry(search_frame, placeholder_text="Digite nome ou documento...", 
                                width=400, height=35, border_color="#D4AF37")
        ent_busca.pack(side="left", padx=10)

        # Container do Scroll
        scroll = ctk.CTkScrollableFrame(janela_lista, fg_color="#242424", border_color="#D4AF37", border_width=1)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # --- FUNÇÃO INTERNA (CORRIGIDA) ---
        def atualizar_lista(termo=""):
            """Filtra os clientes na tela conforme a busca"""
            
            # Limpa o scroll
            for widget in scroll.winfo_children():
                widget.destroy()

            # Configuração de colunas
            scroll.grid_columnconfigure(0, weight=12)
            scroll.grid_columnconfigure(1, weight=2)
            scroll.grid_columnconfigure(2, weight=5)
            scroll.grid_columnconfigure(3, weight=5)

            # Cabeçalho
            titulos = [("NOME / RAZÃO SOCIAL", "w"), ("TIPO", "center"), ("DOCUMENTO", "w"), ("TELEFONE", "w")]
            for j, (texto, alinhar) in enumerate(titulos):
                ctk.CTkLabel(scroll, text=texto, font=("Segoe UI", 11, "bold"), 
                            text_color="#D4AF37", anchor=alinhar).grid(row=0, column=j, sticky="ew", padx=15, pady=15)

            # Filtra os dados
            termo = termo.lower()
            clientes_filtrados = [c for c in clientes if termo in c['nome_razao'].lower() or termo in str(c.get('documento', '')).lower()]

            # --- A MÁGICA ACONTECE AQUI ---
            # Definimos a ação fora do loop de colunas para ser mais limpo
            def ao_clicar_cliente(event, cliente_selecionado):
                self.controller.exibir_ficha_financeira_completa(cliente_selecionado)
                janela_lista.destroy()

            for i, c in enumerate(clientes_filtrados):
                row_idx = i + 2
                bg_color = "#2d2d2d" if i % 2 == 0 else "#242424"
                params = {"height": 45, "fg_color": bg_color, "cursor": "hand2"}
                
                # Renderiza as células
                campos = [('nome_razao', 'w'), ('tipo', 'center'), ('documento', 'w'), ('telefone', 'w')]
                
                for j, (key, anchor) in enumerate(campos):
                    texto = f"  {c[key].upper()}" if key == 'nome_razao' else str(c.get(key, '-') or '-')
                    
                    lbl = ctk.CTkLabel(scroll, text=texto, font=("Segoe UI", 11, "bold" if j==0 else "normal"),
                                     text_color="white" if j==0 else "#bbbbbb", anchor=anchor, **params)
                    lbl.grid(row=row_idx, column=j, sticky="ew", padx=0, pady=1)
                    
                    # O FIX DEFINITIVO:
                    # Passamos 'c' (o cliente atual do loop) como default argument 'cli=c'
                    # Isso "congela" o valor de c naquele momento.
                    lbl.bind("<Button-1>", lambda e, cli=c: ao_clicar_cliente(e, cli))

        # Evento de busca ao digitar
        ent_busca.bind("<KeyRelease>", lambda e: atualizar_lista(ent_busca.get()))
        
        # Inicializa a lista cheia
        atualizar_lista()
        
        # Foco na busca para digitar direto
        ent_busca.focus_force()

    def exibir_ficha_financeira(self, cliente, resumo, timeline):
        """Timeline Inovadora com Dashboard de Saúde Financeira Real"""
        # 1. Limpa a tela atual
        for widget in self.winfo_children():
            widget.destroy()

        # --- CABEÇALHO ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(header, text="← VOLTAR", width=80, fg_color="#555", 
                    command=self.exibir_escolha_inicial).pack(side="left")
        
        ctk.CTkLabel(header, text=f"FINANCEIRO: {cliente['nome_razao'].upper()}", 
                    font=("Segoe UI", 20, "bold"), text_color="#D4AF37").pack(side="left", padx=20)

        # --- CONTAINER DO DASHBOARD (Indicadores) ---
        dash_container = ctk.CTkFrame(self, fg_color="transparent")
        dash_container.pack(fill="x", padx=20, pady=10)

        self._criar_card_financeiro(dash_container, "TOTAL COMPRAS", f"R$ {resumo['total_compras']:.2f}", "#3498DB")
        self._criar_card_financeiro(dash_container, "A VENCER", f"R$ {resumo['a_vencer']:.2f}", "#F1C40F")
        self._criar_card_financeiro(dash_container, "VENCIDAS", f"R$ {resumo['vencidas']:.2f}", "#E74C3C")
        self._criar_card_financeiro(dash_container, "PAGAS", f"R$ {resumo['total_pago']:.2f}", "#27AE60")

        # --- MARCADOR DE SAÚDE (SCORE) ---
        score = resumo.get('score', 100) # Prevencao contra None
        cor_saude = "#27AE60" if score > 70 else "#F1C40F" if score > 40 else "#E74C3C"
        status_texto = "EXCELENTE PAGADOR" if score > 70 else "PAGADOR REGULAR" if score > 40 else "ALTO RISCO"

        score_frame = ctk.CTkFrame(self, fg_color="#242424", border_width=1, border_color=cor_saude)
        score_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(score_frame, text=f"SAÚDE DO CLIENTE: {status_texto} ({score} pts)", 
                    font=("Segoe UI", 14, "bold"), text_color=cor_saude).pack(pady=(10, 0))

        progresso = ctk.CTkProgressBar(score_frame, progress_color=cor_saude, height=15)
        progresso.pack(fill="x", padx=100, pady=15)
        progresso.set(score / 100) 

        btn_receber = ctk.CTkButton(score_frame, text="💵 RECEBER / BAIXA", 
                                    fg_color="#27AE60", hover_color="#1e8449",
                                    font=("Segoe UI", 14, "bold"), height=40,
                                    # A MUDANÇA É AQUI: Chama o Controller
                                    command=lambda: self.controller.iniciar_recebimento_selecao(cliente, view_origem=self))
            
        btn_receber.pack(pady=(0, 15))


        # --- ÁREA DA TIMELINE (O LOOP ESTÁ AQUI AGORA) ---
        self._criar_subtitulo(self, "Histórico de Movimentações")
        
        timeline_scroll = ctk.CTkScrollableFrame(self, fg_color="#1a1a1a", height=300)
        timeline_scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # === AQUI ESTÁ O LOOP QUE FALTAVA ===
        if not timeline:
            ctk.CTkLabel(timeline_scroll, text="Nenhuma movimentação registrada.", text_color="#666").pack(pady=20)
        else:
            for mov in timeline:
                # 1. Define a cor baseada no status ou tipo
                status = mov.get('status', '').upper()
                cor_item = "white"
                
                if status == "PENDENTE": cor_item = "#E74C3C"  # Vermelho
                elif status == "PAGO": cor_item = "#27AE60"      # Verde
                elif status == "FINALIZADO": cor_item = "#3498DB" # Azul (Venda)

                # Formatação do valor
                val_fmt = f"R$ {mov['valor']:.2f}".replace('.', ',')

                # 2. Chama a função de renderizar passando o venda_id
                self._renderizar_item_timeline(
                    master=timeline_scroll,
                    data=mov['data'],
                    acao=mov['acao'], # Ex: "VENDA A PRAZO"
                    valor=val_fmt,
                    cor=cor_item,
                    venda_id=mov.get('venda_id') # <--- IMPORTANTE: Passa o ID para o botão funcionar
                )

       

    def _criar_card_financeiro(self, master, titulo, valor, cor):
        card = ctk.CTkFrame(master, fg_color="#242424", border_width=1, border_color="#333", height=100)
        card.pack(side="left", padx=5, expand=True, fill="both")
        
        ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 11), text_color="#888").pack(pady=(15, 0))
        ctk.CTkLabel(card, text=valor, font=("Segoe UI", 18, "bold"), text_color=cor).pack(pady=(5, 15))

    def _renderizar_item_timeline(self, master, data, acao, valor, cor, venda_id=None):
        # Cria o frame da linha
        item = ctk.CTkFrame(master, fg_color="#2d2d2d", height=50)
        item.pack(fill="x", pady=2, padx=5)
        
        # 1. Data (Esquerda)
        ctk.CTkLabel(item, text=data, font=("Arial", 11), text_color="#888", width=100).pack(side="left", padx=10)
        
        # 2. Ação (Centro/Expandir)
        ctk.CTkLabel(item, text=acao, font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left", padx=20, expand=True, fill="x")
        
        # 3. Botão de Impressão (Direita Extrema - Só aparece se tiver ID)
        if venda_id:
            ctk.CTkButton(item, text="🖨️", width=35, height=25, corner_radius=5,
                          fg_color="#444", hover_color="#666",
                          font=("Segoe UI", 14),
                          command=lambda: self.controller.reimprimir_comprovante(venda_id)
                          ).pack(side="right", padx=(5, 15))

        # 4. Valor (Antes do botão)
        ctk.CTkLabel(item, text=valor, font=("Segoe UI", 13, "bold"), text_color=cor).pack(side="right", padx=5)
    


    def abrir_modal_recebimento_selecao(self, pendencias, callback_pagar, callback_refresh=None):
        """
        Modal de Seleção de Contas (Versão Corrigida: Data e Total)
        """
        modal = ctk.CTkToplevel(self)
        modal.title("SELECIONAR CONTAS A PAGAR")
        modal.geometry("550x750")
        modal.attributes("-topmost", True)
        
        from app.views.base_view import BaseView
        BaseView.center_window(modal, 550, 750)

        ctk.CTkLabel(modal, text="SELECIONE AS CONTAS PARA BAIXA", 
                     font=("Segoe UI", 18, "bold"), text_color="#D4AF37").pack(pady=15)

        # Cabeçalho
        header_text = f"{'DATA':<12} {'DESCRIÇÃO':<20} {'VALOR (R$)':>12}"
        ctk.CTkLabel(modal, text=header_text, font=("Consolas", 14, "bold"), text_color="#2b2b2b").pack(pady=(0, 5))

        # Scroll
        scroll = ctk.CTkScrollableFrame(modal, width=550, height=350, fg_color="#2b2b2b")
        scroll.pack(pady=5, padx=10)

        self.selecionados_ids = []
        lista_checkboxes = [] 

        # --- ÁREA INFERIOR (RESUMO) ---
        frame_resumo = ctk.CTkFrame(modal, fg_color="#1f1f1f", corner_radius=10)
        frame_resumo.pack(fill="x", side="bottom", padx=20, pady=20)

        ctk.CTkLabel(frame_resumo, text="TOTAL SELECIONADO:", text_color="white", font=("Segoe UI", 12)).pack(pady=(15,0))
        
        # LABEL DO TOTAL (Criamos vazio ou zerado inicialmente)
        lbl_total = ctk.CTkLabel(frame_resumo, text="R$ 0,00", 
                                 font=("Segoe UI", 26, "bold"), text_color="#27AE60")
        lbl_total.pack(pady=(0, 15))

        # --- FUNÇÃO DE SOMA ROBUSTA ---
        def atualizar_total():
            soma = 0.0
            ids_temp = []
            for chk_var, valor_conta, id_conta in lista_checkboxes:
                if chk_var.get() == 1:
                    soma += valor_conta
                    ids_temp.append(id_conta)
            
            self.selecionados_ids = ids_temp
            
            # ATUALIZAÇÃO DIRETA (Sem StringVar)
            texto_valor = f"R$ {soma:.2f}".replace('.', ',')
            lbl_total.configure(text=texto_valor)

        # --- PREENCHIMENTO DA LISTA ---
        for p in pendencias:
            id_conta = p['id']
            
            # TRATAMENTO DE DATA (Se vier YYYY-MM-DD, converte. Se vier texto, mantem)
            raw_data = str(p.get('data_venc') or "")
            if "-" in raw_data and len(raw_data) == 10: # Formato 2026-01-20
                try:
                    ano, mes, dia = raw_data.split('-')
                    data_exibicao = f"{dia}/{mes}/{ano}"
                except:
                    data_exibicao = raw_data
            elif not raw_data or raw_data == "None":
                data_exibicao = "--/--/--"
            else:
                data_exibicao = raw_data # Já deve ser DD/MM/AAAA

            desc_raw = p.get('acao') or "VENDA"
            desc = (desc_raw[:18] + '..') if len(desc_raw) > 18 else desc_raw
            valor = float(p['saldo_restante'])

            # Formatação alinhada
            texto_linha = f"{data_exibicao:<12} {desc:<20} {valor:>12.2f}"
            
            linha = ctk.CTkFrame(scroll, fg_color="transparent")
            linha.pack(fill="x", pady=2)
            
            chk_var = ctk.IntVar(value=0)
            chk = ctk.CTkCheckBox(linha, text=texto_linha, variable=chk_var,
                                  font=("Consolas", 14), text_color="white", hover_color="#27AE60",
                                  command=atualizar_total)
            chk.pack(side="left", padx=10, pady=5)
            
            lista_checkboxes.append((chk_var, valor, id_conta))

        # Botão Confirmar
        # --- PARTE IMPORTANTE: O BOTÃO CONFIRMAR ---
        def confirmar_acao():
            if not self.selecionados_ids:
                from tkinter import messagebox
                messagebox.showwarning("Atenção", "Selecione pelo menos uma conta.", parent=modal)
                return
            
            # 1. Tenta pagar (O Controller vai salvar no banco e retornar True, SEM atualizar a tela)
            sucesso = callback_pagar(self.selecionados_ids)
            
            if sucesso:
                from tkinter import messagebox
                # 2. Exibe a mensagem. O modal ainda está vivo, então parent=modal funciona!
                messagebox.showinfo("Sucesso", "Pagamento realizado com sucesso!", parent=modal)
                
                # 3. Fecha o modal
                modal.destroy()
                
                # 4. AGORA SIM, chamamos o refresh da tela de fundo
                if callback_refresh:
                    callback_refresh()

            else:
                from tkinter import messagebox
                messagebox.showerror("Erro", "Erro ao processar pagamento.", parent=modal)

        ctk.CTkButton(frame_resumo, text="✅ CONFIRMAR PAGAMENTO", 
                      fg_color="#27AE60", hover_color="#1E8449", height=50, 
                      font=("Segoe UI", 14, "bold"), command=confirmar_acao
                      ).pack(fill="x", padx=20, pady=(0, 20))