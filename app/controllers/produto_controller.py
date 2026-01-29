import sqlite3
from tkinter import messagebox
import customtkinter as ctk
import math
import random

# Tenta importar a View de Grade, se não existir, usa fallback
try:
    from app.views.components.grade_produtos_view import GradeProdutosView
except ImportError:
    GradeProdutosView = None

class ProdutoController:

    def __init__(self, main_controller):
        self.main = main_controller
        self.view = main_controller.view
        if hasattr(main_controller, 'caixa_model'):
            self.db = main_controller.caixa_model.db
        else:
            self.db = main_controller.db

    # --- MÉTODOS DE BUSCA E PDV ---
    
    def executar_busca_pdv(self, event=None):
        pagina_pdv = getattr(self.view, 'pagina_pdv', None)
        if not pagina_pdv: return
        
        termo = pagina_pdv.ent_busca_pdv.get().strip()
        if not termo: return

        # 1. TENTA BUSCA NORMAL (Por código de barras ou Nome)
        produto = self.buscar_por_codigo_ou_nome(termo)
        
        if produto:
            # Detecta se o produto encontrado é de balança
            eh_balanca = bool(produto.get('codigo_balanca'))
            
            self.main.venda_ctrl.adicionar_item_ao_carrinho(
                nome=produto['nome'], 
                qtd=1.0, 
                preco_unit=produto['preco'],
                produto_id=produto.get('id'),
                is_balanca=eh_balanca
            )
            self._limpar_e_focar_busca(pagina_pdv)
            return

        # 2. LÓGICA DE ETIQUETA DE BALANÇA (Código 2...)
        if termo.startswith('2') and len(termo) >= 13:
            id_extraido, valor_total = self.main.balanca_model.extrair_dados_etiqueta(termo)
            if id_extraido:
                produto_balanca = self.buscar_por_codigo_balanca(id_extraido)
                if produto_balanca:
                    preco_kg = float(produto_balanca['preco'])
                    peso_calculado = valor_total / preco_kg if preco_kg > 0 else 0
                    
                    self.main.venda_ctrl.adicionar_item_ao_carrinho(
                        nome=produto_balanca['nome'], 
                        qtd=round(peso_calculado, 3), 
                        preco_unit=preco_kg,
                        produto_id=produto_balanca.get('id'), 
                        is_balanca=True
                    )
                    self._limpar_e_focar_busca(pagina_pdv)
                    return

        messagebox.showwarning("Aviso", f"Produto '{termo}' não encontrado.")
        self._limpar_e_focar_busca(pagina_pdv)

    def _limpar_e_focar_busca(self, pagina_pdv):
        pagina_pdv.ent_busca_pdv.delete(0, 'end')
        pagina_pdv.ent_busca_pdv.focus()

    def buscar_por_codigo_ou_nome(self, termo):
        try:
            query = "SELECT * FROM produtos WHERE codigo_barras = ?"
            res = self.db.fetch_all(query, (termo,))
            if not res:
                query = "SELECT * FROM produtos WHERE nome LIKE ? LIMIT 1"
                res = self.db.fetch_all(query, (f'%{termo}%',))
            return res[0] if res else None
        except Exception:
            return None

    def buscar_por_codigo_balanca(self, codigo_interno):
        try:
            # Garante que o código tenha 5 dígitos (ex: "01010")
            cod_str = str(codigo_interno).strip().zfill(5) 
            
            # Busca no banco de dados pelo campo 'codigo_balanca'
            query = "SELECT * FROM produtos WHERE codigo_balanca = ?"
            res = self.db.fetch_all(query, (cod_str,))
            
            # Se não achar com zeros, tenta sem os zeros (ex: "1010")
            if not res:
                id_limpo = str(int(cod_str))
                res = self.db.fetch_all(query, (id_limpo,))
                
            return res[0] if res else None
        except Exception as e:
            print(f"Erro na busca de balança: {e}")
            return None

    # --- GESTÃO E LISTAGEM ---

    def listar_produtos_atalho(self):
        try:
            # Lista produtos marcados para aparecer no atalho
            query = "SELECT * FROM produtos WHERE exibir_atalho = 1 OR exibir_atalho = 'true'"
            res = self.db.fetch_all(query)
            
            # Se não houver nenhum configurado, traz os primeiros 30 para não ficar vazio
            if not res:
                res = self.db.fetch_all("SELECT * FROM produtos LIMIT 30")
            return res
        except Exception as e:
            print(f"Erro ao listar: {e}")
            return []

    # =========================================================
    # CORREÇÃO AQUI: ADICIONADO O MÉTODO QUE FALTAVA
    # =========================================================
    def renderizar_botoes_produtos_modal(self, tabview, callback):
        """
        Método chamado pelo ComandaController (Modal).
        Redireciona para a renderização da grade.
        """
        self.renderizar_grade(tabview, callback)

    def renderizar_grade(self, tabview, callback_item):
        """
        Delega a renderização visual para o componente especializado.
        """
        # 1. Busca os dados
        produtos = self.listar_produtos_atalho()
        
        if not produtos:
            return

        # 2. Verifica se a classe de View existe
        if GradeProdutosView:
            visualizador = GradeProdutosView(tabview)
            visualizador.renderizar(produtos, callback_item)
        else:
            # Fallback caso a classe GradeProdutosView não tenha sido importada corretamente
            self._renderizar_grade_manual_fallback(tabview, produtos, callback_item)

    def _renderizar_grade_manual_fallback(self, parent, produtos, callback):
        """Método de segurança caso a View externa falhe"""
        for widget in parent.winfo_children():
            widget.destroy()
            
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        for i, prod in enumerate(produtos):
            self._criar_botao_produto(scroll, prod, i, callback)

    def _criar_botao_produto(self, parent, prod, index, callback):
        # Lógica de Grid (4 colunas)
        row = index // 4
        col = index % 4
        
        texto_btn = f"{prod['nome']}\nR$ {prod['preco']:.2f}"
        
        # Cores (Destaque para balança)
        cor_btn = "#2B2B2B" 
        if prod.get('codigo_balanca'):
            cor_btn = "#3b4a5a"

        btn = ctk.CTkButton(
            parent, 
            text=texto_btn,
            width=100,
            height=80,
            fg_color=cor_btn, 
            font=("Arial", 12, "bold"),
            # Passa o produto inteiro para o callback
            command=lambda p=prod: callback(p)
        )
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

    def cadastrar_produto(self, dados):
        if not dados.get('nome') or float(dados.get('preco_venda', 0)) <= 0:
            return False, "Nome ou Preço Inválidos"
        sucesso = self.db.salvar_produto(dados)
        return sucesso, "Produto salvo!" if sucesso else "Erro ao salvar no banco"

    def excluir(self, codigo):
        try:
            conn = self.db.conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produtos WHERE codigo_barras = ?", (codigo,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao excluir: {e}")
            return False

# --- FUNÇÃO DE UTILIDADE (FORA DA CLASSE) ---
def gerar_ean13_cadastro(id_referencia=None):
    """
    Gera um código EAN-13 válido.
    """
    prefixo = "20"
    
    if id_referencia:
        id_limpo = str(id_referencia).strip()
        corpo = prefixo + id_limpo.zfill(10)[-10:]
    else:
        corpo = prefixo + "".join([str(random.randint(0, 9)) for _ in range(10)])
    
    soma = 0
    for i, digito in enumerate(corpo):
        num = int(digito)
        if i % 2 == 0:
            soma += num * 1  
        else:
            soma += num * 3  
    
    digito_verificador = (10 - (soma % 10)) % 10
    return corpo + str(digito_verificador)