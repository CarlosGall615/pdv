from tkinter import messagebox

class VendaController:
    
    def __init__(self, main_controller):
        # Usaremos self.main para ser curto e evitar erros de digitação
        self.main = main_controller  
        self.view = main_controller.view
        #self.db = main_controller.db

        self.caixa_model = main_controller.caixa_model
        self.clientes_model = main_controller.clientes_model
        self.venda_model = main_controller.venda_model

        self.produto_service = main_controller.produto_service
        self.cliente_atual_venda = None
        self.carrinho = []
        self.pagamentos_atuais = []
        self.venda_atual = None
        self.comanda_id_atual = None

    def adicionar_item_ao_carrinho(self, nome, qtd, preco_unit, produto_id=None, is_balanca=False):
        """Usa a lógica de agrupamento e força a atualização visual"""
        
        # --- CORREÇÃO DE SINCRONIZAÇÃO DO CAIXA ---
        # Se o ID no model estiver vazio, tenta recuperar do MainController
        if not self.caixa_model.sessao_id:
            if hasattr(self.main, 'sessao_atual') and self.main.sessao_atual:
                self.caixa_model.sessao_id = self.main.sessao_atual.get('id')
        
        # Se mesmo assim continuar vazio, aí sim bloqueia
        if not self.caixa_model.sessao_id:
            print("ERRO: Tentativa de venda com caixa fechado!")
            messagebox.showwarning("Caixa Fechado", "Abra o caixa antes de iniciar uma venda.")
            return

        # Garantir que qtd e preco sejam números
        try:
            qtd_num = float(str(qtd).replace(',', '.'))
            preco_num = float(str(preco_unit).replace(',', '.'))
        except ValueError:
            return

        # 1. TENTA AGRUPAR (Regra original)
        #if not is_balanca:
        #    for item in self.carrinho:
        #        mesmo_id = (produto_id is not None and item.get('id') == produto_id)
        #       mesmo_nome = (item.get('nome') == nome.upper())
         #       
         #       if (mesmo_id or mesmo_nome) and not item.get('is_balanca'):
          #          item['qtd'] += qtd_num
           #         item['total'] = round(item['qtd'] * item['preco_unit'], 2)
            #        self.atualizar_visual_carrinho()
             #       return

        # 2. SE NÃO AGRUPOU (Item novo ou Balança)
        novo_item = {
            'id': produto_id,
            'nome': nome.upper(),
            'qtd': qtd_num,
            'preco_unit': preco_num,
            'total': round(qtd_num * preco_num, 2),
            'is_balanca': is_balanca,
            'unidade': 'kg' if is_balanca else 'un',
            'observacao': ''
        }
        
        self.carrinho.append(novo_item)
        self.atualizar_visual_carrinho()

    def alterar_quantidade(self, index, delta):
        """Altera a quantidade baseada no índice numérico da lista"""
        try:
            if 0 <= index < len(self.carrinho):
                item = self.carrinho[index]
                nova_qtd = item["qtd"] + delta
                
                if nova_qtd >= 0.01:
                    item["qtd"] = round(nova_qtd, 3)
                    item["total"] = round(item["qtd"] * item["preco_unit"], 2)
                    self.atualizar_visual_carrinho()
                else:
                    self.remover_item(index)
        except Exception as e:
            print(f"Erro ao alterar quantidade: {e}")

    def remover_item(self, index):
        if 0 <= index < len(self.carrinho):
            self.carrinho.pop(index)
            self.atualizar_visual_carrinho()

    def atualizar_visual_carrinho(self):
        """Redesenha a lista de itens com busca profunda da interface e BLINDAGEM de dados"""
        try:
            pagina_pdv = None
            
            # 1. BUSCA PROFUNDA: Tenta encontrar a instância ativa da PdvView
            if hasattr(self.main, 'sistema_gestao'):
                # Primeiro tenta na view do gestao
                pagina_pdv = getattr(self.main.sistema_gestao.view, 'pagina_pdv', None)
                # Se não estiver lá, tenta no próprio controller
                if not pagina_pdv:
                    pagina_pdv = getattr(self.main.sistema_gestao, 'pagina_pdv', None)
            
            # Caminho B: No Main direto
            if not pagina_pdv:
                pagina_pdv = getattr(self.main, 'pagina_pdv', None)

            # 2. VALIDAÇÃO DA TELA
            if not pagina_pdv or not pagina_pdv.winfo_exists():
                return

            container = getattr(pagina_pdv, 'lista_carrinho_ui', None)
            if not container or not container.winfo_exists():
                return

            # 3. LIMPEZA E REDESENHO
            for w in container.winfo_children():
                w.destroy()

            for idx, item in enumerate(self.carrinho):
                # ==========================================================
                # BLINDAGEM DE DADOS (Resolve o erro 'preco_unit')
                # ==========================================================
                # Garante que 'preco_unit' exista, buscando alternativas se falhar
                if 'preco_unit' not in item:
                    # Tenta pegar de 'preco_venda', depois 'preco', ou assume 0.0
                    item['preco_unit'] = float(item.get('preco_venda') or item.get('preco') or 0.0)
                
                # Garante que 'total' exista
                if 'total' not in item:
                     qtd = float(item.get('qtd', 1))
                     item['total'] = qtd * item['preco_unit']

                # Garante chaves opcionais para não quebrar a view
                item.setdefault('unidade', 'un')
                item.setdefault('is_balanca', False)
                # ==========================================================

                is_peso = item.get('unidade') == 'kg' or item.get('is_balanca')
                incremento = 0.1 if is_peso else 1.0
                
                # Agora chamamos a View com o item sanitizado
                pagina_pdv.criar_linha_carrinho(
                    item=item,
                    cb_mais=lambda i=idx, inc=incremento: self.alterar_quantidade(i, inc),
                    cb_menos=lambda i=idx, inc=incremento: self.alterar_quantidade(i, -inc),
                    cb_remover=lambda i=idx: self.remover_item(i),
                    cb_manual=lambda valor, i=idx: self.definir_quantidade_manual(i, valor),
                    cb_obs=None,
                    container_pai=container 
                )
            
            # Atualiza Total
            total = sum(float(i.get('total', 0)) for i in self.carrinho)
            if hasattr(pagina_pdv, 'lbl_total') and pagina_pdv.lbl_total.winfo_exists():
                pagina_pdv.lbl_total.configure(text=f"TOTAL: R$ {total:.2f}")

        except Exception as e:
            print(f"Erro ao renderizar carrinho: {e}")
            import traceback
            traceback.print_exc()

    def definir_observacao_item(self, index, texto):
        """Atualiza a observação do item no carrinho sem redesenhar a tela inteira"""
        try:
            if 0 <= index < len(self.carrinho):
                self.carrinho[index]['observacao'] = texto
                print(f"DEBUG PDV: Item {index} atualizado com obs: {texto}")
        except Exception as e:
            print(f"Erro ao definir obs: {e}")


    def definir_quantidade_manual(self, index, novo_valor_str):
        try:
            nova_qtd = float(novo_valor_str.replace(',', '.'))
            if nova_qtd <= 0:
                return self.remover_item(index)

            item = self.carrinho[index]
            item['qtd'] = round(nova_qtd, 3)
            item['total'] = round(item['qtd'] * item['preco_unit'], 2)
            self.atualizar_visual_carrinho()
        except:
            self.atualizar_visual_carrinho()

    def limpar_venda(self):
        """Limpa os dados da venda e reseta o estado para o PDV voltar à espera"""
        self.carrinho = []
        self.pagamentos_atuais = []
        self.cliente_atual_venda = None
        # ESTA LINHA É A CHAVE PARA VOLTAR AO BOTÃO "INICIAR CUPOM"
        self.venda_atual = None 
        
        try:
            self.atualizar_visual_carrinho()
        except:
            pass

    def finalizar_venda(self, modal_pgto=None):
        """Finaliza a venda, salva no banco e limpa o carrinho"""
        try:
            total_venda = sum(item['total'] for item in self.carrinho)
            
            # Monta string de pagamentos (Ex: "DINHEIRO, PIX")
            formas = [p['metodo'] for p in self.pagamentos_atuais]
            forma_pagamento_str = " + ".join(formas)

            # Define usuário (se não tiver login, usa ADMIN)
            usuario_atual = getattr(self.main, 'usuario_atual', 'ADMIN')

            # Pega o ID da sessão do caixa (Obrigatório)
            sessao_id = self.caixa_model.sessao_id
            if not sessao_id:
                from tkinter import messagebox
                messagebox.showerror("Erro", "Caixa fechado! Abra o caixa antes de vender.")
                return False

            # ID do Cliente (se houver)
            cli_id = self.cliente_atual_venda['id'] if self.cliente_atual_venda else None

            # --- A CORREÇÃO PRINCIPAL ESTÁ AQUI ---
            # Antes estava self.caixa_model.registrar_venda (ERRADO)
            # Agora chamamos self.venda_model.registrar_venda (CERTO)
            sucesso = self.venda_model.registrar_venda(
                carrinho=self.carrinho,
                total=total_venda,
                forma_pagamento=forma_pagamento_str,
                usuario=usuario_atual,
                sessao_id=sessao_id,
                cliente_id=cli_id
            )

            if sucesso:
                # Se a venda veio de uma comanda, finalizamos ela agora
                if self.comanda_id_atual:
                    print(f"DEBUG: Finalizando comanda de origem ID {self.comanda_id_atual}")
                    # Chama o GestaoController ou ComandaController para encerrar a comanda
                    if hasattr(self.main, 'comanda_ctrl'):
                        self.main.comanda_ctrl.encerrar_comanda_definitivo(self.comanda_id_atual)
                    self.comanda_id_atual = None # Limpa vínculo

                # Limpa tudo para a próxima venda
                self.limpar_venda()
                
                # Fecha o modal de pagamento se existir
                if modal_pgto:
                    modal_pgto.destroy()
                
                # Atualiza a interface do PDV
                self.main.exibir_pdv() 
                
                from tkinter import messagebox
                messagebox.showinfo("Sucesso", "Venda Finalizada com Sucesso!")
                return True
            else:
                return False

        except Exception as e:
            print(f"ERRO AO FINALIZAR VENDA: {e}")
            import traceback
            traceback.print_exc()
            return False
        


    def executar_impressao(self, total):
        try:
            dict_pagamentos = {}
            for p in self.pagamentos_atuais:
                metodo = p['metodo']
                dict_pagamentos[metodo] = dict_pagamentos.get(metodo, 0) + p['valor']

            from app.services.impressao_service import ImpressaoService
            servico_impressao = ImpressaoService(largura_papel=38) 
            conteudo = servico_impressao.gerar_cupom_venda(
                itens=self.carrinho,
                total=total,
                pagamentos=dict_pagamentos,
                cliente=self.cliente_atual_venda
            )
            servico_impressao.imprimir_raw(conteudo)
        except Exception as e:
            print(f"Erro na impressão: {e}")

    def adicionar_pagamento_parcial(self, metodo, valor, total_venda):
        try:
            valor = float(str(valor).replace(",", "."))
        except ValueError: return False, "Valor inválido"

        pago_ate_agora = sum(p['valor'] for p in self.pagamentos_atuais)
        restante = round(total_venda - pago_ate_agora, 2)

        if valor <= 0: return False, "Valor deve ser > 0"
        
        if metodo == "Crediário":
            if valor > restante: return False, f"Não pode exceder R$ {restante:.2f}"
            sucesso, msg = self.validar_limite_crediario(valor)
            if not sucesso: return False, msg

        if metodo != "Dinheiro" and valor > restante:
            return False, f"Para {metodo}, o valor não pode exceder o restante."

        self.pagamentos_atuais.append({'metodo': metodo, 'valor': valor})
        novo_total_pago = sum(p['valor'] for p in self.pagamentos_atuais)
        return True, max(0, round(total_venda - novo_total_pago, 2))

    def validar_limite_crediario(self, valor_tentativa):
        if not self.cliente_atual_venda: return False, "Identifique um cliente."
        cliente_id = self.cliente_atual_venda['id']
        dados_cliente = self.clientes_model.buscar_por_id(cliente_id)
        if not dados_cliente: return False, "Cliente não encontrado."
        
        disponivel = float(dados_cliente.get('limite_credito', 0) or 0) - float(dados_cliente.get('saldo_devedor', 0) or 0)
        if valor_tentativa > disponivel:
            return False, f"Limite insuficiente! Disponível: R$ {disponivel:.2f}"
        return True, "Sucesso"

    def limpar_pagamentos_parciais(self):
        self.pagamentos_atuais = []


    # ============= BUSCAR COMANDAS POR ID ======================= #

    def processar_busca_pdv(self, codigo_ou_nome):
        """
        Tenta buscar produto. Se não achar e for número, tenta buscar Comanda.
        """
        if not codigo_ou_nome: return

        # 1. Tenta buscar produto (Lógica padrão)
        produto = self.main.produto_service.buscar_por_codigo_ou_nome(codigo_ou_nome)
        
        if produto:
            # Se achou produto, adiciona 1 unidade
            self.adicionar_item_ao_carrinho(produto['nome'], 1, produto['preco'], produto['id'])
            # Limpa o campo de busca na view
            if hasattr(self.view, 'pdv_view'):
                self.view.pdv_view.ent_busca_pdv.delete(0, 'end')
            return

        # 2. Se não é produto e é numérico, pode ser uma COMANDA
        if codigo_ou_nome.isdigit():
            id_comanda = int(codigo_ou_nome)
            self.importar_comanda(id_comanda)
        else:
            from tkinter import messagebox
            messagebox.showwarning("Não encontrado", "Produto ou Comanda não encontrados.")


    # No arquivo: app/controllers/venda_controller.py

    def importar_comanda(self, id_comanda):
        print(f"Tentando importar comanda {id_comanda}...")
        try:
            # 1. Garante acesso ao DB
            db = self.db if hasattr(self, 'db') else self.main.db

            # 2. Busca itens
            query_itens = "SELECT * FROM comandas_itens WHERE comanda_id = ?"
            itens_db = db.fetch_all(query_itens, (str(id_comanda),))
            
            if not itens_db:
                print("Comanda vazia ou não encontrada na tabela comandas_itens.")
                return

            # 3. Limpa o carrinho atual antes de importar
            self.carrinho = []

            # 4. Converte e adiciona ao carrinho
            for item in itens_db:
                # O banco chama a coluna de 'preco_unitario'
                val_unit = float(item['preco_unitario']) 
                val_qtd = float(item['quantidade'])
                val_total = float(item['total_item'])

                novo_item = {
                    'id': item['produto_id'],
                    'nome': item['nome_produto'],
                    
                    # O PDV precisa de 'preco_unit', então mapeamos o valor do banco para cá
                    'preco_unit': val_unit,   
                    'preco': val_unit,        # Backup
                    'preco_venda': val_unit,  # Backup 2
                    
                    'qtd': val_qtd,
                    'total': val_total,
                    'observacao': item.get('observacao', ''),
                    'unidade': 'un',
                    'is_balanca': False
                }
                
                # Debug para garantir que está certo
                print(f"DEBUG: Item importado: {novo_item['nome']} | Preço Unit: {novo_item['preco_unit']}")
                
                self.carrinho.append(novo_item)
            
            print(f"Comanda {id_comanda} importada com {len(self.carrinho)} itens.")
            
            # 5. Atualiza a View (PDV)
            # Verifica qual método sua view usa e chama o correto
            if hasattr(self.view, 'atualizar_lista_carrinho'):
                self.view.atualizar_lista_carrinho()
            elif hasattr(self, 'atualizar_visual_carrinho'):
                self.atualizar_visual_carrinho()
                
            if hasattr(self.view, 'atualizar_totais'):
                self.view.atualizar_totais()
            
            # 6. Fecha o modal de comandas
            if hasattr(self.view, 'modal_comandas') and self.view.modal_comandas:
                self.view.modal_comandas.destroy()

        except Exception as e:
            print(f"ERRO CRÍTICO AO IMPORTAR COMANDA: {e}")
            import traceback
            traceback.print_exc()