import customtkinter as ctk
from tkinter import messagebox

class CadastroProdutoView(ctk.CTkFrame):
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, **kwargs)
        self.controller = controller
        self.configure(fg_color="transparent")
        
        # Título da Tela
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(header, text="CADASTRO E GESTÃO DE PRODUTOS", 
                     font=("Segoe UI", 24, "bold"), text_color="#D4AF37").pack(side="left")

        # Container com Scroll para caber todos os campos
        self.scroll_canvas = ctk.CTkScrollableFrame(self, fg_color="#6C3940", border_width=2, border_color="#D4AF37")
        self.scroll_canvas.pack(fill="both", expand=True, padx=20, pady=10)

        # --- SEÇÃO 1: IDENTIFICAÇÃO ---
        self._criar_subtitulo(self.scroll_canvas, "Identificação e Tipo")
        
        self.ent_nome = self._add_entry(self.scroll_canvas, "Descrição/Nome:", "Ex: Arroz Tipo 1 5kg")
        self.cb_tipo = self._add_combo(self.scroll_canvas, "Tipo de Item:", ["Produto", "Kit", "Serviço"])
        self.cb_unidade = self._add_combo(self.scroll_canvas, "Unidade:", ["UND", "KG", "LITRO", "CAIXA"])
        
        # Categoria com botão de adicionar
        frame_cat = self._criar_linha_dupla(self.scroll_canvas)
        self.cb_categoria = self._add_combo(frame_cat, "Categoria:", ["Geral", "Refrigerantes", "Refeições", "Espetinhos", "Cervejas", "Comidas"], side="left", expand=True)
        ctk.CTkButton(frame_cat, text="+", width=30, command=self._nova_categoria).pack(side="left", padx=5, pady=(20,0))

        # --- SEÇÃO 2: CÓDIGOS E BALANÇA ---
        self._criar_subtitulo(self.scroll_canvas, "Códigos e Balança")
        
        frame_cod = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_cod_interno = self._add_entry(frame_cod, "Código Interno:", "ID Automático", side="left")
        self.ent_cod_balanca = self._add_entry(frame_cod, "Código Balança:", "Ex: 101", side="left")
        
        frame_ean = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_ean = self._add_entry(frame_ean, "EAN-13:", "789...", side="left", expand=True)
        ctk.CTkButton(frame_ean, text="GERAR EAN", width=100, 
                      command=self._gerar_ean_automatico).pack(side="left", padx=5, pady=(20,0))

        # --- SEÇÃO 3: FINANCEIRO ---
        self._criar_subtitulo(self.scroll_canvas, "Preços e Lucro")
        
        frame_precos = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_custo = self._add_entry(frame_precos, "Preço de Custo (R$):", "0.00", side="left")
        self.ent_venda = self._add_entry(frame_precos, "Preço de Venda (R$):", "0.00", side="left")
        
        # Evento para calcular lucro em tempo real
        self.ent_custo.bind("<KeyRelease>", lambda e: self._calcular_lucro())
        self.ent_venda.bind("<KeyRelease>", lambda e: self._calcular_lucro())
        
        self.lbl_lucro = ctk.CTkLabel(self.scroll_canvas, text="Margem de Lucro: 0.00%", 
                                      font=("Segoe UI", 13, "italic"), text_color="#27AE60")
        self.lbl_lucro.pack(anchor="w", padx=15)

        # --- SEÇÃO 4: ESTOQUE E ATALHOS ---
        self._criar_subtitulo(self.scroll_canvas, "Controle e PDV")
        
        self.sw_estoque = ctk.CTkSwitch(self.scroll_canvas, text="Controlar Estoque")
        self.sw_estoque.pack(anchor="w", padx=15, pady=5)
        
        frame_est = self._criar_linha_dupla(self.scroll_canvas)
        self.ent_est_min = self._add_entry(frame_est, "Estoque Mínimo:", "0", side="left")
        self.ent_est_max = self._add_entry(frame_est, "Estoque Máximo:", "0", side="left")
        
        self.sw_atalho = ctk.CTkSwitch(self.scroll_canvas, text="Exibir como atalho no PDV", progress_color="#D4AF37")
        self.sw_atalho.pack(anchor="w", padx=15, pady=10)

        # --- SEÇÃO 5: FISCAL ---
        self._criar_subtitulo(self.scroll_canvas, "Dados Fiscais")
        
        self.ent_ncm = self._add_entry(self.scroll_canvas, "NCM:", "8 dígitos")
        self.ent_cest = self._add_entry(self.scroll_canvas, "CEST:", "Opcional")
        self.cb_origem = self._add_combo(self.scroll_canvas, "Origem:", ["0 - Nacional", "1 - Importada"])
        self.cb_classificacao = self._add_combo(self.scroll_canvas, "Classificação:", ["Alimentos", "Serviços", "Outros"])

        # --- RODAPÉ: BOTÕES DE AÇÃO ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=20)

        # Botões da Esquerda
        btn_listar = ctk.CTkButton(footer, text="LISTAR PRODUTOS", fg_color="#555", command=self.controller.listar_todos_produtos)
        btn_listar.pack(side="left", padx=5)
        
        

        # Botão da Direita (Salvar)
        btn_salvar = ctk.CTkButton(footer, text="SALVAR PRODUTO", fg_color="#27AE60", hover_color="#1e8449",
                                   font=("Segoe UI", 14, "bold"), width=200, height=40, command=self._coletar_e_salvar)
        btn_salvar.pack(side="right", padx=5)

    # --- FUNÇÕES AUXILIARES DE UI ---
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

    def _add_combo(self, master, label, values, side="top", expand=True):
        frame = ctk.CTkFrame(master, fg_color="transparent")
        frame.pack(side=side, fill="x", expand=expand, padx=10, pady=2)
        ctk.CTkLabel(frame, text=label, font=("Segoe UI", 14), text_color="white").pack(anchor="w")
        combo = ctk.CTkComboBox(frame, values=values,
                                border_color="#D4AF37", fg_color="#4C727D",
                                border_width=1, height=35)
        combo.pack(fill="x", pady=2)
        return combo

    def _criar_linha_dupla(self, master):
        f = ctk.CTkFrame(master, fg_color="transparent")
        f.pack(fill="x")
        return f

    # --- LÓGICA DE TELA ---
    def _calcular_lucro(self):
        try:
            custo = float(self.ent_custo.get() or 0)
            venda = float(self.ent_venda.get() or 0)
            if venda > 0 and custo > 0:
                margem = ((venda - custo) / venda) * 100
                self.lbl_lucro.configure(text=f"Margem de Lucro: {margem:.2f}%", text_color="#27AE60" if margem > 0 else "#E74C3C")
        except: pass

        # Dentro da classe CadastroProdutoView
    def _gerar_ean_automatico(self):
        # Pegamos o que estiver no campo 'Código Interno' ou 'Código Balança'
        id_referencia = self.ent_cod_interno.get() or self.ent_cod_balanca.get()
        
        # Chamamos a função (certifique-se de que o import está correto)
        from app.controllers.produto_controller import gerar_ean13_cadastro
        novo_ean = gerar_ean13_cadastro(id_referencia)
        
        # Atualizamos o campo EAN na tela
        self.ent_ean.delete(0, 'end')
        self.ent_ean.insert(0, novo_ean)

    def _nova_categoria(self):
        # Janela simples para nova categoria
        dialog = ctk.CTkInputDialog(text="Nome da Nova Categoria:", title="Nova Categoria")
        nova = dialog.get_input()
        if nova:
            vals = list(self.cb_categoria.cget("values"))
            vals.append(nova)
            self.cb_categoria.configure(values=vals)
            self.cb_categoria.set(nova)

    def _coletar_e_salvar(self):
        dados = {
            "nome": self.ent_nome.get(),
            "tipo": self.cb_tipo.get(),
            "unidade": self.cb_unidade.get(),
            "categoria": self.cb_categoria.get(),
            "codigo_interno": self.ent_cod_interno.get(),
            "codigo_balanca": self.ent_cod_balanca.get(),
            "preco_custo": self.ent_custo.get(),
            "preco_venda": self.ent_venda.get(),
            "estoque_min": self.ent_est_min.get(),
            "estoque_max": self.ent_est_max.get(),
            "controlar_estoque": self.sw_estoque.get(),
            "exibir_atalho": self.sw_atalho.get(),
            "ncm": self.ent_ncm.get(),
            "cest": self.ent_cest.get(),
            "origem": self.cb_origem.get(),
            "classificacao": self.cb_classificacao.get(),
            "ean": self.ent_ean.get()
        }
        self.controller.processar_salvamento_produto(dados)