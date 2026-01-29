# ARQUIVO: app/services/produto_service.py

from app.models.database import DatabaseManager

class ProdutoService:
    def __init__(self, db_manager=None):
        # Se receber um gerenciador de banco, usa ele. Se não, cria um novo.
        self.db = db_manager if db_manager else DatabaseManager()

    def buscar_por_codigo_ou_nome(self, termo):
        """
        Busca um produto pelo código de barras OU pelo nome.
        Retorna um dicionário do produto ou None.
        """
        termo = str(termo).strip()
        
        # 1. Tenta buscar por Código de Barras exato
        query_codigo = "SELECT * FROM produtos WHERE codigo_barras = ?"
        produto = self.db.fetch_one(query_codigo, (termo,))
        
        if produto:
            return produto

        # 2. Tenta buscar por Código Interno (ID)
        if termo.isdigit():
            query_id = "SELECT * FROM produtos WHERE id = ?"
            produto = self.db.fetch_one(query_id, (termo,))
            if produto:
                return produto

        # 3. Tenta buscar por Nome (contendo o termo)
        # O '%' serve para buscar partes do nome (ex: "cola" acha "Coca Cola")
        query_nome = "SELECT * FROM produtos WHERE nome LIKE ?"
        produto = self.db.fetch_one(query_nome, (f"%{termo}%",))
        
        return produto

    def listar_todos(self):
        return self.db.fetch_all("SELECT * FROM produtos")