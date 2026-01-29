from .database import DatabaseManager

class EmpresaModel:
    def __init__(self, db_manager=None):

        if db_manager:
            self.db = db_manager
        else:
            from .database import DatabaseManager
            self.db = DatabaseManager()
            
        self._inicializar_tabela()


    def _inicializar_tabela(self):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresa_dados (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome_fantasia TEXT, razao_social TEXT, cnpj TEXT,
                endereco TEXT, telefone TEXT, mensagem_rodape TEXT
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO empresa_dados (id) VALUES (1)")
        conn.commit()
        conn.close()

        
    def obter_dados(self):
        """Busca os dados da empresa. Se não existir, retorna um dicionário vazio."""
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM empresa_dados WHERE id = 1")
        colunas = [d[0] for d in cursor.description]
        linha = cursor.fetchone()
        conn.close()
        
        if linha:
            return dict(zip(colunas, linha))
        return {}

    def salvar_dados(self, dados):
        """Faz o UPDATE dos dados no ID 1."""
        conn = self.db.conectar()
        cursor = conn.cursor()
        
        query = """
            UPDATE empresa_dados SET 
            nome_fantasia = ?, razao_social = ?, cnpj = ?, 
            endereco = ?, telefone = ?, mensagem_rodape = ?
            WHERE id = 1
        """
        valores = (
            dados.get('nome_fantasia'), dados.get('razao_social'),
            dados.get('cnpj'), dados.get('endereco'),
            dados.get('telefone'), dados.get('mensagem_rodape')
        )
        
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
        return True