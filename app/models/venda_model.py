import json
import os
from datetime import datetime

class VendaModel:

    def __init__(self, db_manager=None):


        if db_manager:
            self.db = db_manager
        else:
            from .database import DatabaseManager
            self.db = DatabaseManager()
            
        self.diretorio = "vendas_detalhadas"
        self.arquivo_index = "todas_vendas.json"
        
        # Cria uma pasta para organizar se não existir
        if not os.path.exists(self.diretorio):
            os.makedirs(self.diretorio)
            
        # Cria o arquivo de índice se não existir
        if not os.path.exists(self.arquivo_index):
            with open(self.arquivo_index, 'w', encoding="utf-8") as f:
                json.dump([], f)



    def registrar_venda(self, carrinho, total, forma_pagamento, usuario, sessao_id=None, cliente_id=None):
        """Salva a venda no SQL (Gestão) e no JSON (Backup/Cupom)"""
        agora = datetime.now()
        venda_id_formatado = agora.strftime("%Y%m%d%H%M%S")
        
        # --- 1. PERSISTÊNCIA NO BANCO DE DADOS (Coração do Fechamento) ---
        try:
            query = """
                INSERT INTO vendas (data_venda, cliente_id, total, usuario, sessao_id)
                VALUES (?, ?, ?, ?, ?)
            """
            # Usando o conectar direto para garantir a transação se necessário
            conn = self.db.conectar()
            cursor = conn.cursor()
            cursor.execute(query, (
                agora.strftime("%Y-%m-%d %H:%M:%S"),
                cliente_id,
                float(total),
                usuario,
                sessao_id
            ))
            id_sql = cursor.lastrowid # ID real do banco para vincular itens se quiser
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao salvar venda no SQL: {e}")

        # --- 2. PERSISTÊNCIA EM JSON (Seu backup atual) ---
        cupom_detalhado = {
            "venda_id": venda_id_formatado,
            "sql_id": id_sql if 'id_sql' in locals() else None,
            "data": agora.strftime("%d/%m/%Y"),
            "hora": agora.strftime("%H:%M:%S"),
            "vendedor": usuario,
            "itens": carrinho,
            "total": float(total),
            "forma_pagamento": forma_pagamento,
            "sessao_id": sessao_id
        }

        try:
            # Atualiza o índice geral
            with open(self.arquivo_index, 'r', encoding="utf-8") as f:
                vendas = json.load(f)
            vendas.append(cupom_detalhado)
            with open(self.arquivo_index, 'w', encoding="utf-8") as f:
                json.dump(vendas, f, indent=4)

            # Salva o arquivo individual
            caminho_cupom = os.path.join(self.diretorio, f"cupom_{venda_id_formatado}.json")
            with open(caminho_cupom, 'w', encoding="utf-8") as f:
                json.dump(cupom_detalhado, f, indent=4)
        except Exception as e:
            print(f"Erro ao salvar JSON: {e}")

        return venda_id_formatado



    def buscar_venda_por_id(self, venda_id):

        """Busca um cupom específico pelo ID."""
        caminho = os.path.join(self.diretorio, f"cupom_{venda_id}.json")
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding="utf-8") as f:
                return json.load(f)
        return None
    

    def buscar_vendas_por_periodo(self, periodo):
        """Filtra as vendas do arquivo JSON com base no período: Dia, Semana ou Mês."""
        try:
            if not os.path.exists(self.arquivo_index):
                return []

            with open(self.arquivo_index, 'r', encoding="utf-8") as f:
                todas_vendas = json.load(f)

            agora = datetime.now()
            vendas_filtradas = []

            for venda in todas_vendas:
                # Converte a string de data do JSON para objeto datetime para comparar
                # Formato no seu JSON: "27/10/2023"
                data_venda = datetime.strptime(venda['data'], "%d/%m/%Y")
                
                diferenca_dias = (agora - data_venda).days

                if periodo == "Dia":
                    if data_venda.date() == agora.date():
                        vendas_filtradas.append(venda)
                
                elif periodo == "Semana":
                    if diferenca_dias <= 7:
                        vendas_filtradas.append(venda)
                
                elif periodo == "Mês":
                    if diferenca_dias <= 30:
                        vendas_filtradas.append(venda)

            return vendas_filtradas

        except Exception as e:
            print(f"Erro ao filtrar vendas por período: {e}")
            return []
    

    def obter_extrato_fechamento(self, sessao_id):
        """Busca todas as vendas vinculadas à sessão atual para o fechamento."""
        query = """
            SELECT 
                v.id, 
                strftime('%H:%M', v.data_venda) as hora, 
                v.total, 
                IFNULL(c.nome_razao, 'CONSUMIDOR') as cliente
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE v.sessao_id = ?
            ORDER BY v.data_venda DESC
        """
        return self.db.fetch_all(query, (sessao_id,))