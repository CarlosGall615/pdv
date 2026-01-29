import customtkinter as ctk

class GradeProdutosView:
    """
    Componente reutilizável para renderizar a grelha de produtos
    dentro de um CTkTabview (abas).
    """

    def __init__(self, tabview):
        self.tabview = tabview
        # Dicionário para controlar a posição (linha/coluna) em cada aba
        # Ex: {'Bebidas': {'lin': 0, 'col': 0}, 'Geral': ...}
        self.controle_grid = {}

    def renderizar(self, lista_produtos, callback_clique):
        """
        Desenha os botões dos produtos organizados por abas/categorias.
        
        :param lista_produtos: Lista de dicionários com dados dos produtos
        :param callback_clique: Função a chamar ao clicar (deve aceitar nome, qtd, preco)
        """
        
        # Opcional: Limpar widgets antigos se necessário, 
        # mas cuidado para não apagar abas fixas se houver.
        # Aqui assumimos que é uma renderização incremental ou inicial.

        for prod in lista_produtos:
            # 1. Determina a Categoria
            cat = prod.get('categoria') or prod.get('cat') or "Geral"
            
            # 2. Prepara a Aba (cria se não existir)
            self._preparar_aba(cat)

            # 3. Desenha o Botão
            self._criar_botao(cat, prod, callback_clique)

    def _preparar_aba(self, nome_categoria):
        # Se a aba ainda não existe no dicionário de controle, inicializamos
        if nome_categoria not in self.controle_grid:
            
            # Verifica se a aba existe fisicamente no TabView
            try:
                self.tabview.tab(nome_categoria)
            except ValueError:
                self.tabview.add(nome_categoria)

            # Configura o grid da aba para ficar bonito (4 colunas)
            aba = self.tabview.tab(nome_categoria)
            aba.grid_columnconfigure((0, 1, 2, 3), weight=1)
            
            # Inicializa contador
            self.controle_grid[nome_categoria] = {"linha": 0, "coluna": 0}

    def _criar_botao(self, categoria, prod, callback):
        aba = self.tabview.tab(categoria)
        pos = self.controle_grid[categoria]

        # Texto e Cor
        texto_btn = f"{prod['nome']}\nR$ {prod.get('preco', 0):.2f}"
        
        # Identifica se é balança para cor e lógica
        tem_balanca = bool(prod.get('codigo_balanca'))
        cor_btn = "#3b4a5a" if tem_balanca else "#2B2B2B"

        btn = ctk.CTkButton(
            aba,
            text=texto_btn,
            width=100,
            height=80,
            font=("Arial", 12, "bold"),
            fg_color=cor_btn,
            # PASSAGEM DE DADOS COMPLETA:
            command=lambda p=prod: callback(
                nome=p['nome'], 
                qtd=1.0, 
                preco_unit=p.get('preco', 0),
                produto_id=p.get('id'), # Importante para agrupar
                is_balanca=tem_balanca  # Importante para NÃO agrupar peso
            )
        )
        
        btn.grid(row=pos['linha'], column=pos['coluna'], padx=5, pady=5, sticky="nsew")

        pos['coluna'] += 1
        if pos['coluna'] >= 4:
            pos['coluna'] = 0
            pos['linha'] += 1