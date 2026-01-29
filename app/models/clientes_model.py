from .database import DatabaseManager

class ClientesModel:
    def __init__(self, db_manager=None):
        # Se não passarmos um manager, ele cria um (flexibilidade)
        if db_manager:
            self.db = db_manager
        else:
            from .database import DatabaseManager
            self.db = DatabaseManager()

    def salvar_cliente(self, dados):
        """Salva ou atualiza cliente, incluindo configurações de limite de crédito."""
        conn = self.db.conectar()
        cursor = conn.cursor()
        
        documento = dados.get('documento')
        nome_razao = dados.get('nome_razao') or dados.get('nome') or dados.get('razao')
        tipo = dados.get('tipo', 'F')
        limite = dados.get('limite_credito', 0.0)
        
        try:
            # Note que adicionamos limite_credito tanto no INSERT quanto no UPDATE
            query = """
                INSERT INTO clientes (
                    tipo, nome_razao, apelido_fantasia, documento, 
                    ie_rg, telefone, email, endereco, limite_credito
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(documento) DO UPDATE SET
                    nome_razao=excluded.nome_razao,
                    apelido_fantasia=excluded.apelido_fantasia,
                    ie_rg=excluded.ie_rg,
                    telefone=excluded.telefone,
                    email=excluded.email,
                    endereco=excluded.endereco,
                    limite_credito=excluded.limite_credito
            """
            cursor.execute(query, (
                tipo, 
                nome_razao, 
                dados.get('apelido_fantasia') or dados.get('fantasia', ''), 
                documento, 
                dados.get('ie_rg') or dados.get('rg') or dados.get('ie'), 
                dados.get('telefone'), 
                dados.get('email'), 
                dados.get('endereco'),
                limite
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro no ClientesModel ao salvar: {e}")
            return False
        finally:
            conn.close()

    def buscar_por_id(self, cliente_id):
        """Busca um único cliente pelo ID (usado na validação de limite)."""
        query = "SELECT * FROM clientes WHERE id = ?"
        resultado = self.db.fetch_all(query, (cliente_id,))
        return resultado[0] if resultado else None

    def listar_clientes(self, busca=""):
        """Retorna clientes filtrando por Nome OU Documento."""
        if busca:
            query = "SELECT * FROM clientes WHERE nome_razao LIKE ? OR documento LIKE ?"
            termo = f'%{busca}%'
            return self.db.fetch_all(query, (termo, termo))
        else:
            query = "SELECT * FROM clientes ORDER BY nome_razao ASC"
            return self.db.fetch_all(query)
        

    def deletar(self, cliente_id):
        """Remove um cliente usando o método conectar() do DatabaseManager."""
        conexao = None
        try:
            # 1. Abre a conexão usando o seu método existente
            conexao = self.db.conectar()
            cursor = conexao.cursor()
            
            # 2. Executa o comando
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            
            # 3. Salva as alterações
            conexao.commit()
            return True
        except Exception as e:
            print(f"Erro ao deletar cliente no Model: {e}")
            return False
        finally:
            # 4. Sempre fecha a conexão para não travar o arquivo do banco
            if conexao:
                conexao.close()

    def buscar_resumo_financeiro(self, cliente_id):
        """Calcula os totais para os Cards Financeiros usando fetch_all"""
        query = """
        SELECT 
            IFNULL(SUM(valor_total), 0) as total_compras,
            IFNULL(SUM(CASE WHEN status != 'PAGO' AND data_vencimento >= DATE('now') 
                    THEN (valor_total - valor_pago) ELSE 0 END), 0) as a_vencer,
            IFNULL(SUM(CASE WHEN status != 'PAGO' AND data_vencimento < DATE('now') 
                    THEN (valor_total - valor_pago) ELSE 0 END), 0) as vencidas,
            IFNULL(SUM(valor_pago), 0) as total_pago
        FROM crediario
        WHERE cliente_id = ?
        """
        # Usando o seu método fetch_all
        resultado = self.db.fetch_all(query, (cliente_id,))
        
        if resultado:
            return resultado[0]
        
        return {"total_compras": 0, "a_vencer": 0, "vencidas": 0, "total_pago": 0}
    

    def buscar_movimentacoes_timeline(self, cliente_id):
        """Busca o histórico para a timeline usando fetch_all"""
        query = """
        SELECT 
            id,
            venda_id,
            strftime('%d/%m/%Y', data_criacao) as data,
            'VENDA A PRAZO' as acao,
            valor_total as valor,
            status,
            data_vencimento
        FROM crediario
        WHERE cliente_id = ?
        ORDER BY data_criacao DESC
        LIMIT 20
        """
        # Usando o seu método fetch_all
        return self.db.fetch_all(query, (cliente_id,))
    
    def buscar_contas_pendentes(self, cliente_id):
        # O COALESCE garante que não dê erro matemático se valor_pago for Null
        # 'VENDA' as acao resolve o erro de coluna inexistente
        query = """
            SELECT 
                id, 
                strftime('%d/%m/%Y', data_vencimento) as data_venc,
                'VENDA' as acao, 
                (valor_total - COALESCE(valor_pago, 0)) as saldo_restante
            FROM crediario 
            WHERE cliente_id = ? 
            AND status != 'PAGO' 
            ORDER BY data_vencimento ASC
        """
        return self.db.fetch_all(query, (cliente_id,))
    
    def quitar_contas_lote(self, lista_ids):
        """Recebe uma lista de IDs e marca todos como PAGO"""
        conn = self.db.conectar()
        cursor = conn.cursor()
        try:
            # Para cada ID na lista, marcamos como pago
            for id_conta in lista_ids:
                # Primeiro pegamos o valor total para preencher o valor_pago
                cursor.execute("SELECT valor_total FROM crediario WHERE id = ?", (id_conta,))
                row = cursor.fetchone()
                if row:
                    total = row[0]
                    cursor.execute("""
                        UPDATE crediario 
                        SET status = 'PAGO', valor_pago = ? 
                        WHERE id = ?
                    """, (total, id_conta))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao quitar lote: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def atualizar_pagamento_crediario(self, crediario_id, novo_valor, status):
        query = "UPDATE crediario SET valor_pago = ?, status = ? WHERE id = ?"
        # Como o DatabaseManager não tem um método 'execute_non_query', 
        # podemos usar o conectar() diretamente ou criar um método save no DB
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute(query, (novo_valor, status, crediario_id))
        conn.commit()
        conn.close()