import sqlite3

class DatabaseManager:

    def __init__(self, db_name="sistema_vendas.db"):
        self.db_name = db_name
        self.criar_tabelas()
        self.corrigir_banco_obs()
        


    def conectar(self):
        return sqlite3.connect(self.db_name)



    def criar_tabelas(self):
        conn = self.conectar()
        cursor = conn.cursor()

        # 1. Tabela de Produtos Completa (Preparada para o Fiscal)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                categoria TEXT,
                exibir_atalho INTEGER DEFAULT 0,
                cor_botao TEXT DEFAULT "#4C727D",
                tipo TEXT DEFAULT 'Produto',
                unidade TEXT DEFAULT 'UND',
                codigo_interno TEXT,
                codigo_balanca TEXT,
                preco_custo REAL DEFAULT 0,
                estoque_min REAL DEFAULT 0,
                estoque_max REAL DEFAULT 0,
                controlar_estoque INTEGER DEFAULT 0,
                ncm TEXT,
                cest TEXT,
                origem TEXT,
                classificacao TEXT
            )
        ''')

        # --- LOGICA PARA ADICIONAR COLUNAS EM BANCOS JÁ EXISTENTES ---
        # Se você já tinha o banco e ele só tinha 5 colunas, esse código abaixo
        # adiciona as novas sem apagar seus dados antigos.
        colunas_novas = [
            ('tipo', 'TEXT DEFAULT "Produto"'),
            ('unidade', 'TEXT DEFAULT "UND"'),
            ('codigo_interno', 'TEXT'),
            ('codigo_balanca', 'TEXT'),
            ('preco_custo', 'REAL DEFAULT 0'),
            ('estoque_min', 'REAL DEFAULT 0'),
            ('estoque_max', 'REAL DEFAULT 0'),
            ('controlar_estoque', 'INTEGER DEFAULT 0'),
            ('ncm', 'TEXT'),
            ('cest', 'TEXT'),
            ('origem', 'TEXT'),
            ('classificacao', 'TEXT')
        ]

        for nome_col, tipo_col in colunas_novas:
            try:
                cursor.execute(f"ALTER TABLE produtos ADD COLUMN {nome_col} {tipo_col}")
            except sqlite3.OperationalError:
                pass # Se a coluna já existir, ele ignora e vai para a próxima

        # 2. Tabela de Configurações (Mantida)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome_fantasia TEXT,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                mensagem_cupom TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empresa_dados (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome_fantasia TEXT,
                razao_social TEXT,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                mensagem_rodape TEXT
            )
        ''')
        cursor.execute("INSERT OR IGNORE INTO empresa_dados (id) VALUES (1)")
        

        # --- TABELA CLIENTES (Mova para cá) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                nome_razao TEXT NOT NULL,
                apelido_fantasia TEXT,
                documento TEXT UNIQUE NOT NULL,
                ie_rg TEXT,
                telefone TEXT,
                email TEXT,
                endereco TEXT,
                limite_credito REAL DEFAULT 0.0,
                saldo_devedor REAL DEFAULT 0.0,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de Vendas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cliente_id INTEGER,
                sessao_id INTEGER,         -- Faltava esta coluna
                forma_pagamento TEXT,      -- Faltava esta coluna
                total REAL NOT NULL,
                usuario TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sessao_id INTEGER,
                tipo TEXT, -- 'REFORÇO' ou 'SANGRIA'
                valor REAL NOT NULL,
                motivo TEXT,
                usuario TEXT,
                hora TEXT,
                data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sessao_id) REFERENCES caixa_sessoes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER,
                produto_id INTEGER,
                nome_produto TEXT,
                quantidade REAL,
                preco_unitario REAL,
                total_item REAL,
                FOREIGN KEY (venda_id) REFERENCES vendas (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crediario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                venda_id INTEGER, -- Vincula à venda que gerou o débito
                valor_total REAL NOT NULL,
                valor_pago REAL DEFAULT 0.0,
                status TEXT DEFAULT 'PENDENTE', -- 'PENDENTE', 'PAGO', 'PARCIAL'
                data_vencimento DATE,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)       
        # No seu DatabaseManager.criar_tabelas() adicione:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caixa_sessoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_fechamento TIMESTAMP,
                valor_inicial REAL NOT NULL,
                valor_final REAL,
                status TEXT DEFAULT 'ABERTO' -- 'ABERTO' ou 'FECHADO'
            )
        """)
        # ... (suas tabelas de produtos, empresa e clientes continuam iguais acima) ...

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comandas (
                id TEXT PRIMARY KEY,
                categoria TEXT DEFAULT 'BALCÃO',
                status TEXT DEFAULT 'ABERTO',
                cliente_id INTEGER,
                cliente_nome_temp TEXT,
                endereco_entrega TEXT,
                data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL DEFAULT 0.0,
                usuario TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        # 2. Adição de colunas novas (Modo seguro para não dar erro se já existirem)
        colunas_novas = [
            ("telefone_temp", "TEXT"),
            ("troco_para", "REAL DEFAULT 0"),
            ("forma_pagamento_entrega", "TEXT")
        ]

        for nome_col, tipo_col in colunas_novas:
            try:
                cursor.execute(f"ALTER TABLE comandas ADD COLUMN {nome_col} {tipo_col}")
            except:
                # Se a coluna já existir, o SQLite lançará um erro que ignoramos aqui
                pass

        # 2. TABELA DE ITENS DA COMANDA (O que o cliente está a consumir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comandas_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comanda_id TEXT,
                produto_id INTEGER,
                nome_produto TEXT,
                observacao TEXT DEFAULT '',
                quantidade REAL,
                preco_unitario REAL,
                total_item REAL,
                FOREIGN KEY (comanda_id) REFERENCES comandas (id),
                FOREIGN KEY (produto_id) REFERENCES produtos (id)
            )
        """)


        conn.commit()
        conn.close()
        print("BANCO DE DADOS: Tabelas e colunas atualizadas com sucesso(database).")

    def atualizar_estrutura_comandas(self):
        conn = self.conectar()
        cursor = conn.cursor()
        colunas = [
            ("cliente_nome_temp", "TEXT"),
            ("endereco_entrega", "TEXT"),
            ("telefone_temp", "TEXT"),
            ("troco_para", "REAL"),
            ("forma_pagamento_entrega", "TEXT")
        ]
        for nome, tipo in colunas:
            try:
                cursor.execute(f"ALTER TABLE comandas ADD COLUMN {nome} {tipo}")
            except:
                pass # Coluna já existe
        conn.commit()
        conn.close()

    def salvar_produto(self, dados):
        """Insere ou Atualiza o produto com todos os campos novos"""
        conn = self.conectar()
        cursor = conn.cursor()
        try:
            # Mapeamos o dicionário que vem da View para as colunas do Banco
            query = '''
                INSERT OR REPLACE INTO produtos (
                    codigo_barras, nome, preco, categoria, exibir_atalho,
                    tipo, unidade, codigo_interno, codigo_balanca, preco_custo,
                    estoque_min, estoque_max, controlar_estoque, ncm, cest,
                    origem, classificacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            valores = (
                dados.get('ean'), dados.get('nome'), dados.get('preco_venda'),
                dados.get('categoria'), dados.get('exibir_atalho'),
                dados.get('tipo'), dados.get('unidade'), dados.get('codigo_interno'),
                dados.get('codigo_balanca'), dados.get('preco_custo'),
                dados.get('estoque_min'), dados.get('estoque_max'),
                dados.get('controlar_estoque'), dados.get('ncm'),
                dados.get('cest'), dados.get('origem'), dados.get('classificacao')
            )

            cursor.execute(query, valores)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao salvar no Banco: {e}")
            return False
        finally:
            conn.close()



    def buscar_produtos_atalho(self):
        """Busca apenas produtos marcados para aparecer no PDV"""
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE exibir_atalho = 1")
        colunas = [desc[0] for desc in cursor.description]
        produtos = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        conn.close()
        return produtos



    def fetch_all(self, query, params=()):
        """Executa uma query e retorna os dados como uma lista de dicionários"""
        conn = self.conectar() # Abre a conexão
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            colunas = [desc[0] for desc in cursor.description]
            resultado = [dict(zip(colunas, row)) for row in cursor.fetchall()]
            return resultado
        finally:
            conn.close() # Fecha sempre para não travar o banco



    def execute(self, query, params=()):
        """Executa comandos de alteração (INSERT, UPDATE, DELETE) e salva as mudanças"""
        conn = self.conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"ERRO DE BANCO (execute): {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

            

    def buscar_produto_por_codigo(self, codigo):
        """Busca um produto específico pelo código de barras EAN-13"""
        conn = self.conectar()
        # Configuramos para retornar como um dicionário facilitando o uso no Controller
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        try:
            # Buscamos pelo campo codigo_barras
            cursor.execute("SELECT * FROM produtos WHERE codigo_barras = ?", (codigo,))
            row = cursor.fetchone()
            
            if row:
                return dict(row) # Converte a linha do banco em um dicionário Python
            return None
        except sqlite3.Error as e:
            print(f"Erro ao buscar produto: {e}")
            return None
        finally:
            conn.close()



    def buscar_produto_por_nome(self, nome_parcial):
        """Busca um produto pelo nome usando busca aproximada"""
        conn = self.conectar()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            # O '%' serve para buscar qualquer texto antes ou depois do que foi digitado
            # Ex: 'CERV' encontra 'CERVEJA AMSTEL' e 'CERVEJA SKOL'
            cursor.execute("SELECT * FROM produtos WHERE nome LIKE ? LIMIT 1", (f'%{nome_parcial}%',))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
        finally:
            conn.close()


    def criar_tabela_empresa(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresa_dados (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                nome_fantasia TEXT,
                razao_social TEXT,
                cnpj TEXT,
                endereco TEXT,
                telefone TEXT,
                mensagem_rodape TEXT
            )
        """)
        # Insere uma linha vazia se não existir, para usarmos sempre UPDATE depois
        cursor.execute("INSERT OR IGNORE INTO empresa_dados (id) VALUES (1)")
        self.conn.commit()      

    # --- NOVOS MÉTODOS PARA COMANDAS ---

    def salvar_nova_comanda(self, id_comanda, categoria):
        """Cria uma comanda vazia no banco"""
        query = "INSERT OR IGNORE INTO comandas (id, categoria, status, total) VALUES (?, ?, 'ABERTO', 0.0)"
        return self.execute(query, (id_comanda, categoria))

    def atualizar_status_comanda(self, id_comanda, novo_status):
        """Muda o status (Ex: de 'ABERTO' para 'EM PREPARO')"""
        query = "UPDATE comandas SET status = ? WHERE id = ?"
        return self.execute(query, (novo_status.upper(), id_comanda))

    def buscar_comandas_ativas(self):
        """Retorna todas as comandas que não foram finalizadas ou canceladas"""
        query = "SELECT * FROM comandas WHERE status NOT IN ('FINALIZADO', 'CANCELADO')"
        return self.fetch_all(query)
    
    def fetch_one(self, query, params=()):
        """Retorna um único dicionário ou None"""
        conn = self.conectar()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            conn.close()

    def corrigir_banco_obs(self):
        """Método robusto para adicionar a coluna caso não exista"""
        conn = self.conectar()
        cursor = conn.cursor()
        try:
            # Tenta adicionar a coluna
            cursor.execute("ALTER TABLE comandas_itens ADD COLUMN observacao TEXT DEFAULT ''")
            conn.commit()
            print("BANCO DE DADOS: Coluna 'observacao' sincronizada com sucesso.")
        except sqlite3.OperationalError as e:
            # Se o erro for que a coluna já existe, apenas ignoramos silenciosamente
            if "duplicate column name" in str(e).lower():
                pass 
            else:
                print(f"AVISO AO ATUALIZAR TABELA: {e}")
        finally:
            conn.close()