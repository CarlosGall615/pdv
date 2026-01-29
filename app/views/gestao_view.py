import customtkinter as ctk
import os
from tkinter import messagebox

from app.views.base_view import BaseView
from app.views.pages.dashboard_view import DashboardView

class GestaoView(ctk.CTk, BaseView):

    # ADICIONADO: Agora recebe o controller como argumento
    def __init__(self, usuario, controller):

        super().__init__()
        self.controller = controller # Salva a referência do controller

        self.title(f"Sistema de Gestão - Logado como: {usuario}")
        self.geometry("1200x700")
        self.protocol("WM_DELETE_WINDOW", self.confirmar_saida)
        self.center_window(1200, 700)
        # Cores da Paleta
        self.configure(fg_color="#2F5965") # Fundo Principal

        # Configuração de Grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- MENU LATERAL ---
        # Alterado para as cores da paleta
        self.menu_lateral = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e3d45")
        self.menu_lateral.grid(row=0, column=0, sticky="nsew")

        self.lbl_logo = ctk.CTkLabel(self.menu_lateral, text="GESTOR DE VENDAS", 
                                     font=("Segoe UI", 18, "bold"), text_color="#D4AF37")
        self.lbl_logo.pack(pady=30)

        # Botões do Menu
        # --- Configuração dos Botões com Bloqueio de Segurança ---
        # --- MENU LATERAL (Ajuste os comandos aqui) ---
        self.btn_dash = self._criar_botao_menu("Dashboard")
        self.btn_dash.configure(command=lambda: self.pode_navegar(lambda: self.controller.filtrar_dashboard("Dia")))

        self.btn_pdv = self._criar_botao_menu("PDV - Vendas")
        self.btn_pdv.configure(command=lambda: self.pode_navegar(self.controller.exibir_pdv))

        self.btn_comandas = self._criar_botao_menu("Comandas")
        self.btn_comandas.configure(command=lambda: self.pode_navegar(self.controller.exibir_comandas_pendentes))

        self.btn_cadastros = self._criar_botao_menu("Cadastros")
        self.btn_cadastros.configure(command=lambda: self.pode_navegar(self.controller.exibir_cadastros))
        
        self.btn_clientes = self._criar_botao_menu("Clientes")
        self.btn_clientes.configure(command=lambda: self.pode_navegar(self.controller.inicializar_cards_clientes))
        
        # Botão Configurações
        self.btn_configuracoes = self._criar_botao_menu("⚙️ Configurações")
        self.btn_configuracoes.configure(command=lambda: self.pode_navegar(self.controller.abrir_configuracoes_empresa))
        
        
        # CORRIGIDO: Agora usa self.menu_lateral e o comando correto
        self.btn_caixa = ctk.CTkButton(
            self.menu_lateral, 
            text="💰 GESTÃO DE CAIXA", 
            font=("Segoe UI", 13, "bold"),
            fg_color="#4C727D",
            hover_color="#D4AF37",
            command=self.controller.abrir_gestao_caixa
        )
        self.btn_caixa.pack(pady=10, padx=20)

        # Indicadores de Hardware
        self.criar_indicadores_status()

        self.btn_sair = ctk.CTkButton(self.menu_lateral, text="Sair",
                                      command=self.confirmar_saida,
                                      fg_color="#6C3940", hover_color="#990000", height=40)
        self.btn_sair.pack(side="bottom", pady=20, padx=20)
        # Botão Sair (também com trava para não deslogar com venda aberta)
        self.btn_sair.configure(command=lambda: self.pode_navegar(self.controller.fazer_logout))
        # --- CONTAINER PRINCIPAL ---
        self.container_principal = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.container_principal.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

  
  
    def _criar_botao_menu(self, texto):
        btn = ctk.CTkButton(self.menu_lateral, text=texto, height=40, 
                            fg_color="transparent", anchor="w", font=("Segoe UI", 16))
        btn.pack(pady=5, padx=20, fill="x")
        return btn

    
    
    # 1. Primeiro, defina a função de trava dentro da GestaoView
    def pode_navegar(self, destino_callback):
        # Verificação dupla: se tem itens OU se o cupom foi iniciado (venda_atual é True)
        venda_ativa = hasattr(self.controller.venda_ctrl, 'venda_atual') and self.controller.venda_ctrl.venda_atual is not None
        tem_itens = len(self.controller.venda_ctrl.carrinho) > 0

        if venda_ativa or tem_itens:
            if messagebox.askyesno("Venda em Aberto", "Deseja CANCELAR o cupom atual para sair?"):
                self.controller.venda_ctrl.limpar_venda()
                # Após limpar, venda_atual vira None e o carrinho vira []
                destino_callback()
        else:
            # Se não iniciou venda nem tem itens, navega livremente
            destino_callback()



    def configurar_comandos_menu(self):
        self.btn_dash.configure(command=lambda: self.pode_navegar(self.controller.exibir_dashboard))
        
        # O botão PDV leva para a função que decide entre "Espera" ou "Venda"
        self.btn_pdv.configure(command=lambda: self.pode_navegar(self.controller.exibir_pdv))
        
        self.btn_comandas.configure(command=lambda: self.pode_navegar(self.controller.exibir_comandas_pendentes))
        self.btn_cadastros.configure(command=lambda: self.pode_navegar(self.controller.exibir_cadastros))
        self.btn_clientes.configure(command=lambda: self.pode_navegar(self.controller.inicializar_cards_clientes))
        self.btn_configuracoes.configure(command=lambda: self.pode_navegar(self.controller.abrir_configuracoes_empresa))



    def limpar_container(self):
        """Limpa a área central para receber uma nova tela"""
        for widget in self.container_principal.winfo_children():
            widget.destroy()
    # ==========================================================
    # SEÇÃO DE STATUS (HARDWARE)
    # ==========================================================
    def criar_indicadores_status(self):
        # Frame de status fixado acima do botão sair
        self.frame_status = ctk.CTkFrame(self.menu_lateral, fg_color="transparent")
        self.frame_status.pack(side="bottom", pady=10, padx=20, fill="x")

        self.lbl_balanca_status = ctk.CTkLabel(self.frame_status, text="❌ BALANÇA", 
                                              text_color="#ff4444", font=("Arial", 11, "bold"))
        self.lbl_balanca_status.pack(anchor="w")

        self.lbl_impressora_status = ctk.CTkLabel(self.frame_status, text="❌ IMPRESSORA", 
                                                 text_color="#ff4444", font=("Arial", 11, "bold"))
        self.lbl_impressora_status.pack(anchor="w", pady=(5, 0))



    def atualizar_cor_status(self, hardware, online):
        cor = "#44ff44" if online else "#ff4444"
        icone = "✅" if online else "❌"
        if hardware == "balanca":
            self.lbl_balanca_status.configure(text=f"{icone} BALANÇA", text_color=cor)
        elif hardware == "impressora":
            self.lbl_impressora_status.configure(text=f"{icone} IMPRESSORA", text_color=cor)
    # ==========================================================
    # COMPONENTES DE TELA (REFATORAÇÃO DO PDV)
    # ==========================================================
    def criar_card_comanda(self, container, id_c, dados):
        # COR Hex em vez de RGBA para evitar o erro de 'unknown color'
        cor_fundo = "#3d3d3d"  # Cinza escuro elegante
        
        # Aumentamos o height para o card não ficar pequeno
        card = ctk.CTkFrame(container, fg_color=cor_fundo, height=100, corner_radius=10)
        card.pack(fill="x", padx=15, pady=8)
        card.pack_propagate(False) # Mantém o tamanho que definimos

        # Texto mais visível
        info_texto = f"COMANDA {id_c}\nTotal: R$ {dados['total']:.2f}"
        lbl = ctk.CTkLabel(card, text=info_texto, font=("Arial", 16, "bold"), justify="left")
        lbl.pack(side="left", padx=20)

        # CORREÇÃO DO BOTÃO: id_comanda=id_c dentro do lambda é vital!
        btn = ctk.CTkButton(
            card, 
            text="ABRIR", 
            width=100,
            height=40,
            fg_color="#D4AF37",
            text_color="black",
            command=lambda id_comanda=id_c: self.controller.abrir_detalhes_comanda(id_comanda)
        )
        btn.pack(side="right", padx=20)



    def desenhar_tela_configuracoes(self, porta_atual, callback_salvar):
        self.limpar_container()
        
        self.tabview = ctk.CTkTabview(self.container_principal, 
                                     segmented_button_selected_color="#D4AF37",
                                     segmented_button_selected_hover_color="#B8962E",
                                     segmented_button_fg_color="#2F5965",
                                     text_color="#6C3940"
                                     )
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)

        custom_font = ctk.CTkFont(family="Segoe UI", size=25, weight="bold")
        self.tabview._segmented_button.configure(font=custom_font)
        # --- ABA 1: HARDWARE ---
        tab_h = self.tabview.add("Hardware")
        ctk.CTkLabel(tab_h, text="Configurações de Hardware", font=("Arial", 16, "bold"), text_color="#D4AF37").pack(pady=10)
        
        ctk.CTkLabel(tab_h, text="Porta Balança:").pack(pady=5)
        self.combo_b = ctk.CTkComboBox(tab_h, values=["COM1","COM2","COM3","COM4","COM5","COM6"])
        self.combo_b.set(porta_atual)
        self.combo_b.pack()
        
        btn_salvar_h = ctk.CTkButton(tab_h, text="Salvar Configurações", fg_color="#D4AF37", text_color="black",
                                    command=lambda: callback_salvar(self.combo_b.get()))
        btn_salvar_h.pack(pady=20)

        # --- ABA 2: PRODUTOS ---
        tab_p = self.tabview.add("Produtos")
        tab_p.grid_columnconfigure(0, weight=1) # Cadastro
        tab_p.grid_columnconfigure(1, weight=1) # Lista
        tab_p.grid_rowconfigure(0, weight=1)

        # --- LADO ESQUERDO: FORMULÁRIO ---
        frame_esquerda = ctk.CTkFrame(tab_p, fg_color="transparent")
        frame_esquerda.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_esquerda, text="📝 DADOS DO PRODUTO", font=("Arial", 16, "bold"), text_color="#D4AF37").pack(pady=10)

        # Nome e Preço (Usando sua função de alinhamento)
        self.ent_nome = self._criar_input_alinhado(frame_esquerda, "Nome:")
        self.ent_preco = self._criar_input_alinhado(frame_esquerda, "Preço R$:")
        
        # --- CAMPO CÓDIGO COM VARINHA MÁGICA (EAN-13) ---
        f_cod_container = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        f_cod_container.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(f_cod_container, text="Código/ID:", width=100, anchor="w").pack(side="left")
        
        # Input do Código
        self.ent_codigo = ctk.CTkEntry(f_cod_container, border_color="#D4AF37")
        self.ent_codigo.pack(side="left", expand=True, fill="x")
        
        # Botão Varinha Mágica
        self.btn_gerar_ean = ctk.CTkButton(f_cod_container, text="🪄", width=35, 
                                          fg_color="#3d3d3d", hover_color="#D4AF37",
                                          command=self.sugerir_ean)
        self.btn_gerar_ean.pack(side="left", padx=(5, 0))

        # Categoria
        f_cat = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        f_cat.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f_cat, text="Categoria:", width=100, anchor="w").pack(side="left")
        self.combo_cat = ctk.CTkComboBox(f_cat, values=["Refeições", "Bebidas", "Doces", "Outros"])
        self.combo_cat.set("Refeições")
        self.combo_cat.pack(side="left", expand=True, fill="x")

        # Switch Atalho
        self.var_atalho = ctk.IntVar(value=0)
        self.sw_atalho = ctk.CTkSwitch(frame_esquerda, text="EXIBIR COMO ATALHO NO PDV", 
                                     variable=self.var_atalho, progress_color="#D4AF37")
        self.sw_atalho.pack(pady=20)

        # --- BOTÕES SALVAR/CANCELAR ---
        f_botoes_form = ctk.CTkFrame(frame_esquerda, fg_color="transparent")
        f_botoes_form.pack(fill="x", padx=20, pady=10)

        self.btn_salvar_p = ctk.CTkButton(f_botoes_form, text="💾 SALVAR", font=("Arial", 14, "bold"),
                                         fg_color="#2fa572", hover_color="#1d7a52",
                                         command=self.executar_salvamento_produto)
        self.btn_salvar_p.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_cancelar_p = ctk.CTkButton(f_botoes_form, text="✖ CANCELAR", font=("Arial", 14, "bold"),
                                           fg_color="#3d3d3d", hover_color="#555555",
                                           command=self.limpar_formulario_produto)
        self.btn_cancelar_p.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # --- LADO DIREITO: LISTA E BUSCA ---
        frame_direita = ctk.CTkFrame(tab_p, fg_color="#1a1a1a")
        frame_direita.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        
        ctk.CTkLabel(frame_direita, text="📦 PRODUTOS CADASTRADOS", font=("Arial", 14, "bold")).pack(pady=10)

        # RENOMEADO para self.ent_busca_config para não conflitar com o PDV
        self.ent_busca_config = ctk.CTkEntry(frame_direita, placeholder_text="🔍 Pesquisar produto ou código...", border_color="#D4AF37")
        self.ent_busca_config.pack(fill="x", padx=15, pady=(0, 10))
        
        # O BIND correto usando o novo nome
        self.ent_busca_config.bind("<KeyRelease>", lambda e: self.controller.atualizar_lista_produtos_config(self.ent_busca_config.get()))
        # Scroll da Lista
        self.scroll_lista_produtos = ctk.CTkScrollableFrame(frame_direita, fg_color="transparent")
        self.scroll_lista_produtos.pack(fill="both", expand=True, padx=5, pady=5)

        # Carrega a lista pela primeira vez ao abrir a tela
        self.controller.atualizar_lista_produtos_config()



    def limpar_formulario_produto(self):
        """Reseta o formulário para o estado inicial de novo cadastro"""
        self.ent_nome.delete(0, 'end')
        self.ent_preco.delete(0, 'end')
        
        # Reativa o campo código e limpa
        self.ent_codigo.configure(state="normal")
        self.ent_codigo.delete(0, 'end')
        
        # Reseta os controles
        self.var_atalho.set(0)
        self.combo_cat.set("Refeições")
        
        # Restaura o botão de salvar original
        self.btn_salvar_p.configure(text="💾 SALVAR PRODUTO", fg_color="#2fa572")
        
        # Opcional: focar no primeiro campo
        self.ent_nome.focus()

    # 2. Nova função para criar inputs perfeitamente alinhados

    def _criar_input_alinhado(self, master, texto):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        
        lbl = ctk.CTkLabel(frame, text=texto, width=100, anchor="w")
        lbl.pack(side="left")
        
        entry = ctk.CTkEntry(frame, border_color="#D4AF37")
        entry.pack(side="left", expand=True, fill="x")
        return entry

    # 3. Atualize a função de salvar para pegar a categoria do combo

    def executar_salvamento_produto(self):
        try:
            # 1. Coleta e limpa os dados
            nome = self.ent_nome.get().strip()
            codigo = self.ent_codigo.get().strip()
            preco_raw = self.ent_preco.get().replace(",", ".")
            
            # 2. Validação de campos vazios
            if not nome or not codigo or not preco_raw:
                from tkinter import messagebox
                messagebox.showwarning("Atenção", "Preencha Nome, Código e Preço!")
                return

            dados = {
                "nome": nome,
                "preco": float(preco_raw),
                "codigo": codigo,
                "categoria": self.combo_cat.get(),
                "atalho": self.var_atalho.get()
            }

            # 3. Tenta salvar no banco de dados
            if self.controller.salvar_produto_no_banco(dados):
                from tkinter import messagebox
                messagebox.showinfo("Sucesso", f"Produto '{dados['nome']}' salvo com sucesso!")
                
                # Reseta a tela (usa a função que criamos para o botão cancelar)
                self.limpar_formulario_produto()
                
                # Atualiza a lista da direita para mostrar as mudanças
                self.controller.atualizar_lista_produtos_config()
                
            else:
                from tkinter import messagebox
                messagebox.showerror("Erro", "Não foi possível salvar o produto no banco.")
                
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Erro", "Preço inválido! Use apenas números (ex: 10.50)")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro: {e}")


    
    def sugerir_ean(self):
        from app.controllers.produto_controller import gerar_ean13_cadastro
        
        """Pega o ID digitado e transforma em EAN-13 completo"""
        valor_atual = self.ent_codigo.get().strip()
        
        if valor_atual.isdigit():
            # Gera o código baseado no que o usuário digitou no campo
            novo_ean = gerar_ean13_cadastro(valor_atual)
            
            # Limpa e insere o código completo
            self.ent_codigo.delete(0, 'end')
            self.ent_codigo.insert(0, novo_ean)
        else:
            from tkinter import messagebox
            messagebox.showwarning("Atenção", "Digite um número (ID) para gerar o EAN.")
    # ============================================================================================
    # -------------------------    BOTÃO SIDE -> *DASHBOARD*     ---------------------------------
    # ============================================================================================
    def exibir_dashboard(self):
        
        self.limpar_container()
        
        # Instancia a classe que está no outro arquivo
        self.pagina_dashboard = DashboardView(self.container_principal, self.controller)
        self.pagina_dashboard.pack(fill="both", expand=True)
        
        # Já pede ao controller para carregar os dados iniciais (ex: do "Dia")
        self.controller.filtrar_dashboard("Dia")

    
 
    def desenhar_tela_comandas(self):
        self.limpar_container()
        
        # Import local para evitar erro de importação circular
        from app.views.pages.comandas_view import ComandasView
        
        # Instancia a tela real de comandas (a que tem abas e lógica de renderização)
        tela_comandas = ComandasView(self.container_principal, self.controller)
        tela_comandas.pack(fill="both", expand=True)
        
        return tela_comandas # RETORNA o objeto para o Controller salvar



    def confirmar_saida(self):
        if messagebox.askyesno("Confirmar Saída", "Deseja realmente encerrar o sistema?"):
            self.destroy()
            os._exit(0)

 
    