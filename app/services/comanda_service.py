class ComandaService:

    def __init__(self):
        self.comandas_abertas = {}
        self.carrinho_atual = []
        self.comanda_em_edicao = None

   
   
    def carregar_carrinho(self, id_comanda):
        """Prepara o carrinho com os itens de uma comanda específica"""
        if id_comanda in self.comandas_abertas:
            self.comanda_em_edicao = id_comanda
            self.carrinho_atual = self.comandas_abertas[id_comanda]['itens'].copy()
            return self.carrinho_atual
        return []



    def salvar_carrinho_na_comanda(self):
        """Salva o que está no carrinho de volta para a comanda"""
        if self.comanda_em_edicao:
            id_id = self.comanda_em_edicao
            total = sum(item['total'] for item in self.carrinho_atual)
            self.comandas_abertas[id_id] = {
                'itens': self.carrinho_atual.copy(),
                'total': total,
                'status': 'aberta'
            }
            self.limpar_sessao()

  
  
    def limpar_sessao(self):
        self.carrinho_atual = []
        self.comanda_em_edicao = None


