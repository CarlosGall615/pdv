from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime
from collections import Counter
from app.views.popups.modal_identificacao_comanda import ModalIdentificacao

class ComandaController:
    def __init__(self, main_controller):
        self.main = main_controller
        self.db = main_controller.db 
        self.modal_comanda = None
        
        # --- AUTO-CORREÇÃO DO BANCO DE DADOS ---
        # Verifica se a tabela aceita duplicatas assim que inicia
        self.verificar_e_corrigir_tabela()

    def verificar_e_corrigir_tabela(self):
        """
        Verifica se a tabela comandas_itens tem a coluna 'id'.
        Se não tiver, recria a tabela para permitir itens duplicados.
        """
        try:
            # Verifica colunas da tabela
            colunas = self.db.fetch_all("PRAGMA table_info(comandas_itens)")
            tem_id = any(c['name'] == 'id' for c in colunas)
            
            if not tem_id:
                print("AVISO: Tabela comandas_itens antiga detectada. Iniciando migração para suportar duplicatas...")
                
                # 1. Renomeia a tabela atual
                self.db.execute("ALTER TABLE comandas_itens RENAME TO comandas_itens_old")
                
                # 2. Cria a nova tabela com ID (Primary Key)
                query_nova = """
                CREATE TABLE comandas_itens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comanda_id TEXT,
                    nome_produto TEXT,
                    quantidade REAL,
                    preco_unitario REAL,
                    total_item REAL,
                    observacao TEXT
                )
                """
                self.db.execute(query_nova)
                
                # 3. Copia os dados (agrupando para não perder info, ou copia direta)
                self.db.execute("""
                    INSERT INTO comandas_itens (comanda_id, nome_produto, quantidade, preco_unitario, total_item, observacao)
                    SELECT comanda_id, nome_produto, quantidade, preco_unitario, total_item, observacao 
                    FROM comandas_itens_old
                """)
                
                # 4. Remove a velha
                self.db.execute("DROP TABLE comandas_itens_old")
                
                if hasattr(self.db, 'conn'): self.db.conn.commit()
                print("SUCESSO: Tabela comandas_itens atualizada para suportar itens repetidos!")
                
        except Exception as e:
            print(f"Erro na verificação da tabela (pode ser ignorado se já estiver ok): {e}")

    # ============================================================
    # 1. GESTÃO DE PERSISTÊNCIA (BANCO DE DADOS)
    # ============================================================

    def atualizar_visual_comandas(self):
        try:
            query = "SELECT * FROM comandas WHERE UPPER(status) NOT IN ('CANCELADO', 'FINALIZADO')"
            comandas_db = self.db.fetch_all(query)
            
            comandas_dict = {}
            for c in comandas_db:
                id_c = c['id']
                comandas_dict[id_c] = {
                    "total": c['total'],
                    "status": c['status'],
                    "categoria": c.get('categoria', 'BALCÃO')
                }

            self.comandas_abertas = comandas_dict

            view_alvo = None
            if hasattr(self.main.view, 'view_comandas'):
                view_alvo = self.main.view.view_comandas
            elif hasattr(self.main, 'view_comandas'):
                view_alvo = self.main.view_comandas

            if view_alvo and view_alvo.winfo_exists():
                view_alvo.renderizar_comandas(comandas_dict)
                
        except Exception as e:
            print(f"Erro ao atualizar visual: {e}")

    def salvar_dados_comanda_direto(self, id_comanda, dados, janela_modal=None, imprimir=True):
        """
        Salva mantendo itens SEPARADOS (mesmo se iguais).
        """
        try:
            print(f"DEBUG: Iniciando salvamento da comanda {id_comanda}. Itens na memória: {len(dados['itens'])}")
            
            # Recalcula total
            total_real = sum(item['total'] for item in dados['itens'])
            dados['total'] = total_real

            # --- LÓGICA DE IMPRESSÃO (O que é novo?) ---
            itens_antigos = self.db.fetch_all(
                "SELECT nome_produto, observacao FROM comandas_itens WHERE comanda_id = ?", 
                (id_comanda,)
            )
            
            # Contador do que já existia: {('MARMITA', 'SEM CEBOLA'): 1, ('COCA', ''): 2}
            counter_antigos = Counter()
            for i in itens_antigos:
                chave = (str(i['nome_produto']).strip().upper(), str(i.get('observacao', '')).strip().upper())
                counter_antigos[chave] += 1

            counter_novos = Counter()
            lista_para_impressao = []

            # --- ATUALIZAÇÃO DO BANCO ---
            # Remove itens antigos
            self.db.execute("DELETE FROM comandas_itens WHERE comanda_id = ?", (id_comanda,))
            
            for item in dados['itens']:
                nome_upper = str(item['nome']).strip().upper()
                obs_upper = str(item.get('observacao', '')).strip().upper()
                
                # Controle de impressão
                chave = (nome_upper, obs_upper)
                counter_novos[chave] += 1
                
                if imprimir and dados['status'].upper() == "EM PREPARO":
                    if counter_novos[chave] > counter_antigos[chave]:
                        lista_para_impressao.append(item)

                # INSERÇÃO (Agora segura graças à correção da tabela)
                self.db.execute(
                    """INSERT INTO comandas_itens 
                       (comanda_id, nome_produto, quantidade, preco_unitario, total_item, observacao)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (id_comanda, nome_upper, item['qtd'], item['preco_unit'], item['total'], item.get('observacao', ''))
                )

            # Atualiza Cabeçalho
            self.db.execute(
                "UPDATE comandas SET total = ?, status = ?, categoria = ? WHERE id = ?",
                (dados['total'], dados['status'].upper(), dados['categoria'].upper(), id_comanda)
            )
            
            if hasattr(self.db, 'conn'): self.db.conn.commit()
            print(f"DEBUG: Comanda {id_comanda} salva com sucesso.")

            # --- IMPRESSÃO ---
            if lista_para_impressao:
                print(f"DEBUG: Enviando {len(lista_para_impressao)} itens novos para impressão.")
                if hasattr(self.main, 'impressao_service'):
                    for item_print in lista_para_impressao:
                        self.main.impressao_service.imprimir_item_avulso_comanda(id_comanda, item_print)

            # Atualiza Service (Memória)
            if hasattr(self.main, 'comanda_service'):
                self.main.comanda_service.comandas_abertas[id_comanda] = dados.copy()
                self.main.comanda_service.carregar_carrinho(id_comanda)

            if janela_modal and hasattr(janela_modal, 'winfo_exists') and janela_modal.winfo_exists():
                janela_modal.destroy()
            
            self.atualizar_visual_comandas()

        except Exception as e:
            print(f"Erro crítico ao salvar comanda: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Não foi possível salvar: {e}")

    # ============================================================
    # 2. FLUXO DE ENTRADA
    # ============================================================

    def nova_comanda(self, categoria=None):
        if not categoria:
            try:
                categoria = self.main.view.view_comandas.tabview.get().upper()
            except:
                categoria = "BALCÃO"

        dialog = ctk.CTkInputDialog(text=f"ID da nova entrada ({categoria}):", title="Nova Comanda")
        id_comanda = dialog.get_input()
        
        if id_comanda and id_comanda.strip():
            id_comanda = id_comanda.strip()
            
            c = self.db.fetch_one("SELECT id, status FROM comandas WHERE id = ?", (id_comanda,))
            if c:
                if str(c['status']).upper() not in ('CANCELADO', 'FINALIZADO'):
                    messagebox.showwarning("Aviso", f"A comanda {id_comanda} já está aberta!")
                    return
                else:
                    self.db.execute("DELETE FROM comandas_itens WHERE comanda_id = ?", (id_comanda,))
                    self.db.execute("DELETE FROM comandas WHERE id = ?", (id_comanda,))

            if messagebox.askyesno("Identificação", f"Identificar cliente na comanda {id_comanda}?"):
                ModalIdentificacao(
                    self.main.view, 
                    id_comanda, 
                    categoria.upper(), 
                    0.0, 
                    self.callback_finalizar_criacao
                )
            else:
                self.callback_finalizar_criacao(id_comanda, {
                    'nome': '', 'endereco': '', 'categoria': categoria.upper()
                })

    def callback_finalizar_criacao(self, id_comanda, dados, janela_modal=None):
        try:
            query = """
                INSERT INTO comandas (
                    id, categoria, status, total, 
                    cliente_nome_temp, endereco_entrega, telefone_temp, 
                    troco_para, forma_pagamento_entrega
                ) 
                VALUES (?, ?, 'ABERTO', 0.0, ?, ?, ?, ?, ?)
            """
            valores = (
                id_comanda,
                dados['categoria'].upper(),
                dados.get('nome', '').upper(),
                dados.get('endereco', '').upper(),
                dados.get('telefone', ''),
                dados.get('troco_para', 0),
                dados.get('forma_pagamento', 'NÃO INFORMADO').upper()
            )
            
            self.db.execute(query, valores)
            if hasattr(self.db, 'conn'): self.db.conn.commit()

            if janela_modal:
                janela_modal.destroy()

            self.atualizar_visual_comandas()
            
            # Inicializa no Service
            if hasattr(self.main, 'comanda_service'):
                dict_dados = {
                    'itens': [], 'total': 0.0, 'status': 'ABERTO', 
                    'categoria': dados['categoria'].upper()
                }
                self.main.comanda_service.comandas_abertas[id_comanda] = dict_dados

            self.gerenciar_comanda(id_comanda)
            
        except Exception as e:
            print(f"Erro ao criar comanda: {e}")
            messagebox.showerror("Erro", f"Falha ao criar: {e}")

    def receber_leitura_balanca(self, leitura):
        # Implementar se necessário
        pass

    def gerenciar_comanda(self, id_comanda):
        c = self.db.fetch_one("SELECT * FROM comandas WHERE id = ?", (id_comanda,))
        if not c: return

        itens_db = self.db.fetch_all("SELECT * FROM comandas_itens WHERE comanda_id = ?", (id_comanda,))
        
        dados = {
            "total": c['total'],
            "status": c['status'],
            "categoria": c.get('categoria', 'BALCÃO'),
            "itens": [
                {
                    "nome": i['nome_produto'], "qtd": i['quantidade'], 
                    "preco_unit": i['preco_unitario'], "total": i['total_item'],
                    "observacao": i.get('observacao', '')
                } for i in itens_db
            ]
        }
        
        if hasattr(self.main, 'comanda_service'):
            self.main.comanda_service.comandas_abertas[id_comanda] = dados.copy()
            self.main.comanda_service.carregar_carrinho(id_comanda)
        
        # --- CORREÇÃO DO ERRO 'object has no attribute root' ---
        # Tenta pegar o root corretamente, seja via view ou direto
        root_window = None
        if hasattr(self.main, 'view') and hasattr(self.main.view, 'root'):
            root_window = self.main.view.root
        elif hasattr(self.main, 'root'):
            root_window = self.main.root
        else:
            # Fallback se não achar
            root_window = self.main.view if hasattr(self.main, 'view') else None

        from app.views.popups.comanda_modal_view import ComandaModalView
        self.modal_comanda = ComandaModalView(root_window, id_comanda, dados, self)

    # ============================================================
    # 3. LÓGICA DE ITENS (MANIPULAÇÃO DA LISTA)
    # ============================================================
    
    def definir_obs_item(self, index, texto_obs):
        try:
            if not hasattr(self, 'modal_comanda') or not self.modal_comanda: return
            itens = self.modal_comanda.dados['itens']
            if 0 <= index < len(itens):
                itens[index]['observacao'] = texto_obs
        except Exception as e:
            print(f"ERRO AO DEFINIR OBS: {e}")

    def adicionar_item_comanda_direto(self, id_comanda, produto):
        try:
            if hasattr(self, 'modal_comanda') and self.modal_comanda:
                itens_lista = self.modal_comanda.dados['itens']
            else:
                return

            preco_real = float(produto.get('preco') or produto.get('preco_venda') or produto.get('preco_unit') or 0.0)
            qtd_real = float(produto.get('qtd', 1.0))
            nome_real = str(produto.get('nome') or produto.get('nome_produto') or "Item").strip()
            total_real = round(qtd_real * preco_real, 2)
            
            # ADICIONA SEMPRE UM NOVO (Não agrupa)
            novo_item_tela = {
                'id_produto': produto.get('id'), 
                'nome': nome_real, 
                'qtd': qtd_real, 
                'preco_unit': preco_real,
                'total': total_real, 
                'observacao': '',
                'is_balanca': produto.get('is_balanca', False)
            }
            
            itens_lista.append(novo_item_tela)
            
            if hasattr(self.main, 'comanda_service'):
                self.main.comanda_service.carrinho_atual.append(novo_item_tela)

            self._recalcular_total_modal()
                
        except Exception as e:
            print(f"ERRO AO ADICIONAR ITEM: {e}")
            import traceback
            traceback.print_exc()

    def alterar_qtd_comanda(self, index, delta):
        item = self.modal_comanda.dados['itens'][index]
        is_peso = item.get('is_balanca') or item.get('qtd') < 1
        passo = 0.1 if is_peso else 1
        
        nova_qtd = item["qtd"] + (passo * (1 if delta > 0 else -1))
        if nova_qtd >= 0.01:
            item["qtd"] = round(nova_qtd, 3)
            item["total"] = round(item["qtd"] * item["preco_unit"], 2)
            self._recalcular_total_modal()

    def definir_qtd_manual_comanda(self, index, novo_valor_str):
        try:
            nova_qtd = float(novo_valor_str.replace(',', '.'))
            item = self.modal_comanda.dados['itens'][index]
            item['qtd'] = round(nova_qtd, 3)
            item['total'] = round(item['qtd'] * item['preco_unit'], 2)
            self._recalcular_total_modal()
        except:
            self.modal_comanda.atualizar_lista_itens()

    def remover_item_comanda(self, index):
        self.modal_comanda.dados['itens'].pop(index)
        self._recalcular_total_modal()

    def _recalcular_total_modal(self):
        if hasattr(self.modal_comanda, 'dados'):
            total = sum(i['total'] for i in self.modal_comanda.dados['itens'])
            self.modal_comanda.dados['total'] = total
            if hasattr(self.modal_comanda, 'lbl_total'):
                self.modal_comanda.lbl_total.configure(text=f"TOTAL: R$ {total:.2f}")
            if hasattr(self.modal_comanda, 'atualizar_lista_itens'):
                self.modal_comanda.atualizar_lista_itens()

    # ============================================================
    # 4. FINALIZAÇÃO, CANCELAMENTO E STATUS
    # ============================================================

    def cancelar_comanda_total(self, id_comanda, modal_window):
        if messagebox.askyesno("Confirmar", f"Deseja EXCLUIR a comanda {id_comanda}?"):
            try:
                modal_window.cancelando = True
                self.db.execute("DELETE FROM comandas_itens WHERE comanda_id = ?", (id_comanda,))
                self.db.execute("DELETE FROM comandas WHERE id = ?", (id_comanda,))
                if modal_window.winfo_exists():
                    modal_window.destroy()
                self.atualizar_visual_comandas()
            except Exception as e:
                print(f"Erro ao excluir: {e}")

    def finalizar_comanda(self, id_comanda):
        self.salvar_dados_comanda_direto(id_comanda, self.modal_comanda.dados, janela_modal=None, imprimir=False)
        self.main.finalizar_comanda(id_comanda)

    def alterar_status_comanda(self, id_comanda, novo_status):
        try:
            if hasattr(self, 'modal_comanda') and self.modal_comanda:
                self.modal_comanda.dados['status'] = novo_status
                deve_imprimir = (novo_status == "EM PREPARO")
                self.salvar_dados_comanda_direto(id_comanda, self.modal_comanda.dados, janela_modal=None, imprimir=deve_imprimir)
            else:
                query = "UPDATE comandas SET status = ? WHERE id = ?"
                self.db.execute(query, (novo_status, id_comanda))
                if hasattr(self.db, 'conn'): self.db.conn.commit()
                self.atualizar_visual_comandas()
        except Exception as e:
            print(f"ERRO AO ALTERAR STATUS: {e}")

    def encerrar_comanda_definitivo(self, id_comanda):
        self.db.execute("UPDATE comandas SET status = 'FINALIZADO' WHERE id = ?", (id_comanda,))
        if hasattr(self.db, 'conn'): self.db.conn.commit()
        self.atualizar_visual_comandas()

    # ============================================================
    # 5. AUXILIARES DE RENDERIZAÇÃO
    # ============================================================

    def renderizar_botoes_produtos_modal(self, tabview, callback):
        if hasattr(self.main, 'produto_ctrl'):
            self.main.produto_ctrl.renderizar_botoes_produtos_modal(tabview, callback)

    def desenhar_linha_comanda_modal(self, scroll, idx, item):
        row = ctk.CTkFrame(scroll, fg_color="#2b2b2b")
        row.pack(fill="x", pady=2, padx=5)

        nome_display = item['nome']
        if item.get('observacao'):
            nome_display += f" ({item['observacao']})"

        ctk.CTkLabel(row, text=nome_display, width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        
        ent_qtd = ctk.CTkEntry(row, width=60, height=25, justify="center")
        val_qtd = f"{item['qtd']:.3f}" if item.get('is_balanca') or item['qtd'] < 1 else str(int(item['qtd']))
        ent_qtd.insert(0, val_qtd)
        ent_qtd.pack(side="left", padx=5)
        ent_qtd.bind("<Return>", lambda e, i=idx, v=ent_qtd: self.definir_qtd_manual_comanda(i, v.get()))

        ctk.CTkButton(row, text="-", width=30, height=25, fg_color="#c0392b", command=lambda i=idx: self.alterar_qtd_comanda(i, -1)).pack(side="left", padx=2)
        ctk.CTkButton(row, text="+", width=30, height=25, fg_color="#2980b9", command=lambda i=idx: self.alterar_qtd_comanda(i, 1)).pack(side="left", padx=2)

        ctk.CTkLabel(row, text=f"R$ {item['total']:.2f}", width=80, font=("Arial", 12, "bold"), text_color="#2ecc71").pack(side="left", padx=10)
        
        ctk.CTkButton(row, text="🗑️", width=35, height=25, fg_color="transparent", text_color="#e74c3c", hover_color="#3d3d3d",
                      command=lambda i=idx: self.remover_item_comanda(i)).pack(side="right", padx=5)

    def get_comanda_por_id(self, id_comanda):
        try:
            db = self.db if hasattr(self, 'db') else self.main.db
            cabecalho = db.fetch_one("SELECT * FROM comandas WHERE id = ?", (str(id_comanda),))
            if not cabecalho: return None
            itens = db.fetch_all("SELECT * FROM comandas_itens WHERE comanda_id = ?", (str(id_comanda),))
            dados = dict(cabecalho)
            dados['itens'] = []
            for i in itens:
                item_dict = dict(i)
                if 'nome' not in item_dict and 'nome_produto' in item_dict:
                    item_dict['nome'] = item_dict['nome_produto']
                if 'qtd' not in item_dict and 'quantidade' in item_dict:
                    item_dict['qtd'] = item_dict['quantidade']
                dados['itens'].append(item_dict)
            return dados
        except Exception as e:
            print(f"Erro ao buscar comanda: {e}")
            return None