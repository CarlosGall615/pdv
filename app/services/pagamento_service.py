


class PagamentoService:

    @staticmethod
    def calcular_troco(total, recebido):
        if recebido < total:
            return 0, False
        return (recebido - total), True



    @staticmethod
    def preparar_venda_db(carrinho, total, forma, usuario_id, comanda_id=None):
        return {
            "usuario_id": usuario_id,
            "itens": carrinho,
            "total": total,
            "forma_pagamento": forma,
            "comanda_origem": comanda_id
        }
    

