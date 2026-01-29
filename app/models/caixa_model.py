from datetime import datetime, timedelta



class CaixaModel:

    def __init__(self, db_manager=None):
        
        from .database import DatabaseManager
        self.db = db_manager if db_manager else DatabaseManager()
        # Status e Saldo
        self.caixa_aberto = False
        self.sessao_id = None
        self.saldo_inicial = 0.0
        self.produtos = self.carregar_produtos_do_banco()
        # Listas de armazenamento em memória
        self.vendas_dia = []
        self.movimentacoes = [] # Armazena Sangrias e Reforços
        
    # ==========================================================
    # GESTÃO DE STATUS
    # ==========================================================
    
    def carregar_produtos_do_banco(self):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos")
        # Transforma as linhas do banco em dicionários para o seu sistema
        colunas = [description[0] for description in cursor.description]
        produtos = [dict(zip(colunas, row)) for row in cursor.fetchall()]
        conn.close()
        return produtos
    
    

    def verificar_status_caixa(self):
        """Verifica se existe sessão aberta e retorna True/False"""
        query = "SELECT id FROM caixa_sessoes WHERE status = 'ABERTO' ORDER BY id DESC LIMIT 1"
        res = self.db.fetch_all(query)
        
        if res:
            self.sessao_id = res[0]['id']
            self.caixa_aberto = True  # <--- ADICIONE ESTA LINHA AQUI!
            return True
        
        self.sessao_id = None
        self.caixa_aberto = False # <--- GARANTA QUE ESTEJA FALSE AQUI
        return False

   
   
    def abrir_caixa(self, valor_inicial):
        try:
            # 1. Segurança: Fecha qualquer sessão que tenha ficado aberta por erro
            self.db.execute("UPDATE caixa_sessoes SET status = 'FECHADO' WHERE status = 'ABERTO'")

            # 2. Abre a nova sessão usando o nome correto da coluna: valor_inicial
            query = """
                INSERT INTO caixa_sessoes (data_abertura, valor_inicial, status) 
                VALUES (CURRENT_TIMESTAMP, ?, 'ABERTO')
            """
            self.db.execute(query, (valor_inicial,))
            
            # 3. Recupera o ID gerado para esta nova sessão
            res = self.db.fetch_all("SELECT last_insert_rowid() as id")
            if res:
                self.sessao_id = res[0]['id']
                self.caixa_aberto = True
                return True
            return False

        except Exception as e:
            print(f"Erro ao abrir caixa no Model: {e}")
            return False

   
   
    def fechar_caixa(self, valor_final):
        """Atualiza o status da sessão e grava o valor final real em dinheiro/total"""
        try:
            query = """
                UPDATE caixa_sessoes 
                SET status = 'FECHADO', 
                    data_fechamento = datetime('now', 'localtime'),
                    valor_final = ? 
                WHERE id = ?
            """
            self.db.execute(query, (valor_final, self.sessao_id))
            return True
        except Exception as e:
            print(f"Erro ao gravar valor_final no banco: {e}")
            return False


    def _gerar_resumo_vazio(self):
        """Retorna um dicionário padrão com valores zerados"""
        return {
            'abertura': 0.0,
            'vendas_dinheiro': 0.0,
            'pix': 0.0,
            'cartao': 0.0,
            'outros': 0.0,
            'reforcos': 0.0,
            'sangrias': 0.0,
            'saldo_atual_dinheiro': 0.0,
            'faturamento_total': 0.0
        }
    # ==========================================================
    # LANÇAMENTOS (COM CADEADOS DE SEGURANÇA)
    # ==========================================================

    def registrar_venda(self, total, lista_pagamentos, itens=None, cliente_id=None):
        """
        Versão Corrigida: Garante a recuperação do sessao_id e sincroniza o status do caixa.
        """
        # 1. SINCRONIZAÇÃO FORÇADA: Se não tem ID, tenta buscar no banco agora mesmo
        if not getattr(self, 'sessao_id', None):
            self.verificar_status_caixa()

        # 2. VERIFICAÇÃO FINAL: Se após a busca ainda não tem ID, o caixa realmente está fechado
        if not self.sessao_id:
            print(f"ERRO: Tentativa de venda com caixa fechado! (Sessão ID não encontrada)")
            return False

        # Garante que a flag de memória esteja correta para o resto do sistema
        self.caixa_aberto = True

        # 3. Define a forma de pagamento principal para o resumo
        forma_principal = "Dinheiro"
        if lista_pagamentos and len(lista_pagamentos) > 0:
            # Pega o método do primeiro pagamento da lista
            forma_principal = lista_pagamentos[0].get('metodo', 'Dinheiro')

        conn = self.db.conectar()
        cursor = conn.cursor()
        
        try:
            # Iniciamos uma transação (Tudo ou Nada)
            cursor.execute("BEGIN TRANSACTION")

            # 4. Salva o CABEÇALHO da venda
            query_venda = """
                INSERT INTO vendas (cliente_id, total, usuario, sessao_id, forma_pagamento, data_venda) 
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
            """
            cursor.execute(query_venda, (
                cliente_id, 
                float(total), 
                "CAIXA 01", 
                self.sessao_id, 
                forma_principal
            ))
            
            venda_id = cursor.lastrowid

            # 5. Salva os ITENS da venda
            if itens:
                for item in itens:
                    # Suporte para diferentes nomes de chaves (preco vs preco_unit)
                    preco_un = item.get('preco_unit') or item.get('preco') or 0
                    qtd = item.get('qtd') or 0
                    p_id = item.get('id')
                    nome_prod = item.get('nome', 'Produto')

                    cursor.execute("""
                        INSERT INTO vendas_itens (venda_id, produto_id, nome_produto, quantidade, preco_unitario, total_item)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (venda_id, p_id, nome_prod, qtd, preco_un, round(qtd * preco_un, 2)))

                    # Baixa o estoque (Apenas se o produto tiver ID e controle ativado)
                    if p_id:
                        cursor.execute("""
                            UPDATE produtos SET estoque_max = estoque_max - ? 
                            WHERE id = ? AND controlar_estoque = 1
                        """, (qtd, p_id))

            # 6. Processa Crediário (Se houver esse método de pagamento)
            for pgto in lista_pagamentos:
                if (pgto['metodo'] == "Crediário" or pgto['metodo'] == "A Prazo") and cliente_id:
                    
                    # CÁLCULO DA DATA DE VENCIMENTO (30 DIAS)
                    data_vencimento = datetime.now() + timedelta(days=30)

                    # INSERÇÃO COMPLETA COM DATA E STATUS
                    cursor.execute("""
                        INSERT INTO crediario (cliente_id, venda_id, valor_total, data_vencimento, status)
                        VALUES (?, ?, ?, ?, 'PENDENTE')
                    """, (cliente_id, venda_id, pgto['valor'], data_vencimento))
                    
                    # Atualiza o saldo devedor na ficha do cliente
                    cursor.execute("""
                        UPDATE clientes SET saldo_devedor = saldo_devedor + ? WHERE id = ?
                    """, (pgto['valor'], cliente_id))

            # Finaliza a transação no banco
            conn.commit()
            
            # 7. Atualiza memória para a lista de vendas aparecer na hora na gestão
            nova_venda_memoria = {
                "id": venda_id,
                "hora": datetime.now().strftime("%H:%M"),
                "total": float(total),
                "tipo": forma_principal,
                "categoria": "VENDA"
            }
            if not hasattr(self, 'vendas_dia'): self.vendas_dia = []
            self.vendas_dia.append(nova_venda_memoria)
            
            print(f"SUCESSO: Venda #{venda_id} gravada na SESSÃO: {self.sessao_id}")
            return True

        except Exception as e:
            if conn: conn.rollback()
            print(f"ERRO CRÍTICO NO BANCO (registrar_venda): {e}")
            return False
        finally:
            if conn: conn.close()



    def lancar_movimentacao(self, tipo, valor, motivo, operador, sessao_id=None):
        """Regista sangrias ou reforços no banco de dados vinculados a uma sessão"""
        if not self.caixa_aberto and not sessao_id:
            return False

        # Se não foi passado ID, tenta usar o que está no model
        if not sessao_id:
            sessao_id = getattr(self, 'sessao_id', None)

        agora_hora = datetime.now().strftime("%H:%M")
        
        try:
            # 1. GRAVAÇÃO NO SQL (Obrigatório para persistência)
            query = """
                INSERT INTO movimentacoes_caixa (sessao_id, tipo, valor, motivo, usuario, hora)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            # Substitua pelo seu método de execução (ex: self.db.execute_query ou manual)
            conn = self.db.conectar()
            cursor = conn.cursor()
            cursor.execute(query, (sessao_id, tipo.upper(), float(valor), motivo, operador, agora_hora))
            conn.commit()
            conn.close()

            print(f"SQL: {tipo} de R$ {valor} gravado para Sessão ID: {sessao_id}")

            # 2. ATUALIZA MEMÓRIA (Para exibição imediata se necessário)
            nova_mov = {
                "tipo": tipo.upper(),
                "valor": float(valor),
                "motivo": motivo,
                "usuario": operador,
                "hora": agora_hora
            }
            self.movimentacoes.append(nova_mov)
            return True

        except Exception as e:
            print(f"ERRO AO GRAVAR MOVIMENTAÇÃO NO BANCO: {e}")
            return False

    # ==========================================================
    # CONSULTAS E RELATÓRIOS
    # ==========================================================

    def obter_resumo_caixa(self, sessao_id):
        try:
            if not sessao_id: return None

            # 1. BUSCA VALOR INICIAL (Para o Label de Abertura)
            res_sessao = self.db.fetch_all("SELECT valor_inicial FROM caixa_sessoes WHERE id = ?", (sessao_id,))
            abertura = float(res_sessao[0]['valor_inicial']) if res_sessao else 0.0

            # 2. BUSCA VENDAS
            query_vendas = "SELECT forma_pagamento, SUM(total) as total FROM vendas WHERE sessao_id = ? GROUP BY forma_pagamento"
            vendas_db = self.db.fetch_all(query_vendas, (sessao_id,))
            
            detalhado = {
                "Dinheiro": 0.0, "Pix": 0.0, "Crédito": 0.0, "Débito": 0.0,
                "Vale Refeição": 0.0, "Vale Alimentação": 0.0, "Crediário": 0.0
            }
            
            for v in vendas_db:
                metodo = v['forma_pagamento']
                if metodo in detalhado:
                    detalhado[metodo] = float(v['total'])

            # 3. MOVIMENTAÇÕES
            movs = self.db.fetch_all("SELECT tipo, SUM(valor) as total FROM movimentacoes_caixa WHERE sessao_id = ? GROUP BY tipo", (sessao_id,))
            reforcos = sum(float(m['total']) for m in movs if m['tipo'] == 'REFORÇO')
            sangrias = sum(float(m['total']) for m in movs if m['tipo'] == 'SANGRIA')

            # 4. CÁLCULO DO LABEL AMARELO (Saldo em Dinheiro na Gaveta)
            saldo_atual_dinheiro = abertura + detalhado["Dinheiro"] + reforcos - sangrias
            
            # FATURAMENTO TOTAL (Soma de tudo)
            faturamento_total = sum(detalhado.values())

            return {
                "abertura": abertura,                # <--- Restaura o Label Abertura
                "faturamento_total": faturamento_total,
                "saldo_atual_dinheiro": saldo_atual_dinheiro, # <--- Restaura o Label Amarelo
                "reforcos": reforcos,
                "sangrias": sangrias,
                "dinheiro": detalhado["Dinheiro"],
                "pix": detalhado["Pix"],
                "cartao": detalhado["Crédito"] + detalhado["Débito"],
                "outros": detalhado["Vale Refeição"] + detalhado["Vale Alimentação"] + detalhado["Crediário"],
                "detalhado": detalhado 
            }
        except Exception as e:
            print(f"Erro ao restaurar resumo: {e}")
            return None


    def obter_totais_por_metodo(self):
        totais = {
            "Dinheiro": 0.0, "Pix": 0.0, "Débito": 0.0,
            "Crédito": 0.0, "Vale Refeição": 0.0, "Vale Alimentação": 0.0
        }
        
        # Percorre cada venda do dia
        for v in self.vendas_dia:
            # Percorre cada pagamento dentro daquela venda
            for p in v['pagamentos']:
                metodo = p['metodo']
                valor = p['valor']
                if metodo in totais:
                    totais[metodo] += valor
        
        # Soma fundo de caixa e movimentações ao Dinheiro
        reforcos = sum(m['valor'] for m in self.movimentacoes if m['tipo'] == "REFORÇO")
        sangrias = sum(m['valor'] for m in self.movimentacoes if m['tipo'] == "SANGRIA")
        
        totais["Dinheiro"] += (self.saldo_inicial + reforcos - sangrias)
        
        return totais



    def remover_venda_do_banco(self, venda_id):
        """Exclusão de segurança (Estorno)"""
        self.vendas_dia = [v for v in self.vendas_dia if v['id'] != venda_id]
        return True
    


    def obter_vendas_dia(self, sessao_id):
        """Busca vendas e identifica explicitamente como VENDA"""
        query = """
            SELECT 
                id, 
                strftime('%H:%M', data_venda) as hora, 
                total AS valor, 
                forma_pagamento as tipo,
                'VENDA' as categoria,  -- <--- GARANTE O RÓTULO CORRETO
                '' as motivo,
                usuario
            FROM vendas 
            WHERE sessao_id = ?
        """
        return self.db.fetch_all(query, (sessao_id,))
    


    def obter_relatorio_fechamento(self, valores_informados):
        """
        valores_informados: dicionário vindo da View {'Dinheiro': 100.0, 'PIX': 50.0...}
        """
        totais_sistema = self.obter_totais_por_metodo()
        resumo_caixa = self.obter_resumo_caixa()
        
        relatorio = {
            "abertura": self.saldo_inicial,
            "vendas_por_metodo": totais_sistema,
            "movimentacoes": self.movimentacoes, # Lista de Sangrias/Reforços
            "fechamento_detalhado": [],
            "status_final": "OK"
        }

        # Cálculo de Sobra/Falta para cada método
        for metodo, valor_sistema in totais_sistema.items():
            # Se for dinheiro, o sistema considera: Abertura + Vendas + Reforços - Sangrias
            esperado = valor_sistema
            if metodo == "Dinheiro":
                esperado = resumo_caixa['saldo_atual_dinheiro']

            informado = valores_informados.get(metodo, 0.0)
            diferenca = informado - esperado
            
            relatorio["fechamento_detalhado"].append({
                "metodo": metodo,
                "esperado": esperado,
                "informado": informado,
                "diferenca": diferenca
            })

        return relatorio



    def obter_movimentacoes_dia(self, sessao_id):
        """Busca reforços/sangrias e mantém a sua categoria original"""
        query = """
            SELECT 
                id, 
                hora, 
                valor, 
                tipo,        -- Aqui virá 'REFORÇO' ou 'SANGRIA' do banco
                tipo as categoria, -- <--- USA O TIPO DO BANCO COMO CATEGORIA
                motivo, 
                usuario
            FROM movimentacoes_caixa 
            WHERE sessao_id = ?
        """
        return self.db.fetch_all(query, (sessao_id,))



    def validar_senha_gerente(self, usuario, senha):
        """
        Verifica se a senha digitada confere com a do gerente/administrador.
        Por enquanto, vamos usar uma senha mestre para teste.
        """
        SENHA_MESTRE = "123" # Você pode mudar isso depois
        return senha == SENHA_MESTRE

 
    
    def excluir_venda(self, venda_id):
        """Remove a venda e seus itens do banco de dados permanentemente"""
        if not venda_id:
            return False

        # 1. Primeiro removemos os itens da venda (Integridade)
        # 2. Depois removemos a venda principal
        try:
            # Usando o novo método que acabamos de criar no DatabaseManager
            self.db.execute("DELETE FROM vendas_itens WHERE venda_id = ?", (venda_id,))
            self.db.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
            
            print(f"SISTEMA: Venda ID {venda_id} excluída com sucesso.")
            return True
        except Exception as e:
            print(f"ERRO ao excluir venda: {e}")
            return False

    


    def obter_vendas_dia_db(self, sessao_id):
        """Busca vendas do banco vinculadas à sessão atual"""
        query = """
            SELECT id, strftime('%H:%M', data_venda) as hora, total, 'VENDA' as tipo 
            FROM vendas 
            WHERE sessao_id = ?
        """
        return self.db.fetch_all(query, (sessao_id,))

    def obter_movimentacoes_dia_db(self, sessao_id):
        """Busca sangrias e reforços do banco"""
        query = """
            SELECT id, hora, valor, tipo, motivo 
            FROM movimentacoes_caixa 
            WHERE sessao_id = ?
        """
        return self.db.fetch_all(query, (sessao_id,))
    
    
    

    def calcular_total_caixa(self, sessao_id):
        """Calcula o saldo final: Abertura + Vendas (Dinheiro) + Reforços - Sangrias"""
        try:
            # 1. Busca o valor de abertura
            res = self.db.fetch_all("SELECT valor_inicial FROM caixa_sessoes WHERE id = ?", (sessao_id,))
            abertura = res[0]['valor_inicial'] if res else 0.0

            # 2. Soma Vendas em Dinheiro (Cartão/Pix não entram no físico do caixa)
            vendas = self.db.fetch_all("SELECT SUM(total) as total FROM vendas WHERE sessao_id = ? AND forma_pagamento = 'Dinheiro'", (sessao_id,))
            total_vendas = vendas[0]['total'] if vendas[0]['total'] else 0.0

            # 3. Soma Reforços e subtrai Sangrias
            movs = self.db.fetch_all("SELECT tipo, SUM(valor) as total FROM movimentacoes_caixa WHERE sessao_id = ? GROUP BY tipo", (sessao_id,))
            reforcos = 0.0
            sangrias = 0.0
            for m in movs:
                if m['tipo'] == 'REFORÇO': reforcos = m['total']
                if m['tipo'] == 'SANGRIA': sangrias = m['total']

            return abertura + total_vendas + reforcos - sangrias
        except Exception as e:
            print(f"Erro ao calcular total: {e}")
            return 0.0
        

    def obter_sessao_ativa(self):
        """Busca apenas a sessão aberta mais recente"""
        try:
            # Usamos uma consulta simples que não bloqueia o banco
            query = "SELECT * FROM caixa_sessoes WHERE status = 'ABERTO' ORDER BY id DESC LIMIT 1"
            resultado = self.db.fetch_all(query)
            
            if resultado:
                # Se achou, atualiza o ID na memória e retorna
                self.sessao_id = resultado[0]['id']
                return resultado[0]
            
            # Se não achou, limpa a memória
            self.sessao_id = None
            return None
        except Exception as e:
            print(f"Erro ao buscar sessão: {e}")
            return None