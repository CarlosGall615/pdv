import customtkinter as ctk
from app.views.base_view import BaseView

class ListaProdutosView(ctk.CTkToplevel, BaseView):
    def __init__(self, master, controller, produtos):
        super().__init__(master)
        
        self.controller = controller
        self.title("Gestão de Produtos Cadastrados")
        self.geometry("1000x700")
        self.configure(fg_color="#2F5965") # Fundo padrão
        self.attributes('-topmost', False)
        self.transient(master)
        self.center_window(1000, 700)

        # --- CABEÇALHO (Estilo Gestão Caixa) ---
        self.header = ctk.CTkFrame(self, fg_color="#4C727D", border_color="#D4AF37", border_width=2)
        self.header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(self.header, text="PRODUTOS CADASTRADOS", 
                     font=("Arial", 20, "bold"), text_color="#D4AF37").pack(pady=15)
        # ---- BOTAO DE PESQUISA ----

        self.search_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=20, pady=(0, 15))

        # Ícone ou Label de busca
        ctk.CTkLabel(self.search_frame, text="🔍 BUSCAR:", font=("Arial", 12, "bold")).pack(side="left", padx=10)

        # Campo de entrada (Entry)
        self.ent_busca = ctk.CTkEntry(
            self.search_frame, 
            placeholder_text="Digite o nome ou código de barras...",
            height=35,
            fg_color="#2F5965",
            border_color="#D4AF37"
        )
        self.ent_busca.pack(side="left", fill="x", expand=True, padx=5)

        # Evento: Chamar o filtro a cada tecla digitada
        self.ent_busca.bind("<KeyRelease>", lambda e: self.controller.filtrar_produtos_popup(self.ent_busca.get()))

        # Botão para limpar a busca
        ctk.CTkButton(
            self.search_frame, 
            text="LIMPAR", 
            width=80, 
            height=35,
            fg_color="#555",
            command=self._limpar_busca
        ).pack(side="left", padx=5)

        # --- LISTA DE PRODUTOS ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#4C727D", border_color="#D4AF37", border_width=1)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=(0, 20))

        # Container de Scroll
        self.scroll_produtos = ctk.CTkScrollableFrame(self.main_frame, fg_color="#2F5965")
        self.scroll_produtos.pack(expand=True, fill="both", padx=15, pady=15)

        # Preencher a lista
        self.renderizar_lista(produtos)

        # --- RODAPÉ (Botões) ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(self.footer, text="✖ FECHAR", fg_color="#6C3940", 
                      width=150, height=45, command=self.destroy).pack(side="right", padx=10)


    def _limpar_busca(self):
        self.ent_busca.delete(0, 'end')
        # Chama o filtro vazio para mostrar todos os produtos novamente
        self.controller.filtrar_produtos_popup("")
        
     
    def renderizar_lista(self, produtos):
        """Desenha cada produto no estilo 'Venda' do Gestão de Caixa"""
        for widget in self.scroll_produtos.winfo_children():
            widget.destroy()

        if not produtos:
            ctk.CTkLabel(self.scroll_produtos, text="Nenhum produto encontrado.", font=("Arial", 14)).pack(pady=20)
            return

        for item in produtos:
            # Container da linha (Card)
            f = ctk.CTkFrame(self.scroll_produtos, fg_color="#4C727D")
            f.pack(fill="x", pady=5, padx=5)
            
            # Texto Principal: EAN | NOME | PREÇO
            info = f"📦 EAN: {item.get('codigo_barras', 'N/A')}  |  {item['nome'].upper()}  |  Preço: R$ {item['preco']:.2f}"
            
            # Subtexto: Categoria e Estoque
            sub_info = f"Categoria: {item.get('categoria', 'Geral')}  |  Estoque: {item.get('estoque_min', 0)} min / {item.get('estoque_max', 0)} max"
            
            # Frame para textos (esquerda)
            txt_frame = ctk.CTkFrame(f, fg_color="transparent")
            txt_frame.pack(side="left", padx=15, pady=10)
            
            ctk.CTkLabel(txt_frame, text=info, font=("Arial", 13, "bold"), text_color="white").pack(anchor="w")
            ctk.CTkLabel(txt_frame, text=sub_info, font=("Arial", 11), text_color="#D4AF37").pack(anchor="w")

            # --- BOTÕES DE AÇÃO (Direita) ---
            btn_container = ctk.CTkFrame(f, fg_color="transparent")
            btn_container.pack(side="right", padx=10)

            # Botão Editar (Azul claro/Cinza)
            ctk.CTkButton(btn_container, text="✏️", width=40, fg_color="#555", 
                          command=lambda p=item: self.controller.carregar_produto_para_edicao(p)).pack(side="left", padx=5)
            
            # Botão Excluir (Vinho igual ao Gestão Caixa)
            ctk.CTkButton(btn_container, text="🗑️", width=40, fg_color="#6C3940", 
                          command=lambda p=item: self.controller.solicitar_exclusao_produto(p)).pack(side="left", padx=5)